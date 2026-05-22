# Metadata Checker

A full-stack tool to upload PDFs, images, and DOCX files, extract embedded metadata, detect privacy and tampering signals, and present a risk score with both simple and technical views.

## Screenshots

## Philosophy

The application is calibrated to **under-flag** rather than over-flag — confidence thresholds are conservative to avoid false alarms on legitimate documents.

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```
