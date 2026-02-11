import base64
import io
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ======================
# CONFIG GERAL
# ======================
st.set_page_config(page_title="Painel NIR - Censo Diário", layout="wide")

TIMEZONE = "America/Sao_Paulo"

PRIMARY = "#163A9A"
PRIMARY_DARK = "#0B2B6B"
ACCENT_GREEN = "#22A34A"
SCS_PURPLE = "#4B3FA6"
SCS_CYAN = "#33C7D6"

BG = "#F6F8FB"
CARD_BG = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT = "#0F172A"
MUTED = "#64748B"

LOGO_LEFT_PATH = Path("assets/logo_esquerda.png")
LOGO_RIGHT_PATH = Path("assets/logo_direita.png")

SHEET_ID = "1wA--gbvOmHWcUvMBTldVC8HriI3IXfQoEvQEskCKGDk"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Folha1"

REFRESH_SECONDS = 60
st_autorefresh(interval=REFRESH_SECONDS * 1000, key="nir_autorefresh")


def agora_local() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))


# ======================
# CSS (números centralizados + título "Altas previstas..." em 2 linhas)
# ======================
st.markdown(
    f"""
    <style>
      .stApp {{
        background: {BG};
        color: {TEXT};
      }}

      /* Header: mobile-first com logos maiores e faixa central menor */
      .nir-header {{
        display: grid;
        grid-template-columns: 86px 1fr 86px;
        gap: 10px;
        align-items: stretch;
        width: 100%;
      }}

      .nir-header-box {{ border-radius: 16px; }}

      .nir-header-logo {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        display: flex;
        align-items: center;
        justify-content: center;
        height: var(--nir-header-h);
        padding: 6px;
      }}

      .nir-header-logo img {{
        height: var(--nir-logo-h);
        width: auto;
        object-fit: contain;
        display: block;
      }}

      .nir-header-center {{
        border: 1px solid rgba(255,255,255,0.15);
        background: linear-gradient(90deg, {PRIMARY_DARK}, {PRIMARY} 45%, {SCS_PURPLE});
        color: white;
        height: var(--nir-header-h);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 6px 10px;
      }}

      .nir-top-title {{
        font-weight: 980;
        letter-spacing: 0.2px;
        line-height: 1.06;
        margin: 0;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        overflow: hidden;
      }}

      /* Subtítulo removido */
      .nir-top-sub {{
        display: none;
      }}

      /* Métricas - GRID com colunas mais estreitas */
      .nir-metrics-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-top: 10px;
      }}

      /* Cards - centralização TOTAL */
      .nir-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 12px 10px; /* padding menor para colunas mais estreitas */
        box-shadow: 0 1px 0 rgba(16,24,40,0.02);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        min-height: 100px;
      }}

      .nir-card-title {{
        color: {MUTED};
        font-weight: 800;
        margin-bottom: 8px;
        font-size: 12px;
        text-align: center;
        line-height: 1.2;
        width: 100%;
      }}

      .nir-card-value {{
        font-weight: 950;
        margin: 0;
        line-height: 1.0;
        font-size: 22px;
        text-align: center;
        width: 100%;
      }}

      /* Classe especial para título em duas linhas */
      .two-line-title {{
        line-height: 1.1;
        white-space: normal;
        display: block;
      }}

      .nir-section-title {{
        font-weight: 950;
        margin-bottom: 8px;
        color: {TEXT};
        font-size: 15px;
      }}

      /* Lista mobile */
      .nir-list {{
        display: flex;
        flex-direction: column;
        gap: 10px;
      }}
      .nir-item {{
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 10px 12px;
        background: #FFFFFF;
      }}
      .nir-item-title {{
        font-weight: 900;
        font-size: 13px;
        margin-bottom: 6px;
        color: {TEXT};
      }}
      .nir-item-row {{
        display: flex;
        justify-content: space-between;
        gap: 12px;
        font-size: 12px;
        color: {TEXT};
      }}
      .nir-item-row span {{
        color: {MUTED};
        font-weight: 800;
        margin-right: 6px;
      }}

      /* Variáveis: mobile */
      :root {{
        --nir-header-h: 62px;
        --nir-logo-h: 48px;
      }}

      @media (max-width: 768px) {{
        .block-container {{
          padding-top: 0.7rem;
          padding-left: 0.85rem;
          padding-right: 0.85rem;
        }}
        .nir-top-title {{ font-size: 18px; }}
        .nir-card {{
          padding: 10px 8px;
          min-height: 90px;
        }}
        .nir-card-title {{ font-size: 11px; }}
        .nir-card-value {{ font-size: 20px; }}
      }}

      /* Desktop/TV */
      @media (min-width: 1200px) {{
        :root {{
          --nir-header-h: 96px;
          --nir-logo-h: 78px;
        }}

        .nir-header {{
          grid-template-columns: 1fr 3.2fr 1fr;
          gap: 12px;
        }}

        .nir-top-title {{
          font-size: 40px;
          -webkit-line-clamp: unset;
          display: block;
          overflow: visible;
        }}

        .nir-metrics-grid {{
          grid-template-columns: 1fr 1fr 1fr 1fr;
          gap: 14px;
        }}

        .nir-card {{
          padding: 14px 12px;
          min-height: 110px;
        }}
        .nir-card-title {{ font-size: 13px; }}
        .nir-card-value {{ font-size: 32px; }}
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================
# Helpers (dados)
# ======================
def _remover_acentos(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")


def _norm(s: str) -> str:
    return _remover_acentos((s or "").strip().upper())


def to_int_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0).astype(int)


@st.cache_data(ttl=30)
def baixar_csv_como_matriz(url: str) -> list[list[str]]:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text), header=None, dtype=str, engine="python").fillna("")
    return df.values.tolist()


def achar_linha_por_substring(rows: list[list[str]], substring: str) -> int | None:
    alvo = _norm(substring)
    for i, row in enumerate(rows):
        for cell in row:
            if alvo in _norm(cell):
                return i
    return None


def slice_rows(rows: list[list[str]], start: int, end: int) -> list[list[str]]:
    bloco = rows[start:end]
    return [r for r in bloco if any(str(c).strip() for c in r)]


def safe_df_for_display(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()

    cols = list(df.columns)
    seen: dict[str, int] = {}
    new_cols = []
    for c in cols:
        key = str(c).strip()
        if key in seen:
            seen[key] += 1
            new_cols.append(f"{key}_{seen[key]}")
        else:
            seen[key] = 0
            new_cols.append(key)
    df.columns = new_cols
    return df


def find_col_by_contains(df: pd.DataFrame, contains_norm: str) -> str | None:
    target = _norm(contains_norm)
    for c in df.columns:
        if target in _norm(str(c)):
            return c
    return None


def img_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


def section_title(title: str):
    st.markdown(f"<div class='nir-section-title'>{title}</div>", unsafe_allow_html=True)


def render_metric_cards(total_realizadas: int, total_previstas: int, total_vagas: int, total_transf: int):
    metrics_html = f"""
    <div class="nir-metrics-grid">
      <div class="nir-card">
        <div class="nir-card-title">Altas realizadas<br>(até 19h)</div>
        <div class="nir-card-value" style="color:{PRIMARY}">{total_realizadas}</div>
      </div>

      <div class="nir-card">
        <div class="nir-card-title two-line-title">Altas previstas<br>em 24h</div>
        <div class="nir-card-value" style="color:{ACCENT_GREEN}">{total_previstas}</div>
      </div>

      <div class="nir-card">
        <div class="nir-card-title">Vagas reservadas<br>(dia seguinte)</div>
        <div class="nir-card-value" style="color:{SCS_PURPLE}">{total_vagas}</div>
      </div>

      <div class="nir-card">
        <div class="nir-card-title">Transferências/<br>Saídas (total)</div>
        <div class="nir-card-value" style="color:{SCS_CYAN}">{total_transf}</div>
      </div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)


