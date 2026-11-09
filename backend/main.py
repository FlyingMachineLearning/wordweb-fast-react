"""Bounded, in-memory document analysis. No uploads are persisted."""
import io
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from docx import Document

app = FastAPI(title="Wordweb API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET", "POST"], allow_headers=["*"])
STOP = set("a an the and or but if then than of to in on at by for with from as is are was were be been being it its this that these those i me my we our you your he she they them their his her not no do does did have has had can could will would should may might must also into about more most some any all each such very just out up so which who what when where how there here through over under between within only other both same own".split())
MAX_BYTES = 10 * 1024 * 1024
MAX_TEXT = 1_000_000

def extract(name: str, data: bytes) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in {".txt", ".md"}:
        return data.decode("utf-8-sig")
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > 300:
            raise ValueError("PDF limit: 300 pages per file.")
        chunks, total = [], 0
        for page in reader.pages:
            text = page.extract_text() or ""
            total += len(text)
            if total > MAX_TEXT:
                raise ValueError("Extracted text exceeds 1 million characters.")
            chunks.append(text)
        return "\n".join(chunks)
    if suffix == ".docx":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(i.file_size for i in archive.infolist()) > 30 * 1024 * 1024:
                raise ValueError("DOCX expands beyond the 30 MB limit.")
        doc = Document(io.BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs] + [c.text for t in doc.tables for r in t.rows for c in r.cells])
    raise ValueError("Supported formats: PDF, DOCX, TXT, Markdown.")

def analyze(documents, window=5, min_count=2, max_nodes=80, extra_stopwords=""):
    stop = STOP | set(re.findall(r"[^\W\d_]+", extra_stopwords.lower()))
    counts, edges, sources = Counter(), Counter(), defaultdict(set)
    total_tokens = 0
    for doc_id, (name, text) in enumerate(documents):
        # Punctuation boundaries prevent links across sentences; documents never mix.
        for sentence in re.split(r"[.!?;\n]+", text):
            tokens = re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)?", sentence.lower())
            total_tokens += len(tokens)
            for token in tokens:
                if len(token) > 2 and token not in stop:
                    counts[token] += 1
                    sources[token].add(doc_id)
            for i, left in enumerate(tokens):
                if len(left) <= 2 or left in stop:
                    continue
                for right in tokens[i+1:i+window+1]:
                    if right != left and len(right) > 2 and right not in stop:
                        edges[tuple(sorted((left, right)))] += 1
    selected = {word for word, n in counts.most_common() if n >= min_count}
    selected = set(sorted(selected, key=lambda w: (-counts[w], w))[:max_nodes])
    links = [{"source": a, "target": b, "weight": n} for (a,b),n in edges.most_common() if a in selected and b in selected]
    return {"nodes": [{"id": w, "count": counts[w], "documents": [documents[i][0] for i in sorted(sources[w])]} for w in sorted(selected, key=lambda w: (-counts[w],w))], "links": links, "stats": {"documents": len(documents), "tokens": total_tokens, "unique_words": len(counts), "displayed_words": len(selected)}}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/analyze")
async def upload(files: list[UploadFile] = File(...), window: int = Form(5), min_count: int = Form(2), max_nodes: int = Form(80), extra_stopwords: str = Form("")):
    try:
        if not 1 <= len(files) <= 10:
            raise HTTPException(400, "Upload between 1 and 10 files.")
        if not (2 <= window <= 20 and 1 <= min_count <= 100 and 10 <= max_nodes <= 150):
            raise HTTPException(400, "Invalid graph parameters.")
        documents, total = [], 0
        for file in files:
            data = await file.read(MAX_BYTES + 1)
            total += len(data)
            if len(data) > MAX_BYTES or total > 25 * 1024 * 1024:
                raise HTTPException(413, "Limit: 10 MB per file and 25 MB total.")
            try:
                text = extract(file.filename or "", data)
            except Exception as exc:
                raise HTTPException(400, f"Could not read {file.filename}. Use a valid, unencrypted PDF, DOCX, or UTF-8 text file.") from exc
            if len(text) > MAX_TEXT:
                raise HTTPException(413, "Limit: 1 million extracted characters per file.")
            if not text.strip():
                raise HTTPException(400, f"No text found in {file.filename}. Scanned PDFs require OCR first.")
            documents.append((file.filename or "Untitled", text))
        if sum(len(t) for _, t in documents) > 2_000_000:
            raise HTTPException(413, "Limit: 2 million extracted characters total.")
        return analyze(documents, window, min_count, max_nodes, extra_stopwords)
    finally:
        for file in files:
            await file.close()
