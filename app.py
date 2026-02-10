import base64
import io
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ======================
# CONFIG GERAL
# ======================
st.set_page_config(page_title="Painel NIR - Censo Diário", layout="wide")

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

# ======================
# CSS (mobile-friendly)
# ======================
st.markdown(
    f"""
    <style>
      .stApp {{
        background: {BG};
        color: {TEXT};
      }}

      /* Header */
      .nir-header {{
        display: grid;
        grid-template-columns: 72px 1fr 72px;
        gap: 8px;
        align-items: stretch;
        width: 100%;
      }}
      @media (min-width: 1200px) {{
        .nir-header {{
          grid-template-columns: 1fr 4fr 1fr;
          gap: 10px;
        }}
      }}

      .nir-header-box {{ border-radius: 16px; }}

      .nir-header-logo {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        display: flex;
        align-items: center;
        justify-content: center;
        height: var(--nir-header-h);
        padding: 8px;
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
        padding: 10px 12px;
      }}

      .nir-top-title {{
        font-weight: 980;
        letter-spacing: 0.2px;
        line-height: 1.05;
        margin: 0;
      }}
      .nir-top-sub {{
        margin-top: 6px;
        opacity: 0.92;
        margin-bottom: 0;
      }}

      /* Grids */
      .nir-metrics-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-top: 10px;
      }}
      @media (min-width: 1200px) {{
        .nir-metrics-grid {{
          grid-template-columns: 1fr 1fr 1fr 1fr;
        }}
      }}

      .nir-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 12px 14px;
        box-shadow: 0 1px 0 rgba(16,24,40,0.02);
      }}
      .nir-card-title {{
        color: {MUTED};
        font-weight: 800;
        margin-bottom: 6px;
        font-size: 12px;
      }}
      .nir-card-value {{
        font-weight: 950;
        margin: 0;
        line-height: 1.0;
        font-size: 22px;
      }}

      @media (min-width: 1200px) {{
        .nir-card {{
          padding: 14px 16px;
        }}
        .nir-card-title {{ font-size: 13px; }}
        .nir-card-value {{ font-size: 32px; }}
      }}

      .nir-section-title {{
        font-weight: 950;
        margin-bottom: 8px;
        color: {TEXT};
        font-size: 15px;
      }}

      /* Lista mobile (em vez de tabela) */
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

      /* Variáveis de altura do header */
      :root {{
        --nir-header-h: 72px;
        --nir-logo-h: 44px;
      }}
      @media (min-width: 1200px) {{
        :root {{
          --nir-header-h: 110px;
          --nir-logo-h: 72px;
        }}
        .nir-top-title {{ font-size: 40px; }}
        .nir-top-sub {{ font-size: 15px; }}
      }}

      @media (max-width: 768px) {{
        .block-container {{
          padding-top: 0.7rem;
          padding-left: 0.85rem;
          padding-right: 0.85rem;
        }}
        .nir-top-title {{ font-size: 18px; }}
        .nir-top-sub {{ font-size: 12px; }}
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================
# Helpers
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
        <div class="nir-card-title">Altas realizadas (até 19h)</div>
        <div class="nir-card-value" style="color:{PRIMARY}">{total_realizadas}</div>
      </div>

      <div class="nir-card">
        <div class="nir-card-title">Altas previstas (24h)</div>
        <div class="nir-card-value" style="color:{ACCENT_GREEN}">{total_previstas}</div>
      </div>

      <div class="nir-card">
        <div class="nir-card-title">Vagas reservadas (dia seguinte)</div>
        <div class="nir-card-value" style="color:{SCS_PURPLE}">{total_vagas}</div>
      </div>

      <div class="nir-card">
        <div class="nir-card-title">Transferências/Saídas (total)</div>
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
        # título: concatena colunas principais que existirem
        parts = []
        for c in title_cols:
            if c in df.columns:
                v = str(row.get(c, "")).strip()
                if v:
                    parts.append(v)
        item_title = " • ".join(parts) if parts else "Item"

        # linhas chave-valor (só se coluna existir)
        rows_html = ""
        for label, colname in kv_cols:
            if colname in df.columns:
                v = str(row.get(colname, "")).strip()
                rows_html += f"<div class='nir-item-row'><div><span>{label}:</span>{v}</div></div>"

        items_html += f"<div class='nir-item'><div class='nir-item-title'>{item_title}</div>{rows_html}</div>"

    items_html += "</div>"
    st.markdown(items_html, unsafe_allow_html=True)


# ======================
# Parsing do CSV (3 blocos)
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
right_img_html = f"<img src='{right_uri}' alt='Logo direita' />" if right_uri else "<div style='color:#64748B;font-weight:700'>Logo direita</div>"

st.markdown(
    f"""
    <div class="nir-header">
      <div class="nir-header-box nir-header-logo">{left_img_html}</div>
      <div class="nir-header-box nir-header-center">
        <div class="nir-top-title">Painel NIR – Censo Diário</div>
        <div class="nir-top-sub">Atualização automática a cada {REFRESH_SECONDS}s • Fonte: Google Sheets</div>
      </div>
      <div class="nir-header-box nir-header-logo">{right_img_html}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

# ======================
# CONTROLES + MODO CELULAR
# ======================
c1, c2, c3 = st.columns([1.4, 2.6, 2.0])
with c1:
    if st.button("Atualizar agora"):
        st.cache_data.clear()
with c2:
    modo_mobile = st.toggle("Modo celular (lista)", value=True)
with c3:
    st.caption(f"Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

st.markdown("")

# ======================
# LOAD + PARSE
# ======================
try:
    rows = baixar_csv_como_matriz(CSV_URL)
except Exception:
    st.error("Não foi possível carregar o CSV da planilha. Verifique permissões/publicação do Google Sheets.")
    st.stop()

i_altas_header = achar_linha_por_substring(rows, "ALTAS")
i_vagas_title = achar_linha_por_substring(rows, "VAGAS RESERVADAS")
i_transf_title = achar_linha_por_substring(rows, "TRANSFERENCIAS")

missing = []
if i_altas_header is None:
    missing.append("ALTAS")
if i_vagas_title is None:
    missing.append("VAGAS RESERVADAS")
if i_transf_title is None:
    missing.append("TRANSFERENCIAS")

if missing:
    st.error("Não encontrei estes marcadores no CSV: " + ", ".join(missing))
    st.stop()

df_altas = montar_altas(rows, i_altas_header, i_vagas_title)
df_vagas = montar_vagas(rows, i_vagas_title, i_transf_title)
df_transf = montar_transferencias(rows, i_transf_title)

# ======================
# MÉTRICAS
# ======================
col_realizadas = find_col_by_contains(df_altas, "ALTAS DO DIA") if not df_altas.empty else None
col_previstas = find_col_by_contains(df_altas, "ALTAS PREVISTAS") if not df_altas.empty else None

total_realizadas = int(df_altas[col_realizadas].sum()) if col_realizadas else 0
total_previstas = int(df_altas[col_previstas].sum()) if col_previstas else 0
total_vagas = int(df_vagas["VAGAS_RESERVADAS"].sum()) if not df_vagas.empty else 0
total_transf = int(df_transf["TOTAL"].sum()) if not df_transf.empty else 0

render_metric_cards(total_realizadas, total_previstas, total_vagas, total_transf)

st.markdown("")

# ======================
# CONTEÚDO (Mobile: lista | Web: tabela)
# ======================
if modo_mobile:
    section_title("ALTAS")
    # Título do item: Hospital + Setor (se existirem)
    # Campos: Altas do dia / previstas (se existirem)
    col_dia = find_col_by_contains(df_altas, "ALTAS DO DIA") or "ALTAS DO DIA"
    col_prev = find_col_by_contains(df_altas, "ALTAS PREVISTAS") or "ALTAS PREVISTAS"
    render_mobile_list(
        df_altas,
        title_cols=["HOSPITAL", "SETOR"],
        kv_cols=[("Altas do dia", col_dia), ("Previstas", col_prev)],
        max_items=None,
    )

    st.markdown("")
    section_title("VAGAS RESERVADAS (DIA SEGUINTE)")
    render_mobile_list(
        df_vagas,
        title_cols=["HOSPITAL", "SETOR"],
        kv_cols=[("Vagas", "VAGAS_RESERVADAS")],
        max_items=None,
    )

    st.markdown("")
    section_title("TRANSFERÊNCIAS/SAÍDAS")
    render_mobile_list(
        df_transf,
        title_cols=["DESCRIÇÃO"],
        kv_cols=[("Total", "TOTAL")],
        max_items=None,
    )
else:
    # Web/TV: tabelas normais
    st.subheader("ALTAS")
    st.dataframe(safe_df_for_display(df_altas), use_container_width=True, hide_index=True)

    st.subheader("VAGAS RESERVADAS - MAPA CIRÚRGICO (DIA SEGUINTE)")
    st.dataframe(safe_df_for_display(df_vagas), use_container_width=True, hide_index=True)

    st.subheader("TRANSFERÊNCIAS/SAÍDAS")
    st.dataframe(safe_df_for_display(df_transf), use_container_width=True, hide_index=True)

st.caption("Fonte: Google Sheets (Folha1).")
