"""Streamlit entrypoint for the suppression quote MVP."""

from __future__ import annotations

from src.ui.main import render_app


def main() -> None:
    """Render the Streamlit application without embedding calculation rules."""
    render_app()


if __name__ == "__main__":
    main()
