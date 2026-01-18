# Nebras Financial Analysis Server

This is the FastAPI backend for the Nebras Financial Analysis application. It provides endpoints for file analysis and PDF report generation.

## 1. Setup

### Prerequisites

- Python 3.8+
- [Node.js](https://nodejs.org/) (for Playwright dependencies)

### Installation

1.  **Create/Activate Virtual Environment**:

    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

2.  **Install Python Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright Browsers (One-time setup)**:
    This is required for PDF generation.
    ```bash
    python -m playwright install chromium
    ```

## 2. Running the Server

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`.

## 3. Reports

Generated PDF reports are stored in the `reports/` directory.

- **Directory**: `server/reports/`
- **Access**: PDFs are served via `GET /reports/{filename}`.

## 4. API Endpoints

- `GET /health`: Health check.
- `POST /api/analyze`: Accepts a CSV/Excel file and returns analysis JSON + PDF URL.
