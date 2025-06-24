import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configurar página
st.set_page_config(
    page_title="📊 Dashboard Report Safra ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS melhorado com responsividade
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFD700 0%, #1E90FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.5rem;
        }
    }
    
    .metric-card {
        background: linear-gradient(135deg, #FFF8DC 0%, #E6F3FF 100%);
        padding: 1.5rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.2);
        border: 2px solid rgba(255, 215, 0, 0.3);
        text-align: center;
        transition: transform 0.3s ease;
        min-height: 120px;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(31, 38, 135, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0.5rem 0;
        font-family: 'Inter', sans-serif;
    }
    
    @media (max-width: 768px) {
        .metric-value {
            font-size: 2rem;
        }
    }
    
    .metric-label {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2C5282;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
    }
    
    .metric-delta-red {
        color: #DC2626;
        font-size: 1rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }
    
    .metric-delta-green {
        color: #059669;
        font-size: 1rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }
    
    .section-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E3A8A;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #FFD700;
        font-family: 'Inter', sans-serif;
    }
    
    .ranking-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #DC2626;
        margin: 1.5rem 0;
        font-family: 'Inter', sans-serif;
    }
    
    .highlight-red {
        color: #DC2626;
        font-weight: 800;
        font-size: 1.1rem;
    }
    
    .highlight-green {
        color: #059669;
        font-weight: 800;
        font-size: 1.1rem;
    }
    
    .search-box {
        margin-bottom: 1rem;
    }
    
    .polo-list {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        background: white;
    }
    
    .polo-item {
        padding: 0.5rem;
        border-bottom: 1px solid #f1f5f9;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .polo-item:hover {
        background-color: #f8fafc;
    }
    
    .container-responsive {
        max-width: 100%;
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)

# Paleta de cores
CORES_STATUS = {
    'Em Aberto': '#DC2626',
    'Finalizado com Sucesso': '#059669',
    'Finalizado com Insucesso': '#D97706',
    'Pendente': '#2563EB',
    'Em Análise': '#7C3AED',
    'Aguardando': '#F59E0B',
    'Cancelado': '#6B7280'
}

CORES_POLOS = ['#FFD700', '#1E90FF', '#87CEEB',
               '#F0E68C', '#4169E1', '#FFA500', '#20B2AA', '#DDA0DD']


