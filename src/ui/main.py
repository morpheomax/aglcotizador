"""Main Streamlit workflow for the MVP."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
import re
from uuid import uuid4

import pandas as pd
import streamlit as st

from src.bom.bom_builder import available_options, bom_lines_to_dataframe, build_optional_bom, build_system_bom
from src.bom.catalog_loader import (
    load_altitude_factors,
    load_bom_catalog,
    load_concentration_profiles,
    load_cylinder_catalog,
    load_dead_volume_factors,
    load_flooding_factors,
    load_nozzle_coverage,
    load_optional_items,
)
from src.bom.consolidator import consolidate_bom
from src.engine.calculator import calculate_room_requirements
from src.engine.cylinder_selector import list_valid_cylinder_selections, select_cylinder
from src.exporters.excel_exporter import export_quote_to_excel
from src.models.project import ProjectInfo
from src.models.room import AgentType, RoomInput
from src.models.system_config import DischargeConnection, SystemConfig, SystemType
from src.ui.rooms_editor import delete_room_by_id


COMPLIANCE_NOTE = (
    "Este cálculo es preliminar para cotización. Debe ser revisado y validado "
    "por ingeniería mediante metodología/software certificado antes de usarlo "
    "para instalación o emisión final."
)
KG_TO_LB = 2.2046226218

ROOM_COLUMNS = [
    "room_id",
    "remove",
    "selected",
    "name",
    "system_type",
    "agent_type",
    "forced_cylinder_code",
    "forced_cylinder_qty",
    "length_m",
    "width_m",
    "height_m",
    "raised_floor_m",
    "false_ceiling_m",
    "protect_raised_floor",
    "protect_false_ceiling",
    "structural_reductions_m3",
    "object_reductions_m3",
    "min_temp_c",
    "max_temp_c",
    "design_concentration_pct",
    "concentration_profile_id",
    "altitude_m",
    "discharge_connection",
    "include_optional_items",
    "include_reserve",
    "include_main_reserve",
    "override_nozzles",
    "nozzle_qty_manual",
    "nozzle_override_reason",
    "object_reductions_are_permanent",
    "manifold_nominal_diameter_dn",
    "reserve_sections_qty",
    "custom_dead_volume_l",
]

ROOM_PREVIEW_COLUMNS = ["area_m2", "gross_volume_m3", "net_volume_m3"]

ROOM_DISPLAY_COLUMNS = [
    "remove",
    "selected",
    "name",
    "agent_type",
    "length_m",
    "width_m",
    "height_m",
    "area_m2",
    "gross_volume_m3",
    "net_volume_m3",
    "raised_floor_m",
    "false_ceiling_m",
    "structural_reductions_m3",
    "object_reductions_m3",
    "min_temp_c",
    "max_temp_c",
    "design_concentration_pct",
    "altitude_m",
    "discharge_connection",
    "include_optional_items",
    "include_reserve",
    "include_main_reserve",
]


@st.cache_data
def _load_catalogs(cache_key: tuple[tuple[str, float], ...]) -> dict[str, pd.DataFrame]:
    del cache_key
    return {
        "flooding": load_flooding_factors(),
        "altitude": load_altitude_factors(),
        "nozzles": load_nozzle_coverage(),
        "cylinders": load_cylinder_catalog(),
        "bom": load_bom_catalog(),
        "optional": load_optional_items(),
        "concentration_profiles": load_concentration_profiles(),
        "dead_volume": load_dead_volume_factors(),
    }


def render_app() -> None:
    st.set_page_config(page_title="Cotizador Supresión", layout="wide")
    _inject_style()

    with st.sidebar:
        if st.button("Recargar catálogos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    catalogs = _load_catalogs(_catalog_cache_key())
    if "rooms_df" not in st.session_state:
        st.session_state["rooms_df"] = _default_rooms_df()
    project = _render_sidebar_project()
    st.session_state["project_info"] = project

    _render_app_hero()

    _render_status_bar()
    tabs = st.tabs(["1. Sistemas y salas", "2. Resultados", "3. BOM y opcionales"])

    with tabs[0]:
        _render_rooms_tab(catalogs)

    with tabs[1]:
        _render_results_tab(catalogs)

    with tabs[2]:
        _render_bom_tab(catalogs)


def _render_app_hero() -> None:
    st.markdown(
        """
        <div class="app-hero">
            <div class="app-hero-eyebrow">Predimensionamiento técnico-comercial</div>
            <div class="app-hero-title">Cotizador de supresión por agente limpio</div>
            <div class="app-hero-subtitle">
                Carga salas, valida agente y cilindros, revisa concentraciones y genera un BOM preliminar trazable a manuales ANSUL.
            </div>
        </div>
        <div class="flow-rail">
            <div class="flow-card">
                <div class="flow-number">1</div>
                <div class="flow-title">Proyecto</div>
                <div class="flow-text">Completa cliente, ubicación y moneda en el panel lateral.</div>
            </div>
            <div class="flow-card">
                <div class="flow-number">2</div>
                <div class="flow-title">Salas</div>
                <div class="flow-text">Define agente, perfil, sistema, dimensiones y condiciones de diseño.</div>
            </div>
            <div class="flow-card">
                <div class="flow-number">3</div>
                <div class="flow-title">Validación</div>
                <div class="flow-text">Revisa agente, concentración lograda, cilindros y advertencias técnicas.</div>
            </div>
            <div class="flow-card">
                <div class="flow-number">4</div>
                <div class="flow-title">BOM</div>
                <div class="flow-text">Genera detalle, consolida códigos y descarga el Excel de cotización.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _catalog_cache_key() -> tuple[tuple[str, float], ...]:
    catalog_paths = [
        Path("data/processed/flooding_factors.csv"),
        Path("data/processed/altitude_factors.csv"),
        Path("data/processed/nozzle_coverage.csv"),
        Path("data/processed/cylinder_catalog.csv"),
        Path("data/processed/bom_catalog.csv"),
        Path("data/processed/optional_items.csv"),
        Path("data/processed/concentration_profiles.csv"),
        Path("data/processed/dead_volume_factors.csv"),
    ]
    return tuple((str(path), path.stat().st_mtime if path.exists() else 0.0) for path in catalog_paths)


def _cylinder_option_labels(agent_type: str | None = None) -> list[str]:
    try:
        cylinders_df = load_cylinder_catalog()
    except FileNotFoundError:
        return ["Automático"]
    if agent_type:
        cylinders_df = cylinders_df[cylinders_df["agent_type"] == agent_type]
    labels = ["Automático"]
    for _, row in cylinders_df.sort_values(["agent_type", "size_l"]).iterrows():
        labels.append(f"{row['agent_type']} · {row['cylinder_label']} · {row['cylinder_code']}")
    return labels


def _extract_cylinder_code(label: str) -> str | None:
    if label == "Automático":
        return None
    parts = [part.strip() for part in label.split("·")]
    return parts[-1] if parts else None