def render_mobile_list(df: pd.DataFrame, title_cols: list[str], kv_cols: list[tuple[str, str]], max_items: int | None = None):
    df = safe_df_for_display(df)
    if df.empty:
        st.info("Sem dados para exibir.")
        return

    if max_items is not None:
        df = df.head(max_items)

    items_html = "<div class='nir-list'>"
    for _, row in df.iterrows():
        parts = []
        for c in title_cols:
            if c in df.columns:
                v = str(row.get(c, "")).strip()
                if v:
                    parts.append(v)
        item_title = " • ".join(parts) if parts else "Item"

        rows_html = ""
        for label, colname in kv_cols:
            if colname in df.columns:
                v = str(row.get(colname, "")).strip()
                rows_html += f"<div class='nir-item-row'><div><span>{label}:</span>{v}</div></div>"

        items_html += f"<div class='nir-item'><div class='nir-item-title'>{item_title}</div>{rows_html}</div>"

    items_html += "</div>"
    st.markdown(items_html, unsafe_allow_html=True)


# ======================
# Parsing do CSV
# ======================
def montar_altas(rows: list[list[str]], i_altas_header: int, i_vagas_title: int) -> pd.DataFrame:
    bloco = slice_rows(rows, i_altas_header, i_vagas_title)
    if len(bloco) < 2:
        return pd.DataFrame()

    raw_header = [str(c).strip() for c in bloco[0]]
    header = []
    for h in raw_header:
        if h != "":
            header.append(h)
        else:
            break

    if len(header) < 2:
        return pd.DataFrame()

    data = []
    for r in bloco[1:]:
        row = [str(c).strip() for c in r[: len(header)]]
        if any(v != "" for v in row):
            data.append(row)

    df = pd.DataFrame(data, columns=header)

    rename = {"ALTAS HOSPITAL": "HOSPITAL", "SETOR": "SETOR"}
    df = df.rename(columns={c: rename.get(str(c).strip(), str(c).strip()) for c in df.columns})

    col_realizadas = find_col_by_contains(df, "ALTAS DO DIA")
    col_previstas = find_col_by_contains(df, "ALTAS PREVISTAS")
    if col_realizadas:
        df[col_realizadas] = to_int_series(df[col_realizadas])
    if col_previstas:
        df[col_previstas] = to_int_series(df[col_previstas])

    if "HOSPITAL" in df.columns and "SETOR" in df.columns:
        df = df[(df["HOSPITAL"].astype(str).str.strip() != "") & (df["SETOR"].astype(str).str.strip() != "")]
    return df


