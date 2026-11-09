# Wordweb

React + FastAPI document explorer. Upload documents and explore an interactive word co-occurrence network. No AI key required.

## Start on Windows, macOS, or Linux

Install **Node.js 22+** and **Python 3.12+**, then open a terminal in this folder (the one containing this README and the root `package.json`).

```powershell
npm install
npm run dev
```

Open **http://localhost:5173**. Keep the terminal open; **Ctrl+C stops both servers**.

The first `npm install` automatically creates `.venv`, installs FastAPI and document readers, and installs the React frontend. It can take a few minutes and requires an internet connection. Later launches only need `npm run dev`. No virtual-environment activation, administrator privileges, or separate backend terminal is needed.

### If setup reports that Python is missing

Install Python from https://www.python.org/downloads/ and enable **Add Python to PATH** if the installer offers it. Close and reopen PowerShell, return to this folder, and retry `npm install`. On Windows the setup also detects the Python launcher (`py -3`).

To select a specific Python installation in PowerShell:

```powershell
$env:WORDWEB_PYTHON = 'C:\path\to\python.exe'
npm install
```

If npm lifecycle scripts are disabled on your machine, run `npm run setup` after `npm install`. If PowerShell blocks `npm.ps1`, use `npm.cmd install` and `npm.cmd run dev`.

### Commands from the root folder

| Command | Action |
| --- | --- |
| `npm install` | Install the frontend and set up Python automatically |
| `npm run setup` | Retry setup or install changed backend requirements |
| `npm run dev` | Start React and FastAPI together |
| `npm run build` | Build React into `frontend/dist` |
| `npm test` | Run backend tests |

FastAPI listens on http://127.0.0.1:8000; API documentation is at http://localhost:8000/docs. Vite proxies `/api` requests to FastAPI. The launcher checks ports 5173 and 8000 before starting and reports conflicts. The build command creates frontend assets; it does not start a production API server.

## Features

- UTF-8 TXT/Markdown, text-based PDF, and DOCX (paragraphs and tables).
- Multi-file analysis; per-word source document attribution.
- Frequency-based node sizes; weighted co-occurrence links.
- Draggable nodes, zoom, search, keyboard-selectable words, neighbor highlighting.
- Context window, minimum frequency, maximum node count, custom stopwords.
- Immediate link-strength filtering and JSON graph export.
- Responsive UI with a clearly marked example graph before your first upload.

## Methodology

Words are lowercased and tokenized with Unicode letters. English stopwords and words shorter than three characters are omitted from the graph. Counts are raw occurrences. Links count pairs of different eligible words appearing within the next N **original token positions**, within the same sentence or line and document. Repeated pairs increase weight. Nodes are the most frequent eligible words after minimum-count filtering. There is no stemming, lemmatization, entity resolution, semantic embedding, or OCR. Sentence splitting is punctuation-based and treats abbreviations approximately. Search highlights nodes; it does not alter the exported graph. Link filtering affects the view only; export contains the full latest analysis.

## Limits and deployment

10 files per request, 10 MB per file, 25 MB total upload, 300 PDF pages per file, 1 million extracted characters per file, 2 million total; up to 150 nodes. PDF must contain selectable text. Password-protected or malformed documents return an error. Files are processed in backend memory and discarded; the browser retains the graph until refresh. Uploads are sent to whichever server hosts your backend. Fonts optionally load from Google Fonts, with local system fallbacks.

This is a local/single-user starter, with no authentication, database, OCR, rate limiting, or background job queue. Parsing untrusted documents is resource intensive: place the API behind authentication, request-size limits, worker resource limits, and rate limiting before exposing it publicly. Application upload limits are enforced after multipart parsing; production hosting should also impose request-size limits at a reverse proxy. For heavy corpora, move extraction to sandboxed background workers. Do not expose the backend port publicly without appropriate access controls.

## Verify

```sh
npm test
npm run build
```

GitHub Actions runs backend tests and the frontend production build.

## Add to GitHub

Create an empty repository named `wordweb` in your GitHub account, then run these commands from this folder (replace `YOUR_USERNAME`):

```sh
git init -b main
git add .
git commit -m "Build Wordweb document network explorer"
git remote add origin https://github.com/YOUR_USERNAME/wordweb.git
git push -u origin main
```

Or, with the GitHub CLI installed and authenticated:

```sh
git init -b main
git add .
git commit -m "Build Wordweb document network explorer"
gh repo create wordweb --private --source=. --remote=origin --push
```

No license has been selected; add one before distributing under open-source terms.
