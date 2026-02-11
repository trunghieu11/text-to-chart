"""
Image parser: extracts tabular data from images using OCR or Vision LLM.
"""

from __future__ import annotations

import logging
from typing import Optional, Union

import pandas as pd

from chart_service.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class ImageParser(BaseParser):
    """Parse images containing tabular data into a DataFrame."""

    name = "image"
    supported_extensions = [".png", ".jpg", ".jpeg", ".webp"]
    supported_mime_types = ["image/png", "image/jpeg", "image/webp"]

    def can_handle(
        self, raw_input: Union[str, bytes], filename: Optional[str] = None
    ) -> bool:
        if filename:
            return self._get_extension(filename) in self.supported_extensions
        # Check if it looks like image bytes (check magic bytes)
        if isinstance(raw_input, bytes) and len(raw_input) > 8:
            return self._is_image_bytes(raw_input)
        return False

    def parse(
        self, raw_input: Union[str, bytes], filename: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Extract tabular data from an image.

        Strategy:
        1. Try Vision LLM (GPT-4V) if API key available
        2. Fall back to pytesseract OCR
        3. Raise error if neither works
        """
        if isinstance(raw_input, str):
            raise ValueError("Image parser requires bytes input")

        # Determine MIME type
        mime_type = self._guess_mime_type(raw_input, filename)
        logger.info(
            "[DEBUG] Image parse started: filename=%s, mime_type=%s, image_size_bytes=%s",
            filename,
            mime_type,
            len(raw_input),
        )
        print(f"[IMAGE] parse started filename={filename!r} mime={mime_type} size={len(raw_input)}", flush=True)

        # Strategy 1: Vision LLM
        df, vision_error = self._try_vision_llm(raw_input, mime_type)
        if df is not None:
            logger.info("[DEBUG] Image parse succeeded via Vision LLM: shape=%s", df.shape)
            print(f"[IMAGE] parse OK via Vision LLM shape={df.shape}", flush=True)
            return df
        err_str = f"{type(vision_error).__name__}: {vision_error}" if vision_error else "None"
        logger.info("[DEBUG] Vision LLM did not return data. vision_error=%s", err_str)
        print(f"[IMAGE] Vision LLM no data. vision_error={err_str}", flush=True)

        # Strategy 2: OCR with pytesseract
        df = self._try_ocr(raw_input)
        if df is not None:
            logger.info("[DEBUG] Image parse succeeded via OCR: shape=%s", df.shape)
            print(f"[IMAGE] parse OK via OCR shape={df.shape}", flush=True)
            return df
        logger.info("[DEBUG] OCR did not return data.")
        print("[IMAGE] OCR did not return data", flush=True)

        msg = (
            "Could not extract tabular data from image. "
            "Set OPENAI_API_KEY in .env for Vision LLM, or install tesseract + pytesseract for OCR."
        )
        if vision_error is not None:
            msg += f" Vision API error: {vision_error!s}"
        logger.warning("[DEBUG] Image parse failed. %s", msg)
        print(f"[IMAGE] parse FAILED: {msg}", flush=True)
        raise ValueError(msg)

    def _try_vision_llm(self, image_bytes: bytes, mime_type: str) -> tuple[pd.DataFrame | None, Exception | None]:
        """Try to extract table using Vision LLM. Returns (df or None, last error if failed)."""
        last_error = None
        try:
            from chart_service.llm.client import llm_client

            logger.info("[DEBUG] Vision LLM: is_available=%s", llm_client.is_available)
            print(f"[IMAGE] Vision LLM is_available={llm_client.is_available}", flush=True)
            if not llm_client.is_available:
                logger.info("[DEBUG] Vision LLM: skipped (no API key)")
                print("[IMAGE] Vision LLM skipped (no API key)", flush=True)
                last_error = None
                return None, last_error

            logger.info("[DEBUG] Vision LLM: calling API (image_bytes=%s, mime=%s)", len(image_bytes), mime_type)
            print(f"[IMAGE] Vision LLM calling API size={len(image_bytes)} mime={mime_type}", flush=True)
            result = llm_client.extract_table_from_image(image_bytes, mime_type)
            logger.info(
                "[DEBUG] Vision LLM: result keys=%s, rows_count=%s",
                list(result.keys()) if result else None,
                len(result.get("rows", [])) if result else 0,
            )
            if result and "columns" in result and "rows" in result:
                df = pd.DataFrame(result["rows"], columns=result["columns"])
                # Convert numeric columns
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except (ValueError, TypeError):
                        pass
                if not df.empty:
                    logger.info("Vision LLM extracted table: %s", df.shape)
                    return df, None
                logger.info("[DEBUG] Vision LLM: result had empty DataFrame after conversion")
            else:
                logger.info("[DEBUG] Vision LLM: result missing columns/rows or empty")
        except Exception as e:
            last_error = e
            logger.warning("Vision LLM extraction failed: %s", e, exc_info=True)
        return None, last_error

    def _try_ocr(self, image_bytes: bytes) -> pd.DataFrame | None:
        """Try to extract table using pytesseract OCR."""
        try:
            from io import BytesIO, StringIO

            from PIL import Image
            import pytesseract

            logger.info("[DEBUG] OCR: opening image (size=%s bytes)", len(image_bytes))
            img = Image.open(BytesIO(image_bytes))
            text = pytesseract.image_to_string(img)
            logger.info("[DEBUG] OCR: extracted text length=%s chars, preview=%s", len(text), repr(text[:200]) if text else "")

            if not text.strip():
                logger.info("[DEBUG] OCR: no text extracted")
                return None

            # Try to parse the OCR text as tabular data
            df = pd.read_csv(StringIO(text), sep=None, engine="python", skipinitialspace=True)
            if not df.empty:
                # Convert numeric columns
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except (ValueError, TypeError):
                        pass
                logger.info("OCR extracted table: %s", df.shape)
                return df
            logger.info("[DEBUG] OCR: read_csv produced empty DataFrame")
        except ImportError as e:
            logger.warning("pytesseract not available for OCR: %s", e)
        except Exception as e:
            logger.warning("OCR extraction failed: %s", e, exc_info=True)
        return None

    @staticmethod
    def _is_image_bytes(data: bytes) -> bool:
        """Check if bytes look like an image based on magic bytes."""
        # PNG: 89 50 4E 47
        if data[:4] == b"\x89PNG":
            return True
        # JPEG: FF D8 FF
        if data[:3] == b"\xff\xd8\xff":
            return True
        # WebP: RIFF....WEBP
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return True
        return False

    @staticmethod
    def _guess_mime_type(data: bytes, filename: str | None) -> str:
        """Guess MIME type from filename or magic bytes."""
        if filename:
            ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
            mime_map = {
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "webp": "image/webp",
            }
            if ext in mime_map:
                return mime_map[ext]

        if data[:4] == b"\x89PNG":
            return "image/png"
        if data[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if data[:4] == b"RIFF":
            return "image/webp"
        return "image/png"
