import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import sys
import os

# Adicionar config ao path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import config

class SafraExtractor:
    """Extrator de dados otimizado e robusto"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extrair_relatorio_diario(self, arquivo_path: Optional[str] = None) -> pd.DataFrame:
        """Extrai dados do relatório diário com validação robusta"""
        if arquivo_path is None:
            arquivo_path = config.INPUT_DIR / config.RELATORIO_DIARIO
        
        try:
            self.logger.info(f"🔄 Extraindo relatório diário: {arquivo_path}")
            
            if not Path(arquivo_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_path}")
            
            df = pd.read_excel(
                arquivo_path,
                sheet_name=0,
                na_values=['', ' ', 'N/A', 'n/a', '#N/D', '#REF!', '#VALOR!'],
                keep_default_na=True
            )
            
            if df.empty:
                raise ValueError("Arquivo está vazio")
            
            if 'Ordem PagBank' not in df.columns:
                raise ValueError("Coluna 'Ordem PagBank' não encontrada")
            
            self.logger.info(f"✅ Extraídos {len(df):,} registros do relatório diário")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao extrair relatório diário: {e}")
            raise
    
    def extrair_base_historica(self) -> pd.DataFrame:
        """Extrai base histórica ou cria uma nova se não existir"""
        arquivo_historico = config.PROCESSED_DIR / config.BASE_HISTORICA
        
        try:
            if arquivo_historico.exists():
                self.logger.info(f"🔄 Carregando base histórica: {arquivo_historico}")
                df = pd.read_parquet(arquivo_historico)
                self.logger.info(f"✅ Base histórica carregada: {len(df):,} registros")
                return df
            else:
                self.logger.info("📝 Base histórica não existe, será criada no primeiro processamento")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar base histórica: {e}")
            return pd.DataFrame()
