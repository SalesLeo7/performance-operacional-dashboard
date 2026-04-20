import streamlit as st
import pandas as pd

st.set_page_config(page_title="Performance Outbound OTIF", layout="wide")
st.title("📊 Performance Outbound OTIF")


def calculate_performance(df):
    # Padronizar nomes das colunas
    df.columns = [col.strip().upper() for col in df.columns]

    # Lista de colunas de data
    date_cols = ['ORDER_DATE', 'CREATION_DATE', 'SHIPPED', 'DATA_ENTREGA']

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # --- MÉTRICAS ---

    # 1. Lead Time
    if 'ORDER_DATE' in df.columns and 'SHIPPED' in df.columns:
        df['LEAD_TIME_DAYS'] = (
            (df['SHIPPED'] - df['ORDER_DATE']).dt.total_seconds() / (24 * 3600)
        )
        st.metric("Lead Time Médio (dias)", f"{df['LEAD_TIME_DAYS'].mean():.2f}")

    # 2. OTIF
    if 'PERFORMANCE_OTIF' in df.columns:
        otif_counts = df['PERFORMANCE_OTIF'].value_counts(normalize=True) * 100

        st.subheader("Distribuição OTIF")
        st.dataframe(otif_counts)

        if 'ON_TIME' in otif_counts:
            st.metric("Taxa ON_TIME (%)", f"{otif_counts['ON_TIME']:.2f}")

    else:
        st.warning("Coluna PERFORMANCE_OTIF não encontrada")

    # 3. Tempo de Processamento
    if 'CREATION_DATE' in df.columns and 'SHIPPED' in df.columns:
        df['WH_PROCESS_TIME_HOURS'] = (
            (df['SHIPPED'] - df['CREATION_DATE']).dt.total_seconds() / 3600
        )
        st.metric(
            "Tempo Médio Armazém (horas)",
            f"{df['WH_PROCESS_TIME_HOURS'].mean():.2f}"
        )

    return df


# --- UPLOAD ---
uploaded_file = st.file_uploader("📂 Faça upload do CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=",", quotechar='"')

        st.success("Arquivo carregado com sucesso!")

        df = calculate_performance(df)

        st.subheader("Preview dos dados")
        st.dataframe(df.head())

        # Download do arquivo processado
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Baixar arquivo processado",
            csv,
            "performance_processada.csv",
            "text/csv"
        )

    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
