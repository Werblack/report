import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import logging
from typing import Dict, List, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import config

class SafraTransformer:
    """Transformador baseado APENAS nas colunas reais do Relatorio_Diario"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.brasilia_tz = pytz.timezone('America/Sao_Paulo')
    
    def processar_dados_completo(self, relatorio_diario: pd.DataFrame, 
                                base_historica: pd.DataFrame) -> pd.DataFrame:
        """Processamento usando APENAS colunas existentes"""
        try:
            self.logger.info("🔄 Iniciando processamento com colunas reais")
            
            # 1. Limpar e padronizar dados
            relatorio_limpo = self._limpar_dados_reais(relatorio_diario.copy())
            
            # 2. Aplicar filtros básicos
            relatorio_filtrado = self._aplicar_filtros_basicos(relatorio_limpo)
            
            # 3. Padronizar campos existentes
            relatorio_processado = self._padronizar_campos_reais(relatorio_filtrado)
            
            # 4. Merge simples com histórico
            if not base_historica.empty:
                resultado = self._merge_simples(relatorio_processado, base_historica)
            else:
                resultado = relatorio_processado.copy()
                self.logger.info("📝 Primeira execução - criando nova base")
            
            # 5. Validações finais
            resultado = self._validacoes_finais(resultado)
            
            self.logger.info(f"✅ Processamento concluído: {len(resultado):,} registros")
            return resultado
            
        except Exception as e:
            self.logger.error(f"❌ Erro no processamento: {e}")
            raise
    
    def _limpar_dados_reais(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpeza usando apenas colunas que existem"""
        self.logger.info("🧹 Limpando dados reais")
        
        # Remover linhas completamente vazias
        df = df.dropna(how='all')
        
        # Limpar campos de texto
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(['nan', 'None', '', 'NaT'], np.nan)
        
        # Padronizar Provider (campo crítico)
        if 'Provider' in df.columns:
            df['Provider'] = df['Provider'].str.strip()
            self.logger.info("✅ Provider padronizado")
        
        return df
    
    def _aplicar_filtros_basicos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtros básicos usando apenas colunas existentes"""
        self.logger.info("🔍 Aplicando filtros básicos")
        
        tamanho_inicial = len(df)
        
        # Filtrar TEFTI
        if 'Provider' in df.columns:
            df = df[df['Provider'] != 'TEFTI']
            self.logger.info("🚫 TEFTI removido")
        
        # Filtrar por SLA mínimo (se existir)
        if 'SLA Cliente' in df.columns:
            df = df[pd.to_numeric(df['SLA Cliente'], errors='coerce') >= config.SLA_CLIENTE_MINIMO]
            self.logger.info(f"📊 Filtro SLA >= {config.SLA_CLIENTE_MINIMO}")
        
        # Manter apenas registros com Ordem PagBank válida
        if 'Ordem PagBank' in df.columns:
            df = df[df['Ordem PagBank'].notna()]
        
        registros_removidos = tamanho_inicial - len(df)
        self.logger.info(f"📉 Registros removidos: {registros_removidos:,}")
        
        return df
    
    def _padronizar_campos_reais(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padroniza apenas campos que existem"""
        self.logger.info("🔧 Padronizando campos existentes")
        
        # Adicionar timestamp de processamento
        df['Data_Processamento'] = datetime.now(self.brasilia_tz)
        
        # Converter tipos seguros
        df = self._converter_tipos_reais(df)
        
        return df
    
    def _converter_tipos_reais(self, df: pd.DataFrame) -> pd.DataFrame:
        """Conversão segura apenas das colunas que existem"""
        
        # Números inteiros (apenas se existirem)
        colunas_int = ['Ordem PagBank', 'Ordem SAP', 'SLA Cliente', 'SLA Logística', 
                      'Ordem Workfinity', 'Cód. Último Tracking']
        for col in colunas_int:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
        
        # Datas (apenas se existirem)
        colunas_data = ['Criação da Ordem', 'Início Indoor', 'Data Últ. Tracking Indoor', 
                       'Início Transporte', 'Data Últ. Tracking Transporte', 'Data Tracking', 
                       'Data Coleta', 'Previsão do Gerenciador']
        for col in colunas_data:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
        
        # Textos (apenas se existirem)
        colunas_texto = ['Provider', 'Status da Ordem', 'Tipo da Ordem', 'Estado', 
                        'Cidade', 'CEP', 'Transportadora', 'Último Tracking']
        for col in colunas_texto:
            if col in df.columns:
                df[col] = df[col].astype('string')
        
        return df
    
    def _merge_simples(self, relatorio_novo: pd.DataFrame, 
                      base_historica: pd.DataFrame) -> pd.DataFrame:
        """Merge simples preservando histórico"""
        self.logger.info("🔄 Merge com base histórica")
        
        chave_primaria = 'Ordem PagBank'
        
        # Combinar dados novos com histórico
        chaves_historicas = set(base_historica[chave_primaria].dropna())
        chaves_novas = set(relatorio_novo[chave_primaria].dropna())
        
        # Registros só no histórico (manter)
        so_historico = chaves_historicas - chaves_novas
        df_so_historico = base_historica[
            base_historica[chave_primaria].isin(so_historico)
        ].copy()
        
        # Registros novos ou atualizados
        df_atualizados = relatorio_novo.copy()
        
        # Combinar
        resultado_final = pd.concat([df_so_historico, df_atualizados], ignore_index=True)
        
        self.logger.info(f"📊 Merge concluído: {len(resultado_final):,} registros")
        
        return resultado_final
    
    def _validacoes_finais(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validações finais"""
        self.logger.info("✅ Validações finais")
        
        # Remover duplicatas por Ordem PagBank
        tamanho_antes = len(df)
        df = df.drop_duplicates(subset=['Ordem PagBank'], keep='last')
        duplicatas_removidas = tamanho_antes - len(df)
        
        if duplicatas_removidas > 0:
            self.logger.warning(f"⚠️ Duplicatas removidas: {duplicatas_removidas}")
        
        # Ordenar por data de processamento
        if 'Data_Processamento' in df.columns:
            df = df.sort_values('Data_Processamento', ascending=False)
        
        return df
