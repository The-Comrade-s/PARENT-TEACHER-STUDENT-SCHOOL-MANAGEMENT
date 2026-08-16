"""Small reusable Streamlit UI building blocks shared across pages."""

from pathlib import Path

import streamlit as st


def load_theme():
    css_path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""<div class="ptms-header-bar"><h1>{title}</h1>{subtitle_html}</div>""",
        unsafe_allow_html=True,
    )


def metric_row(items: list[tuple[str, str]]):
    """items: list of (label, value) pairs, rendered as Streamlit metrics in a row."""
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        with col:
            st.metric(label, value)


def status_badge(text: str, pending: bool = False) -> str:
    css_class = "ptms-badge ptms-badge-pending" if pending else "ptms-badge"
    return f'<span class="{css_class}">{text}</span>'


def empty_state(message: str):
    st.markdown(f'<div class="ptms-card">{message}</div>', unsafe_allow_html=True)
