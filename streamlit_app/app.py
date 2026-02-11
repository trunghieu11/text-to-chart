"""
Streamlit UI for Text-to-Chart.

Run with: streamlit run streamlit_app/app.py --server.port 5001
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load .env
import config  # noqa: F401, E402

import streamlit as st

from chart_service import create_chart
from chart_service.chart_types import chart_type_registry
from chart_service.exporters.code import CodeExporter
from chart_service.exporters.embed import EmbedExporter
from chart_service.exporters.image import ImageExporter
from chart_service.plotters.addons.color_palette import PALETTES

# Page config
st.set_page_config(page_title="Text to Chart", page_icon="📊", layout="wide")

# Chart type and palette options
CHART_TYPE_OPTIONS = ["Let AI decide"] + chart_type_registry.list_types()
COLOR_PALETTE_OPTIONS = list(PALETTES.keys())


def _inject_css():
    """Load and inject custom CSS for styling."""
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        css = css_path.read_text()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _try_export_png_bytes(fig, width: int = 1200, height: int = 700):
    """Export figure as PNG bytes. Returns bytes or None."""
    try:
        return ImageExporter.to_bytes(fig, width=width, height=height)
    except Exception:
        return None


def main():
    _inject_css()

    with st.container():
        st.title("Text to Chart")
        st.caption("Transform your data into beautiful charts instantly.")

    # Initialize session state
    if "chart_fig" not in st.session_state:
        st.session_state.chart_fig = None
    if "parsed_df" not in st.session_state:
        st.session_state.parsed_df = None
    if "embed_url" not in st.session_state:
        st.session_state.embed_url = ""
    if "python_code" not in st.session_state:
        st.session_state.python_code = ""
    if "error" not in st.session_state:
        st.session_state.error = None

    # Input section
    st.divider()
    with st.container():
        st.header("Input Data")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Paste Text Data")
            input_text = st.text_area(
                "Paste tabular data (tab, comma, or space separated)",
                height=180,
                placeholder="e.g.\nA\tB\n1\t10\n2\t20",
                label_visibility="collapsed",
            )

        with col2:
            st.subheader("Or Upload File")
            uploaded_file = st.file_uploader(
                "Upload CSV, Excel, or Image",
                type=["csv", "xlsx", "xls", "png", "jpg", "jpeg", "webp"],
                label_visibility="collapsed",
            )
            # Persist uploaded file for use when Generate is clicked (uploader clears on rerun)
            if uploaded_file:
                st.session_state.uploaded_file = uploaded_file
            elif "uploaded_file" in st.session_state:
                del st.session_state["uploaded_file"]
            if "uploaded_file" in st.session_state:
                st.caption(f"Uploaded: {st.session_state.uploaded_file.name}")

    # Chart type and advanced options
    chart_type = st.selectbox("Chart Type", CHART_TYPE_OPTIONS)

    with st.expander("Advanced Options"):
        adv_col1, adv_col2 = st.columns(2)
        with adv_col1:
            color_palette = st.selectbox("Color Palette", COLOR_PALETTE_OPTIONS)
            ref_value = st.text_input("Reference Line Value (number)", "")
            ref_orientation = st.selectbox(
                "Reference Line Orientation",
                ["horizontal", "vertical"],
            )
            ref_color = st.text_input("Reference Line Color", "red")
            ref_label = st.text_input("Reference Line Label", "")
        with adv_col2:
            ann_text = st.text_input("Annotation Text", "")
            ann_x = st.text_input("Annotation X", "")
            ann_y = st.text_input("Annotation Y", "")

    # Generate button
    if st.button("Generate Chart", type="primary"):
        st.session_state.error = None

        # Resolve input (use persisted upload if uploader was cleared on rerun)
        raw_input = None
        filename = None
        uf = uploaded_file or st.session_state.get("uploaded_file")
        if input_text and input_text.strip():
            raw_input = input_text.strip()
        elif uf:
            raw_input = uf.read()
            filename = uf.name
        else:
            st.session_state.error = "Please paste text data or upload a file."

        if st.session_state.error is None:
            with st.spinner("Processing your data..."):
                try:
                    ct = "auto" if chart_type == "Let AI decide" else chart_type
                    parsed, config_obj, fig = create_chart(
                        raw_input=raw_input,
                        filename=filename,
                        chart_type=ct,
                    )

                    # Apply advanced options
                    if color_palette and color_palette != "default":
                        config_obj.color_palette = [color_palette]
                    if ref_value:
                        try:
                            rv = float(ref_value)
                            orient = "h" if ref_orientation == "horizontal" else "v"
                            config_obj.reference_lines = [
                                {
                                    "orientation": orient,
                                    "value": rv,
                                    "color": ref_color or "red",
                                    "label": ref_label,
                                }
                            ]
                        except ValueError:
                            pass
                    if ann_text and ann_x and ann_y:
                        try:
                            ax = float(ann_x) if str(ann_x).replace(".", "", 1).replace("-", "", 1).isdigit() else ann_x
                            ay = float(ann_y)
                            config_obj.annotations = [
                                {"x": ax, "y": ay, "text": ann_text, "showarrow": True}
                            ]
                        except (ValueError, TypeError):
                            pass

                    from chart_service.plotters import plotter_registry

                    fig = plotter_registry.plot(parsed.dataframe, config_obj)

                    chart_id = EmbedExporter.store_chart(fig)

                    st.session_state.chart_fig = fig
                    st.session_state.parsed_df = parsed.dataframe
                    st.session_state.parsed_source = parsed.source_type
                    st.session_state.embed_url = f"http://localhost:8000/v1/charts/{chart_id}/embed"
                    st.session_state.python_code = CodeExporter.generate(parsed.dataframe, config_obj)

                except Exception as e:
                    st.session_state.error = str(e)
                    st.session_state.chart_fig = None
                    st.session_state.parsed_df = None

    # Error display
    if st.session_state.error:
        st.error(st.session_state.error)

    # Results
    if st.session_state.parsed_df is not None and not st.session_state.parsed_df.empty:
        st.divider()
        with st.container():
            st.header("Parsed Data")
            df = st.session_state.parsed_df
            st.caption(f"Source: {st.session_state.get('parsed_source', '')} — Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            st.dataframe(df, use_container_width=True, hide_index=True)

    if st.session_state.chart_fig is not None:
        st.divider()
        with st.container():
            st.header("Chart Preview")
            st.plotly_chart(st.session_state.chart_fig, use_container_width=True)

        st.divider()
        with st.container():
            st.header("Export Options")
            png_preview = _try_export_png_bytes(st.session_state.chart_fig, width=600, height=350)
            png_full = _try_export_png_bytes(st.session_state.chart_fig)
            exp_col1, exp_col2, exp_col3 = st.columns(3)

            with exp_col1:
                st.subheader("Embed Link")
                if png_preview:
                    st.image(png_preview, use_container_width=True)
                st.text_input(
                    "Copy this URL to embed the chart",
                    value=st.session_state.embed_url,
                    key="embed_url_display",
                    disabled=True,
                    label_visibility="collapsed",
                )

            with exp_col2:
                st.subheader("PNG Image")
                if png_preview:
                    st.image(png_preview, use_container_width=True)
                if png_full:
                    st.download_button(
                        "Download PNG",
                        data=png_full,
                        file_name="chart.png",
                        mime="image/png",
                        key="dl_png",
                    )
                else:
                    st.caption("PNG export unavailable (install kaleido)")

            with exp_col3:
                st.subheader("Python Code")
                st.code(
                    st.session_state.python_code,
                    language="python",
                    line_numbers=True,
                    height=200,
                )
                st.download_button(
                    "Download .py",
                    data=st.session_state.python_code,
                    file_name="chart.py",
                    mime="text/x-python",
                    key="dl_code",
                )


if __name__ == "__main__":
    main()
