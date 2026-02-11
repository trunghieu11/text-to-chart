# Text-to-Chart — Usage Guide

This document gives step-by-step instructions for using Text-to-Chart: CLI, REST API, Web UI, Developer Portal, and Admin UI.

---

## Overview

**Text-to-Chart** turns text, CSV, Excel, or images into charts. You can use it as an **end user** (CLI or Web UI), as a **developer** (REST API or Developer Portal to get API keys), or as an **administrator** (Admin UI to manage tenants and usage). For technical details (stack, architecture, how to add parsers or chart types), see [DEVELOPMENT.md](DEVELOPMENT.md).

---

## Prerequisites

- **Python 3.10+** and **pip**
- **Optional:** [OpenAI API key](https://platform.openai.com/api-keys) for:
  - “Let AI decide” chart type in the Web UI
  - `chart_type=auto` in the API/CLI
  - Image-to-table parsing (photos of tables)

Without an OpenAI key, rule-based chart selection and all chart types (line, bar, scatter, pie) still work when you choose the type explicitly.

---

## Installation

1. **Get the project** (clone or download) and go to the project root:

   ```bash
   cd text_to_chart
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Optional — configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env (e.g. OPENAI_API_KEY, API_KEYS, ADMIN_USERNAME/ADMIN_PASSWORD)
   ```

   The app loads `.env` automatically when you run the CLI, API, or any Streamlit app.

---

## Configuration

Copy [.env.example](../.env.example) to `.env` in the project root and set values as needed.

| Variable | When you need it | Description |
|----------|------------------|-------------|
| `OPENAI_API_KEY` | AI chart type or image parsing | OpenAI API key |
| `LLM_MODEL` | Override default LLM | e.g. `gpt-4o-mini` |
| `VISION_MODEL` | Override vision model | e.g. `gpt-4o` |
| `API_KEYS` | API auth (env fallback) | Comma-separated keys; empty = dev (no auth) |
| `RATE_LIMIT` | API rate limit (env fallback) | e.g. `60/minute` |
| `API_HOST`, `API_PORT` | Run API on different host/port | Default `0.0.0.0:8000` |
| `UI_HOST`, `UI_PORT` | Streamlit Web UI | Default port 5001 |
| `CHART_TTL_HOURS` | Chart expiry | Default 24 |
| `USAGE_DB_PATH` | Usage DB path | Default `usage.db` |
| `SAAS_DB_PATH` | SaaS DB (tenants, keys) | Default `saas.db` |
| `JWT_SECRET` | Developer Portal / account JWTs | Change in production |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Admin UI login | Required for Admin UI |
| `API_BASE_URL` | Developer Portal / Admin UI | API base URL; default `http://localhost:8000` |
| `CHART_TEMPLATE` | Plotly template | Default `plotly_white` |

---

## Using the CLI

Run from the **project root**. You must provide either a file (`--input`) or raw text (`--text`).

**Chart from a file (CSV, Excel, or text):**

```bash
python cli.py chart --input data.csv --output chart.png
```

**Chart from raw text (tab/comma/space separated):**

```bash
python cli.py chart --text "Month,Sales
Jan,100
Feb,150
Mar,200" --output chart.png
```

On the command line, you can use `\t` and `\n` in `--text`:

```bash
python cli.py chart --text "Month\tSales\nJan\t100\nFeb\t150" --type bar --output out.png
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--input` | `-i` | Path to input file (CSV, Excel, TXT) |
| `--text` | `-t` | Raw text input |
| `--output` | `-o` | Output PNG path; if omitted, chart opens in browser |
| `--type` | `-T` | Chart type: `auto`, `line`, `bar`, `scatter`, `pie` (default: `auto`) |
| `--title` | | Chart title |

**Examples:**

```bash
# Save to file
python cli.py chart --input data.csv --type line --output chart.png

# Open in browser (no --output)
python cli.py chart --input data.csv

# Custom title
python cli.py chart --text "A,B\n1,10\n2,20" --type scatter --title "My Chart" --output scatter.png
```

---

## Using the REST API

**1. Start the API server:**

```bash
uvicorn api.main:app --reload --port 8000
```

- API base: `http://localhost:8000`
- Interactive docs: **http://localhost:8000/docs**
- ReDoc: http://localhost:8000/redoc

**2. Authentication**

- **Development:** If `API_KEYS` is not set in `.env`, the API runs without auth (no key required).
- **With API keys:** Set `API_KEYS=key1,key2` in `.env` and send:
  ```bash
  -H "X-API-Key: your-key"
  ```
- **SaaS (Developer Portal):** Register → log in → create an API key in the portal, then use that key in `X-API-Key`. Tenant keys use plan-based rate limits and quotas.

**3. Create a chart**

From **text data** (form field `data`):

```bash
curl -X POST http://localhost:8000/v1/charts \
  -H "X-API-Key: your-key" \
  -F "data=Month,Sales
Jan,100
Feb,150
Mar,200" \
  -F "chart_type=bar" \
  -F "title=Monthly Sales"
```

From **file upload** (field `file`):

```bash
curl -X POST http://localhost:8000/v1/charts \
  -H "X-API-Key: your-key" \
  -F "file=@data.csv" \
  -F "chart_type=line" \
  -F "title=My Chart"
```

Use `chart_type=auto` for AI-based selection (requires `OPENAI_API_KEY`).

**Response:** JSON with `id`, `embed_url`, `chart_type`, `title`, `created_at`.

**4. Get chart metadata**

```bash
curl http://localhost:8000/v1/charts/{id} -H "X-API-Key: your-key"
```

**5. Get chart as PNG**

```bash
curl http://localhost:8000/v1/charts/{id}/image \
  -H "X-API-Key: your-key" \
  --output chart.png
```

**6. Get embeddable HTML** (no auth)

```bash
curl http://localhost:8000/v1/charts/{id}/embed
```

**7. Get reproducible Python code**

```bash
curl http://localhost:8000/v1/charts/{id}/code -H "X-API-Key: your-key"
```

**8. Check usage**

```bash
curl http://localhost:8000/v1/usage -H "X-API-Key: your-key"
```

**9. Health check** (no auth)

```bash
curl http://localhost:8000/health
```

---

## Using the Web UI

**1. Start the Web UI:**

```bash
streamlit run streamlit_app/app.py --server.port 5001
```

Open **http://localhost:5001** in your browser.

**2. Provide data**

- **Paste** tab- or comma-separated text into the text area, or  
- **Upload** a file (CSV, Excel, or image of a table).

**3. Choose chart type**

- Pick **Let AI decide** (needs `OPENAI_API_KEY`), or  
- Choose **Line**, **Bar**, **Scatter**, or **Pie**.

**4. Generate and export**

- View the chart and parsed data table.
- Use **Embed URL** to get a link for embedding.
- Use **PNG** to download the image.
- Use **Python code** to get reproducible Plotly code.

---

## Using the Developer Portal

The Developer Portal lets users register, log in, create API keys, and view usage. The **API must be running** (e.g. `uvicorn api.main:app --port 8000`).

**1. Start the Developer Portal:**

```bash
streamlit run developer_portal/app.py --server.port 5002
```

Open **http://localhost:5002**.

**2. Set API base (if needed)**

If the API is not at `http://localhost:8000`, set the `API_BASE_URL` environment variable (or in `.env`) before starting the portal.

**3. Register**

- Use **Register**: email, password, name.
- On success you receive a JWT and are logged in.

**4. Log in** (if you already have an account)

- Use **Login** with email and password to get a JWT.

**5. Dashboard**

- **API Keys:** Create a key (name optional); the **full key is shown once** — copy and store it. List keys (masked) and revoke as needed.
- **Usage:** View current period and history.
- **Account:** View plan (e.g. free) and account info.
- **Docs:** Link to the API Swagger UI (`/docs`).

Use the created API key in the `X-API-Key` header when calling the REST API.

---

## Using the Admin UI

The Admin UI is for operators: list tenants, change status/plan, manage keys, view usage. You must set **ADMIN_USERNAME** and **ADMIN_PASSWORD** in `.env`.

**1. Start the Admin UI:**

```bash
streamlit run admin_ui/app.py --server.port 5003
```

Open **http://localhost:5003**.

**2. Log in**

- Use the admin username and password from `.env`.

**3. Tenants**

- **List:** See all tenants (name, plan, status, created).
- **Search/filter** as available in the UI.
- **Detail:** Click a tenant to see:
  - **Status:** Suspend or reactivate.
  - **Plan:** Change plan (e.g. free, pro, enterprise).
  - **Keys:** List keys (masked), create a key, revoke a key.
  - **Usage:** View current month and history.

---

## Running tests

From the project root:

```bash
pytest tests/ -v
```

**Note:** Account and admin tests require **bcrypt** (e.g. `pip install bcrypt` or `passlib[bcrypt]`). If bcrypt is not installed, those tests are skipped.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| **Chart doesn’t open in browser (CLI)** | Ensure you didn’t pass `--output`. Some environments may need a default browser set. |
| **401 from API** | Missing or invalid `X-API-Key`; or for account routes, missing/expired JWT. Check key or log in again in the Developer Portal. |
| **403 from API** | Same as 401 for Bearer auth: invalid or missing token. |
| **Admin UI shows 503 or “Admin auth not configured”** | Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`. |
| **AI chart type / “Let AI decide” not working** | Set `OPENAI_API_KEY` in `.env`. |
| **Developer Portal can’t reach API** | Ensure the API is running and set `API_BASE_URL` if it’s not at `http://localhost:8000`. |
| **Quota exceeded (429)** | Tenant’s monthly quota is exceeded; wait for next period or change plan in Admin UI. |

For more on architecture and extending the project (parsers, chart types), see the main [README](../README.md).