def _inject_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #f4f7fb;
            --surface: #ffffff;
            --surface-muted: #f8fafc;
            --border: #d7e0ea;
            --border-strong: #9fb0c3;
            --text: #102033;
            --text-muted: #506276;
            --text-soft: #6f8092;
            --primary: #0f4c75;
            --primary-dark: #08243a;
            --primary-soft: #e7f3fb;
            --accent: #38bdf8;
            --sidebar-bg: #071b2d;
            --sidebar-panel: #0b2942;
            --sidebar-border: rgba(148, 189, 219, 0.22);
            --success-soft: #ecfdf5;
            --warning-soft: #fffbeb;
            --danger-soft: #fef2f2;
            --shadow: 0 10px 28px rgba(12, 32, 52, 0.07);
        }
        .stApp {
            background: var(--app-bg);
            color: var(--text);
        }
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 2.5rem;
            max-width: 1480px;
        }
        h1, h2, h3, h4, p, label {
            color: var(--text);
        }
        h1 {
            font-size: 2rem;
            font-weight: 750;
            line-height: 1.15;
            margin-bottom: 0.15rem;
            letter-spacing: -0.02em;
        }
        h2, h3 {
            letter-spacing: -0.01em;
        }
        div[data-testid="stCaptionContainer"] p {
            color: var(--text-muted);
            font-size: 0.96rem;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #071b2d 0%, #0c2a43 100%);
            border-right: 1px solid var(--sidebar-border);
            box-shadow: 10px 0 30px rgba(7, 27, 45, 0.18);
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p {
            color: #e8f3fb !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] span {
            color: inherit !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] {
            background: rgba(11, 41, 66, 0.92);
            border-color: var(--sidebar-border);
            box-shadow: none;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary,
        section[data-testid="stSidebar"] div[data-testid="stExpander"] summary * {
            color: #f2f8fc !important;
        }
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea,
        section[data-testid="stSidebar"] select {
            background: #ffffff !important;
            color: #102033 !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background: #ffffff !important;
            border-color: rgba(184, 215, 236, 0.45) !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div *,
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea {
            color: #102033 !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stTextInput"] label,
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"] label,
        section[data-testid="stSidebar"] div[data-testid="stDateInput"] label,
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
        section[data-testid="stSidebar"] div[data-testid="stTextArea"] label {
            color: #e8f3fb !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] label,
        section[data-testid="stSidebar"] div[data-testid="stExpander"] p {
            color: #e8f3fb !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stAlert"] {
            background: rgba(255, 251, 235, 0.98) !important;
            border-color: rgba(245, 158, 11, 0.45) !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stAlert"] * {
            color: #5b3413 !important;
        }
        .sidebar-brand {
            padding: 0.85rem 0.9rem;
            margin: 0 0 1rem 0;
            border: 1px solid var(--sidebar-border);
            border-radius: 16px;
            background: rgba(56, 189, 248, 0.08);
        }
        .sidebar-brand-title {
            color: #ffffff !important;
            font-weight: 820;
            font-size: 1.12rem;
            letter-spacing: -0.02em;
        }
        .sidebar-brand-subtitle {
            color: #b8d7ec !important;
            font-size: 0.84rem;
            margin-top: 0.2rem;
        }
        div[data-testid="stTabs"] {
            background: transparent;
        }
        div[data-testid="stTabs"] div[role="tablist"] {
            gap: 0.35rem;
            border-bottom: 1px solid var(--border);
        }
        div[data-testid="stTabs"] button {
            color: var(--text-muted) !important;
            background: transparent;
            border-radius: 10px 10px 0 0;
            font-weight: 650;
            padding: 0.75rem 1rem;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--primary-dark) !important;
            background: var(--surface);
            border-bottom: 3px solid var(--primary);
        }
        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button {
            border-radius: 10px;
            font-weight: 700;
            border: 1px solid var(--primary);
            transition: background 140ms ease, border-color 140ms ease, color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
        }
        div[data-testid="stButton"] button:not([kind="primary"]),
        div[data-testid="stDownloadButton"] button:not([kind="primary"]) {
            background: #ffffff;
            color: var(--primary-dark) !important;
        }
        div[data-testid="stButton"] button:not([kind="primary"]) p,
        div[data-testid="stDownloadButton"] button:not([kind="primary"]) p {
            color: var(--primary-dark) !important;
        }
        div[data-testid="stButton"] button:hover,
        div[data-testid="stDownloadButton"] button:hover {
            border-color: var(--primary-dark) !important;
            box-shadow: 0 8px 18px rgba(15, 76, 117, 0.15);
            transform: translateY(-1px);
        }
        div[data-testid="stButton"] button:not([kind="primary"]):hover,
        div[data-testid="stDownloadButton"] button:not([kind="primary"]):hover {
            background: var(--primary-soft) !important;
            color: var(--primary-dark) !important;
        }
        div[data-testid="stButton"] button:not([kind="primary"]):hover p,
        div[data-testid="stDownloadButton"] button:not([kind="primary"]):hover p {
            color: var(--primary-dark) !important;
        }
        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stDownloadButton"] button[kind="primary"] {
            background: var(--primary);
            color: #ffffff !important;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover,
        div[data-testid="stDownloadButton"] button[kind="primary"]:hover {
            background: #0b3a5b !important;
            color: #ffffff !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button {
            background: #ffffff !important;
            color: #0b2942 !important;
            border-color: rgba(184, 215, 236, 0.65) !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button p {
            color: #0b2942 !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            background: #dff3ff !important;
            border-color: #38bdf8 !important;
            color: #071b2d !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover p {
            color: #071b2d !important;
        }
        div[data-testid="stButton"] button[kind="primary"] p,
        div[data-testid="stDownloadButton"] button[kind="primary"] p {
            color: #ffffff !important;
        }
        div[data-testid="stAlert"] {
            color: var(--text) !important;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: var(--surface) !important;
        }
        div[data-testid="stAlert"] * {
            color: var(--text) !important;
        }
        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.95rem 1rem;
            box-shadow: var(--shadow);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: var(--text) !important;
        }
        div[data-testid="stMetric"] label {
            color: var(--text-muted) !important;
            font-weight: 650;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.55rem;
            font-weight: 760;
        }
        div[data-testid="stDataFrame"],
        div[data-testid="stDataEditor"] {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            background: var(--surface);
            box-shadow: var(--shadow);
        }
        div[data-testid="stDataFrame"] * ,
        div[data-testid="stDataEditor"] * {
            color: var(--text) !important;
        }
        input, textarea, select {
            color: var(--text) !important;
            background: var(--surface) !important;
            border-color: var(--border-strong) !important;
        }
        div[data-baseweb="select"] > div * {
            color: var(--text) !important;
        }
        .app-hero {
            background: linear-gradient(135deg, #08243a 0%, #0f4c75 58%, #155f8d 100%);
            border-radius: 22px;
            padding: 1.35rem 1.45rem;
            margin: 0.2rem 0 1rem 0;
            color: #ffffff;
            box-shadow: 0 18px 38px rgba(8, 36, 58, 0.18);
        }
        .app-hero-eyebrow {
            color: #b8e6ff;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.75rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }
        .app-hero-title {
            color: #ffffff;
            font-size: 1.9rem;
            font-weight: 850;
            letter-spacing: -0.03em;
            line-height: 1.1;
        }
        .app-hero-subtitle {
            color: #d9effb;
            margin-top: 0.45rem;
            max-width: 860px;
            font-size: 0.98rem;
        }
        .flow-rail {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.85rem 0 1.15rem 0;
        }
        .flow-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0.85rem 0.9rem;
            box-shadow: 0 8px 20px rgba(12, 32, 52, 0.06);
        }
        .flow-number {
            width: 1.75rem;
            height: 1.75rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--primary-soft);
            color: var(--primary-dark);
            font-weight: 850;
            margin-bottom: 0.45rem;
        }
        .flow-title {
            color: var(--text);
            font-weight: 800;
            margin-bottom: 0.18rem;
        }
        .flow-text {
            color: var(--text-muted);
            font-size: 0.88rem;
            line-height: 1.35;
        }
        .small-note {
            color: var(--text-muted);
            font-size: 0.92rem;
            margin: 0.15rem 0 0.8rem 0;
        }
        .section-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.95rem 1rem;
            margin: 0.55rem 0 1rem 0;
            box-shadow: var(--shadow);
        }
        .section-title {
            color: var(--text);
            font-size: 1.1rem;
            font-weight: 760;
            margin-bottom: 0.2rem;
        }
        .section-subtitle {
            color: var(--text-muted);
            font-size: 0.93rem;
        }
        .workflow-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.65rem;
            margin: 0.25rem 0 1rem 0;
        }
        .workflow-step {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.75rem 0.85rem;
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        .workflow-step strong {
            display: block;
            color: var(--primary-dark);
            margin-bottom: 0.15rem;
        }
        .room-quickbar {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 0.65rem;
            align-items: center;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.65rem 0.75rem;
            margin: 0.55rem 0 0.3rem 0;
            box-shadow: 0 4px 14px rgba(12, 32, 52, 0.05);
        }
        .room-quickbar-title {
            color: var(--text);
            font-weight: 760;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .room-quickbar-meta {
            color: var(--text-muted);
            font-size: 0.86rem;
            margin-top: 0.12rem;
        }
        .form-step {
            margin: 0.9rem 0 0.45rem 0;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border);
            color: var(--primary-dark);
            font-weight: 760;
        }
        .technical-note {
            background: var(--primary-soft);
            border: 1px solid #b9d9ee;
            border-radius: 12px;
            padding: 0.7rem 0.85rem;
            color: var(--primary-dark);
            font-size: 0.9rem;
            margin-top: 0.65rem;
        }
        div[data-testid="stExpander"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            margin-bottom: 0.75rem;
            box-shadow: var(--shadow);
        }
        @media (max-width: 900px) {
            .flow-rail { grid-template-columns: 1fr 1fr; }
        }
        @media (max-width: 700px) {
            .workflow-strip { grid-template-columns: 1fr; }
            .flow-rail { grid-template-columns: 1fr; }
        }
        hr {
            border-color: var(--border);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar_project() -> ProjectInfo:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">Cotizador Supresión</div>
                <div class="sidebar-brand-subtitle">FK-5-1-12 / FM-200 · cálculo preliminar</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.header("Proyecto")
        client = st.text_input("Cliente", value="Cliente demo")
        project_name = st.text_input("Proyecto", value="Proyecto supresión")
        country = st.text_input("País", value="Chile")
        city = st.text_input("Ciudad", value="Santiago")

        with st.expander("Datos comerciales", expanded=False):
            base_altitude_m = st.number_input("Altitud base msnm", value=0.0, step=50.0)
            currency = st.selectbox("Moneda", ["USD", "CLP", "EUR"], index=0)
            seller = st.text_input("Responsable", value="")
            quote_date = st.date_input("Fecha", value=date.today())
            notes = st.text_area("Observaciones", value="")

        st.divider()
        st.warning(COMPLIANCE_NOTE)

    return ProjectInfo(
        client=client,
        project_name=project_name,
        country=country,
        city=city or None,
        base_altitude_m=float(base_altitude_m),
        currency=currency,
        seller=seller or None,
        quote_date=quote_date,
        notes=notes or None,
    )


def _render_status_bar() -> None:
    rooms_df = st.session_state.get("rooms_df", _default_rooms_df())
    results_df = st.session_state.get("results_df", pd.DataFrame())
    bom_detail_df = st.session_state.get("bom_detail_df", pd.DataFrame())

    selected_rooms = int(rooms_df.get("selected", pd.Series(dtype=bool)).map(_as_bool).sum()) if not rooms_df.empty else 0
    col1, col2, col3, col4 = st.columns(4, gap="small")
    col1.metric("Salas activas", selected_rooms)
    col2.metric("Salas calculadas", 0 if results_df.empty else len(results_df))
    col3.metric("Agente total kg", "0.0" if results_df.empty else f"{results_df['agent_required_rounded_kg'].sum():,.1f}")
    col4.metric("Ítems BOM", 0 if bom_detail_df.empty else len(bom_detail_df))


def _render_rooms_tab(catalogs: dict[str, pd.DataFrame]) -> None:
    _section_header(
        "Sistemas y salas",
        "Completa cada sala y usa Guardar y calcular. El resultado y las alternativas aparecen en la misma tarjeta.",
    )

    if message := st.session_state.pop("room_flash", None):
        st.success(message)

    rooms_df = _clean_rooms_df(st.session_state.get("rooms_df", pd.DataFrame()))
    st.markdown(
        """
        <div class="workflow-strip">
            <div class="workflow-step"><strong>Datos mínimos</strong>Nombre, agente, perfil, sistema y dimensiones.</div>
            <div class="workflow-step"><strong>Protección</strong>Activa piso técnico, cielo falso o reducciones solo cuando apliquen.</div>
            <div class="workflow-step"><strong>Resultado inmediato</strong>Guarda para ver agente, concentración, cilindros y boquillas.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    action_col, note_col = st.columns([1, 4], gap="small")
    with action_col:
        if st.button("Agregar sala", type="primary", use_container_width=True):
            _add_room()
            st.rerun()
    with note_col:
        st.caption("Completa solo los campos visibles para un caso estándar. Usa Ajustes avanzados para manifold, reducciones u opcionales.")

    if rooms_df.empty:
        st.info("No hay salas cargadas. Usa Agregar sala para comenzar.")
        return

    for _, row in rooms_df.iterrows():
        _render_room_card(row, catalogs)


def _render_room_card(row: pd.Series, catalogs: dict[str, pd.DataFrame]) -> None:
    room_id = str(row["room_id"])
    result = _result_for_room(room_id)
    has_error = any(room_id in message for message in st.session_state.get("calculation_errors", []))
    if not _as_bool(row["selected"]):
        status = "No incluida en la cotización"
    elif has_error:
        status = "Requiere revisión"
    else:
        status = "Calculada" if result is not None else "Pendiente"
    title = f"{row['name']}  |  {row['agent_type']}  |  {status}"
    expanded = result is None or st.session_state.get("active_room_id") == room_id
    quick_info, quick_delete = st.columns([6, 1], gap="small")
    with quick_info:
        st.markdown(
            f"""
            <div class="room-quickbar">
                <div>
                    <div class="room-quickbar-title">{row['name']}</div>
                    <div class="room-quickbar-meta">{row['agent_type']} · {row['system_type']} · {status}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with quick_delete:
        st.write("")
        if st.button("Eliminar", key=f"quick_delete_{room_id}", use_container_width=True):
            _delete_room(room_id)
            st.session_state["room_flash"] = f"Sala {row['name']} eliminada."
            st.rerun()
    with st.expander(title, expanded=expanded):
        with st.form(f"room_form_{room_id}"):
            st.markdown('<div class="form-step">1. Sala y sistema</div>', unsafe_allow_html=True)
            top1, top2, top3 = st.columns([2.4, 1.4, 1.4])
            name = top1.text_input("Nombre de sala", value=str(row["name"]))
            agent_values = [item.value for item in AgentType]
            agent_type = top2.selectbox(
                "Agente limpio",
                agent_values,
                index=agent_values.index(str(row["agent_type"])),
                help="Selecciona el agente definido para esta cotización. La concentración válida depende del agente.",
            )
            system_values = [item.value for item in SystemType]
            system_type = top3.selectbox(
                "Tipo de sistema",
                system_values,
                index=system_values.index(str(row["system_type"])),
                help="Sistema simple o manifold. El selector validará cilindros compatibles.",
            )
            selected = st.checkbox(
                "Incluir esta sala en el cálculo, los totales y el BOM de la cotización",
                value=_as_bool(row["selected"]),
                help="Desmárcala solo si quieres conservar sus datos sin considerarla en la cotización actual.",
            )

            st.markdown('<div class="form-step">2. Dimensiones de la sala principal</div>', unsafe_allow_html=True)
            st.caption("La sala principal siempre se considera protegida.")
            dim1, dim2, dim3 = st.columns(3)
            length_m = dim1.number_input("Largo (m)", min_value=0.01, value=float(row["length_m"]), step=0.1)
            width_m = dim2.number_input("Ancho (m)", min_value=0.01, value=float(row["width_m"]), step=0.1)
            height_m = dim3.number_input("Alto (m)", min_value=0.01, value=float(row["height_m"]), step=0.1)

            st.markdown('<div class="form-step">3. Espacios adicionales</div>', unsafe_allow_html=True)
            st.caption("Marca únicamente los espacios que recibirán agente y tendrán una boquilla propia.")
            sub1, sub2 = st.columns(2, gap="medium")
            protect_raised_floor = sub1.checkbox(
                "Proteger piso técnico",
                value=_as_bool(row["protect_raised_floor"]),
                help="Incluye su volumen en el agente y agrega al menos una boquilla para este espacio.",
            )
            raised_floor_m = sub1.number_input(
                "Altura del piso técnico (m)",
                min_value=0.0,
                value=float(row["raised_floor_m"]),
                step=0.1,
                help="Déjalo en 0 si no existe piso técnico.",
            )
            protect_false_ceiling = sub2.checkbox(
                "Proteger cielo falso",
                value=_as_bool(row["protect_false_ceiling"]),
                help="Incluye su volumen en el agente y agrega al menos una boquilla para este espacio.",
            )
            false_ceiling_m = sub2.number_input(
                "Altura del cielo falso (m)",
                min_value=0.0,
                value=float(row["false_ceiling_m"]),
                step=0.1,
                help="Déjalo en 0 si no existe cielo falso.",
            )

            st.markdown('<div class="form-step">4. Condiciones de diseño</div>', unsafe_allow_html=True)
            profiles = catalogs["concentration_profiles"]
            agent_profiles = profiles[
                (profiles["agent_type"].astype(str) == agent_type) & profiles["active"].map(_as_bool)
            ]
            profile_by_label: dict[str, str | None] = {"Manual": None}
            for _, profile in agent_profiles.iterrows():
                profile_by_label[
                    f"{profile['profile_label']} · {float(profile['design_concentration_pct']):g}%"
                ] = str(profile["profile_id"])
            current_profile_id = (
                str(row["concentration_profile_id"])
                if pd.notna(row["concentration_profile_id"]) and str(row["concentration_profile_id"]).strip()
                else None
            )
            current_profile_label = next(
                (label for label, profile_id in profile_by_label.items() if profile_id == current_profile_id),
                "Manual",
            )
            selected_profile_label = st.selectbox(
                "Perfil de concentración",
                list(profile_by_label),
                index=list(profile_by_label).index(current_profile_label),
                help="Los perfiles provienen de las tablas de diseño ANSUL. Usa Manual solo con respaldo técnico.",
            )
            concentration_profile_id = profile_by_label[selected_profile_label]
            selected_profile_rows = agent_profiles[
                agent_profiles["profile_id"].astype(str) == str(concentration_profile_id)
            ]
            concentration_value = (
                float(selected_profile_rows.iloc[0]["design_concentration_pct"])
                if concentration_profile_id and not selected_profile_rows.empty
                else float(row["design_concentration_pct"])
            )
            tech1, tech2, tech3, tech4 = st.columns(4)
            min_temp_c = tech1.number_input(
                "Temperatura mínima (°C)", value=float(row["min_temp_c"]), step=1.0, help="Menor temperatura prevista."
            )
            max_temp_c = tech2.number_input(
                "Temperatura máxima (°C)", value=float(row["max_temp_c"]), step=1.0, help="Mayor temperatura prevista."
            )
            concentration = tech3.number_input(
                "Concentración de diseño (%)",
                min_value=0.01,
                value=concentration_value,
                step=0.01,
                disabled=concentration_profile_id is not None,
                help="El perfil fija este valor. En modo Manual: FM-200 6.4%-15%; FK-5-1-12 4%-10%.",
            )
            altitude_m = tech4.number_input(
                "Altitud del proyecto (msnm)", value=float(row["altitude_m"]), step=50.0
            )

            with st.expander("Ajustes avanzados (solo si aplica)", expanded=False):
                st.caption("Puedes omitir esta sección: el sistema seleccionará cilindros y boquillas automáticamente.")
                red1, red2 = st.columns(2)
                structural_reductions_m3 = red1.number_input(
                    "Volumen ocupado por estructura (m³)",
                    min_value=0.0,
                    value=float(row["structural_reductions_m3"]),
                    help="Volumen sólido que no debe llenarse con agente.",
                )
                object_reductions_m3 = red2.number_input(
                    "Volumen de objetos sólidos permanentes (m³)",
                    min_value=0.0,
                    value=float(row["object_reductions_m3"]),
                    help="Solo objetos no removibles y no permeables ubicados dentro del recinto.",
                )
                object_reductions_are_permanent = st.checkbox(
                    "Confirmo que los objetos descontados son sólidos, permanentes, no removibles y sin aberturas",
                    value=_as_bool(row["object_reductions_are_permanent"]),
                    disabled=object_reductions_m3 <= 0,
                )
                st.write("**Volumen muerto de manifold/tubería**")
                dead1, dead2, dead3 = st.columns(3)
                dn_options: list[int | None] = [None, 65, 80, 100, 150]
                current_dn = int(row["manifold_nominal_diameter_dn"]) if pd.notna(row["manifold_nominal_diameter_dn"]) else None
                manifold_dn = dead1.selectbox(
                    "Diámetro de manifold",
                    dn_options,
                    index=dn_options.index(current_dn) if current_dn in dn_options else 0,
                    format_func=lambda value: "Sin manifold" if value is None else f"DN{value}",
                    help="Agrega el volumen de extremo muerto publicado en la Tabla 5-8.",
                )
                reserve_sections_qty = dead2.number_input(
                    "Secciones de reserva",
                    min_value=0,
                    value=max(0, int(row["reserve_sections_qty"])),
                    step=1,
                    help="Cada sección suma el volumen publicado para el diámetro seleccionado.",
                )
                custom_dead_volume_l = dead3.number_input(
                    "Volumen muerto adicional (L)",
                    min_value=0.0,
                    value=float(row["custom_dead_volume_l"]),
                    step=0.1,
                    help="Solo volumen donde quedará agente retenido y que no forma parte del cálculo hidráulico.",
                )
                st.write("**Boquillas**")
                nozzle_override = st.checkbox(
                    "Usar una cantidad distinta de la recomendación automática",
                    value=_as_bool(row["override_nozzles"]),
                    help="La cantidad nunca puede ser menor al mínimo técnico calculado.",
                )
                noz1, noz2 = st.columns([1, 3])
                nozzle_qty = noz1.number_input(
                    "Cantidad deseada",
                    min_value=1,
                    value=max(1, int(row["nozzle_qty_manual"])) if pd.notna(row["nozzle_qty_manual"]) else 1,
                    step=1,
                )
                nozzle_reason = noz2.text_input(
                    "Justificación técnica si es impar",
                    value=str(row["nozzle_override_reason"]) if pd.notna(row["nozzle_override_reason"]) else "",
                )
                st.write("**Alcance comercial**")
                opt1, opt2, opt3 = st.columns(3)
                include_optional = opt1.checkbox(
                    "Mostrar opcionales en el BOM", value=_as_bool(row["include_optional_items"])
                )
                include_reserve = opt2.checkbox(
                    "Registrar solicitud de reserva",
                    value=_as_bool(row["include_reserve"]),
                    help="La regla específica de BOM de reserva aún requiere definición.",
                )
                include_main_reserve = opt3.checkbox(
                    "Registrar solicitud de main reserve",
                    value=_as_bool(row["include_main_reserve"]),
                    help="La regla específica de BOM de main reserve aún requiere definición.",
                )

            st.caption("Al guardar se validarán los datos y se actualizarán agente, cilindros y boquillas.")
            save_col, delete_col = st.columns([3, 1])
            save = save_col.form_submit_button("Guardar y calcular esta sala", type="primary", use_container_width=True)
            delete = delete_col.form_submit_button("Eliminar esta sala", use_container_width=True)

        if delete:
            _delete_room(room_id)
            st.session_state["room_flash"] = f"Sala {row['name']} eliminada."
            st.rerun()

        if save:
            updated = row.to_dict()
            updated.update(
                {
                    "name": name.strip(),
                    "agent_type": agent_type,
                    "system_type": system_type,
                    "selected": selected,
                    "length_m": length_m,
                    "width_m": width_m,
                    "height_m": height_m,
                    "raised_floor_m": raised_floor_m,
                    "false_ceiling_m": false_ceiling_m,
                    "protect_raised_floor": protect_raised_floor,
                    "protect_false_ceiling": protect_false_ceiling,
                    "structural_reductions_m3": structural_reductions_m3,
                    "object_reductions_m3": object_reductions_m3,
                    "min_temp_c": min_temp_c,
                    "max_temp_c": max_temp_c,
                    "design_concentration_pct": concentration,
                    "concentration_profile_id": concentration_profile_id,
                    "altitude_m": altitude_m,
                    "include_optional_items": include_optional,
                    "include_reserve": include_reserve,
                    "include_main_reserve": include_main_reserve,
                    "override_nozzles": nozzle_override,
                    "nozzle_qty_manual": int(nozzle_qty) if nozzle_override else None,
                    "nozzle_override_reason": nozzle_reason.strip() or None,
                    "object_reductions_are_permanent": object_reductions_are_permanent,
                    "manifold_nominal_diameter_dn": manifold_dn,
                    "reserve_sections_qty": int(reserve_sections_qty),
                    "custom_dead_volume_l": custom_dead_volume_l,
                }
            )
            if not updated["name"]:
                st.error("El nombre de la sala no puede estar vacío.")
            else:
                current = st.session_state["rooms_df"].copy()
                current.loc[current["room_id"] == room_id, ROOM_COLUMNS] = [updated[column] for column in ROOM_COLUMNS]
                st.session_state["rooms_df"] = _clean_rooms_df(current)
                _calculate_selected_rooms(catalogs)
                st.session_state["room_flash"] = f"Sala {updated['name']} guardada y calculada."
                st.session_state["active_room_id"] = room_id
                st.rerun()

        _render_inline_room_result(room_id, catalogs)


def _result_for_room(room_id: str) -> pd.Series | None:
    results_df = st.session_state.get("results_df", pd.DataFrame())
    if results_df.empty or "room_id" not in results_df.columns:
        return None
    matches = results_df[results_df["room_id"].astype(str) == room_id]
    return None if matches.empty else matches.iloc[0]


def _render_inline_room_result(room_id: str, catalogs: dict[str, pd.DataFrame]) -> None:
    result = _result_for_room(room_id)
    if result is None:
        errors = [message for message in st.session_state.get("calculation_errors", []) if room_id in message]
        for message in errors:
            st.error(message)
        return

    cylinders_df = st.session_state.get("selected_cylinders_df", pd.DataFrame())
    cylinder_rows = (
        cylinders_df[cylinders_df["room_id"].astype(str) == room_id]
        if not cylinders_df.empty and "room_id" in cylinders_df.columns
        else pd.DataFrame()
    )
    cylinder = None if cylinder_rows.empty else cylinder_rows.iloc[0]

    st.divider()
    st.write("**Resultado inmediato**")
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Volumen protegido", f"{float(result['net_volume_m3']):,.2f} m³")
    metric2.metric("Agente", f"{float(result['agent_required_rounded_kg']):,.0f} kg")
    metric3.metric("Agente", f"{float(result['agent_required_rounded_lb']):,.1f} lb")
    metric4.metric("Boquillas", int(result["nozzle_final_qty"]))

    detail1, detail2, detail3 = st.columns(3)
    detail1.caption(f"Flooding: {float(result['flooding_factor']):.4f} kg/m³")
    detail2.caption(f"Factor atmosférico: {float(result['altitude_factor']):.4f}")
    detail3.caption(
        f"Mínimo técnico: {int(result['nozzle_min_qty'])} · Recomendado: {int(result['nozzle_recommended_qty'])}"
    )
    st.markdown(
        f"""
        <div class="technical-note">
            Perfil: <strong>{result.get('concentration_profile_label', 'Manual')}</strong> ·
            Concentración diseño: <strong>{float(result.get('design_concentration_applied_pct', 0.0)):.3f}%</strong><br>
            Agente recinto: <strong>{float(result.get('enclosure_agent_required_exact_kg', result['agent_required_exact_kg'])):,.2f} kg</strong> ·
            Tubería/manifold: <strong>{float(result.get('pipe_agent_allowance_kg', 0.0)):,.2f} kg</strong> ·
            Total exacto: <strong>{float(result['agent_required_exact_kg']):,.2f} kg</strong><br>
            Concentración ajustada: <strong>{float(result['minimum_concentration_achieved_pct']):.3f}%</strong> ·
            Concentración máxima: <strong>{float(result['maximum_concentration_achieved_pct']):.2f}%</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Distribución mínima por volumen: {result['nozzle_area_summary']}")

    if cylinder is not None:
        fill_pct = float(cylinder["fill_pct_of_max"])
        st.info(
            f"Cilindro seleccionado: {int(cylinder['quantity'])} × {cylinder['cylinder_label']} "
            f"({cylinder['cylinder_code']}) · {float(cylinder['fill_per_cylinder_kg']):.1f} kg / "
            f"{float(cylinder['fill_per_cylinder_lb']):.1f} lb por cilindro · {fill_pct:.1f}% del máximo."
        )

    _render_inline_cylinder_options(room_id, result, catalogs)
    warnings = result.get("warnings", [])
    if isinstance(warnings, list):
        for warning in warnings:
            st.warning(warning)
    for message in st.session_state.get("calculation_errors", []):
        if room_id in message:
            st.error(message)


def _render_inline_cylinder_options(
    room_id: str,
    result: pd.Series,
    catalogs: dict[str, pd.DataFrame],
) -> None:
    rooms_df = st.session_state["rooms_df"]
    room_rows = rooms_df[rooms_df["room_id"].astype(str) == room_id]
    if room_rows.empty:
        return
    room_row = room_rows.iloc[0]
    alternatives = list_valid_cylinder_selections(
        room_id=room_id,
        agent_required_kg=float(result["agent_required_rounded_kg"]),
        agent_type=AgentType(str(room_row["agent_type"])),
        system_type=SystemType(str(room_row["system_type"])),
        catalog_df=catalogs["cylinders"],
    )
    if not alternatives:
        st.error("No hay una configuración de cilindros válida para esta cantidad de agente.")
        return

    labels_by_key: dict[str, tuple[str, int] | None] = {}
    automatic = alternatives[0]
    automatic_label = (
        f"Automático recomendado · {automatic.quantity} × {automatic.cylinder.cylinder_label} · "
        f"{automatic.fill_per_cylinder_kg:.1f} kg/cil"
    )
    labels_by_key[automatic_label] = None
    for item in alternatives:
        fill_pct = item.fill_per_cylinder_kg / item.cylinder.max_fill_kg * 100
        label = (
            f"{item.quantity} × {item.cylinder.cylinder_label} · {item.cylinder.cylinder_code} · "
            f"{item.fill_per_cylinder_kg:.1f} kg/cil · {fill_pct:.1f}%"
        )
        labels_by_key[label] = (item.cylinder.cylinder_code, item.quantity)

    current_code = _extract_cylinder_code(str(room_row.get("forced_cylinder_code", "Automático")))
    current_qty = int(room_row.get("forced_cylinder_qty", 1) or 1)
    current_index = 0
    if current_code:
        for option_index, value in enumerate(labels_by_key.values()):
            if value == (current_code, current_qty):
                current_index = option_index
                break

    with st.form(f"cylinder_form_{room_id}"):
        selected_label = st.selectbox(
            "Configuración de cilindros",
            list(labels_by_key),
            index=current_index,
            help="Solo se muestran configuraciones dentro del rango absoluto de llenado.",
        )
        apply_selection = st.form_submit_button("Aplicar configuración", use_container_width=True)

    if apply_selection:
        selection = labels_by_key[selected_label]
        current = st.session_state["rooms_df"].copy()
        mask = current["room_id"].astype(str) == room_id
        current.loc[mask, "forced_cylinder_code"] = "Automático" if selection is None else selection[0]
        current.loc[mask, "forced_cylinder_qty"] = 1 if selection is None else selection[1]
        st.session_state["rooms_df"] = current
        _calculate_selected_rooms(catalogs)
        st.session_state["room_flash"] = "Configuración de cilindros actualizada."
        st.rerun()


def _delete_room(room_id: str) -> None:
    rooms_df = st.session_state.get("rooms_df", pd.DataFrame())
    if rooms_df.empty:
        return
    st.session_state["rooms_df"] = delete_room_by_id(rooms_df, room_id)
    if st.session_state.get("active_room_id") == room_id:
        st.session_state.pop("active_room_id", None)
    _calculate_selected_rooms(_load_catalogs(_catalog_cache_key()))


def _render_cylinder_override_controls() -> None:
    rooms_df = st.session_state.get("rooms_df", _default_rooms_df())
    if rooms_df.empty:
        return

    st.divider()
    st.write("**Selección manual de cilindro**")
    st.caption("Usa este control si quieres cambiar el cilindro recomendado automáticamente para una sala específica.")

    room_names = rooms_df["name"].astype(str).tolist()
    selected_room_name = st.selectbox("Sala a ajustar", room_names, key="cylinder_override_room")
    selected_index = int(rooms_df[rooms_df["name"].astype(str) == selected_room_name].index[0])
    selected_agent = str(rooms_df.loc[selected_index, "agent_type"])
    options = _cylinder_option_labels(selected_agent)
    current_value = str(rooms_df.loc[selected_index].get("forced_cylinder_code", "Automático"))
    current_index = options.index(current_value) if current_value in options else 0
    selected_cylinder_label = st.selectbox("Cilindro para esta sala", options, index=current_index)

    col1, col2 = st.columns([1, 3], gap="small")
    with col1:
        if st.button("Aplicar cilindro", type="primary", use_container_width=True):
            updated_rooms_df = rooms_df.copy()
            updated_rooms_df.loc[selected_index, "forced_cylinder_code"] = selected_cylinder_label
            st.session_state["rooms_df"] = _clean_rooms_df(updated_rooms_df)
            _invalidate_calculation_state()
            st.success("Cilindro actualizado. Calcula nuevamente en la pestaña Resultados.")
            st.rerun()
    with col2:
        st.caption(f"Agente de la sala: {selected_agent}. Selección actual: {selected_cylinder_label}.")


def _render_room_actions() -> None:
    rooms_df = st.session_state.get("rooms_df", _default_rooms_df())
    rooms_preview_df = _rooms_with_preview(rooms_df)
    selected_qty = int(rooms_preview_df.get("selected", pd.Series(dtype=bool)).map(_as_bool).sum()) if not rooms_preview_df.empty else 0
    remove_qty = int(rooms_preview_df.get("remove", pd.Series(dtype=bool)).map(_as_bool).sum()) if not rooms_preview_df.empty else 0
    col1, col2, col3 = st.columns([1, 1, 3], gap="small")
    with col1:
        if st.button("Agregar sala", use_container_width=True):
            _add_room()
            st.rerun()
    with col2:
        if st.button("Quitar salas", use_container_width=True, disabled=remove_qty == 0):
            _remove_selected_rooms()
            st.rerun()
    with col3:
        st.caption(
            f"Salas cargadas: {len(rooms_preview_df)} · Marcadas para cálculo: {selected_qty}. "
            "Marca Quitar solo en las filas que quieres eliminar."
        )


def _add_room() -> None:
    rooms_df = st.session_state.get("rooms_df", _default_rooms_df()).copy()
    next_index = len(rooms_df) + 1
    existing_names = set(rooms_df.get("name", pd.Series(dtype=str)).astype(str))
    while f"Sala {next_index}" in existing_names:
        next_index += 1
    new_room = _new_room_row(next_index)
    rooms_df = pd.concat([rooms_df, pd.DataFrame([new_room])], ignore_index=True)
    st.session_state["rooms_df"] = _clean_rooms_df(rooms_df)
    st.session_state["active_room_id"] = new_room["room_id"]
    _invalidate_calculation_state()
    st.session_state["rooms_editor_version"] = st.session_state.get("rooms_editor_version", 0) + 1


def _remove_selected_rooms() -> None:
    rooms_df = _rooms_with_preview(st.session_state.get("rooms_df", _default_rooms_df())).copy()
    if rooms_df.empty:
        return
    keep_mask = ~rooms_df["remove"].map(_as_bool)
    remaining = rooms_df[keep_mask].reset_index(drop=True)
    st.session_state["rooms_df"] = _clean_rooms_df(remaining if not remaining.empty else pd.DataFrame([_new_room_row(1)]))
    _invalidate_calculation_state()
    st.session_state["rooms_editor_version"] = st.session_state.get("rooms_editor_version", 0) + 1


def _invalidate_calculation_state() -> None:
    for key in [
        "results_df",
        "selected_cylinders_df",
        "calculated_rooms",
        "calculation_errors",
        "calculated_room_pairs",
        "bom_detail_df",
        "bom_consolidated_df",
    ]:
        st.session_state.pop(key, None)


def _render_results_tab(catalogs: dict[str, pd.DataFrame]) -> None:
    _section_header(
        "Resultados técnicos",
        "Calcula las salas marcadas. Los errores quedan asociados a cada sala para corregir rápido.",
    )

    if st.button("Recalcular todas las salas", type="primary", use_container_width=True):
        _calculate_selected_rooms(catalogs)

    results_df = st.session_state.get("results_df", pd.DataFrame())
    cylinders_df = st.session_state.get("selected_cylinders_df", pd.DataFrame())
    errors = st.session_state.get("calculation_errors", [])

    if errors:
        with st.expander(f"Revisar advertencias y errores ({len(errors)})", expanded=True):
            for message in errors:
                st.warning(message)

    if results_df.empty:
        st.info("Aún no hay resultados. Revisa las salas y presiona calcular.")
        return

    col1, col2, col3, col4 = st.columns(4, gap="small")
    col1.metric("Volumen neto total", f"{results_df['net_volume_m3'].sum():,.1f} m³")
    col2.metric("Agente total", f"{results_df['agent_required_rounded_kg'].sum():,.1f} kg")
    col3.metric("Agente total", f"{results_df['agent_required_rounded_lb'].sum():,.1f} lb")
    col4.metric("Cilindros", f"{int(cylinders_df['quantity'].sum()) if not cylinders_df.empty else 0}")

    st.write("**Resumen por sala**")
    st.dataframe(_results_display_df(results_df), use_container_width=True, hide_index=True)

    st.write("**Cilindros seleccionados**")
    st.dataframe(_cylinders_display_df(cylinders_df), use_container_width=True, hide_index=True)
    st.warning(COMPLIANCE_NOTE)


def _render_cylinder_preview(catalogs: dict[str, pd.DataFrame]) -> None:
    calculated_rooms = st.session_state.get("calculated_rooms", [])
    if not calculated_rooms:
        return
    with st.expander("Previsualizar alternativas de cilindro", expanded=False):
        room_names = [item["room"].name for item in calculated_rooms]
        selected_room_name = st.selectbox("Sala", room_names, key="cylinder_preview_room")
        selected_item = next(item for item in calculated_rooms if item["room"].name == selected_room_name)
        preview_df = _cylinder_preview_df(
            selected_item["room"].agent_type.value,
            selected_item["result"].agent_required_rounded_kg,
            catalogs["cylinders"],
        )
        st.dataframe(preview_df.drop(columns=["option_label"]), use_container_width=True, hide_index=True)

        valid_options_df = preview_df[preview_df["Estado"] != "Fuera de rango"]
        if valid_options_df.empty:
            st.warning("No hay cilindros dentro del rango absoluto para esta carga.")
            return

        selected_option = st.selectbox(
            "Aplicar cilindro a esta sala",
            valid_options_df["option_label"].tolist(),
            key=f"apply_cylinder_{selected_item['room'].room_id}",
        )
        selected_status = valid_options_df[valid_options_df["option_label"] == selected_option]["Estado"].iloc[0]
        col1, col2 = st.columns([1, 3], gap="small")
        with col1:
            if st.button(
                "Aplicar cilindro",
                type="primary",
                use_container_width=True,
                key=f"apply_cylinder_button_{selected_item['room'].room_id}",
            ):
                _apply_cylinder_override_by_room_id(selected_item["room"].room_id, selected_option)
                st.success("Cilindro aplicado. Calcula nuevamente para actualizar resultados y BOM.")
                st.rerun()
        with col2:
            st.caption(f"Estado de la alternativa seleccionada: {selected_status}.")


def _cylinder_preview_df(agent_type: str, agent_required_kg: float, cylinder_catalog_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in cylinder_catalog_df[cylinder_catalog_df["agent_type"] == agent_type].sort_values("size_l").iterrows():
        max_fill_kg = float(row["max_fill_kg"])
        min_fill_kg = float(row["min_fill_kg"])
        fill_pct = (agent_required_kg / max_fill_kg) * 100
        recommended_pct = float(row.get("recommended_max_fill_pct", 85))
        in_range = min_fill_kg <= agent_required_kg <= max_fill_kg
        rows.append(
            {
                "option_label": f"{agent_type} · {row['cylinder_label']} · {row['cylinder_code']}",
                "Cilindro": row["cylinder_label"],
                "Código": row["cylinder_code"],
                "Agente lb": round(agent_required_kg * KG_TO_LB, 2),
                "Rango lb": f"{row['min_fill_lb']:.0f}-{row['max_fill_lb']:.0f}",
                "% llenado": round(fill_pct, 2),
                "% recomendado": recommended_pct,
                "Estado": _fill_status(in_range, fill_pct, recommended_pct),
            }
        )
    return pd.DataFrame(rows)


def _apply_cylinder_override_by_room_id(room_id: str, cylinder_option_label: str) -> None:
    rooms_df = st.session_state.get("rooms_df", _default_rooms_df()).copy()
    try:
        room_index = int(room_id.split("-")[-1]) - 1
    except ValueError:
        room_index = 0

    if room_index < 0 or room_index >= len(rooms_df):
        st.warning("No se encontró la sala para aplicar el cilindro.")
        return

    rooms_df.loc[room_index, "forced_cylinder_code"] = cylinder_option_label
    st.session_state["rooms_df"] = _clean_rooms_df(rooms_df)
    _invalidate_calculation_state()


def _fill_status(in_range: bool, fill_pct: float, recommended_pct: float) -> str:
    if not in_range:
        return "Fuera de rango"
    if fill_pct <= 80:
        return "OK"
    if fill_pct <= recommended_pct + 0.5:
        return "Cerca del límite"
    return "Sobre recomendado"


def _render_bom_tab(catalogs: dict[str, pd.DataFrame]) -> None:
    _section_header("BOM y opcionales", "Selecciona opcionales, genera el BOM y descarga el Excel de cotización.")
    calculated_rooms = st.session_state.get("calculated_rooms", [])
    if not calculated_rooms:
        st.info("Calcula primero las salas seleccionadas.")
        return
    selected_ids = {
        str(row["room_id"])
        for _, row in st.session_state.get("rooms_df", pd.DataFrame()).iterrows()
        if _as_bool(row.get("selected", True))
    }
    valid_ids = {item["room"].room_id for item in calculated_rooms}
    if selected_ids - valid_ids:
        st.error("Hay salas incluidas sin una configuración técnica válida. Corrígelas antes de generar el BOM.")
        return

    st.markdown(
        '<p class="small-note">Los opcionales se aplican a las salas compatibles que tengan opcionales activos.</p>',
        unsafe_allow_html=True,
    )
    options_df = _combined_available_options(calculated_rooms, catalogs["optional"])
    if not options_df.empty:
        edited_options_df = st.data_editor(
            options_df[["selected", "quantity", "agent_type", "system_type", "code", "product", "unit", "notes", "unit_price"]],
            use_container_width=True,
            hide_index=True,
            disabled=["agent_type", "system_type", "code", "product", "unit", "notes"],
            column_config={
                "selected": st.column_config.CheckboxColumn("Incluir"),
                "quantity": st.column_config.NumberColumn("Cant.", min_value=0.0, step=1.0),
                "agent_type": st.column_config.TextColumn("Agente"),
                "system_type": st.column_config.TextColumn("Sistema"),
                "code": st.column_config.TextColumn("Código"),
                "product": st.column_config.TextColumn("Producto", width="large"),
                "unit": st.column_config.TextColumn("U/M"),
                "notes": st.column_config.TextColumn("Notas", width="medium"),
                "unit_price": st.column_config.NumberColumn("Precio", min_value=0.0),
            },
            key="options_editor",
        )
    else:
        edited_options_df = pd.DataFrame()
        st.info("No hay opcionales compatibles para las salas calculadas.")

    left, right = st.columns([1, 1], gap="medium")
    with left:
        generate_bom = st.button("Generar BOM", type="primary", use_container_width=True)
    with right:
        st.caption("Después de generar el BOM podrás descargar el Excel.")

    if generate_bom:
        _build_quote_bom(catalogs, edited_options_df)

    bom_detail_df = st.session_state.get("bom_detail_df", pd.DataFrame())
    bom_consolidated_df = st.session_state.get("bom_consolidated_df", pd.DataFrame())
    if bom_detail_df.empty:
        st.info("Aún no hay BOM generado.")
        return

    col1, col2, col3 = st.columns(3, gap="small")
    col1.metric("Ítems detalle", len(bom_detail_df))
    col2.metric("Códigos consolidados", len(bom_consolidated_df))
    col3.metric("Salas en BOM", bom_detail_df["room_id"].nunique())

    detail_tab, consolidated_tab = st.tabs(["Detalle", "Consolidado"])
    with detail_tab:
        st.dataframe(_bom_detail_display_df(bom_detail_df), use_container_width=True, hide_index=True)
    with consolidated_tab:
        st.dataframe(_bom_consolidated_display_df(bom_consolidated_df), use_container_width=True, hide_index=True)

    _render_excel_download()


def _calculate_selected_rooms(catalogs: dict[str, pd.DataFrame]) -> None:
    rooms_df = st.session_state.get("rooms_df", _default_rooms_df())
    rooms: list[tuple[RoomInput, SystemConfig]] = []
    results: list[dict[str, object]] = []
    cylinders: list[dict[str, object]] = []
    errors: list[str] = []
    calculated_rooms: list[dict[str, object]] = []

    for index, row in rooms_df.iterrows():
        if not _as_bool(row.get("selected", True)):
            continue
        try:
            room, config = _row_to_room_and_config(index, row)
            result = calculate_room_requirements(
                room=room,
                config=config,
                flooding_factors_df=catalogs["flooding"],
                altitude_factors_df=catalogs["altitude"],
                nozzle_catalog_df=catalogs["nozzles"],
                concentration_profiles_df=catalogs["concentration_profiles"],
                dead_volume_factors_df=catalogs["dead_volume"],
            )
            rooms.append((room, config))
            try:
                selected_cylinder = select_cylinder(
                    room_id=room.room_id,
                    agent_required_kg=result.agent_required_rounded_kg,
                    agent_type=room.agent_type,
                    system_type=config.system_type,
                    catalog_df=catalogs["cylinders"],
                    forced_cylinder_code=config.forced_cylinder_code if config.force_cylinder else None,
                    forced_cylinder_qty=config.forced_cylinder_qty if config.force_cylinder else None,
                )
            except ValueError as exc:
                results.append(_result_row(room, config, result))
                errors.append(f"{room.room_id} · {room.name}: {exc}")
                continue
            result.warnings.extend(selected_cylinder.warnings)
            results.append(_result_row(room, config, result))
            cylinders.append(_cylinder_row(room, config, selected_cylinder))
            calculated_rooms.append(
                {"room": room, "config": config, "result": result, "selected_cylinder": selected_cylinder}
            )
            if config.include_reserve:
                errors.append(f"{room.name}: Reserva marcada; BOM específico de reserva pendiente de implementación.")
            if config.include_main_reserve:
                errors.append(f"{room.name}: Main reserve marcado; BOM específico de main reserve pendiente de implementación.")
            for warning in result.warnings:
                errors.append(f"{room.name}: {warning}")
        except (TypeError, ValueError) as exc:
            errors.append(f"{row.get('room_id', f'Fila {index + 1}')} · {row.get('name', 'Sala')}: {exc}")

    st.session_state["calculated_room_pairs"] = rooms
    st.session_state["results_df"] = pd.DataFrame(results)
    st.session_state["selected_cylinders_df"] = pd.DataFrame(cylinders)
    st.session_state["calculated_rooms"] = calculated_rooms
    st.session_state["calculation_errors"] = errors
    st.session_state["bom_detail_df"] = pd.DataFrame()
    st.session_state["bom_consolidated_df"] = pd.DataFrame()


def _render_excel_download() -> None:
    project_info = st.session_state.get("project_info")
    rooms_df = st.session_state.get("rooms_df", pd.DataFrame())
    results_df = st.session_state.get("results_df", pd.DataFrame())
    cylinders_df = st.session_state.get("selected_cylinders_df", pd.DataFrame())
    bom_detail_df = st.session_state.get("bom_detail_df", pd.DataFrame())
    bom_consolidated_df = st.session_state.get("bom_consolidated_df", pd.DataFrame())
    warnings = st.session_state.get("calculation_errors", [])

    excel_bytes = export_quote_to_excel(
        project_info=project_info,
        rooms_df=rooms_df,
        results_df=results_df,
        cylinders_df=cylinders_df,
        bom_detail_df=_excel_ready_df(bom_detail_df),
        bom_consolidated_df=_excel_ready_df(bom_consolidated_df),
        warnings=warnings,
    )
    file_name = _quote_file_name(project_info)

    st.divider()
    st.download_button(
        label="Descargar Excel de cotización",
        data=excel_bytes,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )


def _section_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">{title}</div>
            <div class="section-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _results_display_df(results_df: pd.DataFrame) -> pd.DataFrame:
    columns = {
        "room_name": "Sala",
        "system_type": "Sistema",
        "agent_type": "Agente",
        "area_m2": "Área m²",
        "net_volume_m3": "Vol. neto m³",
        "concentration_profile_label": "Perfil",
        "design_concentration_applied_pct": "Conc. diseño %",
        "flooding_factor": "Flooding",
        "altitude_factor": "Factor atm.",
        "enclosure_agent_required_exact_kg": "Agente recinto kg",
        "pipe_agent_allowance_kg": "Tubería kg",
        "agent_required_exact_kg": "Mínimo kg",
        "agent_required_rounded_kg": "Ajustado kg",
        "agent_required_rounded_lb": "Ajustado lb",
        "minimum_concentration_achieved_pct": "Conc. ajustada %",
        "maximum_concentration_achieved_pct": "Conc. máx. %",
        "nozzle_min_qty": "Boquillas",
        "nozzle_recommended_qty": "Boquillas recomendadas",
        "nozzle_final_qty": "Boquillas finales",
    }
    return _rename_existing_columns(results_df, columns)


def _cylinders_display_df(cylinders_df: pd.DataFrame) -> pd.DataFrame:
    columns = {
        "room_name": "Sala",
        "system_type": "Sistema",
        "agent_type": "Agente",
        "cylinder_label": "Cilindro",
        "cylinder_code": "Código",
        "quantity": "Cant.",
        "fill_per_cylinder_kg": "Kg/cilindro",
        "fill_per_cylinder_lb": "Lb/cilindro",
        "fill_pct_of_max": "% llenado máx.",
        "recommended_max_fill_pct": "% recomendado",
        "fill_status": "Estado llenado",
        "total_fill_kg": "Kg total",
        "total_fill_lb": "Lb total",
        "min_fill_lb": "Mín lb",
        "max_fill_lb": "Máx lb",
    }
    return _rename_existing_columns(cylinders_df, columns)


def _bom_detail_display_df(bom_detail_df: pd.DataFrame) -> pd.DataFrame:
    columns = {
        "room_name": "Sala",
        "system_type": "Sistema",
        "bom_type": "Tipo",
        "agent_type": "Agente",
        "cylinder_label": "Cilindro",
        "code": "Código",
        "product": "Producto",
        "unit": "U/M",
        "quantity": "Cant.",
        "unit_price": "Precio",
        "total_price": "Total",
        "delivery": "Entrega",
    }
    return _rename_existing_columns(_excel_ready_df(bom_detail_df), columns)


def _bom_consolidated_display_df(bom_consolidated_df: pd.DataFrame) -> pd.DataFrame:
    columns = {
        "code": "Código",
        "product": "Producto",
        "unit": "U/M",
        "unit_price": "Precio",
        "quantity": "Cant.",
        "total_price": "Total",
    }
    return _rename_existing_columns(_excel_ready_df(bom_consolidated_df), columns)


def _rename_existing_columns(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    existing = [column for column in columns if column in df.columns]
    return df[existing].rename(columns=columns)


def _excel_ready_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cleaned = df.copy()
    for column in cleaned.columns:
        cleaned[column] = cleaned[column].map(lambda value: getattr(value, "value", value))
    return cleaned


def _quote_file_name(project_info: ProjectInfo | None) -> str:
    if project_info is None:
        return "cotizacion_supresion.xlsx"
    client = _slug(project_info.client or "cliente")
    quote_date = project_info.quote_date.isoformat() if project_info.quote_date else date.today().isoformat()
    return f"cotizacion_supresion_{client}_{quote_date}.xlsx"


def _slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").lower()
    return normalized or "cliente"


def _build_quote_bom(catalogs: dict[str, pd.DataFrame], edited_options_df: pd.DataFrame) -> None:
    all_lines = []
    for item in st.session_state.get("calculated_rooms", []):
        room = item["room"]
        config = item["config"]
        result = item["result"]
        selected_cylinder = item["selected_cylinder"]
        all_lines.extend(build_system_bom(room, result, selected_cylinder, config, catalogs["bom"]))
        room_options = _filter_options_for_room(room, config, edited_options_df)
        all_lines.extend(build_optional_bom(room, config, catalogs["optional"], room_options, selected_cylinder))

    bom_detail_df = bom_lines_to_dataframe(all_lines)
    st.session_state["bom_detail_df"] = bom_detail_df
    st.session_state["bom_consolidated_df"] = consolidate_bom(bom_detail_df)


def _combined_available_options(calculated_rooms: list[dict[str, object]], optional_items_df: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for item in calculated_rooms:
        room = item["room"]
        config = item["config"]
        if config.include_optional_items:
            frames.append(available_options(room, config, optional_items_df))
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["agent_type", "system_type", "code"], keep="first")
    return combined.sort_values(["agent_type", "system_type", "product"])


def _filter_options_for_room(room: RoomInput, config: SystemConfig, edited_options_df: pd.DataFrame) -> pd.DataFrame:
    if edited_options_df.empty:
        return edited_options_df
    return edited_options_df[
        (edited_options_df["agent_type"] == room.agent_type.value)
        & (edited_options_df["system_type"].isin([config.system_type.value, SystemType.SYSTEM.value]))
    ].copy()


def _default_rooms_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _new_room_row(1, "Sala UPS", AgentType.FM200, SystemType.SYSTEM),
            _new_room_row(2, "Sala servidores", AgentType.FK5112, SystemType.SYSTEM, length_m=16.0, width_m=8.0, height_m=3.2),
        ]
    )


def _new_room_row(
    index: int,
    name: str | None = None,
    agent_type: AgentType = AgentType.FM200,
    system_type: SystemType = SystemType.SYSTEM,
    length_m: float = 10.0,
    width_m: float = 5.0,
    height_m: float = 3.0,
) -> dict[str, object]:
    return {
        "room_id": f"ROOM-{uuid4().hex[:10].upper()}",
        "remove": False,
        "selected": True,
        "name": name or f"Sala {index}",
        "system_type": system_type.value,
        "agent_type": agent_type.value,
        "forced_cylinder_code": "Automático",
        "forced_cylinder_qty": 1,
        "length_m": length_m,
        "width_m": width_m,
        "height_m": height_m,
        "raised_floor_m": 0.0,
        "false_ceiling_m": 0.0,
        "protect_raised_floor": False,
        "protect_false_ceiling": False,
        "structural_reductions_m3": 0.0,
        "object_reductions_m3": 0.0,
        "min_temp_c": 18.0,
        "max_temp_c": 27.0,
        "design_concentration_pct": 7.0 if agent_type == AgentType.FM200 else 4.52,
        "concentration_profile_id": "FM_ULFM_A" if agent_type == AgentType.FM200 else "FK_ULFM_C_452",
        "altitude_m": 0.0,
        "discharge_connection": DischargeConnection.FLEXIBLE.value,
        "include_optional_items": True,
        "include_reserve": False,
        "include_main_reserve": False,
        "override_nozzles": False,
        "nozzle_qty_manual": None,
        "nozzle_override_reason": None,
        "object_reductions_are_permanent": True,
        "manifold_nominal_diameter_dn": None,
        "reserve_sections_qty": 0,
        "custom_dead_volume_l": 0.0,
    }


def _rooms_with_preview(rooms_df: pd.DataFrame) -> pd.DataFrame:
    cleaned = _clean_rooms_df(rooms_df)
    area = cleaned["length_m"].astype(float) * cleaned["width_m"].astype(float)
    volume_room = area * cleaned["height_m"].astype(float)
    volume_raised_floor = area * cleaned["raised_floor_m"].astype(float) * cleaned["protect_raised_floor"].map(_as_bool)
    volume_false_ceiling = (
        area * cleaned["false_ceiling_m"].astype(float) * cleaned["protect_false_ceiling"].map(_as_bool)
    )
    gross_volume = volume_room + volume_raised_floor + volume_false_ceiling
    reductions = cleaned["structural_reductions_m3"].astype(float) + cleaned["object_reductions_m3"].astype(float)

    cleaned["area_m2"] = area.round(2)
    cleaned["gross_volume_m3"] = gross_volume.round(2)
    cleaned["net_volume_m3"] = (gross_volume - reductions).round(2)
    return cleaned


def _clean_rooms_df(rooms_df: pd.DataFrame) -> pd.DataFrame:
    cleaned = rooms_df.copy()
    if cleaned.empty:
        return pd.DataFrame(columns=ROOM_COLUMNS)
    defaults = _new_room_row(1)
    for column in ROOM_COLUMNS:
        if column not in cleaned.columns:
            if column == "room_id":
                cleaned[column] = [f"ROOM-{uuid4().hex[:10].upper()}" for _ in range(len(cleaned))]
            else:
                cleaned[column] = defaults[column]
    cleaned = cleaned[ROOM_COLUMNS]
    cleaned = cleaned[cleaned["name"].notna() & (cleaned["name"].astype(str).str.strip() != "")]
    return cleaned.reset_index(drop=True)


def _row_to_room_and_config(index: int, row: pd.Series) -> tuple[RoomInput, SystemConfig]:
    room_id = str(row["room_id"])
    min_temp_c = float(row["min_temp_c"])
    max_temp_c = float(row["max_temp_c"])
    if min_temp_c > max_temp_c:
        raise ValueError("La temperatura mínima no puede ser mayor que la máxima.")

    room = RoomInput(
        room_id=room_id,
        name=str(row["name"]).strip(),
        agent_type=AgentType(str(row["agent_type"])),
        length_m=float(row["length_m"]),
        width_m=float(row["width_m"]),
        height_m=float(row["height_m"]),
        raised_floor_m=float(row["raised_floor_m"]),
        false_ceiling_m=float(row["false_ceiling_m"]),
        structural_reductions_m3=float(row["structural_reductions_m3"]),
        object_reductions_m3=float(row["object_reductions_m3"]),
        min_temp_c=min_temp_c,
        max_temp_c=max_temp_c,
        normal_temp_c=(min_temp_c + max_temp_c) / 2,
        design_concentration_pct=float(row["design_concentration_pct"]),
        altitude_m=float(row["altitude_m"]),
        protect_raised_floor=_as_bool(row["protect_raised_floor"]),
        protect_false_ceiling=_as_bool(row["protect_false_ceiling"]),
        concentration_profile_id=(
            str(row["concentration_profile_id"])
            if pd.notna(row.get("concentration_profile_id")) and str(row.get("concentration_profile_id", "")).strip()
            else None
        ),
        object_reductions_are_permanent=_as_bool(row.get("object_reductions_are_permanent", True)),
    )
    config = SystemConfig(
        room_id=room_id,
        system_type=SystemType(str(row["system_type"])),
        discharge_connection=DischargeConnection(str(row["discharge_connection"])),
        include_optional_items=_as_bool(row["include_optional_items"]),
        include_reserve=_as_bool(row["include_reserve"]),
        include_main_reserve=_as_bool(row["include_main_reserve"]),
        force_cylinder=str(row.get("forced_cylinder_code", "Automático")) not in {"Automático", "None", ""},
        forced_cylinder_code=_extract_cylinder_code(str(row.get("forced_cylinder_code", "Automático"))),
        forced_cylinder_qty=int(row.get("forced_cylinder_qty", 1) or 1),
        override_nozzles=_as_bool(row.get("override_nozzles", False)),
        nozzle_qty_manual=(
            int(row["nozzle_qty_manual"])
            if _as_bool(row.get("override_nozzles", False)) and pd.notna(row.get("nozzle_qty_manual"))
            else None
        ),
        nozzle_override_reason=(
            str(row["nozzle_override_reason"])
            if pd.notna(row.get("nozzle_override_reason")) and str(row.get("nozzle_override_reason", "")).strip()
            else None
        ),
        manifold_nominal_diameter_dn=(
            int(row["manifold_nominal_diameter_dn"])
            if pd.notna(row.get("manifold_nominal_diameter_dn"))
            else None
        ),
        reserve_sections_qty=int(row.get("reserve_sections_qty", 0) or 0),
        custom_dead_volume_l=float(row.get("custom_dead_volume_l", 0.0) or 0.0),
    )
    return room, config


def _result_row(room: RoomInput, config: SystemConfig, result: object) -> dict[str, object]:
    data = _json_ready(asdict(result))
    data["agent_required_exact_lb"] = float(data["agent_required_exact_kg"]) * KG_TO_LB
    data["agent_required_rounded_lb"] = float(data["agent_required_rounded_kg"]) * KG_TO_LB
    data.update({"room_name": room.name, "agent_type": room.agent_type.value, "system_type": config.system_type.value})
    return data


def _cylinder_row(room: RoomInput, config: SystemConfig, selected_cylinder: object) -> dict[str, object]:
    fill_per_cylinder_lb = selected_cylinder.fill_per_cylinder_kg * KG_TO_LB
    total_fill_lb = selected_cylinder.total_fill_kg * KG_TO_LB
    max_fill_kg = selected_cylinder.cylinder.max_fill_kg
    fill_pct = (selected_cylinder.fill_per_cylinder_kg / max_fill_kg) * 100 if max_fill_kg else 0
    recommended_pct = selected_cylinder.cylinder.recommended_max_fill_pct
    return {
        "room_id": room.room_id,
        "room_name": room.name,
        "system_type": config.system_type.value,
        "agent_type": room.agent_type.value,
        "cylinder_label": selected_cylinder.cylinder.cylinder_label,
        "cylinder_code": selected_cylinder.cylinder.cylinder_code,
        "quantity": selected_cylinder.quantity,
        "fill_per_cylinder_kg": selected_cylinder.fill_per_cylinder_kg,
        "fill_per_cylinder_lb": fill_per_cylinder_lb,
        "total_fill_kg": selected_cylinder.total_fill_kg,
        "total_fill_lb": total_fill_lb,
        "min_fill_kg": selected_cylinder.cylinder.min_fill_kg,
        "max_fill_kg": selected_cylinder.cylinder.max_fill_kg,
        "min_fill_lb": selected_cylinder.cylinder.min_fill_kg * KG_TO_LB,
        "max_fill_lb": selected_cylinder.cylinder.max_fill_kg * KG_TO_LB,
        "fill_pct_of_max": fill_pct,
        "recommended_max_fill_pct": recommended_pct,
        "fill_status": _fill_status(True, fill_pct, recommended_pct),
    }


def _json_ready(data: dict[str, object]) -> dict[str, object]:
    return {key: getattr(value, "value", value) for key, value in data.items()}


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "si", "sí"}
