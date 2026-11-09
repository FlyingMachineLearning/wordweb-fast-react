from fastapi.testclient import TestClient
from main import app, analyze
client = TestClient(app)

def test_no_cross_document_or_sentence_edges():
    graph = analyze([("a", "alpha beta. gamma delta"), ("b", "epsilon zeta")], min_count=1)
    pairs = {(x["source"],x["target"]) for x in graph["links"]}
    assert ("alpha", "beta") in pairs
    assert ("beta", "gamma") not in pairs
    assert ("delta", "epsilon") not in pairs

def test_window_uses_original_positions():
    graph = analyze([("a", "alpha is in the beta")], window=2, min_count=1)
    assert graph["links"] == []

def test_ingestion_and_filters():
    response = client.post("/api/analyze", files=[("files", ("notes.txt", b"Data connects ideas. Data supports research."))], data={"min_count":1,"extra_stopwords":"ideas"})
    assert response.status_code == 200
    nodes = {n["id"]:n for n in response.json()["nodes"]}
    assert nodes["data"]["count"] == 2
    assert "ideas" not in nodes

def test_invalid_and_empty():
    for name, content in [("bad.exe", b"anything"), ("empty.txt", b"")]:
        assert client.post("/api/analyze",files={"files":(name,content)}).status_code == 400
    assert client.post("/api/analyze",files={"files":("ok.txt",b"hello world")},data={"window":50}).status_code == 400

def test_docx_and_pdf():
    import io
    from docx import Document
    from pypdf import PdfWriter
    doc=Document();doc.add_paragraph("Network network documents")
    buffer=io.BytesIO();doc.save(buffer)
    assert client.post("/api/analyze",files={"files":("sample.docx",buffer.getvalue())}).status_code == 200
    pdf=PdfWriter();pdf.add_blank_page(width=100,height=100)
    buffer=io.BytesIO();pdf.write(buffer)
    assert client.post("/api/analyze",files={"files":("blank.pdf",buffer.getvalue())}).status_code == 400
