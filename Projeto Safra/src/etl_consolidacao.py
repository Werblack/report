import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List
import warnings
import shutil
warnings.filterwarnings('ignore')

from config import Config
from utils import setup_logging, limpar_dados_problematicos, converter_tipos_seguros, executar_validacoes, calcular_dias_em_aberto

class SafraETLProcessor:
    
    def __init__(self):
        self.config = Config()
        setup_logging(self.config.CAMINHOS['logs'])
        
    def carregar_base_historica(self) -> pd.DataFrame:
        """Carrega a base histórica"""
        logging.info("📂 Carregando base histórica...")
        
        try:
            df = pd.read_excel(
                self.config.CAMINHOS['base_historica'],
                sheet_name=self.config.PARAMETROS['sheet_base']
            )
            logging.info(f"✅ Base histórica carregada: {len(df):,} registros")
            return df
        except Exception as e:
            logging.error(f"❌ Erro ao carregar base histórica: {e}")
            raise
    
    def carregar_relatorio_diario(self) -> pd.DataFrame:
        """Carrega o relatório diário"""
        logging.info("📂 Carregando relatório diário...")
        
        try:
            df = pd.read_excel(
                self.config.CAMINHOS['relatorio_diario'],
                sheet_name=self.config.PARAMETROS['sheet_relatorio']
            )
            logging.info(f"✅ Relatório diário carregado: {len(df):,} registros")
            return df
        except Exception as e:
            logging.error(f"❌ Erro ao carregar relatório diário: {e}")
            raise
    
    def aplicar_filtros_negocio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica filtros específicos no relatório diário"""
        logging.info("🔍 Aplicando filtros de negócio...")
        
        df_filtrado = df.copy()
        registros_inicial = len(df_filtrado)
        
        # Filtro 1: Excluir Provider "TEFTI"
        if 'Provider' in df_filtrado.columns:
            df_filtrado = df_filtrado[~df_filtrado['Provider'].isin(self.config.PROVIDERS_EXCLUIDOS)]
            removidos_provider = registros_inicial - len(df_filtrado)
            logging.info(f"   Filtro Provider: {removidos_provider:,} registros removidos")
        
        # Filtro 2: SLA Cliente >= 2 (tratamento seguro)
        if 'SLA Cliente' in df_filtrado.columns:
            antes_sla = len(df_filtrado)
            df_filtrado['SLA Cliente'] = pd.to_numeric(df_filtrado['SLA Cliente'], errors='coerce').fillna(0)
            df_filtrado = df_filtrado[df_filtrado['SLA Cliente'] >= self.config.SLA_CLIENTE_MINIMO]
            removidos_sla = antes_sla - len(df_filtrado)
            logging.info(f"   Filtro SLA: {removidos_sla:,} registros removidos")
        
        logging.info(f"✅ Filtros aplicados: {registros_inicial:,} → {len(df_filtrado):,} registros")
        return df_filtrado
    
    def processar_caixa3_otimizado(self, base_historica: pd.DataFrame, relatorio_filtrado: pd.DataFrame, em_ambos: set) -> pd.DataFrame:
        """
        Processa Caixa 3 com merge otimizado - CORRIGIDO para atualizar corretamente
        """
        logging.info("🔄 Processando Caixa 3 (atualizações) com merge otimizado...")
        
        if not em_ambos:
            return pd.DataFrame()
        
        # Filtrar apenas registros que estão em ambos
        base_para_merge = base_historica[base_historica['Ordem PagBank'].isin(em_ambos)].copy()
        relatorio_para_merge = relatorio_filtrado[relatorio_filtrado['Ordem PagBank'].isin(em_ambos)].copy()
        
        # Fazer merge
        merged = base_para_merge.merge(
            relatorio_para_merge, 
            on='Ordem PagBank', 
            suffixes=('_hist', '_novo')
        )
        
        # Criar DataFrame resultado com estrutura da base histórica
        resultado = pd.DataFrame()
        
        # Para cada coluna da base histórica
        for col in base_historica.columns:
            col_hist = col + '_hist'
            col_novo = col + '_novo'
            
            if col == 'Ordem PagBank':
                # Chave principal - usar valor original
                resultado[col] = merged[col]
            elif col in self.config.COLUNAS_FEEDBACK:
                # Colunas de feedback - SEMPRE preservar valor histórico
                resultado[col] = merged[col_hist] if col_hist in merged.columns else merged.get(col, None)
                logging.debug(f"   📋 Preservando feedback: {col}")
            elif col in self.config.COLUNAS_ATUALIZAR and col_novo in merged.columns:
                # Colunas para atualizar - usar valor do relatório diário
                resultado[col] = merged[col_novo]
                logging.debug(f"   🔄 Atualizando: {col}")
            else:
                # Outras colunas - usar valor histórico como padrão
                resultado[col] = merged[col_hist] if col_hist in merged.columns else merged.get(col, None)
        
        logging.info(f"   ✅ Caixa 3 processada: {len(resultado):,} registros atualizados")
        
        # Log de colunas atualizadas
        colunas_atualizadas = [col for col in self.config.COLUNAS_ATUALIZAR if col in resultado.columns]
        logging.info(f"   📊 Colunas atualizadas: {len(colunas_atualizadas)} ({', '.join(colunas_atualizadas[:5])}...)")
        
        return resultado
    
    def processar_dias_em_aberto(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula dias em aberto para todos os registros usando data atual de Brasília"""
        logging.info("📅 Calculando dias em aberto com data atual de Brasília...")
        
        df_copy = df.copy()
        
        if 'Data_Status' in df_copy.columns:
            # Aplicar cálculo para cada registro
            df_copy['Dias_Em_Aberto'] = df_copy['Data_Status'].apply(calcular_dias_em_aberto)
            
            # Log de estatísticas
            dias_calculados = df_copy['Dias_Em_Aberto'].notna().sum()
            if dias_calculados > 0:
                dias_medio = df_copy['Dias_Em_Aberto'].mean()
                dias_max = df_copy['Dias_Em_Aberto'].max()
                logging.info(f"   ✅ Calculados dias em aberto para {dias_calculados:,} registros")
                logging.info(f"   📊 Média: {dias_medio:.1f} dias | Máximo: {dias_max} dias")
            else:
                logging.warning("   ⚠️ Nenhum registro com Data_Status válida encontrado")
        else:
            logging.warning("   ⚠️ Coluna 'Data_Status' não encontrada - usando valor padrão")
            df_copy['Dias_Em_Aberto'] = None
        
        return df_copy
    
    def criar_backup_inteligente(self) -> None:
        """Cria backup em pasta separada sem alterar arquivo original"""
        logging.info("📋 Criando backup inteligente...")
        
        try:
            arquivo_original = Path(self.config.CAMINHOS['saida'])
            pasta_backup = Path(self.config.CAMINHOS['backup_dir'])
            
            # Criar pasta de backup se não existir
            pasta_backup.mkdir(parents=True, exist_ok=True)
            
            if arquivo_original.exists():
                # Nome do backup com timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_backup = f"Safra_Gerencial_backup_{timestamp}.xlsx"
                caminho_backup = pasta_backup / nome_backup
                
                # Copiar arquivo para backup
                shutil.copy2(arquivo_original, caminho_backup)
                logging.info(f"   ✅ Backup criado: {nome_backup}")
            else:
                logging.info("   ℹ️ Arquivo original não existe - pulando backup")
                
        except Exception as e:
            logging.warning(f"   ⚠️ Erro ao criar backup: {e}")
    
    def salvar_resultado(self, df: pd.DataFrame) -> None:
        """Salva o resultado final mantendo nome da aba"""
        logging.info("💾 Salvando resultado final...")
        
        try:
            # Criar backup antes de sobrescrever
            self.criar_backup_inteligente()
            
            arquivo_saida = Path(self.config.CAMINHOS['saida'])
            
            # Salvar com nome correto da aba
            with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
                df.to_excel(
                    writer, 
                    sheet_name=self.config.PARAMETROS['sheet_saida'],  # 'Consolidado'
                    index=False
                )
            
            logging.info(f"✅ Arquivo salvo: {arquivo_saida}")
            logging.info(f"   📋 Aba: {self.config.PARAMETROS['sheet_saida']}")
            
        except Exception as e:
            logging.error(f"❌ Erro ao salvar: {e}")
            raise
    
    def preparar_dados_dashboard(self, df: pd.DataFrame) -> None:
        """Prepara datasets otimizados para dashboard com Status_Tratativa"""
        logging.info("📊 Preparando dados para dashboard...")
        
        try:
            # Dataset agregado por Status_Tratativa (não Status da Ordem)
            if 'Status_Tratativa' in df.columns:
                status_summary = df.groupby('Status_Tratativa').agg({
                    'Ordem PagBank': 'count',
                    'SLA Cliente': 'mean',
                    'Dias_Em_Aberto': 'mean'
                }).reset_index()
                status_summary.columns = ['Status_Tratativa', 'Quantidade', 'SLA_Medio', 'Dias_Aberto_Medio']
            else:
                status_summary = pd.DataFrame()
            
            # Dataset temporal
            if 'Criação da Ordem' in df.columns:
                df_temp = df.copy()
                df_temp['Mes_Criacao'] = pd.to_datetime(df_temp['Criação da Ordem'], errors='coerce').dt.to_period('M')
                temporal_summary = df_temp.groupby('Mes_Criacao').size().reset_index(name='Quantidade')
            else:
                temporal_summary = pd.DataFrame()
            
            # Dataset por região
            if 'Região' in df.columns and 'Estado' in df.columns:
                regional_summary = df.groupby(['Região', 'Estado']).size().reset_index(name='Quantidade')
            else:
                regional_summary = pd.DataFrame()
            
            # Dataset por provider
            if 'Provider' in df.columns:
                provider_summary = df.groupby('Provider').size().reset_index(name='Quantidade')
            else:
                provider_summary = pd.DataFrame()
            
            # Dataset de feedback (NOVO)
            colunas_feedback = ['Ordem PagBank', 'Status_Tratativa', 'Feedback', 'Causa_Raiz', 'Data_Feedback', 'Proxima_Acao', 'Dias_Em_Aberto']
            feedback_df = df[colunas_feedback].copy() if all(col in df.columns for col in colunas_feedback) else pd.DataFrame()
            
            # Salvar datasets para dashboard
            dashboard_path = Path(self.config.CAMINHOS['dashboard_data'])
            dashboard_path.parent.mkdir(parents=True, exist_ok=True)
            
            with pd.ExcelWriter(dashboard_path, engine='openpyxl') as writer:
                if not status_summary.empty:
                    status_summary.to_excel(writer, sheet_name='Status_Tratativa', index=False)
                if not temporal_summary.empty:
                    temporal_summary.to_excel(writer, sheet_name='Temporal', index=False)
                if not regional_summary.empty:
                    regional_summary.to_excel(writer, sheet_name='Regional', index=False)
                if not provider_summary.empty:
                    provider_summary.to_excel(writer, sheet_name='Provider', index=False)
                if not feedback_df.empty:
                    feedback_df.to_excel(writer, sheet_name='Feedback', index=False)
                df.to_excel(writer, sheet_name='Dados_Completos', index=False)
            
            logging.info(f"✅ Dados do dashboard salvos: {dashboard_path}")
            
        except Exception as e:
            logging.error(f"❌ Erro ao preparar dados do dashboard: {e}")
    
    def main(self) -> pd.DataFrame:
        """Função principal que executa todo o pipeline ETL"""
        
        logging.info("="*80)
        logging.info("🚀 INICIANDO PIPELINE ETL SAFRA GERENCIAL - VERSÃO CORRIGIDA")
        logging.info("="*80)
        
        try:
            # 1. EXTRAÇÃO
            logging.info("📥 FASE 1: EXTRAÇÃO DE DADOS")
            base_historica = self.carregar_base_historica()
            relatorio_diario = self.carregar_relatorio_diario()
            
            # 2. TRANSFORMAÇÃO
            logging.info("🔄 FASE 2: TRANSFORMAÇÃO DE DADOS")
            
            # Aplicar filtros de negócio no relatório diário
            relatorio_filtrado = self.aplicar_filtros_negocio(relatorio_diario)
            
            # Limpar dados problemáticos
            base_historica = limpar_dados_problematicos(base_historica)
            relatorio_filtrado = limpar_dados_problematicos(relatorio_filtrado)
            
            # Padronizar chave de união
            base_historica['Ordem PagBank'] = base_historica['Ordem PagBank'].astype(str)
            relatorio_filtrado['Ordem PagBank'] = relatorio_filtrado['Ordem PagBank'].astype(str)
            
            # LÓGICA CORRIGIDA DAS TRÊS CAIXAS
            logging.info("📦 Aplicando lógica corrigida das três caixas...")
            
            chaves_historico = set(base_historica['Ordem PagBank'])
            chaves_diario = set(relatorio_filtrado['Ordem PagBank'])
            
            # CAIXA 1: Ordens que só existem na base histórica (manter como estão)
            so_historico = chaves_historico - chaves_diario
            caixa1_historico_puro = base_historica[base_historica['Ordem PagBank'].isin(so_historico)].copy()
            logging.info(f"   📦 Caixa 1 (só no histórico): {len(caixa1_historico_puro):,}")
            
            # CAIXA 2: Ordens que só existem no relatório diário (novas ordens)
            so_diario = chaves_diario - chaves_historico
            caixa2_novas_ordens = relatorio_filtrado[relatorio_filtrado['Ordem PagBank'].isin(so_diario)].copy()
            logging.info(f"   📦 Caixa 2 (novas ordens): {len(caixa2_novas_ordens):,}")
            
            # CAIXA 3: Ordens que existem em ambos (atualizar com merge otimizado)
            em_ambos = chaves_historico & chaves_diario
            logging.info(f"   📦 Caixa 3 (para atualizar): {len(em_ambos):,}")
            
            # Processar Caixa 3 com merge otimizado
            caixa3_df = self.processar_caixa3_otimizado(base_historica, relatorio_filtrado, em_ambos)
            
            # COMBINAR TODAS AS CAIXAS
            logging.info("🔗 Combinando todas as caixas...")
            
            # Garantir que todas tenham as mesmas colunas
            todas_colunas = set()
            for df in [caixa1_historico_puro, caixa2_novas_ordens, caixa3_df]:
                if not df.empty:
                    todas_colunas.update(df.columns)
            
            # Adicionar colunas faltantes
            for df in [caixa1_historico_puro, caixa2_novas_ordens, caixa3_df]:
                if not df.empty:
                    for col in todas_colunas:
                        if col not in df.columns:
                            df[col] = None
            
            # Combinar (sem duplicatas por design)
            dataframes_validos = [df for df in [caixa1_historico_puro, caixa2_novas_ordens, caixa3_df] if not df.empty]
            
            if dataframes_validos:
                resultado_final = pd.concat(dataframes_validos, ignore_index=True)
            else:
                raise ValueError("Nenhum dado válido para combinar!")
            
            # CALCULAR DIAS EM ABERTO COM DATA ATUAL DE BRASÍLIA
            resultado_final = self.processar_dias_em_aberto(resultado_final)
            
            # Converter tipos de dados
            logging.info("🔧 Convertendo tipos de dados...")
            resultado_final = converter_tipos_seguros(resultado_final, self.config.TIPOS_DADOS)
            
            # 3. CARGA
            logging.info("📤 FASE 3: CARGA DE DADOS")
            self.salvar_resultado(resultado_final)
            
            # 4. VALIDAÇÕES
            logging.info("✅ FASE 4: VALIDAÇÕES")
            duplicatas = resultado_final['Ordem PagBank'].duplicated().sum()
            if duplicatas > 0:
                logging.warning(f"⚠️ Encontradas {duplicatas} duplicatas - removendo...")
                resultado_final = resultado_final.drop_duplicates(subset=['Ordem PagBank'], keep='first')
            
            executar_validacoes(resultado_final, base_historica, relatorio_filtrado)
            
            # 5. PREPARAR PARA DASHBOARD
            logging.info("📊 FASE 5: PREPARAÇÃO PARA DASHBOARD")
            self.preparar_dados_dashboard(resultado_final)
            
            # RELATÓRIO FINAL
            logging.info("="*80)
            logging.info("🎉 PIPELINE ETL EXECUTADO COM SUCESSO!")
            logging.info("="*80)
            logging.info(f"📊 Total de registros processados: {len(resultado_final):,}")
            logging.info(f"📦 Histórico puro: {len(caixa1_historico_puro):,}")
            logging.info(f"📦 Novas ordens: {len(caixa2_novas_ordens):,}")
            logging.info(f"📦 Atualizadas: {len(caixa3_df):,}")
            logging.info(f"🕒 Processado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
            logging.info("="*80)
            
            return resultado_final
            
        except Exception as e:
            logging.error(f"❌ Erro no pipeline ETL: {str(e)}")
            raise

if __name__ == "__main__":
    processor = SafraETLProcessor()
    resultado = processor.main()
