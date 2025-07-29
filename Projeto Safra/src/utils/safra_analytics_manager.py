import pandas as pd
import streamlit as st
from pathlib import Path

class SafraAnalyticsManager:
    def __init__(self, config):
        self.config = config

    def carregar_mapeamento_lider_polo(self):
        """Carrega mapeamento líder-polo"""
        arquivo = Path(self.config.INPUT_DIR) / "pagresolve_regionais.xlsx"
        
        if not arquivo.exists():
            st.error(f"❌ Arquivo não encontrado: {arquivo}")
            return pd.DataFrame()
        
        try:
            df = pd.read_excel(arquivo)
            return df
        except Exception as e:
            st.error(f"❌ Erro ao ler mapeamento: {e}")
            return pd.DataFrame()

    def associar_lider(self, df_relatorio, df_mapeamento):
        """Associação simples Provider = Polo + SAP"""
        df = df_relatorio.copy()
        
        # Merge direto
        resultado = df.merge(
            df_mapeamento[['Polo + SAP', 'Líder PagResolve']],
            left_on='Provider',
            right_on='Polo + SAP',
            how='left'
        )
        
        # Renomear
        resultado = resultado.rename(columns={'Líder PagResolve': 'Lider'})
        
        return resultado

    def obter_lideres(self, df):
        """Obtém líderes únicos"""
        return ['TODOS'] + sorted(df['Lider'].dropna().unique().tolist())

    def filtrar_por_lider(self, df, lider):
        """Filtra por líder"""
        if lider == 'TODOS':
            return df
        return df[df['Lider'] == lider]

    def calcular_metricas_reais(self, df_filtrado):
        """Calcula métricas baseadas nas colunas reais"""
        if df_filtrado.empty:
            return {
                'total_ordens': 0,
                'total_em_aberto': 0,
                'perc_em_aberto': 0,
                'acima_2_dias_sla': 0,
                'perc_acima_2_dias': 0,
                'sla_medio': 0
            }
        
        total_ordens = len(df_filtrado)
        
        # Ordens em aberto (baseado no Status da Ordem)
        em_aberto = df_filtrado[df_filtrado['Status da Ordem'].isin(['Em Aberto', 'Pendente', 'Em Andamento'])]
        total_em_aberto = len(em_aberto)
        perc_em_aberto = (total_em_aberto / total_ordens * 100) if total_ordens > 0 else 0
        
        # SLA > 2 dias (baseado na coluna SLA Cliente)
        if 'SLA Cliente' in em_aberto.columns and not em_aberto.empty:
            acima_2_dias = len(em_aberto[em_aberto['SLA Cliente'] > 2])
            perc_acima_2_dias = (acima_2_dias / total_em_aberto * 100) if total_em_aberto > 0 else 0
            sla_medio = em_aberto['SLA Cliente'].mean()
        else:
            acima_2_dias = 0
            perc_acima_2_dias = 0
            sla_medio = 0
        
        return {
            'total_ordens': total_ordens,
            'total_em_aberto': total_em_aberto,
            'perc_em_aberto': perc_em_aberto,
            'acima_2_dias_sla': acima_2_dias,
            'perc_acima_2_dias': perc_acima_2_dias,
            'sla_medio': sla_medio
        }
