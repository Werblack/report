import streamlit as st
import pandas as pd
import io
from pathlib import Path
import sys
import unicodedata
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import base64
import os
from typing import Dict, Tuple, Optional, List
import re

# Adicionar path do projeto
sys.path.append(str(Path(__file__).parent.parent))

# Configuração de cores
CORES = {
    'primaria': 'rgb(255, 231, 45)',
    'secundaria': 'rgb(158, 213, 158)',
    'terciaria': 'rgb(212, 225, 103)',
    'detrator': 'rgb(255, 99, 99)',
    'neutro': 'rgb(240, 240, 240)',
    'texto': 'rgb(51, 51, 51)'
}

# Paleta de cores para gráficos de status
CORES_STATUS = [
    'rgb(255, 231, 45)',   # Amarelo
    'rgb(158, 213, 158)',  # Verde
    'rgb(212, 225, 103)',  # Verde claro
    'rgb(255, 99, 99)',    # Vermelho
    'rgb(135, 206, 235)',  # Azul claro
    'rgb(255, 182, 193)',  # Rosa claro
    'rgb(221, 160, 221)',  # Plum
    'rgb(255, 218, 185)',  # Pêssego
    'rgb(176, 224, 230)',  # Powder Blue
    'rgb(255, 228, 181)'   # Moccasin
]

# Configuração padrão para gráficos
CONFIG_PLOT = {
    'displayModeBar': False,
    'staticPlot': True
}

# Configuração do Azure Logic Apps Webhook
# ATENÇÃO: SUBSTITUA ESTA URL PELA URL REAL DO SEU WEBHOOK DO AZURE LOGIC APPS
LOGIC_APPS_CONFIG = {
    'webhook_url': 'https://prod-110.westus.logic.azure.com:443/workflows/fd5f4751277c4dbfa4be33237150573d/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=p3etm57LOL0Dbyws3NWHHDkCvYHPVmOXGG0RVd_sdys',
    'timeout': 30,
    'retry_attempts': 3
}


