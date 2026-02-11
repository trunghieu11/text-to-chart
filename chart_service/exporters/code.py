"""
Code exporter: generates reproducible Python scripts from chart data and config.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pandas as pd

from chart_service.models import ChartConfig


class CodeExporter:
    """Export charts as reproducible Python scripts."""

    @staticmethod
    def generate(df: pd.DataFrame, config: ChartConfig) -> str:
        """
        Generate a standalone Python script that reproduces the chart.

        Args:
            df: The data used for the chart.
            config: The chart configuration.

        Returns:
            Python script as a string.
        """
        # Serialize data
        data_dict = df.to_dict("list")
        data_str = json.dumps(data_dict, indent=4, default=str)

        # Build the plotly expression
        chart_type = config.chart_type
        x_col = config.x_column
        y_cols = config.y_columns

        if chart_type == "pie":
            plot_call = CodeExporter._generate_pie_code(x_col, y_cols, config)
        elif len(y_cols) == 1:
            plot_call = CodeExporter._generate_single_y_code(chart_type, x_col, y_cols[0], config)
        else:
            plot_call = CodeExporter._generate_multi_y_code(chart_type, x_col, y_cols, config)

        script = textwrap.dedent(f'''\
            """
            Auto-generated chart script by Text-to-Chart.
            Run this script to reproduce the chart.
            """

            import pandas as pd
            import plotly.express as px


            def load_data():
                """Load the chart data."""
                data = {data_str}
                return pd.DataFrame(data)


            def plot_chart():
                """Create and display the chart."""
                df = load_data()
                {plot_call}
                fig.update_layout(template="{config.template}")
                fig.show()
                return fig


            if __name__ == "__main__":
                plot_chart()
        ''')

        return script

    @staticmethod
    def _generate_pie_code(names_col: str, values_cols: list[str], config: ChartConfig) -> str:
        values_col = values_cols[0] if values_cols else "value"
        title = config.title or f"{values_col} Distribution"
        return (
            f'fig = px.pie(df, names="{names_col}", values="{values_col}", '
            f'title="{title}")'
        )

    @staticmethod
    def _generate_single_y_code(chart_type: str, x_col: str, y_col: str, config: ChartConfig) -> str:
        title = config.title or f"{y_col} by {x_col}"
        return (
            f'fig = px.{chart_type}(df, x="{x_col}", y="{y_col}", '
            f'title="{title}")'
        )

    @staticmethod
    def _generate_multi_y_code(chart_type: str, x_col: str, y_cols: list[str], config: ChartConfig) -> str:
        title = config.title or f"Chart"
        y_cols_str = json.dumps(y_cols)
        return (
            f'fig = px.{chart_type}(df, x="{x_col}", y={y_cols_str}, '
            f'title="{title}")'
        )

    @staticmethod
    def save(df: pd.DataFrame, config: ChartConfig, path: str | Path) -> Path:
        """Save the generated script to a file."""
        path = Path(path)
        script = CodeExporter.generate(df, config)
        path.write_text(script)
        return path