@st.cache_data
def carregar_dados():
    """Carrega os dados processados pela ETL com debug"""
    try:
        caminho_dados = r"C:\Users\sbahia\OneDrive - UNIVERSO ONLINE S.A\Área de Trabalho\Ambiente PY\logins\Projeto Safra\data\Safra_Gerencial_Téc.Prop_17.06.xlsx"

        df = pd.read_excel(caminho_dados, sheet_name='Consolidado')
        st.sidebar.write(f"🔍 **Registros carregados:** {len(df):,}")

        df = df.dropna(subset=['Ordem PagBank'])
        st.sidebar.write(f"🔍 **Após filtro:** {len(df):,}")

        # Converter tipos de dados
        if 'Criação da Ordem' in df.columns:
            df['Criação da Ordem'] = pd.to_datetime(
                df['Criação da Ordem'], errors='coerce')
        if 'Data_Status' in df.columns:
            df['Data_Status'] = pd.to_datetime(
                df['Data_Status'], errors='coerce')
        if 'SLA Cliente' in df.columns:
            df['SLA Cliente'] = pd.to_numeric(
                df['SLA Cliente'], errors='coerce')
        if 'Dias_Em_Aberto' in df.columns:
            df['Dias_Em_Aberto'] = pd.to_numeric(
                df['Dias_Em_Aberto'], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


def calcular_comparacoes_semanais(df):
    """Calcula comparações semanais"""
    hoje = datetime.now().date()
    inicio_semana_atual = hoje - timedelta(days=hoje.weekday())
    inicio_semana_passada = inicio_semana_atual - timedelta(days=7)

    # Filtrar dados por semana
    df_semana_atual = df[df['Data_Status'].dt.date >=
                         inicio_semana_atual] if 'Data_Status' in df.columns else pd.DataFrame()
    df_semana_passada = df[
        (df['Data_Status'].dt.date >= inicio_semana_passada) &
        (df['Data_Status'].dt.date < inicio_semana_atual)
    ] if 'Data_Status' in df.columns else pd.DataFrame()

    # Calcular métricas
    total_atual = len(df_semana_atual)
    total_passada = len(df_semana_passada)

    abertos_atual = len(df_semana_atual[df_semana_atual['Status_Tratativa']
                        == 'Em Aberto']) if 'Status_Tratativa' in df_semana_atual.columns else 0
    abertos_passada = len(df_semana_passada[df_semana_passada['Status_Tratativa']
                          == 'Em Aberto']) if 'Status_Tratativa' in df_semana_passada.columns else 0

    return {
        'total_atual': total_atual,
        'total_passada': total_passada,
        'delta_total': total_atual - total_passada,
        'abertos_atual': abertos_atual,
        'abertos_passada': abertos_passada,
        'delta_abertos': abertos_atual - abertos_passada
    }


def criar_filtros_avancados(df):
    """Cria filtros avançados na sidebar SEM filtro automático de data"""
    st.sidebar.markdown("## 🎛️ **Filtros Avançados**")

    df_filtrado = df.copy()

    # Filtro de Período (SEM valor padrão automático)
    st.sidebar.markdown("### 📅 **Período**")
    if 'Data_Status' in df.columns and not df['Data_Status'].isna().all():
        data_min = df['Data_Status'].min().date()
        data_max = df['Data_Status'].max().date()

        # CORREÇÃO: Checkbox para ativar filtro de data
        usar_filtro_data = st.sidebar.checkbox(
            "Filtrar por período", value=False)

        if usar_filtro_data:
            periodo = st.sidebar.date_input(
                "**Selecione o período**",
                value=[data_min, data_max],
                min_value=data_min,
                max_value=data_max,
                key="periodo_filtro"
            )

            if len(periodo) == 2:
                df_filtrado = df_filtrado[
                    (df_filtrado['Data_Status'].dt.date >= periodo[0]) &
                    (df_filtrado['Data_Status'].dt.date <= periodo[1])
                ]

    # Filtro de Status Tratativa
    st.sidebar.markdown("### 📋 **Status Tratativa**")
    if 'Status_Tratativa' in df_filtrado.columns:
        status_options = [
            'Todos'] + sorted(df_filtrado['Status_Tratativa'].dropna().unique().tolist())
        status_selecionado = st.sidebar.selectbox(
            "**Status**", status_options, key="status_filtro")

        if status_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Status_Tratativa']
                                      == status_selecionado]

    # Filtro de Polos (Provider)
    st.sidebar.markdown("### 🏢 **Polos (Providers)**")
    if 'Provider' in df_filtrado.columns:
        provider_options = [
            'Todos'] + sorted(df_filtrado['Provider'].dropna().unique().tolist())
        provider_selecionado = st.sidebar.selectbox(
            "**Polo**", provider_options, key="provider_filtro")

        if provider_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Provider']
                                      == provider_selecionado]

    # Filtro de Região
    st.sidebar.markdown("### 🗺️ **Região**")
    if 'Região' in df_filtrado.columns:
        regiao_options = ['Todas'] + \
            sorted(df_filtrado['Região'].dropna().unique().tolist())
        regiao_selecionada = st.sidebar.selectbox(
            "**Região**", regiao_options, key="regiao_filtro")

        if regiao_selecionada != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['Região']
                                      == regiao_selecionada]

    return df_filtrado


