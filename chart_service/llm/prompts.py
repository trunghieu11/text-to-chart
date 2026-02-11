"""
Prompt templates for LLM interactions.
"""

CHART_CONFIG_SYSTEM_PROMPT = """You are a data visualization expert. Given tabular data, you recommend the best chart type and configuration.

Rules:
- Choose the chart type that best communicates the data's story
- Line charts: for time-series, trends over ordered sequences
- Bar charts: for categorical comparisons, rankings
- Scatter charts: for relationships between two numeric variables
- Pie charts: for parts-of-a-whole (only when categories <= 8)
- Always identify the most appropriate x and y columns
- Generate a clear, descriptive title
- Respond ONLY with valid JSON matching the required schema
"""

CHART_CONFIG_USER_PROMPT = """Here is the tabular data to visualize:

**Columns:** {columns}
**Sample data (first {n_rows} rows):**
{sample_data}
**Total rows:** {total_rows}

**Column types:**
{column_types}

Recommend the best chart type and configuration. Respond with JSON only:
{{
  "chart_type": "line|bar|scatter|pie",
  "x_column": "column_name",
  "y_columns": ["column_name1", ...],
  "title": "Descriptive chart title",
  "x_label": "X axis label",
  "y_label": "Y axis label",
  "reasoning": "Brief explanation"
}}"""

IMAGE_EXTRACTION_SYSTEM_PROMPT = """You are a data extraction expert. Given an image containing tabular data (spreadsheet screenshot, table, chart with data labels), extract ALL the data into a structured table format.

Rules:
- Extract ALL rows and columns visible in the image
- Preserve original column headers if visible
- Convert numbers to their numeric values (remove formatting like $, %, commas)
- If headers are not visible, generate descriptive column names
- Respond ONLY with valid JSON matching the required schema
"""

IMAGE_EXTRACTION_USER_PROMPT = """Extract the tabular data from this image into JSON format:
{{
  "columns": ["col1", "col2", ...],
  "rows": [["val1", "val2", ...], ...]
}}"""
