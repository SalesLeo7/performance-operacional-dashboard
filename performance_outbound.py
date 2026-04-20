import pandas as pd
import os


def calculate_performance(input_file, output_file):
    print(f"Lendo o arquivo: {input_file}")

    try:
        # Lendo o CSV com o separador correto
        df = pd.read_csv(input_file, sep=',', quotechar='"')
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return None

    # Padronizar nomes das colunas
    df.columns = [col.strip().upper() for col in df.columns]

    # Lista de colunas de data para converter
    date_cols = ['ORDER_DATE', 'CREATION_DATE', 'SHIPPED', 'DATA_ENTREGA']

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    print("\n--- MEDIÇÃO DE PERFORMANCE ---")

    # 1. Cálculo de Lead Time (Diferença entre pedido e envio em dias)
    if 'ORDER_DATE' in df.columns and 'SHIPPED' in df.columns:
        df['LEAD_TIME_DAYS'] = (df['SHIPPED'] - df['ORDER_DATE']).dt.total_seconds() / (24 * 3600)
        avg_lead_time = df['LEAD_TIME_DAYS'].mean()
        print(f"Lead Time Médio (Pedido até Envio): {avg_lead_time:.2f} dias")

    # 2. Análise de OTIF (On-Time In-Full)
    # Se a coluna PERFORMANCE_OTIF já existir no seu arquivo, vamos usá-la
    if 'PERFORMANCE_OTIF' in df.columns:
        otif_counts = df['PERFORMANCE_OTIF'].value_counts(normalize=True) * 100
        print("\nDistribuição de Performance (OTIF):")
        for status, percentage in otif_counts.items():
            print(f"- {status}: {percentage:.2f}%")

        # Cálculo da taxa de sucesso (On-Time)
        if 'ON_TIME' in otif_counts:
            print(f"\nTaxa de Sucesso (ON_TIME): {otif_counts['ON_TIME']:.2f}%")
    else:
        print("\nAVISO: Coluna 'PERFORMANCE_OTIF' não encontrada para análise direta.")

    # 3. Tempo de Processamento Interno (Criação até Envio)
    if 'CREATION_DATE' in df.columns and 'SHIPPED' in df.columns:
        df['WH_PROCESS_TIME_HOURS'] = (df['SHIPPED'] - df['CREATION_DATE']).dt.total_seconds() / 3600
        avg_wh_time = df['WH_PROCESS_TIME_HOURS'].mean()
        print(f"Tempo Médio de Processamento no Armazém: {avg_wh_time:.2f} horas")

    # Salvar o resultado com as novas colunas calculadas
    try:
        df.to_csv(output_file, index=False)
        print(f"\nProcessamento concluído. Arquivo com métricas salvo em: {output_file}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

    return df


if __name__ == "__main__":
    # IMPORTANTE: Use r"" para caminhos no Windows
    input_path = r"C:\outbound\outbound.csv"
    output_path = r"C:\outbound\performance_processed.csv"


    if not os.path.exists(r"C:\outbound"):
        input_path = "/home/ubuntu/upload/outbound.csv"
        output_path = "/home/ubuntu/performance_processed_with_metrics.csv"

    calculate_performance(input_path, output_path)