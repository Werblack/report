import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import pytz

def setup_logging(log_path: str) -> None:
    """Configura o sistema de logging"""
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def calcular_dias_em_aberto(data_status):
    """Calcula dias em aberto usando data atual de Brasília"""
    if pd.isna(data_status):
        return None
    
    try:
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        data_atual_brasilia = datetime.now(brasilia_tz).date()
        
        if isinstance(data_status, datetime):
            data_status = data_status.date()
        elif isinstance(data_status, str):
            data_status = pd.to_datetime(data_status, errors='coerce').date()
        elif hasattr(data_status, 'date'):
            data_status = data_status.date()
        else:
            return None
        
        diferenca = (data_atual_brasilia - data_status).days
        return diferenca if diferenca >= 0 else 0
        
    except Exception:
        return None

def limpar_dados_problematicos(df: pd.DataFrame) -> pd.DataFrame:
    """Remove valores problemáticos antes da conversão"""
    valores_problematicos = ['#N/D', '#REF!', '#VALOR!', 'N/A', 'n/a', '', ' ', 'nan']
    df_limpo = df.replace(valores_problematicos, np.nan)
    
    for col in df_limpo.select_dtypes(include=['object']).columns:
        df_limpo[col] = df_limpo[col].astype(str).str.strip()
        df_limpo[col] = df_limpo[col].replace('nan', np.nan)
    
    return df_limpo

def converter_tipos_seguros(df: pd.DataFrame, tipos_map: Dict) -> pd.DataFrame:
    """Conversão segura de tipos com máxima performance"""
    df_copy = df.copy()
    
    # Números inteiros
    for col in tipos_map.get('numeros_inteiros', []):
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').astype('Int64')
    
    # Datas
    for col in tipos_map.get('datas', []):
        if col in df_copy.columns:
            df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce', dayfirst=True)
    
    # Textos
    for col in tipos_map.get('textos', []):
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].astype('string')
    
    return df_copy
