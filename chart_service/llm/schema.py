"""
JSON schema for LLM chart config responses.
"""

# JSON Schema that the LLM should conform to when suggesting chart configuration
CHART_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "chart_type": {
            "type": "string",
            "enum": ["line", "bar", "scatter", "pie"],
            "description": "The recommended chart type for the data.",
        },
        "x_column": {
            "type": "string",
            "description": "The column to use for the x-axis (or names for pie chart).",
        },
        "y_columns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The column(s) to use for the y-axis (or values for pie chart).",
        },
        "title": {
            "type": "string",
            "description": "A descriptive title for the chart.",
        },
        "x_label": {
            "type": "string",
            "description": "Label for the x-axis.",
        },
        "y_label": {
            "type": "string",
            "description": "Label for the y-axis.",
        },
        "reasoning": {
            "type": "string",
            "description": "Brief explanation of why this chart type was chosen.",
        },
    },
    "required": ["chart_type", "x_column", "y_columns", "title"],
    "additionalProperties": False,
}


# Schema for image-to-table extraction
TABLE_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "columns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Column headers for the extracted table.",
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": ["string", "number"]},
            },
            "description": "Rows of data, each row is an array of values.",
        },
    },
    "required": ["columns", "rows"],
    "additionalProperties": False,
}
