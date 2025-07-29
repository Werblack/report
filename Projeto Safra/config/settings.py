from pathlib import Path
from typing import List

class SafraConfig:
    """Configuração simplificada sem YAML"""
    
    def __init__(self):
        # Diretórios base
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.INPUT_DIR = self.DATA_DIR / "input"
        self.PROCESSED_DIR = self.DATA_DIR / "processed"
        self.BACKUP_DIR = self.DATA_DIR / "backup"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        
        # Arquivos principais
        self.RELATORIO_DIARIO = "Relatorio_Diario.xlsx"
        self.BASE_HISTORICA = "safra_base_historica.parquet"
        self.DASHBOARD_DATA = "dashboard_data.parquet"
        
        # Configurações de processamento
        self.CHUNK_SIZE = 10000
        self.MAX_MEMORY_GB = 2.0
        self.BACKUP_RETENTION_DAYS = 30
        
        # Regras de negócio
        self.PROVIDERS_EXCLUIDOS = ["TEFTI"]
        self.SLA_CLIENTE_MINIMO = 2
        self.COLUNAS_CHAVE = ["Ordem PagBank"]
        
        # Tipos de dados para conversão
        self.TIPOS_DADOS = {
            'numeros_inteiros': [
                'Ordem PagBank', 'Ordem SAP', 'SLA Cliente', 'SLA Logística',
                'Cód. Último Tracking', 'Ordem Workfinity', 'SLA', 'SLA Tracking',
                'Dias_Em_Aberto'
            ],
            'datas': [
                'Criação da Ordem', 'Início Indoor', 'Data Últ. Tracking Indoor',
                'Início Transporte', 'Data Últ. Tracking Transporte', 'Data Tracking',
                'Data Coleta', 'Previsão do Gerenciador', 'Data_Status', 'Data_Feedback'
            ],
            'textos': [
                'CEP', 'Material', 'Código Rastreio', 'Provider',
                'Tipo da Ordem', 'Status da Ordem', 'Tipo Atendimento',
                'Transportadora', 'Status Operação', 'Último Tracking',
                'Status Integração', 'Estado', 'Região', 'Classif. Cidade',
                'Origem', 'Cidade', 'status_da_ordem', 'tipo_da_ordem',
                'Status_Tratativa', 'Causa_Raiz', 'Feedback', 'Proxima_Acao', 'Alerta_SLA'
            ]
        }
        
        # Colunas de feedback que devem ser preservadas
        self.COLUNAS_FEEDBACK = [
            'Status_Tratativa', 'Data_Status', 'Causa_Raiz', 'Feedback', 
            'Data_Feedback', 'Proxima_Acao', 'Alerta_SLA'
        ]
        
        # Colunas que devem ser sempre atualizadas
        self.COLUNAS_ATUALIZAR = [
            'SLA Cliente', 'SLA Logística', 'Status da Ordem', 'Tipo da Ordem',
            'Provider', 'Transportadora', 'Status Operação', 'Último Tracking',
            'Data Últ. Tracking Indoor', 'Data Últ. Tracking Transporte',
            'Início Indoor', 'Início Transporte', 'Data Tracking',
            'Código Rastreio', 'Status Integração', 'Estado', 'Região',
            'Classif. Cidade', 'Cidade', 'CEP'
        ]
        
        # Criar diretórios automaticamente
        self._criar_diretorios()
    
    def _criar_diretorios(self):
        """Cria diretórios necessários"""
        for dir_path in [self.DATA_DIR, self.INPUT_DIR, self.PROCESSED_DIR, 
                        self.BACKUP_DIR, self.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

# Instância global
config = SafraConfig()
