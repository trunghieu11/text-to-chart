"""
Image exporter: generates PNG images from Plotly figures.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import plotly.graph_objects as go
import plotly.io as pio


class ImageExporter:
    """Export charts as PNG images."""

    @staticmethod
    def to_bytes(fig: go.Figure, format: str = "png", width: int = 1200, height: int = 700) -> bytes:
        """
        Convert a Plotly figure to image bytes.

        Args:
            fig: The Plotly figure.
            format: Image format (png, jpeg, svg, pdf).
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Image bytes.
        """
        return pio.to_image(fig, format=format, width=width, height=height)

    @staticmethod
    def to_base64(fig: go.Figure, format: str = "png", width: int = 1200, height: int = 700) -> str:
        """
        Convert a Plotly figure to a base64-encoded string.

        Returns:
            Base64-encoded image string.
        """
        img_bytes = ImageExporter.to_bytes(fig, format=format, width=width, height=height)
        return base64.b64encode(img_bytes).decode("utf-8")

    @staticmethod
    def to_data_uri(fig: go.Figure, format: str = "png", width: int = 1200, height: int = 700) -> str:
        """
        Convert a Plotly figure to a data URI for embedding in HTML.

        Returns:
            Data URI string (e.g., data:image/png;base64,...).
        """
        b64 = ImageExporter.to_base64(fig, format=format, width=width, height=height)
        mime_type = f"image/{format}"
        return f"data:{mime_type};base64,{b64}"

    @staticmethod
    def save(fig: go.Figure, path: str | Path, format: str = "png", width: int = 1200, height: int = 700) -> Path:
        """
        Save a Plotly figure as an image file.

        Args:
            fig: The Plotly figure.
            path: Output file path.
            format: Image format.
            width: Image width.
            height: Image height.

        Returns:
            Path to the saved file.
        """
        path = Path(path)
        img_bytes = ImageExporter.to_bytes(fig, format=format, width=width, height=height)
        path.write_bytes(img_bytes)
        return path
