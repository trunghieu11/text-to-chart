# Text-to-Chart

Convert text, CSV, Excel, and images into beautiful charts instantly. Supports automatic chart type selection via AI or rule-based logic.

## Features

- **Flexible Input**: Paste raw text (tab/comma/space separated), upload CSV, Excel (.xlsx/.xls), or even images of tables
- **Smart Chart Selection**: AI-powered (OpenAI) or rule-based chart type inference
- **Multiple Chart Types**: Line, Bar, Scatter, Pie -- extensible via registry pattern
- **Three Export Formats**: Embeddable HTML link, PNG image, reproducible Python code
- **REST API**: Full-featured API with authentication, rate limiting, and OpenAPI docs
- **Web UI**: Streamlit-powered web interface for interactive chart creation
- **CLI**: Command-line tool for quick chart generation
- **Extensible Architecture**: Registry patterns for parsers, chart types, plotters, and add-ons

## Quick Start

### 1. Install Dependencies

```bash
cd text_to_chart
pip install -r requirements.txt
```

### 2. Configure Environment (optional)

```bash
cp .env.example .env
# Edit .env with your settings (e.g., OPENAI_API_KEY for AI features)
```

### 3. Run the CLI

```bash
# From text input
python cli.py chart --text "Month\tSales\nJan\t100\nFeb\t150\nMar\t200" --output chart.png

# From CSV file
python cli.py chart --input data.csv --output chart.png

# Auto-detect chart type and open in browser
python cli.py chart --input data.csv

# Specify chart type
python cli.py chart --text "A\tB\n1\t10\n2\t20" --type scatter --output scatter.png
```

### 4. Run the REST API

```bash
uvicorn api.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 5. Run the Web UI

```bash
streamlit run streamlit_app/app.py --server.port 5001
```

Web UI available at: `http://localhost:5001`

## API Reference

### Authentication

Set API keys via environment variable:

```bash
export API_KEYS="key1,key2,key3"
```

Include in requests:

```bash
-H "X-API-Key: your-key"
```

If `API_KEYS` is not set, the API runs in development mode (no auth required).

### Endpoints

#### Create Chart

```bash
# From text data
curl -X POST http://localhost:8000/v1/charts \
  -H "X-API-Key: your-key" \
  -F "data=Month,Sales
Jan,100
Feb,150
Mar,200" \
  -F "chart_type=auto"

# From file upload
curl -X POST http://localhost:8000/v1/charts \
  -H "X-API-Key: your-key" \
  -F "file=@data.csv" \
  -F "chart_type=bar" \
  -F "title=Monthly Sales"
```

**Response:**

```json
{
  "id": "uuid-here",
  "embed_url": "http://localhost:8000/v1/charts/uuid-here/embed",
  "chart_type": "bar",
  "title": "Monthly Sales",
  "created_at": "2025-01-01T00:00:00+00:00"
}
```

#### Get Chart Metadata

```bash
curl http://localhost:8000/v1/charts/{id} -H "X-API-Key: your-key"
```

#### Get Chart Image (PNG)

```bash
curl http://localhost:8000/v1/charts/{id}/image \
  -H "X-API-Key: your-key" \
  --output chart.png
```

#### Get Embeddable HTML

```bash
curl http://localhost:8000/v1/charts/{id}/embed
```

Note: The embed endpoint is public (no auth) for easy embedding.

#### Get Reproducible Python Code

```bash
curl http://localhost:8000/v1/charts/{id}/code -H "X-API-Key: your-key"
```

#### Check Usage

```bash
curl http://localhost:8000/v1/usage -H "X-API-Key: your-key"
```

#### Health Check

```bash
curl http://localhost:8000/health
```

### Rate Limiting

Default: 60 requests/minute per API key. Configure via:

```bash
export RATE_LIMIT="100/minute"
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key for AI features | (empty) |
| `LLM_MODEL` | LLM model for chart type inference | `gpt-4o-mini` |
| `VISION_MODEL` | Vision model for image parsing | `gpt-4o` |
| `API_KEYS` | Comma-separated valid API keys | (empty = no auth) |
| `RATE_LIMIT` | Rate limit per API key | `60/minute` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |
| `UI_HOST` | Streamlit UI host | `0.0.0.0` |
| `UI_PORT` | Streamlit UI port | `5001` |
| `CHART_TTL_HOURS` | Chart expiry time in hours | `24` |
| `USAGE_DB_PATH` | SQLite path for usage tracking | `usage.db` |
| `CHART_TEMPLATE` | Default Plotly template | `plotly_white` |

## Architecture

```
text_to_chart/
├── chart_service/          # Core chart service
│   ├── models.py           # ChartConfig, ParsedData
│   ├── parsers/            # Parser registry + implementations
│   ├── chart_types/        # Chart type registry + implementations
│   ├── plotters/           # Plotter registry + add-ons
│   ├── llm/                # LLM integration (OpenAI)
│   └── exporters/          # Embed, image, code exporters
├── api/                    # FastAPI REST API
│   ├── main.py             # App entry point
│   ├── routers/            # API routes
│   ├── middleware/          # Auth & rate limiting
│   ├── models.py           # Pydantic models
│   ├── storage.py          # Chart storage
│   └── usage.py            # Usage tracking
├── streamlit_app/          # Streamlit Web UI
│   ├── app.py              # App entry point
├── cli.py                  # CLI interface
├── config.py               # Configuration management
├── tests/                  # Unit & integration tests
├── requirements.txt        # Python dependencies
└── pyproject.toml          # Project metadata
```

### Design Patterns

- **Registry Pattern**: Parsers, chart types, and plotters use registries for extensibility
- **Add-on Pipeline**: Plotters support composable add-ons (color palette, reference lines, layout)
- **Modular Monolith**: Single deployable with clear module boundaries

### Adding a New Parser

```python
# chart_service/parsers/json_parser.py
from chart_service.parsers.base import BaseParser

class JsonParser(BaseParser):
    name = "json"
    supported_extensions = [".json"]

    def can_handle(self, raw_input, filename=None):
        ...

    def parse(self, raw_input, filename=None):
        ...
```

### Adding a New Chart Type

```python
# chart_service/chart_types/histogram_chart.py
from chart_service.chart_types.base import ChartType

class HistogramChartType(ChartType):
    name = "histogram"
    display_name = "Histogram"

    def is_suitable_for(self, df, config=None):
        ...

    def get_default_config(self, df):
        ...
```

## Running Tests

```bash
pytest tests/ -v
```

## License

MIT
