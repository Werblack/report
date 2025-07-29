import logging
from datetime import datetime
from .extractor import SafraExtractor
from .transform import SafraTransformer
import sys
from pathlib import Path

# Adicionar config ao path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import config

class SafraETLPipeline:
    """Pipeline ETL baseado na estrutura real do Relatorio_Diario"""
    
    def __init__(self):
        self.extractor = SafraExtractor()
        self.transformer = SafraTransformer()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def executar_pipeline_completo(self, arquivo_relatorio: str = None) -> bool:
        """Executa pipeline ETL usando apenas colunas existentes"""
        inicio = datetime.now()
        self.logger.info("🚀 Iniciando pipeline ETL Safra")
        
        try:
            # 1. Extração
            self.logger.info("📥 FASE 1: Extração de dados")
            relatorio_diario = self.extractor.extrair_relatorio_diario(arquivo_relatorio)
            base_historica = self.extractor.extrair_base_historica()
            
            # 2. Transformação (apenas limpeza e padronização)
            self.logger.info("🔄 FASE 2: Limpeza e padronização")
            dados_processados = self.transformer.processar_dados_completo(
                relatorio_diario, base_historica
            )
            
            # 3. Salvar dados processados
            self.logger.info("💾 FASE 3: Salvando dados processados")
            arquivo_saida = config.PROCESSED_DIR / config.DASHBOARD_DATA
            dados_processados.to_parquet(arquivo_saida, index=False)
            self.logger.info(f"✅ Dados salvos em: {arquivo_saida}")
            
            # 4. Relatório final
            tempo_execucao = datetime.now() - inicio
            self._gerar_relatorio_execucao(dados_processados, tempo_execucao)
            
            self.logger.info("✅ Pipeline ETL executado com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"💥 Erro crítico no pipeline: {e}")
            return False
    
    def _setup_logging(self):
        """Configura sistema de logging"""
        log_file = config.LOGS_DIR / f"safra_etl_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def _gerar_relatorio_execucao(self, df_final, tempo_execucao):
        """Gera relatório de execução"""
        self.logger.info("📋 RELATÓRIO DE EXECUÇÃO:")
        self.logger.info(f"   ⏱️ Tempo total: {tempo_execucao}")
        self.logger.info(f"   📊 Registros processados: {len(df_final):,}")
        if 'Provider' in df_final.columns:
            self.logger.info(f"   🏢 Providers únicos: {df_final['Provider'].nunique()}")

def executar_etl(arquivo_relatorio: str = None) -> bool:
    """Função principal para executar ETL"""
    pipeline = SafraETLPipeline()
    return pipeline.executar_pipeline_completo(arquivo_relatorio)