def criar_metricas_principais(df, comp_semanal):
    """Cria métricas principais com comparações semanais CORRIGIDAS"""
    st.markdown('<h2 class="section-header">📊 Métricas Principais</h2>',
                unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_pedidos = len(df)
        delta_semanal = comp_semanal['delta_total']

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📦 Total de Pedidos</div>
            <div class="metric-value">{total_pedidos:,}</div>
            <div class="metric-delta-{'green' if delta_semanal >= 0 else 'red'}">
                {delta_semanal:+,} vs semana passada
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        abertos = len(df[df['Status_Tratativa'] == 'Em Aberto']
                      ) if 'Status_Tratativa' in df.columns else 0
        perc_abertos = (abertos / total_pedidos *
                        100) if total_pedidos > 0 else 0
        delta_abertos = comp_semanal['delta_abertos']

        # CORREÇÃO: Para ordens em aberto, aumento é sempre ruim (vermelho)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🔴 Ordens em Aberto</div>
            <div class="metric-value highlight-red">{abertos:,}</div>
            <div class="highlight-red">{perc_abertos:.1f}% do total</div>
            <div class="metric-delta-red">
                {delta_abertos:+,} vs semana passada
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        if 'SLA Cliente' in df.columns:
            sla_medio = df['SLA Cliente'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">⏱️ SLA Médio</div>
                <div class="metric-value">{sla_medio:.1f}d</div>
            </div>
            """.format(sla_medio if pd.notna(sla_medio) else 0), unsafe_allow_html=True)

    with col4:
        if 'Provider' in df.columns:
            polos_ativos = df['Provider'].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🏢 Polos Ativos</div>
                <div class="metric-value">{polos_ativos}</div>
            </div>
            """, unsafe_allow_html=True)


def criar_tabela_detalhada(df_filtrado):
    """Cria tabela detalhada que reflete o consolidado com filtros aplicados"""
    st.markdown('<h2 class="section-header">📋 Tabela Detalhada - Dados Consolidados</h2>',
                unsafe_allow_html=True)

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros aplicados.")
        return

    # Informações sobre os filtros aplicados
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("**Total de Registros**", f"{len(df_filtrado):,}")

    with col2:
        if 'Status_Tratativa' in df_filtrado.columns:
            em_aberto = len(
                df_filtrado[df_filtrado['Status_Tratativa'] == 'Em Aberto'])
            st.metric("**Em Aberto**", f"{em_aberto:,}")

    with col3:
        if 'Provider' in df_filtrado.columns:
            polos_filtrados = df_filtrado['Provider'].nunique()
            st.metric("**Polos Únicos**", polos_filtrados)

    with col4:
        if 'Status_Tratativa' in df_filtrado.columns:
            status_unicos = df_filtrado['Status_Tratativa'].nunique()
            st.metric("**Status Únicos**", status_unicos)

    # Controles da tabela
    st.markdown("### ⚙️ **Controles da Tabela**")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        linhas_por_pagina = st.selectbox(
            "**Linhas por página**",
            [25, 50, 100, 200, 500],
            index=2,
            key="linhas_tabela"
        )

    with col2:
        if not df_filtrado.empty:
            colunas_ordenacao = [
                'Ordem PagBank'] + [col for col in df_filtrado.columns if col != 'Ordem PagBank']
            ordenar_por = st.selectbox(
                "**Ordenar por**",
                colunas_ordenacao,
                index=0,
                key="ordenar_tabela"
            )
        else:
            ordenar_por = None

    with col3:
        ordem_desc = st.checkbox(
            "**Ordem decrescente**", value=False, key="ordem_desc_tabela")

    with col4:
        # Filtro rápido adicional por Status
        if 'Status_Tratativa' in df_filtrado.columns:
            status_rapido = st.selectbox(
                "**Filtro rápido Status**",
                ['Todos'] +
                sorted(
                    df_filtrado['Status_Tratativa'].dropna().unique().tolist()),
                key="status_rapido_tabela"
            )
        else:
            status_rapido = 'Todos'

    # Aplicar filtros adicionais
    df_tabela = df_filtrado.copy()

    if status_rapido != 'Todos':
        df_tabela = df_tabela[df_tabela['Status_Tratativa'] == status_rapido]

    if ordenar_por and not df_tabela.empty:
        df_tabela = df_tabela.sort_values(
            by=ordenar_por, ascending=not ordem_desc)

    # Mostrar resumo dos filtros aplicados
    st.markdown("### 🔍 **Filtros Ativos**")
    filtros_ativos = []

    # Verificar quais filtros estão ativos
    if len(df_tabela) != len(df_filtrado):
        filtros_ativos.append(f"Status rápido: {status_rapido}")

    if filtros_ativos:
        st.info(f"Filtros aplicados: {', '.join(filtros_ativos)}")
    else:
        st.info("Mostrando todos os dados (conforme filtros da sidebar)")

    # Colunas principais para exibir (as mais importantes primeiro)
    colunas_principais = [
        'Ordem PagBank', 'Status_Tratativa', 'Provider', 'Status da Ordem',
        'SLA Cliente', 'Dias_Em_Aberto', 'Criação da Ordem', 'Data_Status',
        'Região', 'Estado', 'Cidade', 'Feedback', 'Causa_Raiz', 'Proxima_Acao'
    ]

    # Filtrar apenas colunas que existem
    colunas_existentes = [
        col for col in colunas_principais if col in df_tabela.columns]

    # Adicionar outras colunas que não estão na lista principal
    outras_colunas = [
        col for col in df_tabela.columns if col not in colunas_existentes]
    colunas_finais = colunas_existentes + outras_colunas

    # Reordenar DataFrame
    df_display = df_tabela[colunas_finais]

    # Mostrar tabela
    st.markdown("### 📊 **Dados Detalhados**")

    # Destacar linhas "Em Aberto" se possível
    if not df_display.empty:
        st.dataframe(
            df_display.head(linhas_por_pagina),
            use_container_width=True,
            hide_index=True,
            height=500
        )

        # Informação sobre paginação
        total_linhas = len(df_display)
        if total_linhas > linhas_por_pagina:
            st.info(
                f"Mostrando {linhas_por_pagina} de {total_linhas:,} registros. Use os controles acima para ver mais.")

    # Seção de Download
    st.markdown("### 💾 **Download dos Dados Filtrados**")

    col1, col2, col3 = st.columns(3)

    with col1:
        # CSV completo dos dados filtrados
        csv_completo = df_display.to_csv(index=False, encoding='utf-8-sig')

        # Nome do arquivo baseado nos filtros
        nome_arquivo = "safra_dados"
        if status_rapido != 'Todos':
            nome_arquivo += f"_{status_rapido.replace(' ', '_')}"
        nome_arquivo += f"_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

        st.download_button(
            label="📥 **Download CSV Completo**",
            data=csv_completo,
            file_name=nome_arquivo,
            mime="text/csv",
            help=f"Baixar {len(df_display):,} registros filtrados"
        )

    with col2:
        # CSV apenas ordens em aberto (se existir)
        if 'Status_Tratativa' in df_display.columns:
            df_abertos = df_display[df_display['Status_Tratativa']
                                    == 'Em Aberto']
            if not df_abertos.empty:
                csv_abertos = df_abertos.to_csv(
                    index=False, encoding='utf-8-sig')
                nome_arquivo_abertos = f"safra_em_aberto_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

                st.download_button(
                    label="🔴 **Download Apenas Em Aberto**",
                    data=csv_abertos,
                    file_name=nome_arquivo_abertos,
                    mime="text/csv",
                    help=f"Baixar {len(df_abertos):,} ordens em aberto"
                )
            else:
                st.info("Nenhuma ordem em aberto nos dados filtrados")

    with col3:
        # Excel com múltiplas abas
        try:
            from io import BytesIO
            output = BytesIO()

            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Aba principal com todos os dados filtrados
                df_display.to_excel(
                    writer, sheet_name='Dados_Filtrados', index=False)

                # Abas por status (se houver dados suficientes)
                if 'Status_Tratativa' in df_display.columns and len(df_display) > 0:
                    for status in df_display['Status_Tratativa'].unique():
                        if pd.notna(status):
                            df_status = df_display[df_display['Status_Tratativa'] == status]
                            if len(df_status) > 0:
                                sheet_name = status.replace(
                                    ' ', '_')[:30]  # Limitar nome da aba
                                df_status.to_excel(
                                    writer, sheet_name=sheet_name, index=False)

            nome_arquivo_excel = f"safra_relatorio_detalhado_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

            st.download_button(
                label="📊 **Download Excel Detalhado**",
                data=output.getvalue(),
                file_name=nome_arquivo_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help=f"Excel com {len(df_display):,} registros em múltiplas abas"
            )
        except Exception as e:
            st.error(f"Erro ao gerar Excel: {e}")

    # Resumo final
    st.markdown("### 📈 **Resumo dos Dados Exibidos**")

    if 'Status_Tratativa' in df_display.columns:
        resumo_status = df_display['Status_Tratativa'].value_counts(
        ).reset_index()
        resumo_status.columns = ['Status', 'Quantidade']
        resumo_status['Percentual'] = (
            resumo_status['Quantidade'] / len(df_display) * 100).round(1)

        st.dataframe(
            resumo_status,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": "Status Tratativa",
                "Quantidade": "Qtd",
                "Percentual": "% do Total"
            }
        )


