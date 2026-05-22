# Metadata Checker

Upload a PDF, image, or DOCX file and get a structured report showing extracted metadata, suspicious pattern findings, and a risk score.

## Stack

Python, FastAPI, PyMuPDF, ReportLab, React, Vite, TypeScript, Tailwind

## Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## What it checks

- Date inconsistencies (missing, impossible order, large gaps)
- Creator and producer tool mismatches
- Known editing software in metadata
- XMP vs document info conflicts
- Incremental PDF updates via raw byte scan

## Scoring

Findings are weighted by severity and confidence, with diminishing returns so weak signals don't stack into false alarms. Common workflow patterns like tool mismatches carry a discount unless backed by a stronger signal.

Risk levels: Low (0-30), Medium (31-65), High (66-100)

## Limitations

This tool reads metadata, not document content. It surfaces signals, not verdicts.
