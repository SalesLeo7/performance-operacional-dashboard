import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Configuração da página
st.set_page_config(
    page_title="Performance Outbound OTIF",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📊 Performance Outbound OTIF")
st.markdown("---")


# Função para carregar os dados
@st.cache_data
def load_data(file):
    """Carrega o arquivo CSV e processa as datas"""
    # Carregar o CSV sem alterar os nomes das colunas inicialmente
    df = pd.read_csv(file, sep=',', quotechar='"')

    # ✅ CORREÇÃO: Tratar as colunas 'STATUS' e 'status' separadamente antes do .upper() geral
    # O Streamlit/Pandas por padrão mantém a distinção de case se não for alterado.
    # Vamos renomear explicitamente para evitar confusão posterior.
    if 'Status' in df.columns:
        df = df.rename(columns={'Status': 'STATUS_TRANSPORT'})

    # Agora padronizamos as OUTRAS colunas, mas mantendo a nossa nova STATUS_TRANSPORT
    new_cols = []
    for col in df.columns:
        c = col.strip()
        if c == 'STATUS_TRANSPORT':
            new_cols.append(c)
        else:
            new_cols.append(c.upper())

    df.columns = new_cols

    # Remover duplicatas se houver (segurança)
    df = df.loc[:, ~df.columns.duplicated()]

    # Converter colunas de data
    date_cols = ['ORDER_DATE', 'CREATION_DATE', 'SHIPPED', 'DATA_ENTREGA']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Resetar o índice
    df = df.reset_index(drop=True)

    # Calcular Lead Time em dias
    if 'ORDER_DATE' in df.columns and 'SHIPPED' in df.columns:
        df['LEAD_TIME_DAYS'] = (df['SHIPPED'] - df['ORDER_DATE']).dt.total_seconds() / (24 * 3600)

    # Calcular tempo de processamento em horas
    if 'CREATION_DATE' in df.columns and 'SHIPPED' in df.columns:
        df['WH_PROCESS_TIME_HOURS'] = (df['SHIPPED'] - df['CREATION_DATE']).dt.total_seconds() / 3600

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

# ============= SIDEBAR - FILTROS =============
st.sidebar.header("🔍 Filtros")

# Filtro de Cliente
if 'CLIENTE_ID' in df.columns:
    clientes = sorted(df['CLIENTE_ID'].unique())
    cliente_selecionado = st.sidebar.multiselect(
        "Cliente",
        options=clientes,
        default=clientes[:3] if len(clientes) > 0 else clientes
    )
else:
    cliente_selecionado = []

# Filtro de Data
col1, col2 = st.sidebar.columns(2)
with col1:
    data_inicio = st.date_input(
        "Data Início",
        value=df['ORDER_DATE'].min().date() if 'ORDER_DATE' in df.columns and not pd.isnull(
            df['ORDER_DATE'].min()) else datetime.now().date()
    )
with col2:
    data_fim = st.date_input(
        "Data Fim",
        value=df['ORDER_DATE'].max().date() if 'ORDER_DATE' in df.columns and not pd.isnull(
            df['ORDER_DATE'].max()) else datetime.now().date()
    )

# Filtro de Status Warehouse (Coluna 'STATUS' original)
if 'STATUS' in df.columns:
    status_options = sorted(df['STATUS'].dropna().unique())
    status_selecionado = st.sidebar.multiselect(
        "Status Warehouse",
        options=status_options,
        default=status_options
    )
else:
    status_selecionado = []

# Filtro de Status Transport (Coluna 'status' que renomeamos para 'STATUS_TRANSPORT')
if 'STATUS_TRANSPORT' in df.columns:
    status_tr_vals = sorted(df['STATUS_TRANSPORT'].dropna().unique())
    status_options_tr = st.sidebar.multiselect(
        "Status Transport",
        options=status_tr_vals,
        default=status_tr_vals
    )
else:
    status_options_tr = []

# Filtro de Performance OTIF
if 'PERFORMANCE_OTIF' in df.columns:
    otif_options = sorted(df['PERFORMANCE_OTIF'].dropna().unique())
    otif_selecionado = st.sidebar.multiselect(
        "Performance OTIF",
        options=otif_options,
        default=otif_options
    )
else:
    otif_selecionado = []

# ============= APLICAR FILTROS =============
df_filtrado = df.copy().reset_index(drop=True)

# Filtro de cliente
if cliente_selecionado and 'CLIENTE_ID' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['CLIENTE_ID'].isin(cliente_selecionado)].reset_index(drop=True)

# Filtro de data
if 'ORDER_DATE' in df_filtrado.columns:
    df_filtrado = df_filtrado[
        (df_filtrado['ORDER_DATE'].dt.date >= data_inicio) &
        (df_filtrado['ORDER_DATE'].dt.date <= data_fim)
        ].reset_index(drop=True)

# Filtro de status Warehouse
if status_selecionado and 'STATUS' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['STATUS'].isin(status_selecionado)].reset_index(drop=True)

# Filtro de Status Transport
if status_options_tr and 'STATUS_TRANSPORT' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['STATUS_TRANSPORT'].isin(status_options_tr)].reset_index(drop=True)

# Filtro de OTIF
if otif_selecionado and 'PERFORMANCE_OTIF' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['PERFORMANCE_OTIF'].isin(otif_selecionado)].reset_index(drop=True)

# ============= MÉTRICAS (KPIs) =============
st.subheader("📈 Indicadores de Performance")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_pedidos = len(df_filtrado)
    st.metric("Total de Pedidos", f"{total_pedidos:,}")

with col2:
    if 'PERFORMANCE_OTIF' in df_filtrado.columns:
        otif_rate = (df_filtrado['PERFORMANCE_OTIF'] == 'ON_TIME').sum() / len(df_filtrado) * 100 if len(
            df_filtrado) > 0 else 0
        st.metric("Taxa OTIF", f"{otif_rate:.1f}%")
    else:
        st.metric("Taxa OTIF", "N/A")

with col3:
    if 'LEAD_TIME_DAYS' in df_filtrado.columns:
        lead_time_avg = df_filtrado['LEAD_TIME_DAYS'].mean()
        st.metric("Lead Time Médio", f"{lead_time_avg:.1f} dias")
    else:
        st.metric("Lead Time Médio", "N/A")

with col4:
    if 'WH_PROCESS_TIME_HOURS' in df_filtrado.columns:
        wh_time_avg = df_filtrado['WH_PROCESS_TIME_HOURS'].mean()
        st.metric("Tempo WH Médio", f"{wh_time_avg:.1f}h")
    else:
        st.metric("Tempo WH Médio", "N/A")

st.markdown("---")

# ================= TABELA =================
st.subheader("📋 Dados")
st.dataframe(df_filtrado)