def criar_relatorio_gerencial_polos(df):
    """Cria relatório gerencial por polos com busca"""
    st.markdown('<h2 class="section-header">📋 Relatório Gerencial por Polos</h2>',
                unsafe_allow_html=True)

    if 'Provider' not in df.columns:
        st.info("Dados de Provider não disponíveis")
        return

    # Campo de busca
    busca = st.text_input("🔍 **Buscar Polo:**",
                          placeholder="Digite o nome do polo...")

    # Calcular estatísticas por polo
    stats_polos = df.groupby('Provider').agg({
        'Ordem PagBank': 'count',
        'SLA Cliente': 'mean',
        'Dias_Em_Aberto': 'mean'
    }).reset_index()

    stats_polos.columns = ['Polo', 'Total_Pedidos',
                           'SLA_Medio', 'Dias_Medio_Aberto']

    # Adicionar ordens em aberto
    if 'Status_Tratativa' in df.columns:
        abertos_por_polo = df[df['Status_Tratativa'] == 'Em Aberto'].groupby(
            'Provider').size().reset_index(name='Ordens_Aberto')
        stats_polos = stats_polos.merge(
            abertos_por_polo, left_on='Polo', right_on='Provider', how='left').fillna(0)
        stats_polos = stats_polos.drop('Provider', axis=1)
        stats_polos['Perc_Aberto'] = (
            stats_polos['Ordens_Aberto'] / stats_polos['Total_Pedidos'] * 100).round(1)

    # Aplicar filtro de busca
    if busca:
        stats_polos = stats_polos[stats_polos['Polo'].str.contains(
            busca, case=False, na=False)]

    # Ordenar por total de pedidos
    stats_polos = stats_polos.sort_values('Total_Pedidos', ascending=False)

    # Formatar valores
    if 'SLA_Medio' in stats_polos.columns:
        stats_polos['SLA_Medio'] = stats_polos['SLA_Medio'].round(1)
    if 'Dias_Medio_Aberto' in stats_polos.columns:
        stats_polos['Dias_Medio_Aberto'] = stats_polos['Dias_Medio_Aberto'].round(
            1)

    # Mostrar tabela
    st.dataframe(
        stats_polos,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Polo": "🏢 Polo",
            "Total_Pedidos": "📦 Total",
            "Ordens_Aberto": "🔴 Em Aberto",
            "Perc_Aberto": "% Aberto",
            "SLA_Medio": "⏱️ SLA Médio",
            "Dias_Medio_Aberto": "📅 Dias Médio"
        }
    )


