import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(
    page_title="Performance Outbound OTIF",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Performance Outbound OTIF")
st.markdown("---")

# ================= LOAD DATA =================
@st.cache_data
def load_data(file):
    df = pd.read_csv(file, sep=',', quotechar='"')

    # 🔥 PADRONIZAÇÃO DE COLUNAS (PRIMEIRO)
    df.columns = (
        df.columns
        .str.strip()
        .str.upper()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # 🔥 PADRONIZAÇÃO DE VALORES (DEPOIS)
    for col in df.columns:
        if any(k in col for k in ["OTIF", "STATUS", "PERFORMANCE"]):
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.upper()
                .str.replace(" ", "_")
                .str.replace("-", "_")
            )

    # Remover duplicadas
    df = df.loc[:, ~df.columns.duplicated()]

    # Datas
    date_cols = ['ORDER_DATE', 'CREATION_DATE', 'SHIPPED', 'DATA_ENTREGA']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Métricas
    if 'ORDER_DATE' in df.columns and 'SHIPPED' in df.columns:
        df['LEAD_TIME_DAYS'] = (
            (df['SHIPPED'] - df['ORDER_DATE']).dt.total_seconds() / 86400
        )

    if 'CREATION_DATE' in df.columns and 'SHIPPED' in df.columns:
        df['WH_PROCESS_TIME_HOURS'] = (
            (df['SHIPPED'] - df['CREATION_DATE']).dt.total_seconds() / 3600
        )

    return df


# ================= UPLOAD =================
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV", type=["csv"])

if uploaded_file is None:
    st.warning("Faça upload de um arquivo CSV")
    st.stop()

df = load_data(uploaded_file)

st.success(f"✅ {len(df)} registros carregados")

# ================= DETECÇÃO INTELIGENTE =================
col_cliente = next((c for c in df.columns if "CLIENTE" in c), None)

col_otif = None
for c in df.columns:
    if any(k in c for k in ["OTIF", "PERFORMANCE", "STATUS"]):
        col_otif = c
        break

# ================= SIDEBAR =================
st.sidebar.header("🔍 Filtros")

# Cliente
if col_cliente:
    clientes = sorted(df[col_cliente].dropna().unique())
    cliente_sel = st.sidebar.multiselect(
        "Cliente",
        clientes,
        default=clientes[:5]
    )
else:
    cliente_sel = []

# Data
if 'ORDER_DATE' in df.columns:
    data_inicio = st.sidebar.date_input(
        "Data início",
        value=df['ORDER_DATE'].min().date()
    )
    data_fim = st.sidebar.date_input(
        "Data fim",
        value=df['ORDER_DATE'].max().date()
    )
else:
    data_inicio = data_fim = None

# ================= FILTROS =================
df_f = df.copy()

if cliente_sel and col_cliente:
    df_f = df_f[df_f[col_cliente].isin(cliente_sel)]

if data_inicio and 'ORDER_DATE' in df_f.columns:
    df_f = df_f[
        (df_f['ORDER_DATE'].dt.date >= data_inicio) &
        (df_f['ORDER_DATE'].dt.date <= data_fim)
    ]

# ================= KPIs =================
st.subheader("📈 Indicadores")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Pedidos", len(df_f))

with c2:
    if col_otif and len(df_f) > 0:

        # 🔥
        on_time = df_f[col_otif].str.contains("ON_TIME", na=False).sum()
        total = len(df_f)

        otif_rate = (on_time / total) * 100 if total > 0 else 0

        st.metric("Taxa OTIF", f"{otif_rate:.1f}%")

    else:
        st.metric("Taxa OTIF", "N/A")

with c3:
    if 'LEAD_TIME_DAYS' in df_f.columns:
        st.metric("Lead Time", f"{df_f['LEAD_TIME_DAYS'].mean():.1f} dias")
    else:
        st.metric("Lead Time", "N/A")

with c4:
    if 'WH_PROCESS_TIME_HOURS' in df_f.columns:
        st.metric("WH Time", f"{df_f['WH_PROCESS_TIME_HOURS'].mean():.1f}h")
    else:
        st.metric("WH Time", "N/A")

st.markdown("---")

# ================= GRÁFICOS =================

# OTIF por dia
if col_otif and 'ORDER_DATE' in df_f.columns:
    df_otif = df_f.copy()
    df_otif['DATA'] = df_otif['ORDER_DATE'].dt.date

    otif_daily = df_otif.groupby('DATA')[col_otif].apply(
        lambda x: x.str.contains("ON", na=False).mean() * 100
    ).reset_index()

    fig_otif = px.line(
        otif_daily,
        x='DATA',
        y=col_otif,
        title="📈 OTIF ao longo do tempo"
    )

    st.plotly_chart(fig_otif, use_container_width=True)

# Lead Time por cliente
if col_cliente and 'LEAD_TIME_DAYS' in df_f.columns:
    ranking = (
        df_f.groupby(col_cliente)['LEAD_TIME_DAYS']
        .mean()
        .sort_values()
        .reset_index()
        .head(10)
    )

    fig_rank = px.bar(
        ranking,
        x='LEAD_TIME_DAYS',
        y=col_cliente,
        orientation='h',
        title="🏆 Top 10 Clientes (Menor Lead Time)"
    )

    st.plotly_chart(fig_rank, use_container_width=True)

# ================= HEATMAP =================
st.subheader("🔥 OTIF por Cliente (Heatmap)")

if col_cliente and col_otif and 'ORDER_DATE' in df_f.columns:

    df_heat = df_f.copy()
    df_heat['MES'] = df_heat['ORDER_DATE'].dt.to_period('M').astype(str)

    heatmap_data = df_heat.groupby([col_cliente, 'MES'])[col_otif].apply(
        lambda x: x.str.contains("ON", na=False).mean() * 100
    ).reset_index()

    heatmap_pivot = heatmap_data.pivot(
        index=col_cliente,
        columns='MES',
        values=col_otif
    )

    fig_heatmap = px.imshow(
        heatmap_pivot,
        aspect="auto",
        color_continuous_scale="RdYlGn",
        title="OTIF (%) por Cliente e Mês"
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)

# ================= TABELA =================
st.subheader("📋 Dados")
st.dataframe(df_f)
