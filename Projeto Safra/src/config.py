from pathlib import Path
from datetime import datetime

class Config:
    # Caminhos específicos do seu ambiente
    BASE_DIR = Path(__file__).parent.parent
    
    CAMINHOS = {
        'base_historica': r"C:\Users\sbahia\OneDrive - UNIVERSO ONLINE S.A\Área de Trabalho\Ambiente PY\logins\Projeto Safra\data\Safra_Gerencial_Téc.Prop_17.06.xlsx",
        'relatorio_diario': r"C:\Users\sbahia\OneDrive - UNIVERSO ONLINE S.A\Área de Trabalho\Ambiente PY\logins\Projeto Safra\data\Relatorio_Diario.xlsx",
        'saida': r"C:\Users\sbahia\OneDrive - UNIVERSO ONLINE S.A\Área de Trabalho\Ambiente PY\logins\Projeto Safra\data\Safra_Gerencial_Téc.Prop_17.06.xlsx",
        'backup_dir': r"C:\Users\sbahia\OneDrive - UNIVERSO ONLINE S.A\Área de Trabalho\Ambiente PY\logins\Projeto Safra\backup",
        'dashboard_data': r"C:\Users\sbahia\OneDrive - UNIVERSO ONLINE S.A\Área de Trabalho\Ambiente PY\logins\Projeto Safra\dashboard\dashboard_data.xlsx",
        'logs': BASE_DIR / "logs" / "etl_log.log"
    }
    
    PARAMETROS = {
        'sheet_base': 'Consolidado',  # Aba da base histórica
        'sheet_relatorio': 'Sheet1',  # Aba do relatório diário
        'sheet_saida': 'Consolidado',  # Nome da aba de saída
        'encoding': 'utf-8',
        'date_format': '%d/%m/%Y'
    }
    
    # Colunas de feedback que devem ser SEMPRE preservadas (não atualizar)
    COLUNAS_FEEDBACK = [
        'Status_Tratativa', 'Data_Status', 'Causa_Raiz', 'Feedback', 
        'Data_Feedback', 'Proxima_Acao', 'Alerta_SLA'
    ]
    
    # Colunas que devem ser SEMPRE atualizadas do relatório diário
    COLUNAS_ATUALIZAR = [
        'SLA Cliente', 'SLA Logística', 'Status da Ordem', 'Tipo da Ordem',
        'Provider', 'Transportadora', 'Status Operação', 'Último Tracking',
        'Data Últ. Tracking Indoor', 'Data Últ. Tracking Transporte',
        'Início Indoor', 'Início Transporte', 'Data Tracking',
        'Código Rastreio', 'Status Integração', 'Estado', 'Região',
        'Classif. Cidade', 'Cidade', 'CEP'
    ]
    
    # Filtros de negócio obrigatórios
    PROVIDERS_EXCLUIDOS = ["TEFTI"]
    SLA_CLIENTE_MINIMO = 2
    
    # Mapeamento de tipos otimizado
    TIPOS_DADOS = {
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
            'Status Prazo 10 Dias', 'Status Prazo 10 Dias Tracking',
            'Status Prazo Tracking Entrada', 'classificacao da ordem',
            'DAX_nam_opl', 'DAX_opl', 'operador_operacao', 'operador_operacao2',
            'operador_operacao3', 'operador_sql', 'Status_Tratativa',
            'Causa_Raiz', 'Feedback', 'Proxima_Acao', 'Alerta_SLA'
        ]
    }