def criar_ranking_polos_abertos(df):
    """Cria ranking de polos por ordens em aberto - CORRIGIDO"""
    st.markdown('<h2 class="ranking-header">🔴 Ranking: Polos com Mais Ordens em Aberto</h2>',
                unsafe_allow_html=True)

    if 'Provider' not in df.columns or 'Status_Tratativa' not in df.columns:
        st.info("Dados de Provider ou Status_Tratativa não disponíveis")
        return

    try:
        # Calcular ranking
        abertos_por_polo = df[df['Status_Tratativa'] == 'Em Aberto'].groupby(
            'Provider').size().reset_index(name='Ordens_Aberto')
        total_por_polo = df.groupby(
            'Provider').size().reset_index(name='Total_Ordens')

        ranking = total_por_polo.merge(
            abertos_por_polo, on='Provider', how='left').fillna(0)
        ranking['Percentual_Aberto'] = (
            ranking['Ordens_Aberto'] / ranking['Total_Ordens'] * 100).round(1)
        ranking = ranking.sort_values(
            'Ordens_Aberto', ascending=False).head(15)

        # Gráfico de barras horizontal CORRIGIDO
        fig_ranking = go.Figure()

        # Cores degradê
        colors = ['#DC2626' if i < 3 else '#F59E0B' if i <
                  6 else '#2563EB' for i in range(len(ranking))]

        fig_ranking.add_trace(go.Bar(
            y=ranking['Provider'],
            x=ranking['Ordens_Aberto'],
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(color='white', width=2)
            ),
            text=[f'{int(val)} ({perc:.1f}%)' for val, perc in zip(
                ranking['Ordens_Aberto'], ranking['Percentual_Aberto'])],
            textposition='outside',
            textfont=dict(size=12, color='#1E3A8A', family='Inter'),
            hovertemplate='<b>%{y}</b><br>Ordens em Aberto: %{x}<br>% do Total: %{customdata:.1f}%<extra></extra>',
            customdata=ranking['Percentual_Aberto']
        ))

        # CORREÇÃO: Sintaxe correta sem titlefont
        fig_ranking.update_layout(
            title={
                'text': '🏆 Top 15 Polos - Ordens em Aberto',
                'x': 0.5,
                'font': {'size': 20, 'color': '#DC2626', 'family': 'Inter'}
            },
            xaxis=dict(title='Quantidade de Ordens em Aberto'),
            yaxis=dict(title='Polos (Providers)'),
            height=600,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', size=12),
            margin=dict(l=150, r=50, t=80, b=50)  # Margem para responsividade
        )

        # Container responsivo
        st.markdown('<div class="container-responsive">',
                    unsafe_allow_html=True)
        st.plotly_chart(fig_ranking, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Tabela complementar
        st.markdown("### 📊 **Tabela Detalhada do Ranking**")
        ranking_display = ranking.copy()
        ranking_display['Ranking'] = range(1, len(ranking_display) + 1)
        ranking_display = ranking_display[[
            'Ranking', 'Provider', 'Total_Ordens', 'Ordens_Aberto', 'Percentual_Aberto']]

        st.dataframe(
            ranking_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ranking": "🏆 Pos",
                "Provider": "Polo",
                "Total_Ordens": "Total",
                "Ordens_Aberto": "Em Aberto",
                "Percentual_Aberto": "% Aberto"
            }
        )

    except Exception as e:
        st.error(f"Erro ao criar ranking: {e}")
        st.info("Verifique se os dados estão no formato correto")


