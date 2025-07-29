import pandas as pd
import logging
from typing import Dict, List, Any, Optional

class DataValidator:
    """Validador de dados para o pipeline ETL"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.erros = []
        self.warnings = []
    
    def validar_schema_relatorio_diario(self, df: pd.DataFrame) -> bool:
        """Valida schema do relatório diário"""
        colunas_obrigatorias = ['Ordem PagBank']
        colunas_recomendadas = ['Provider', 'SLA Cliente', 'Status da Ordem']
        
        # Verificar colunas obrigatórias
        colunas_faltantes = set(colunas_obrigatorias) - set(df.columns)
        if colunas_faltantes:
            self.erros.append(f"Colunas obrigatórias faltantes: {colunas_faltantes}")
            return False
        
        # Verificar colunas recomendadas
        colunas_recomendadas_faltantes = set(colunas_recomendadas) - set(df.columns)
        if colunas_recomendadas_faltantes:
            self.warnings.append(f"Colunas recomendadas faltantes: {colunas_recomendadas_faltantes}")
        
        return True
    
    def validar_dados_ordem_pagbank(self, df: pd.DataFrame) -> bool:
        """Valida dados da coluna Ordem PagBank"""
        if 'Ordem PagBank' not in df.columns:
            self.erros.append("Coluna 'Ordem PagBank' não encontrada")
            return False
        
        # Verificar valores nulos
        nulos = df['Ordem PagBank'].isna().sum()
        if nulos > 0:
            self.warnings.append(f"Encontrados {nulos} valores nulos em 'Ordem PagBank'")
        
        # Verificar duplicatas
        duplicatas = df['Ordem PagBank'].duplicated().sum()
        if duplicatas > 0:
            self.warnings.append(f"Encontradas {duplicatas} duplicatas em 'Ordem PagBank'")
        
        return True
    
    def validar_integridade_dados(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Executa validações de integridade completas"""
        resultado = {
            'valido': True,
            'total_registros': len(df),
            'erros': [],
            'warnings': [],
            'estatisticas': {}
        }
        
        # Validações básicas
        if not self.validar_schema_relatorio_diario(df):
            resultado['valido'] = False
        
        self.validar_dados_ordem_pagbank(df)
        
        # Adicionar erros e warnings
        resultado['erros'] = self.erros.copy()
        resultado['warnings'] = self.warnings.copy()
        
        # Estatísticas básicas
        if 'Provider' in df.columns:
            resultado['estatisticas']['providers_unicos'] = df['Provider'].nunique()
        
        if 'SLA Cliente' in df.columns:
            resultado['estatisticas']['sla_medio'] = df['SLA Cliente'].mean()
        
        # Log dos resultados
        if resultado['erros']:
            self.logger.error(f"Erros de validação: {resultado['erros']}")
        
        if resultado['warnings']:
            self.logger.warning(f"Warnings de validação: {resultado['warnings']}")
        
        return resultado
    
    def limpar_erros_warnings(self):
        """Limpa lista de erros e warnings"""
        self.erros = []
        self.warnings = []
