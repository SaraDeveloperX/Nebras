# API Reference

RESTful API for the Nebras financial analysis platform.

---

## Base URL

```
http://localhost:8000
```

---

## Rate Limiting

| Mode     | Daily Limit       |
| -------- | ----------------- |
| Standard | 1 request per IP  |
| Demo     | 2 requests per IP |

Exceeded limits return `429 Too Many Requests`.

---

## Endpoints

### Analyze Document

Upload a financial file for analysis.

```
POST /api/analyze
```

**Content-Type:** `multipart/form-data`

**Parameters:**

| Name      | Type   | Required | Description                   |
| --------- | ------ | -------- | ----------------------------- |
| `file`    | File   | Yes      | CSV, XLSX, or XLS. Max 10 MB. |
| `concern` | String | No       | Optional analysis context     |
| `is_demo` | String | No       | `"1"` for demo rate limits    |

**Success Response (200):**

```json
{
  "summary": "Executive summary text...",
  "kpis": [
    {
      "name": "Total Revenue",
      "value": "1,250,000",
      "delta": "+12.5%",
      "insight": "Positive growth trend."
    }
  ],
  "risks": ["Marketing expenses at 42% of total costs."],
  "recommendations": ["Review marketing ROI."],
  "report_pdf_url": "/reports/report_20260119.pdf"
}
```

**Response Fields:**

| Field             | Type   | Description                |
| ----------------- | ------ | -------------------------- |
| `summary`         | String | Executive summary          |
| `kpis`            | Array  | Key performance indicators |
| `risks`           | Array  | Identified risks           |
| `recommendations` | Array  | Strategic recommendations  |
| `report_pdf_url`  | String | PDF download URL           |

---

### Get Report

Download a generated PDF.

```
GET /reports/{filename}
```

**Parameters:**

| Name       | Type   | Required | Description                           |
| ---------- | ------ | -------- | ------------------------------------- |
| `filename` | String | Yes      | Report filename from analyze response |

**Success Response (200):**

Returns PDF binary with `Content-Type: application/pdf`

---

### Health Check

Verify API availability.

```
GET /health
```

**Success Response (200):**

```json
{
  "ok": true
}
```

---

## Error Responses

| Status | Description                            |
| ------ | -------------------------------------- |
| 400    | Invalid file format or missing columns |
| 413    | File exceeds 10 MB limit               |
| 429    | Rate limit exceeded                    |
| 404    | Report not found                       |
| 500    | Processing error                       |

**Error Format:**

```json
{
  "detail": "Error description."
}
```

---

## File Requirements

**Supported Types:**

| Extension | MIME Type                                                           |
| --------- | ------------------------------------------------------------------- |
| `.csv`    | `text/csv`                                                          |
| `.xlsx`   | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `.xls`    | `application/vnd.ms-excel`                                          |

**Column Requirements:**

| Schema       | Required Columns         |
| ------------ | ------------------------ |
| Transactions | Date, Amount             |
| P&L          | Month, Revenue, Expenses |

Column names are flexible—common variants recognized automatically.

---

## CORS

**Allowed Origins:**

- `http://localhost:5173`
- Production domains as configured

**Allowed Methods:** GET, POST, OPTIONS