def montar_vagas(rows: list[list[str]], i_vagas_title: int, i_transf_title: int) -> pd.DataFrame:
    bloco = slice_rows(rows, i_vagas_title + 1, i_transf_title)
    if not bloco:
        return pd.DataFrame()

    data = []
    for r in bloco:
        hosp = (r[0] if len(r) > 0 else "").strip()
        setor = (r[1] if len(r) > 1 else "").strip()
        vagas = (r[2] if len(r) > 2 else "").strip()

        if setor == "" and vagas == "":
            continue

        data.append([hosp, setor, vagas])

    df = pd.DataFrame(data, columns=["HOSPITAL", "SETOR", "VAGAS_RESERVADAS"])
    df["HOSPITAL"] = df["HOSPITAL"].replace("", pd.NA).ffill().fillna("")
    df["VAGAS_RESERVADAS"] = to_int_series(df["VAGAS_RESERVADAS"])
    df = df[df["SETOR"].astype(str).str.strip() != ""]
    return df


def montar_transferencias(rows: list[list[str]], i_transf_title: int) -> pd.DataFrame:
    bloco = slice_rows(rows, i_transf_title + 1, len(rows))
    if not bloco:
        return pd.DataFrame()

    data = []
    for r in bloco:
        desc = (r[0] if len(r) > 0 else "").strip()
        val = (r[1] if len(r) > 1 else "").strip()
        if desc:
            data.append([desc, val])

    df = pd.DataFrame(data, columns=["DESCRIÇÃO", "TOTAL"])
    df["TOTAL"] = to_int_series(df["TOTAL"])
    return df


# ======================
# HEADER
# ======================
left_uri = img_to_data_uri(LOGO_LEFT_PATH)
right_uri = img_to_data_uri(LOGO_RIGHT_PATH)

left_img_html = f"<img src='{left_uri}' alt='Logo esquerda' />" if left_uri else "<div style='color:#64748B;font-weight:700'>Logo esquerda</div>"
right_img_html = f"<img src='{right_uri}' alt='Logo direita' />