def criar_grafico_pizza_melhorado(df):
    """Cria gráfico de pizza melhorado"""
    if 'Status_Tratativa' not in df.columns:
        return None

    status_counts = df['Status_Tratativa'].value_counts()

    # Cores personalizadas
    cores_personalizadas = []
    for status in status_counts.index:
        if status == 'Em Aberto':
            cores_personalizadas.append('#DC2626')
        elif status in CORES_STATUS:
            cores_personalizadas.append(CORES_STATUS[status])
        else:
            cores_personalizadas.append('#94A3B8')

    fig = go.Figure(data=[go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        hole=0.5,
        marker=dict(
            colors=cores_personalizadas,
            line=dict(color='#FFFFFF', width=3)
        ),
        textinfo='label+percent+value',
        textfont=dict(size=14, color='white', family='Inter'),
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>',
        pull=[0.1 if status == 'Em Aberto' else 0 for status in status_counts.index]
    )])

    fig.update_layout(
        title={
            'text': '🎯 <b>Distribuição de Status Tratativa</b>',
            'x': 0.5,
            'font': {'size': 20, 'color': '#1E3A8A', 'family': 'Inter'}
        },
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            font=dict(size=12, family='Inter')
        ),
        font=dict(family='Inter'),
        annotations=[
            dict(
                text=f'<b>Total<br>{len(df):,}</b>',
                x=0.5, y=0.5,
                font_size=16,
                font_color='#1E3A8A',
                font_family='Inter',
                showarrow=False
            )
        ]
    )

    return fig


def main():
    # Header
    st.markdown('<h1 class="main-header">📊 Dashboard Report Safra </h1>',
                unsafe_allow_html=True)

    # Carregar dados
    df = carregar_dados()

    if df.empty:
        st.error("❌ Não foi possível carregar os dados.")
        return

    # Aplicar filtros (SEM filtro automático de data)
    df_filtrado = criar_filtros_avancados(df)

    # Calcular comparações semanais
    comp_semanal = calcular_comparacoes_semanais(df_filtrado)

    # Métricas principais
    criar_metricas_principais(df_filtrado, comp_semanal)

    st.markdown("---")

    # NOVA: Tabela detalhada que reflete o consolidado
    criar_tabela_detalhada(df_filtrado)

    st.markdown("---")

    # Relatório gerencial por polos
    criar_relatorio_gerencial_polos(df_filtrado)

    st.markdown("---")

    # Ranking de polos (com tratamento de erro)
    try:
        criar_ranking_polos_abertos(df_filtrado)
    except Exception as e:
        st.error(f"Erro no ranking de polos: {e}")
        st.info("Continuando com outras visualizações...")

    st.markdown("---")

    # Gráfico de pizza
    col1, col2 = st.columns(2)

    with col1:
        fig_pizza = criar_grafico_pizza_melhorado(df_filtrado)
        if fig_pizza:
            st.plotly_chart(fig_pizza, use_container_width=True)

    # Sidebar com resumo
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 **Resumo**")

    total_registros = len(df_filtrado)
    if 'Status_Tratativa' in df_filtrado.columns:
        abertos = len(
            df_filtrado[df_filtrado['Status_Tratativa'] == 'Em Aberto'])
        perc_abertos = (abertos / total_registros *
                        100) if total_registros > 0 else 0

        st.sidebar.markdown(f"""
        **📈 Estatísticas:**
        - **Total:** {total_registros:,}
        - **Em aberto:** {abertos:,}
        - **% Aberto:** {perc_abertos:.1f}%
        """)


if __name__ == "__main__":
    main()