def aplicar_estilo_customizado() -> None:
    """Aplica CSS customizado para o dashboard."""
    st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }

    .header-container {
        background: linear-gradient(135deg, rgb(255, 231, 45) 0%, rgb(212, 225, 103) 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }

    .header-title {
        color: rgb(51, 51, 51);
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }

    .titulo-secao {
        color: rgb(51, 51, 51);
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgb(212, 225, 103);
    }

    .info-box {
        background: linear-gradient(135deg, rgb(158, 213, 158) 0%, rgb(212, 225, 103) 100%);
        padding: 1rem;
        border-radius: 8px;
        color: rgb(51, 51, 51);
        font-weight: 500;
        margin: 1rem 0;
    }

    .comparison-box {
        background: linear-gradient(135deg, rgb(255, 255, 255) 0%, rgb(248, 249, 250) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid rgb(212, 225, 103);
        margin: 1rem 0;
    }

    .comparison-title {
        color: rgb(51, 51, 51);
        font-weight: 600;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }

    .comparison-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid rgb(240, 240, 240);
    }

    .comparison-item:last-child {
        border-bottom: none;
    }

    .delta-positive {
        color: rgb(158, 213, 158);
        font-weight: 600;
    }

    .delta-negative {
        color: rgb(255, 99, 99);
        font-weight: 600;
    }

    .formulario-section {
        background: linear-gradient(135deg, rgb(255, 255, 255) 0%, rgb(248, 249, 250) 100%);
        padding: 2rem;
        border-radius: 12px;
        border: 2px solid rgb(255, 231, 45);
        margin: 2rem 0;
    }

    .polo-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid rgb(255, 231, 45);
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .polo-card-critico {
        border-left-color: rgb(255, 99, 99) !important;
    }

    .polo-card-ok {
        border-left-color: rgb(158, 213, 158) !important;
    }

    .polo-card-atencao { /* Novo estilo para atenção */
        border-left-color: rgb(255, 231, 45) !important;
    }

    .webhook-success {
        background: linear-gradient(135deg, rgb(158, 213, 158) 0%, rgb(212, 225, 103) 100%);
        padding: 1rem;
        border-radius: 8px;
        color: rgb(51, 51, 51);
        font-weight: 500;
        margin: 1rem 0;
        border-left: 4px solid rgb(158, 213, 158);
    }

    .campo-obrigatorio::after {
        content: " *";
        color: rgb(255, 99, 99);
        font-weight: bold;
    }

    /* Melhorias para responsividade */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2rem;
        }

        .comparison-item {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def calcular_semana_ano() -> Tuple[int, str]:
    """
    Calcula a semana atual do ano e o período correspondente.

    Returns:
        Tuple[int, str]: Número da semana e período formatado (DD/MM a DD/MM)
    """
    hoje = datetime.now()
    semana = hoje.isocalendar()[1]
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    periodo = f"{inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m')}"
    return semana, periodo


def remover_acentos(texto: str) -> str:
    """
    Remove acentos de uma string usando normalização Unicode.

    Args:
        texto (str): Texto a ser processado

    Returns:
        str: Texto sem acentos
    """
    if pd.isna(texto):
        return ""
    texto = str(texto)
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('ascii')


def normalizar_provider(provider: str) -> str:
    """
    Normaliza o nome do provider removendo prefixos e acentos.

    Args:
        provider (str): Nome do provider

    Returns:
        str: Provider normalizado
    """
    if pd.isna(provider):
        return ""

    provider_str = str(provider).strip().upper()
    if provider_str.startswith('POLO '):
        provider_str = provider_str[5:]

    return remover_acentos(provider_str)


def normalizar_polo_sap(polo_sap: str) -> str:
    """
    Normaliza o nome do polo SAP removendo acentos.

    Args:
        polo_sap (str): Nome do polo SAP

    Returns:
        str: Polo SAP normalizado
    """
    if pd.isna(polo_sap):
        return ""

    polo_str = str(polo_sap).strip().upper()
    return remover_acentos(polo_str)


def calcular_metricas_safra(df_filtrado: pd.DataFrame) -> Dict[str, float]:
    """
    Calcula métricas principais da safra para um DataFrame filtrado.

    Args:
        df_filtrado (pd.DataFrame): DataFrame com dados filtrados

    Returns:
        Dict[str, float]: Dicionário com métricas calculadas
    """
    if df_filtrado.empty:
        return {
            'total_em_aberto': 0,
            'em_atraso': 0,
            'perc_atraso': 0.0,
            'sla_medio': 0.0
        }

    total_em_aberto = len(df_filtrado)

    if 'SLA Cliente' in df_filtrado.columns:
        sla_validos = pd.to_numeric(
            df_filtrado['SLA Cliente'], errors='coerce').dropna()
        if not sla_validos.empty:
            em_atraso = len(sla_validos[sla_validos >= 2])
            perc_atraso = round(
                (em_atraso / total_em_aberto * 100), 1) if total_em_aberto > 0 else 0.0
            sla_medio = round(sla_validos.mean(), 1)
        else:
            em_atraso = 0
            perc_atraso = 0.0
            sla_medio = 0.0
    else:
        em_atraso = 0
        perc_atraso = 0.0
        sla_medio = 0.0

    return {
        'total_em_aberto': total_em_aberto,
        'em_atraso': em_atraso,
        'perc_atraso': perc_atraso,
        'sla_medio': sla_medio
    }


def calcular_deltas(metricas_hoje: Dict[str, float], metricas_ontem: Dict[str, float]) -> Dict[str, float]:
    """
    Calcula as diferenças entre métricas de hoje e ontem.

    Args:
        metricas_hoje (Dict[str, float]): Métricas de hoje
        metricas_ontem (Dict[str, float]): Métricas de ontem

    Returns:
        Dict[str, float]: Deltas calculados
    """
    return {
        'delta_total': metricas_hoje['total_em_aberto'] - metricas_ontem['total_em_aberto'],
        'delta_atraso': metricas_hoje['em_atraso'] - metricas_ontem['em_atraso'],
        'delta_perc_atraso': round(metricas_hoje['perc_atraso'] - metricas_ontem['perc_atraso'], 1),
        'delta_sla_medio': round(metricas_hoje['sla_medio'] - metricas_ontem['sla_medio'], 1)
    }


def preparar_dataframe_para_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara DataFrame para exportação Excel removendo timezone das colunas datetime.

    Args:
        df (pd.DataFrame): DataFrame original

    Returns:
        pd.DataFrame: DataFrame preparado para Excel
    """
    df_export = df.copy()

    # Identificar e converter colunas com timezone
    cols_with_tz = [
        col for col in df_export.columns if pd.api.types.is_datetime64tz_dtype(df_export[col])]
    for col in cols_with_tz:
        df_export[col] = df_export[col].dt.tz_localize(None)

    return df_export


def criar_ranking_vertical(ranking_data: pd.Series) -> Tuple[Optional[go.Figure], Dict]:
    """
    Cria gráfico de ranking vertical para polos com mais ordens em atraso.

    Args:
        ranking_data (pd.Series): Dados do ranking

    Returns:
        Tuple[Optional[go.Figure], Dict]: Figura do Plotly e configuração
    """
    if ranking_data.empty:
        return None, CONFIG_PLOT

    df_ranking = ranking_data.reset_index()
    df_ranking.columns = ['Polo', 'Ordens_em_Atraso']
    df_ranking = df_ranking.head(10)

    # Definir cores baseadas em quantis
    cores = []
    for valor in df_ranking['Ordens_em_Atraso']:
        if valor >= df_ranking['Ordens_em_Atraso'].quantile(0.8):
            cores.append(CORES['detrator'])
        elif valor >= df_ranking['Ordens_em_Atraso'].quantile(0.5):
            cores.append(CORES['primaria'])
        else:
            cores.append(CORES['secundaria'])

    fig = go.Figure(data=[
        go.Bar(
            y=df_ranking['Polo'],
            x=df_ranking['Ordens_em_Atraso'],
            orientation='h',
            marker_color=cores,
            text=df_ranking['Ordens_em_Atraso'],
            textposition='outside',
            textfont=dict(size=12, color=CORES['texto'])
        )
    ])

    fig.update_layout(
        title={
            'text': 'Top 10 Polos - Ordens em Atraso',
            'x': 0.5,
            'font': {'size': 18, 'color': CORES['texto']}
        },
        xaxis_title='Quantidade de Ordens',
        yaxis_title='',
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color=CORES['texto']),
        showlegend=False,
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True, automargin=True),
        autosize=True
    )

    return fig, CONFIG_PLOT


def criar_grafico_comparacao(metricas_hoje: Dict[str, float], metricas_ontem: Dict[str, float]) -> Tuple[go.Figure, Dict]:
    """
    Cria gráfico de comparação entre métricas de hoje e ontem.

    Args:
        metricas_hoje (Dict[str, float]): Métricas de hoje
        metricas_ontem (Dict[str, float]): Métricas de ontem

    Returns:
        Tuple[go.Figure, Dict]: Figura do Plotly e configuração
    """
    categorias = ['Total em Aberto', 'Em Atraso', '% em Atraso', 'SLA Médio']

    valores_hoje = [
        metricas_hoje['total_em_aberto'],
        metricas_hoje['em_atraso'],
        metricas_hoje['perc_atraso'],
        metricas_hoje['sla_medio']
    ]

    valores_ontem = [
        metricas_ontem['total_em_aberto'],
        metricas_ontem['em_atraso'],
        metricas_ontem['perc_atraso'],
        metricas_ontem['sla_medio']
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Hoje',
        x=categorias,
        y=valores_hoje,
        marker_color=CORES['primaria'],
        text=[f"{val:.1f}" if i >= 2 else f"{val:,}" for i,
              val in enumerate(valores_hoje)],
        textposition='auto',
        textfont=dict(size=11, color=CORES['texto'])
    ))

    fig.add_trace(go.Bar(
        name='Ontem',
        x=categorias,
        y=valores_ontem,
        marker_color=CORES['secundaria'],
        text=[f"{val:.1f}" if i >= 2 else f"{val:,}" for i,
              val in enumerate(valores_ontem)],
        textposition='auto',
        textfont=dict(size=11, color=CORES['texto'])
    ))

    fig.update_layout(
        title={
            'text': 'Comparação: Hoje vs Ontem',
            'x': 0.5,
            'font': {'size': 16, 'color': CORES['texto']}
        },
        barmode='group',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color=CORES['texto'], size=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        xaxis=dict(
            tickangle=0,
            tickfont=dict(size=10),
            fixedrange=True
        ),
        yaxis=dict(
            tickfont=dict(size=10),
            fixedrange=True,
            automargin=True
        ),
        autosize=True
    )

    return fig, CONFIG_PLOT


def criar_graficos_ultimo_tracking(df_em_aberto: pd.DataFrame) -> Tuple[Optional[go.Figure], Optional[go.Figure], Dict]:
    """
    Cria gráficos de pizza (%) e barras (quantidade) para último tracking.

    Args:
        df_em_aberto (pd.DataFrame): DataFrame com ordens em aberto

    Returns:
        Tuple[Optional[go.Figure], Optional[go.Figure], Dict]: Gráfico pizza, barras e configuração
    """
    if df_em_aberto.empty or 'Último Tracking' not in df_em_aberto.columns:
        return None, None, CONFIG_PLOT

    status_counts = df_em_aberto['Último Tracking'].value_counts()

    if status_counts.empty:
        return None, None, CONFIG_PLOT

    total_em_aberto = len(df_em_aberto)

    df_status = pd.DataFrame({
        'Status': status_counts.index,
        'Quantidade': status_counts.values,
        'Percentual': (status_counts.values / total_em_aberto * 100).round(1)
    })

    df_status = df_status.head(10)

    # Gráfico de Pizza (%)
    fig_pizza = go.Figure(data=[go.Pie(
        labels=df_status['Status'],
        values=df_status['Percentual'],
        hole=0.4,
        marker_colors=CORES_STATUS[:len(df_status)],
        textinfo='label+percent',
        textposition='auto',
        textfont=dict(size=10, color='black'),
        hovertemplate='<b>%{label}</b><br>Quantidade: %{customdata}<br>Percentual: %{percent}<extra></extra>',
        customdata=df_status['Quantidade'],
        texttemplate='%{label}<br>%{percent}',
        showlegend=True
    )])

    fig_pizza.update_layout(
        title={
            'text': f'Distribuição por Status (Total: {total_em_aberto:,})',
            'x': 0.5,
            'font': {'size': 14, 'color': CORES['texto']}
        },
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color=CORES['texto']),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=10)
        ),
        margin=dict(l=20, r=150, t=60, b=20),
        autosize=True
    )

    # Gráfico de Barras (Quantidade)
    fig_barras = go.Figure(data=[go.Bar(
        y=df_status['Status'],
        x=df_status['Quantidade'],
        orientation='h',
        marker_color=CORES_STATUS[:len(df_status)],
        text=df_status['Quantidade'],
        textposition='outside',
        textfont=dict(size=11, color=CORES['texto']),
        hovertemplate='<b>%{y}</b><br>Quantidade: %{x}<br>Percentual: %{customdata:.1f}%<extra></extra>',
        customdata=df_status['Percentual']
    )])

    fig_barras.update_layout(
        title={
            'text': 'Quantidade por Status (Ordens em Aberto)',
            'x': 0.5,
            'font': {'size': 14, 'color': CORES['texto']}
        },
        xaxis_title='Quantidade de Ordens',
        yaxis_title='Status do Último Tracking',
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color=CORES['texto']),
        showlegend=False,
        margin=dict(l=150, r=50, t=60, b=50),
        yaxis=dict(
            tickfont=dict(size=10),
            automargin=True,
            fixedrange=True
        ),
        xaxis=dict(
            tickfont=dict(size=10),
            fixedrange=True
        ),
        autosize=True
    )

    return fig_pizza, fig_barras, CONFIG_PLOT


def sanitizar_nome_arquivo(nome: str) -> str:
    """
    Sanitiza nome de arquivo removendo caracteres inválidos.

    Args:
        nome (str): Nome original

    Returns:
        str: Nome sanitizado
    """
    return re.sub(r"[^A-Za-z0-9_\-]", "_", nome)


# --- FUNÇÃO ATUALIZADA PARA ENVIAR PARA LOGIC APPS ---
def enviar_para_power_automate(dados_formulario: Dict) -> Tuple[bool, str]:
    """
    Envia justificativas para Power Automate, que salvará o Excel no SharePoint/OneDrive
    e enviará a notificação no Teams.
    """
    try:
        # Preparar Excel em base64
        excel_buffer = io.BytesIO()
        linhas_excel = []
        for polo in dados_formulario['polos']:
            linhas_excel.append({
                'Data': dados_formulario['data'],
                'Semana': dados_formulario['semana'],
                'Líder': dados_formulario['lider'],
                'Polo': polo['nome'],
                'Ordens_Em_Aberto': polo['ordens_em_aberto'],
                'Ordens_Em_Atraso': polo['ordens_em_atraso'],
                'Perc_Atraso': polo['perc_atraso'],
                'Justificativa': polo['justificativa'],
                'Acao_Corretiva': polo['acao_corretiva'],
                'Observacoes': dados_formulario['observacoes']
            })
        df_excel = pd.DataFrame(linhas_excel)
        df_excel.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        excel_base64 = base64.b64encode(
            excel_buffer.getvalue()).decode('utf-8')

        # Payload para Power Automate
        payload = {
            "lider": dados_formulario['lider'],
            "data": dados_formulario['data'],
            "semana": dados_formulario['semana'],
            "observacoes": dados_formulario['observacoes'],
            "polos": dados_formulario['polos'],
            "excel_base64": excel_base64
        }

        # URL do Power Automate
        webhook_url = "https://acffbd35410feb9e84213ac277b8a8.0b.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/262d324819a1445bad53de1a2006d2f8/triggers/manual/paths/invoke/?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=l0SJxJBbKI4QhV_2DrxA8DfrpYqfABHzN-r5YuYB3Js"

        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            verify=r"C:\Users\sbahia\OneDrive - UNIVERSO ONLINE S.A\Área de Trabalho\Ambiente PY\logins\cacert.pem"
        )
        if response.status_code in [200, 201, 202]:
            return True, f"Dados enviados para processamento! (Status: {response.status_code})"
        else:
            return False, f"Erro Power Automate: {response.status_code} - {response.text[:200]}"
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"


def mostrar_mensagem_status(tipo: str, mensagem: str) -> None:
    """
    Mostra mensagem de status padronizada.

    Args:
        tipo (str): Tipo da mensagem (success, error, info, warning)
        mensagem (str): Texto da mensagem
    """
    emoji_map = {
        'success': '✅',
        'error': '❌',
        'info': 'ℹ️',
        'warning': '⚠️'
    }

    emoji = emoji_map.get(tipo, 'ℹ️')

    if tipo == 'success':
        st.success(f"{emoji} {mensagem}")
    elif tipo == 'error':
        st.error(f"{emoji} {mensagem}")
    elif tipo == 'warning':
        st.warning(f"{emoji} {mensagem}")
    else:
        st.info(f"{emoji} {mensagem}")


# Configuração da página
st.set_page_config(
    page_title="Safra Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)
aplicar_estilo_customizado()

# Header
st.markdown("""
<div class="header-container">
    <h1 class="header-title">📊 Safra Dashboard</h1>
    <p>Monitoramento de Performance por Líder • Integração Azure Logic Apps</p>
</div>
""", unsafe_allow_html=True)

# Cache para dados


@st.cache_data(ttl=300)
def carregar_dados_comparativo() -> Dict[str, pd.DataFrame]:
    """
    Carrega dados comparativos de hoje e ontem com cache.

    Returns:
        Dict[str, pd.DataFrame]: Dados de hoje e ontem
    """
    dados = {}

    # Dados de hoje
    try:
        arquivo_hoje = Path('data/input/Relatorio_Diario1.xlsx')
        if arquivo_hoje.exists():
            dados['hoje'] = pd.read_excel(arquivo_hoje)
            mostrar_mensagem_status(
                'success', f"Dados de HOJE: {len(dados['hoje']):,} registros")
        else:
            dados['hoje'] = pd.DataFrame()
            mostrar_mensagem_status(
                'warning', "Arquivo de dados de hoje não encontrado")
    except Exception as e:
        mostrar_mensagem_status(
            'error', f"Erro ao carregar dados de hoje: {e}")
        dados['hoje'] = pd.DataFrame()

    # Dados de ontem
    try:
        arquivo_ontem = Path('data/input/Relatorio_Diario2.xlsx')
        if arquivo_ontem.exists():
            dados['ontem'] = pd.read_excel(arquivo_ontem)
            mostrar_mensagem_status(
                'success', f"Dados de ONTEM: {len(dados['ontem']):,} registros")
        else:
            dados['ontem'] = pd.DataFrame()
            mostrar_mensagem_status(
                'info', "Arquivo de dados de ontem não encontrado")
    except Exception as e:
        mostrar_mensagem_status(
            'warning', f"Dados de ontem não disponíveis: {e}")
        dados['ontem'] = pd.DataFrame()

    return dados


@st.cache_data(ttl=3600)
def carregar_mapeamento() -> pd.DataFrame:
    """
    Carrega mapeamento de regionais com cache.

    Returns:
        pd.DataFrame: Dados de mapeamento
    """
    try:
        df_map = pd.read_excel('data/input/pagresolve_regionais.xlsx')
        # Pré-processar mapeamento para otimizar joins
        df_map['Polo_SAP_Normalizado'] = df_map['Polo + SAP'].apply(
            normalizar_polo_sap)
        return df_map
    except Exception as e:
        mostrar_mensagem_status('error', f"Erro ao carregar mapeamento: {e}")
        return pd.DataFrame()


# Carregar dados
dados_comparativo = carregar_dados_comparativo()
df_mapeamento = carregar_mapeamento()

if df_mapeamento.empty or dados_comparativo['hoje'].empty:
    mostrar_mensagem_status(
        'error', "Dados essenciais não encontrados. Verifique os arquivos de entrada.")
    st.stop()

# Processar dados
df_hoje = dados_comparativo['hoje'][dados_comparativo['hoje']
                                    ['Provider'] != 'TEFTI'].copy()
tem_dados_ontem = not dados_comparativo['ontem'].empty

if tem_dados_ontem:
    df_ontem = dados_comparativo['ontem'][dados_comparativo['ontem']
                                          ['Provider'] != 'TEFTI'].copy()
else:
    df_ontem = pd.DataFrame()


def processar_dados_com_lider(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processa dados adicionando informação do líder.

    Args:
        df (pd.DataFrame): DataFrame original

    Returns:
        pd.DataFrame: DataFrame com coluna de líder
    """
    if df.empty:
        return df

    df_processado = df.copy()
    df_processado['Provider_Normalizado'] = df_processado['Provider'].apply(
        normalizar_provider)

    df_com_lider = df_processado.merge(
        df_mapeamento[['Polo_SAP_Normalizado', 'Líder PagResolve']],
        left_on='Provider_Normalizado',
        right_on='Polo_SAP_Normalizado',
        how='left'
    ).rename(columns={'Líder PagResolve': 'Lider'})

    return df_com_lider


# Processar dados com líder
df_hoje_com_lider = processar_dados_com_lider(df_hoje)
if tem_dados_ontem:
    df_ontem_com_lider = processar_dados_com_lider(df_ontem)
else:
    df_ontem_com_lider = pd.DataFrame()

# Verificar associação
com_lider_hoje = df_hoje_com_lider['Lider'].notna().sum()

if com_lider_hoje > 0:
    lideres = ['TODOS'] + \
        sorted(df_hoje_com_lider['Lider'].dropna().unique().tolist())

    st.markdown('<h3 class="titulo-secao">🎯 Seleção de Líder</h3>',
                unsafe_allow_html=True)
    lider_selecionado = st.selectbox(
        "Selecione o líder:", lideres, label_visibility="collapsed")

    # Filtrar dados
    if lider_selecionado == 'TODOS':
        df_hoje_filtrado = df_hoje_com_lider.copy()
    else:
        df_hoje_filtrado = df_hoje_com_lider[df_hoje_com_lider['Lider'] == lider_selecionado].copy(
        )

    if tem_dados_ontem and not df_ontem_com_lider.empty:
        if lider_selecionado == 'TODOS':
            df_ontem_filtrado = df_ontem_com_lider.copy()
        else:
            df_ontem_filtrado = df_ontem_com_lider[df_ontem_com_lider['Lider'] == lider_selecionado].copy(
            )
    else:
        df_ontem_filtrado = pd.DataFrame()

    # Mostrar informações do filtro
    st.markdown(
        f'<div class="info-box">📊 Dados de HOJE ({lider_selecionado}): {len(df_hoje_filtrado):,} registros</div>', unsafe_allow_html=True)

    if tem_dados_ontem:
        st.markdown(
            f'<div class="info-box">📊 Dados de ONTEM ({lider_selecionado}): {len(df_ontem_filtrado):,} registros</div>', unsafe_allow_html=True)

    # Mostrar polos do líder
    if lider_selecionado != 'TODOS' and not df_hoje_filtrado.empty:
        polos = df_hoje_filtrado['Provider'].unique()
        st.markdown(
            f'<div class="info-box">🏢 <strong>Polos:</strong> {", ".join(polos)}</div>', unsafe_allow_html=True)

    # Calcular métricas
    metricas_hoje = calcular_metricas_safra(df_hoje_filtrado)

    if tem_dados_ontem and not df_ontem_filtrado.empty:
        metricas_ontem = calcular_metricas_safra(df_ontem_filtrado)
        deltas = calcular_deltas(metricas_hoje, metricas_ontem)
        mostrar_comparacao = True
    else:
        metricas_ontem = {'total_em_aberto': 0,
                          'em_atraso': 0, 'perc_atraso': 0.0, 'sla_medio': 0.0}
        deltas = {'delta_total': 0, 'delta_atraso': 0,
                  'delta_perc_atraso': 0.0, 'delta_sla_medio': 0.0}
        mostrar_comparacao = False

    # Métricas principais com lógica de cores correta
    st.markdown('<h3 class="titulo-secao">📈 Métricas Principais</h3>',
                unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if mostrar_comparacao:
            delta_texto = f"{deltas['delta_total']:+,}"
            # Lógica correta: queda em aberto = verde (normal), aumento = vermelho (inverse)
            delta_color = "normal" if deltas['delta_total'] <= 0 else "inverse"
            st.metric(
                "Total em Aberto", f"{metricas_hoje['total_em_aberto']:,}", delta=delta_texto, delta_color=delta_color)
        else:
            st.metric("Total em Aberto",
                      f"{metricas_hoje['total_em_aberto']:,}")

    with col2:
        if mostrar_comparacao:
            delta_texto = f"{deltas['delta_atraso']:+,}"
            # Lógica correta: queda em atraso = verde (normal), aumento = vermelho (inverse)
            delta_color = "normal" if deltas['delta_atraso'] <= 0 else "inverse"
            st.metric(
                "Em Atraso", f"{metricas_hoje['em_atraso']:,}", delta=delta_texto, delta_color=delta_color)
        else:
            st.metric("Em Atraso", f"{metricas_hoje['em_atraso']:,}")

    with col3:
        if mostrar_comparacao:
            delta_texto = f"{deltas['delta_perc_atraso']:+.1f}%"
            # Lógica correta: queda no % = verde (normal), aumento = vermelho (inverse)
            delta_color = "normal" if deltas['delta_perc_atraso'] <= 0 else "inverse"
            st.metric(
                "% em Atraso", f"{metricas_hoje['perc_atraso']:.1f}%", delta=delta_texto, delta_color=delta_color)
        else:
            st.metric("% em Atraso", f"{metricas_hoje['perc_atraso']:.1f}%")

    with col4:
        if mostrar_comparacao:
            delta_texto = f"{deltas['delta_sla_medio']:+.1f}"
            # Lógica correta: queda no SLA = verde (normal), aumento = vermelho (inverse)
            delta_color = "normal" if deltas['delta_sla_medio'] <= 0 else "inverse"
            st.metric("SLA Médio", f"{metricas_hoje['sla_medio']:.1f} dias",
                      delta=f"{delta_texto} dias", delta_color=delta_color)
        else:
            st.metric("SLA Médio", f"{metricas_hoje['sla_medio']:.1f} dias")

    # Seção de comparação detalhada
    if mostrar_comparacao:
        st.markdown(
            '<h3 class="titulo-secao">📊 Evolução: Hoje vs Ontem</h3>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])

        with col1:
            # Tabela de comparação
            st.markdown("""
            <div class="comparison-box">
                <div class="comparison-title">📈 Resumo Comparativo</div>
            """, unsafe_allow_html=True)

            # Total em Aberto
            delta_cor = "positive" if deltas['delta_total'] <= 0 else "negative"
            st.markdown(f"""
                <div class="comparison-item">
                    <span>Total em Aberto:</span>
                    <span>{metricas_hoje['total_em_aberto']:,} (hoje) vs {metricas_ontem['total_em_aberto']:,} (ontem)</span>
                    <span class="delta-{delta_cor}">{deltas['delta_total']:+,}</span>
                </div>
            """, unsafe_allow_html=True)

            # Em Atraso
            delta_cor = "positive" if deltas['delta_atraso'] <= 0 else "negative"
            st.markdown(f"""
                <div class="comparison-item">
                    <span>Em Atraso:</span>
                    <span>{metricas_hoje['em_atraso']:,} (hoje) vs {metricas_ontem['em_atraso']:,} (ontem)</span>
                    <span class="delta-{delta_cor}">{deltas['delta_atraso']:+,}</span>
                </div>
            """, unsafe_allow_html=True)

            # % em Atraso
            delta_cor = "positive" if deltas['delta_perc_atraso'] <= 0 else "negative"
            st.markdown(f"""
                <div class="comparison-item">
                    <span>% em Atraso:</span>
                    <span>{metricas_hoje['perc_atraso']:.1f}% (hoje) vs {metricas_ontem['perc_atraso']:.1f}% (ontem)</span>
                    <span class="delta-{delta_cor}">{deltas['delta_perc_atraso']:+.1f}%</span>
                </div>
            """, unsafe_allow_html=True)

            # SLA Médio
            delta_cor = "positive" if deltas['delta_sla_medio'] <= 0 else "negative"
            st.markdown(f"""
                <div class="comparison-item">
                    <span>SLA Médio:</span>
                    <span>{metricas_hoje['sla_medio']:.1f} (hoje) vs {metricas_ontem['sla_medio']:.1f} (ontem)</span>
                    <span class="delta-{delta_cor}">{deltas['delta_sla_medio']:+.1f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Gráfico de comparação responsivo
            fig_comparacao, config_comparacao = criar_grafico_comparacao(
                metricas_hoje, metricas_ontem)
            if fig_comparacao:
                st.plotly_chart(
                    fig_comparacao, use_container_width=True, config=config_comparacao)

    # Ranking vertical
    if metricas_hoje['em_atraso'] > 0:
        st.markdown(
            '<h3 class="titulo-secao">🏆 Ranking: Polos com Mais Ordens em Atraso (Hoje)</h3>', unsafe_allow_html=True)

        if 'SLA Cliente' in df_hoje_filtrado.columns:
            sla_validos = pd.to_numeric(
                df_hoje_filtrado['SLA Cliente'], errors='coerce')
            em_atraso_df = df_hoje_filtrado[sla_validos >= 2]

            if not em_atraso_df.empty:
                ranking = em_atraso_df['Provider'].value_counts()
                fig, config = criar_ranking_vertical(ranking)

                if fig:
                    st.plotly_chart(
                        fig, use_container_width=True, config=config)

    # Análise do Último Tracking das Ordens em Aberto
    if metricas_hoje['total_em_aberto'] > 0:
        st.markdown(
            '<h3 class="titulo-secao">📋 Status das Ordens em Aberto (Último Tracking)</h3>', unsafe_allow_html=True)

        df_em_aberto = df_hoje_filtrado.copy()

        if 'Último Tracking' in df_em_aberto.columns and not df_em_aberto.empty:
            fig_pizza, fig_barras, config = criar_graficos_ultimo_tracking(
                df_em_aberto)

            if fig_pizza and fig_barras:
                col1, col2 = st.columns(2)

                with col1:
                    st.plotly_chart(
                        fig_pizza, use_container_width=True, config=config)

                with col2:
                    st.plotly_chart(
                        fig_barras, use_container_width=True, config=config)
            else:
                mostrar_mensagem_status(
                    'info', "Dados de 'Último Tracking' não disponíveis ou insuficientes")
        else:
            mostrar_mensagem_status(
                'info', "Coluna 'Último Tracking' não encontrada nos dados")

    # Dados detalhados
    st.markdown('<h3 class="titulo-secao">📋 Dados Detalhados (Hoje)</h3>',
                unsafe_allow_html=True)

    if not df_hoje_filtrado.empty:
        col1, col2 = st.columns([3, 1])

        with col2:
            max_registros = st.selectbox("Máximo de registros", [
                50, 100, 200, 500, 1000], index=1)

        # Usar height para melhor experiência
        st.dataframe(df_hoje_filtrado.head(max_registros),
                     use_container_width=True, height=400)
        st.caption(
            f"Mostrando {min(max_registros, len(df_hoje_filtrado)):,} de {len(df_hoje_filtrado):,} registros")

    # Exportação
    st.markdown('<h3 class="titulo-secao">📥 Exportação</h3>',
                unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("📊 Gerar Excel (Hoje)"):
            try:
                # Preparar dados para Excel (sem timezone)
                df_export = preparar_dataframe_para_excel(df_hoje_filtrado)
                output = io.BytesIO()
                df_export.to_excel(output, index=False)

                nome_arquivo_sanitizado = sanitizar_nome_arquivo(
                    lider_selecionado)
                nome_arquivo = f"safra_hoje_{nome_arquivo_sanitizado}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx"

                st.download_button(
                    "⬇️ Download Excel (Hoje)",
                    data=output.getvalue(),
                    file_name=nome_arquivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                mostrar_mensagem_status('success', "Excel gerado com sucesso!")

            except Exception as e:
                mostrar_mensagem_status('error', f"Erro ao gerar Excel: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # FORMULÁRIO DE JUSTIFICATIVAS COM AZURE LOGIC APPS (ATUALIZADO)
    # ═══════════════════════════════════════════════════════════════════

    st.markdown('<h3 class="titulo-secao">📝 Formulário de Justificativas</h3>',
                unsafe_allow_html=True)

    # Só mostrar formulário se um líder específico estiver selecionado
    if lider_selecionado != 'TODOS':

        semana_atual, periodo_atual = calcular_semana_ano()

        st.markdown(f"""
        <div class="formulario-section">
            <h4>📋 Justificativas para {lider_selecionado}</h4>
            <p><strong>📅 Data:</strong> {datetime.now().strftime('%d/%m/%Y')} | <strong>📊 Semana:</strong> {semana_atual} ({periodo_atual})</p>
            <p><strong>🔗 Integração:</strong> Azure Logic Apps (SharePoint + Teams)</p>
        </div>
        """, unsafe_allow_html=True)

        # Obter polos do líder
        polos_lider = df_hoje_filtrado['Provider'].unique()

        # Lista para armazenar dados do formulário
        polos_formulario = []

        for polo in polos_lider:
            # Calcular métricas do polo
            df_polo = df_hoje_filtrado[df_hoje_filtrado['Provider'] == polo]
            metricas_polo = calcular_metricas_safra(df_polo)

            # Determinar classe do card
            if metricas_polo['perc_atraso'] >= 30:  # Critico
                card_class = "polo-card-critico"
                status_emoji = "🔴"
            elif metricas_polo['perc_atraso'] >= 20:  # Atenção
                card_class = "polo-card-atencao"
                status_emoji = "🟡"
            else:  # OK
                card_class = "polo-card-ok"
                status_emoji = "🟢"

            # Card do polo
            st.markdown(f"""
            <div class="{card_class}">
                <h5>{status_emoji} {polo}</h5>
                <p>📊 <strong>Ordens em Aberto:</strong> {metricas_polo['total_em_aberto']}</p>
                <p>⚠️ <strong>Em Atraso (≥2 dias):</strong> {metricas_polo['em_atraso']} ({metricas_polo['perc_atraso']:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)

            # Campos de justificativa
            # Adiciona a classe 'campo-obrigatorio' se for crítico
            is_obrigatorio = metricas_polo['perc_atraso'] >= 20
            label_justificativa = f"📝 Justificativa para {polo}:"
            if is_obrigatorio:
                label_justificativa = f"<span class='campo-obrigatorio'>{label_justificativa}</span>"

            justificativa = st.text_area(
                label_justificativa,
                key=f"just_{polo}",
                height=100,
                placeholder="Descreva os motivos dos atrasos..." if metricas_polo[
                    'perc_atraso'] > 0 else "Polo sem atrasos",
                help="Campo obrigatório se o percentual de atraso for 20% ou mais." if is_obrigatorio else ""
            )

            acao_corretiva = st.text_area(
                f"🔧 Ação Corretiva para {polo}:",
                key=f"acao_{polo}",
                height=100,
                placeholder="(Opcional) Descreva ações planejadas ou deixe em branco"
            )

            # Armazenar dados
            polos_formulario.append({
                'nome': polo,
                'ordens_em_aberto': metricas_polo['total_em_aberto'],
                'ordens_em_atraso': metricas_polo['em_atraso'],
                'perc_atraso': metricas_polo['perc_atraso'],
                'justificativa': justificativa,
                'acao_corretiva': acao_corretiva
            })

        # Observações gerais
        st.markdown("**💬 Observações Gerais:**")
        observacoes = st.text_area(
            "Comentários adicionais:",
            height=100,
            placeholder="Observações sobre a semana..."
        )

        # Botão de envio para Logic Apps
        if st.button("🚀 Enviar para Azure Logic Apps", type="primary"):

            # Validar campos obrigatórios (apenas justificativa para polos críticos)
            erros = []
            for polo in polos_formulario:
                if polo['perc_atraso'] >= 20:  # Se o polo tem 20% ou mais de atraso
                    if not polo['justificativa'].strip():
                        erros.append(
                            f"Justificativa obrigatória para {polo['nome']} (% atraso ≥ 20%)")
                    # Ação Corretiva NÃO é obrigatória

            if erros:
                for erro in erros:
                    mostrar_mensagem_status('error', erro)
            else:
                # Preparar dados para envio
                dados_formulario = {
                    'data': datetime.now().strftime('%d/%m/%Y'),
                    'semana': f"Semana {semana_atual} ({periodo_atual})",
                    'lider': lider_selecionado,
                    'polos': polos_formulario,
                    'observacoes': observacoes
                }

                # Enviar para Logic Apps
                with st.spinner("🚀 Enviando para Azure Logic Apps..."):
                    sucesso, mensagem = enviar_para_power_automate(
                        dados_formulario)

                    if sucesso:
                        st.markdown(f"""
                        <div class="webhook-success">
                            <h4>✅ Justificativas Enviadas com Sucesso!</h4>
                            <p>{mensagem}</p>
                            <p><strong>🔗 Processamento:</strong> Azure Logic Apps está processando os dados</p>
                            <p><strong>📧 Notificação:</strong> Você receberá um card no Teams com o link para o Excel no SharePoint</p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.balloons()

                        # Mostrar resumo
                        total_polos = len(polos_formulario)
                        polos_criticos = len(
                            [p for p in polos_formulario if p['perc_atraso'] >= 20])

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total de Polos", total_polos)
                        with col2:
                            st.metric("Polos Críticos", polos_criticos)
                        with col3:
                            st.metric("Status", "✅ Enviado")

                        # Informações adicionais
                        st.markdown("### 📋 Próximos Passos")
                        st.info("""
                        1. **Azure Logic Apps** processará os dados automaticamente.
                        2. O arquivo Excel será salvo no **SharePoint**.
                        3. Um **card no Teams** será enviado com o link direto para o arquivo.
                        """)

                        # Obter o link do Excel salvo no SharePoint
                        # Este é um exemplo de como você pode obter o link do arquivo
                        # Você precisará de uma lógica para obter o caminho do arquivo no SharePoint
                        # e gerar um link direto.
                        # Por enquanto, vamos apenas mostrar uma mensagem de sucesso.
                        # Para obter o link real, você precisaria de uma integração com o SharePoint
                        # ou uma API que retorne o link do arquivo.
                        # Por exemplo:
                        # excel_url = "https://universoonline.sharepoint.com/sites/SafraDashboard/Shared%20Documents/Relatorio_Diario.xlsx"
                        # adaptive_card_payload = montar_adaptive_card_teams(dados_formulario, excel_url)
                        # response = requests.post(webhook_teams_url, json=adaptive_card_payload)
                        # print(response.status_code, response.text)

                    else:
                        mostrar_mensagem_status('error', mensagem)

                        # Oferecer download como backup
                        st.markdown("### 💾 Backup - Download Manual")
                        st.warning(
                            "Como o envio falhou, você pode baixar os dados manualmente:")

                        try:
                            # Gerar Excel de backup
                            excel_buffer = io.BytesIO()
                            linhas_excel = []
                            for polo in dados_formulario['polos']:
                                linhas_excel.append({
                                    'Data': dados_formulario['data'],
                                    'Semana': dados_formulario['semana'],
                                    'Líder': dados_formulario['lider'],
                                    'Polo': polo['nome'],
                                    'Ordens_Em_Aberto': polo['ordens_em_aberto'],
                                    'Ordens_Em_Atraso': polo['ordens_em_atraso'],
                                    'Perc_Atraso': polo['perc_atraso'],
                                    'Justificativa': polo['justificativa'],
                                    'Acao_Corretiva': polo['acao_corretiva'],
                                    'Observacoes': dados_formulario['observacoes']
                                })

                            df_backup = pd.DataFrame(linhas_excel)
                            df_backup.to_excel(excel_buffer, index=False)

                            nome_arquivo_backup = f"Backup_Justificativas_{sanitizar_nome_arquivo(dados_formulario['lider'])}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

                            st.download_button(
                                "📥 Download Backup Excel",
                                data=excel_buffer.getvalue(),
                                file_name=nome_arquivo_backup,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                        except Exception as e:
                            st.error(f"Erro ao gerar backup: {e}")

    else:
        st.markdown("""
        <div class="info-box">
            <h4>💡 Selecione um Líder Específico</h4>
            <p>Para preencher justificativas, selecione um líder específico na lista acima.</p>
            <p><strong>🔗 Integração:</strong> Azure Logic Apps Webhook configurado e pronto!</p>
        </div>
        """, unsafe_allow_html=True)

else:
    mostrar_mensagem_status('error', "Nenhum líder foi associado aos dados!")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: rgb(51, 51, 51); opacity: 0.7; margin-top: 2rem;">'
    'Dashboard Safra • Azure Logic Apps Integration • Última atualização: Julho/2025'
    '</div>',
    unsafe_allow_html=True
)
