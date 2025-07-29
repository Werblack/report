import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import pytz
import io
from pathlib import Path
from typing import Dict, List
import sys

# Adicionar config ao path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import config

class PoloReportManager:
    """Gerenciador simplificado de relatórios por polo"""
    
    def __init__(self):
        self.brasilia_tz = pytz.timezone('America/Sao_Paulo')
        self.arquivo_historico = config.PROCESSED_DIR / "historico_exportacoes.parquet"
    
    def gerar_relatorio_por_polo(self, dados_dashboard: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Gera relatório de ordens em aberto agrupadas por polo"""
        
        filtro_aberto = (
            (dados_dashboard['Status_Tratativa'].isin(['Em Aberto', 'Pendente', ''])) |
            (dados_dashboard['Status_Tratativa'].isna()) |
            (dados_dashboard['Status_SLA'] == 'Vencido')
        )
        
        ordens_abertas = dados_dashboard[filtro_aberto].copy()
        
        if ordens_abertas.empty:
            return {}
        
        ordens_abertas['Nivel_Urgencia'] = ordens_abertas.apply(self._calcular_urgencia, axis=1)
        ordens_abertas['Descricao_Urgencia'] = ordens_abertas['Nivel_Urgencia'].map({
            5: '🔴 CRÍTICO',
            4: '🟠 ALTO',
            3: '🟡 MÉDIO',
            2: '🔵 BAIXO',
            1: '⚪ NORMAL'
        })
        
        relatorio_polos = {}
        
        if 'Provider' in ordens_abertas.columns:
            for polo in ordens_abertas['Provider'].unique():
                if pd.notna(polo):
                    ordens_polo = ordens_abertas[ordens_abertas['Provider'] == polo].copy()
                    
                    ordens_polo = ordens_polo.sort_values(
                        ['Nivel_Urgencia', 'Dias_Em_Aberto'], 
                        ascending=[False, False]
                    )
                    
                    ordens_polo = self._adicionar_estatisticas_polo(ordens_polo)
                    relatorio_polos[polo] = ordens_polo
        
        return relatorio_polos
    
    def _calcular_urgencia(self, row) -> int:
        """Calcula nível de urgência (1-5)"""
        try:
            status_sla = row.get('Status_SLA', '')
            dias_aberto = row.get('Dias_Em_Aberto', 0)
            sla_cliente = row.get('SLA Cliente', 999)
            
            if status_sla == 'Vencido' or dias_aberto > sla_cliente:
                return 5  # CRÍTICO
            elif dias_aberto >= sla_cliente * 0.9:
                return 4  # ALTO
            elif dias_aberto >= sla_cliente * 0.7:
                return 3  # MÉDIO
            elif dias_aberto >= sla_cliente * 0.5:
                return 2  # BAIXO
            else:
                return 1  # NORMAL
        except:
            return 1
    
    def _adicionar_estatisticas_polo(self, df_polo: pd.DataFrame) -> pd.DataFrame:
        """Adiciona estatísticas resumidas do polo"""
        if df_polo.empty:
            return df_polo
        
        total_ordens = len(df_polo)
        criticas = len(df_polo[df_polo['Nivel_Urgencia'] == 5])
        altas = len(df_polo[df_polo['Nivel_Urgencia'] == 4])
        media_dias = df_polo['Dias_Em_Aberto'].mean()
        
        df_polo['Total_Ordens_Polo'] = total_ordens
        df_polo['Ordens_Criticas'] = criticas
        df_polo['Ordens_Altas'] = altas
        df_polo['Media_Dias_Polo'] = round(media_dias, 1)
        
        return df_polo
    
    def registrar_exportacao(self, polo_id: str, quantidade_ordens: int, 
                           formato: str, usuario: str = "dashboard_user") -> bool:
        """Registra exportação realizada no histórico"""
        try:
            if self.arquivo_historico.exists():
                historico = pd.read_parquet(self.arquivo_historico)
            else:
                historico = pd.DataFrame()
            
            novo_registro = pd.DataFrame([{
                'data_exportacao': datetime.now(self.brasilia_tz),
                'polo_id': polo_id,
                'quantidade_ordens': quantidade_ordens,
                'formato_exportacao': formato,
                'usuario': usuario
            }])
            
            historico_atualizado = pd.concat([historico, novo_registro], ignore_index=True)
            historico_atualizado.to_parquet(self.arquivo_historico, index=False)
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao registrar exportação: {e}")
            return False
    
    def obter_historico_exportacoes(self, dias: int = 7) -> pd.DataFrame:
        """Obtém histórico de exportações recentes"""
        if not self.arquivo_historico.exists():
            return pd.DataFrame()
        
        historico = pd.read_parquet(self.arquivo_historico)
        
        data_corte = datetime.now(self.brasilia_tz) - timedelta(days=dias)
        historico_recente = historico[historico['data_exportacao'] >= data_corte]
        
        return historico_recente.sort_values('data_exportacao', ascending=False)
