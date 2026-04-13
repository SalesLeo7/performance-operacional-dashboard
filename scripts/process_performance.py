import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_working_hours(start, end):
    """
    Calcula a diferença em horas entre duas datas, considerando apenas dias úteis.
    Para simplificação inicial, assume-se que 24h em dias úteis significa que 
    se cair no final de semana, o prazo é estendido.
    """
    if pd.isna(start) or pd.isna(end):
        return np.nan
    
    # Gerar range de datas entre start e end
    # Se for no mesmo dia, apenas subtrair
    if start.date() == end.date():
        return (end - start).total_seconds() / 3600
    
    # Usar networkdays ou lógica similar
    # Vamos usar uma abordagem de contar horas úteis
    # Para este script, vamos considerar '24h úteis' como:
    # Se recebido na sexta às 10h, o prazo é segunda às 10h.
    
    days = np.busday_count(start.date(), end.date())
    
    # Se o início for fim de semana, ajustar para o próximo dia útil às 00:00
    # Mas o enunciado pede "recebidas dentro de 24h" em dias úteis.
    # Uma forma comum de interpretar isso é: total de horas - horas de fim de semana.
    
    total_hours = (end - start).total_seconds() / 3600
    
    # Calcular quantos fins de semana existem no intervalo
    # Cada dia de fim de semana remove 24h
    current = start
    weekend_hours = 0
    while current < end:
        if current.weekday() >= 5: # 5=Sábado, 6=Domingo
            # Se o dia atual é fim de semana, adicionamos as horas até o fim do dia ou até o 'end'
            next_day = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            limit = min(next_day, end)
            weekend_hours += (limit - current).total_seconds() / 3600
            current = limit
        else:
            # Pula para o início do próximo dia
            current = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            
    return total_hours - weekend_hours

def process_data(file_path):
    df = pd.read_csv(file_path)
    
    # Converter colunas de data
    date_cols = ['Creation Date', 'Finish Date']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format='%m-%d-%Y %H:%M:%S', errors='coerce')
    
    # Remover linhas sem data
    df = df.dropna(subset=['Creation Date', 'Finish Date'])
    
    # Calcular horas úteis
    df['working_hours'] = df.apply(lambda x: calculate_working_hours(x['Creation Date'], x['Finish Date']), axis=1)
    
    # Definir performance
    df['performance'] = df['working_hours'].apply(lambda x: 'on_time' if x <= 24 else 'out_time')
    
    return df

if __name__ == "__main__":
    input_file = "/home/ubuntu/upload/performance.csv"
    output_file = "/home/ubuntu/performance_processed.csv"
    
    processed_df = process_data(input_file)
    processed_df.to_csv(output_file, index=False)
    print(f"Processamento concluído. Arquivo salvo em: {output_file}")
    print(processed_df['performance'].value_counts())
