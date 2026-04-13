import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configurações da página
st.set_page_config(page_title="Dashboard de Performance Operacional", layout="wide")

# Carregar dados processados
@st.cache_data
def load_data():
    df = pd.read_csv("performance_processed.csv")
    df['Creation Date'] = pd.to_datetime(df['Creation Date'])
    df['Finish Date'] = pd.to_datetime(df['Finish Date'])
    return df

df = load_data()

# Título e Sidebar
st.title("📊 Dashboard de Performance Operacional")
st.markdown("### Visão Estratégica para Supervisão e Gerência")

with st.sidebar:
    st.header("Filtros")
    clientes = st.multiselect("Selecione os Clientes", options=df['Client'].unique(), default=df['Client'].unique())
    tipos = st.multiselect("Tipo de Operação", options=df['Type'].unique(), default=df['Type'].unique())
    data_inicio = st.date_input("Data Início", df['Creation Date'].min().date())
    data_fim = st.date_input("Data Fim", df['Creation Date'].max().date())

# Filtrar dados
df_filtered = df[
    (df['Client'].isin(clientes)) & 
    (df['Type'].isin(tipos)) &
    (df['Creation Date'].dt.date >= data_inicio) &
    (df['Creation Date'].dt.date <= data_fim)
]

# KPIs Principais
col1, col2, col3, col4 = st.columns(4)

total_pedidos = len(df_filtered)
on_time_count = len(df_filtered[df_filtered['performance'] == 'on_time'])
sla_percent = (on_time_count / total_pedidos * 100) if total_pedidos > 0 else 0
avg_working_hours = df_filtered['working_hours'].mean()

with col1:
    st.metric("Total de Pedidos", f"{total_pedidos:,}")
with col2:
    st.metric("SLA (On-Time %)", f"{sla_percent:.1f}%")
with col3:
    st.metric("Média Horas Úteis", f"{avg_working_hours:.1f}h")
with col4:
    st.metric("Pedidos Fora do Prazo", f"{total_pedidos - on_time_count:,}")

# Visualizações
st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Performance por Cliente")
    perf_by_client = df_filtered.groupby(['Client', 'performance']).size().reset_index(name='count')
    fig_client = px.bar(perf_by_client, x='Client', y='count', color='performance', 
                         title="Pedidos On-Time vs Out-Time por Cliente",
                         color_discrete_map={'on_time': '#2ecc71', 'out_time': '#e74c3c'},
                         barmode='group')
    st.plotly_chart(fig_client, use_container_width=True)

with col_right:
    st.subheader("Evolução de SLA Diário")
    df_filtered['Date'] = df_filtered['Creation Date'].dt.date
    daily_sla = df_filtered.groupby('Date').apply(
        lambda x: (len(x[x['performance'] == 'on_time']) / len(x)) * 100
    ).reset_index(name='SLA %')
    
    fig_line = px.line(daily_sla, x='Date', y='SLA %', title="Tendência de SLA ao Longo do Tempo",
                        markers=True, line_shape='spline')
    fig_line.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="Meta 90%")
    st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

col_bot1, col_bot2 = st.columns(2)

with col_bot1:
    st.subheader("Distribuição de Horas Úteis")
    fig_hist = px.histogram(df_filtered, x='working_hours', color='performance',
                             nbins=50, title="Distribuição do Tempo de Processamento",
                             color_discrete_map={'on_time': '#2ecc71', 'out_time': '#e74c3c'})
    fig_hist.add_vline(x=24, line_dash="dash", line_color="black", annotation_text="Limite 24h")
    st.plotly_chart(fig_hist, use_container_width=True)

with col_bot2:
    st.subheader("Top 10 Clientes com Mais Atrasos")
    out_time_df = df_filtered[df_filtered['performance'] == 'out_time']
    top_delay_clients = out_time_df.groupby('Client').size().sort_values(ascending=False).head(10).reset_index(name='Atrasos')
    fig_top = px.bar(top_delay_clients, x='Atrasos', y='Client', orientation='h',
                      title="Clientes Críticos (Out-Time)", color='Atrasos',
                      color_continuous_scale='Reds')
    st.plotly_chart(fig_top, use_container_width=True)

# Tabela de Dados Detalhada
with st.expander("Visualizar Dados Brutos Detalhados"):
    st.dataframe(df_filtered[['Client', 'Pre-Advice ID', 'Creation Date', 'Finish Date', 'working_hours', 'performance']].sort_values(by='working_hours', ascending=False))
