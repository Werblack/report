import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

# Configurar página
st.set_page_config(
    page_title="📊 Dashboard Safra Corporativo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS melhorado
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
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0.5rem 0;
        font-family: 'Inter', sans-serif;
    }
    
    .metric-label {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2C5282;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
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
    
    .highlight-red {
        color: #DC2626;
        font-weight: 800;
        font-size: 1.1rem;
    }
    
    .data-info {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px solid #0ea5e9;
        margin: 1rem 0;
    }
    
    .debug-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 0.9rem;
        border-left: 4px solid #6c757d;
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

@st.cache_data
def carregar_dados_automatico():
    """Carrega dados automaticamente do repositório GitHub - AJUSTADO PARA SUA ESTRUTURA"""
    
    # Debug: Mostrar estrutura atual
    st.sidebar.markdown("### 🔍 **Debug - Estrutura do Repositório**")
    
    try:
        diretorio_atual = os.getcwd()
        st.sidebar.markdown(f"**Diretório atual:** `{os.path.basename(diretorio_atual)}`")
        
        # Listar arquivos na raiz
        arquivos_raiz = os.listdir('.')
        st.sidebar.markdown("**Arquivos na raiz:**")
        for arquivo in arquivos_raiz[:8]:
            st.sidebar.markdown(f"- `{arquivo}`")
        
        # Verificar se existe pasta "Projeto Safra"
        if 'Projeto Safra' in arquivos_raiz:
            st.sidebar.markdown("**✅ Pasta 'Projeto Safra' encontrada**")
            try:
                arquivos_projeto = os.listdir('Projeto Safra')
                st.sidebar.markdown("**Conteúdo 'Projeto Safra':**")
                for arquivo in arquivos_projeto:
                    st.sidebar.markdown(f"- `{arquivo}`")
                    
                # Verificar pasta data
                if 'data' in arquivos_projeto:
                    arquivos_data = os.listdir('Projeto Safra/data')
                    st.sidebar.markdown("**Arquivos em 'data':**")
                    for arquivo in arquivos_data:
                        st.sidebar.markdown(f"- `{arquivo}`")
            except Exception as e:
                st.sidebar.error(f"Erro ao listar Projeto Safra: {e}")
        
    except Exception as e:
        st.sidebar.error(f"Erro no debug: {e}")
    
    # Lista de caminhos possíveis baseados na sua estrutura
    caminhos_possiveis = [
        # Caminho correto baseado na sua estrutura
        "Projeto Safra/data/Safra_Gerencial_Téc.Prop_17.06.xlsx",
        
        # Caminhos alternativos
        "Projeto Safra/data/Relatorio_Diario.xlsx",
        "data/Safra_Gerencial_Téc.Prop_17.06.xlsx",
        "Safra_Gerencial_Téc.Prop_17.06.xlsx",
        
        # Outros possíveis
        "Projeto Safra/Safra_Gerencial_Téc.Prop_17.06.xlsx"
    ]
    
    st.sidebar.markdown("### 📁 **Tentativas de Carregamento**")
    
    # Tentar carregar de cada caminho
    for i, caminho in enumerate(caminhos_possiveis):
        st.sidebar.markdown(f"**Tentativa {i+1}:** `{caminho}`")
        
        if os.path.exists(caminho):
            try:
                # Verificar se é arquivo Excel
                if not caminho.endswith(('.xlsx', '.xls')):
                    st.sidebar.markdown(f"⚠️ Não é arquivo Excel")
                    continue
                
                # Tentar diferentes abas
                abas_possiveis = ['Consolidado', 'Sheet1', 'Dados', 'Base']
                
                for aba in abas_possiveis:
                    try:
                        df = pd.read_excel(caminho, sheet_name=aba)
                        
                        # Verificar se tem dados válidos
                        if df.empty:
                            continue
                        
                        # Verificar coluna chave
                        if 'Ordem PagBank' not in df.columns:
                            # Tentar encontrar coluna similar
                            colunas_similares = [col for col in df.columns if 'ordem' in col.lower() or 'pagbank' in col.lower()]
                            if colunas_similares:
                                df = df.rename(columns={colunas_similares[0]: 'Ordem PagBank'})
                                st.sidebar.info(f"✅ Renomeada '{colunas_similares[0]}' para 'Ordem PagBank'")
                            else:
                                continue
                        
                        # Sucesso!
                        st.sidebar.success(f"✅ **SUCESSO!** Dados carregados:")
                        st.sidebar.success(f"📁 **Arquivo:** `{caminho}`")
                        st.sidebar.success(f"📋 **Aba:** `{aba}`")
                        st.sidebar.info(f"📊 **Registros:** {len(df):,}")
                        st.sidebar.info(f"📋 **Colunas:** {len(df.columns)}")
                        st.sidebar.info(f"🔄 **Carregado em:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                        
                        # Verificar colunas importantes
                        colunas_importantes = ['Status_Tratativa', 'Provider', 'SLA Cliente']
                        colunas_encontradas = [col for col in colunas_importantes if col in df.columns]
                        st.sidebar.info(f"🔑 **Colunas chave:** {len(colunas_encontradas)}/{len(colunas_importantes)}")
                        
                        return df
                        
                    except Exception as e:
                        st.sidebar.markdown(f"❌ Erro na aba '{aba}': {str(e)[:30]}...")
                        continue
                
                # Se chegou aqui, tentar primeira aba disponível
                try:
                    df = pd.read_excel(caminho)
                    if not df.empty:
                        st.sidebar.warning(f"⚠️ Usando primeira aba disponível")
                        st.sidebar.info(f"📁 Arquivo: {caminho}")
                        st.sidebar.info(f"📋 Colunas: {list(df.columns)[:5]}...")
                        return df
                except:
                    pass
                    
            except Exception as e:
                st.sidebar.error(f"❌ Erro: {str(e)[:50]}...")
                continue
        else:
            st.sidebar.markdown(f"❌ Arquivo não existe")
    
    # Se não encontrou nenhum arquivo, criar dados de exemplo
    st.sidebar.warning("📋 **Nenhum arquivo Excel encontrado**")
    st.sidebar.info("💡 **Usando dados de demonstração**")
    st.sidebar.markdown("""
    **Para usar dados reais:**
    1. Verifique se o arquivo está em `Projeto Safra/data/`
    2. Nome: `Safra_Gerencial_Téc.Prop_17.06.xlsx`
    3. Aba: `Consolidado` ou `Sheet1`
    """)
    
    return criar_dados_exemplo()

def criar_dados_exemplo():
    """Cria dados de exemplo para demonstração"""
    import random
    
    dados = []
    providers = ['XAXIM', 'CURITIBA', 'SAO_PAULO', 'RIO_JANEIRO', 'BELO_HORIZONTE', 'BRASILIA', 'SALVADOR']
    status_tratativa = ['Em Aberto', 'Finalizado com Sucesso', 'Finalizado com Insucesso', 'Pendente', 'Em Análise']
    regioes = ['Sul', 'Sudeste', 'Centro-Oeste', 'Nordeste', 'Norte']
    estados = ['PR', 'SP', 'RJ', 'MG', 'GO', 'BA', 'PE', 'AM', 'RS', 'SC']
    
    for i in range(4200):
        data_criacao = datetime.now() - timedelta(days=random.randint(0, 365))
        data_status = data_criacao + timedelta(days=random.randint(0, 45))
        
        status_weights = [0.25, 0.45, 0.15, 0.10, 0.05]
        status_escolhido = random.choices(status_tratativa, weights=status_weights)[0]
        
        dados.append({
            'Ordem PagBank': f'PB{100000+i}',
            'Status_Tratativa': status_escolhido,
            'Provider': random.choice(providers),
            'Status da Ordem': random.choice(['Ativo', 'Finalizado', 'Cancelado']),
            'SLA Cliente': random.randint(1, 25),
            'SLA Logística': random.randint(1, 20),
            'Dias_Em_Aberto': random.randint(0, 90) if status_escolhido == 'Em Aberto' else random.randint(0, 30),
            'Data_Status': data_status,
            'Criação da Ordem': data_criacao,
            'Região': random.choice(regioes),
            'Estado': random.choice(estados),
            'Cidade': f'Cidade_{random.randint(1, 300)}',
            'CEP': f'{random.randint(10000, 99999)}-{random.randint(100, 999)}',
            'Feedback': random.choice([None, None, 'Aguardando retorno', 'Problema entrega', 'Cliente satisfeito']),
            'Causa_Raiz': random.choice([None, None, 'Atraso logística', 'Problema sistema', 'Falta estoque']),
            'Proxima_Acao': random.choice([None, None, 'Contatar cliente', 'Verificar status', 'Reagendar']),
            'Data_Feedback': data_status + timedelta(days=random.randint(0, 10)) if random.random() > 0.6 else None
        })
    
    return pd.DataFrame(dados)

def criar_filtros_avancados(df):
    """Cria filtros avançados na sidebar"""
    st.sidebar.markdown("## 🎛️ **Filtros Avançados**")
    
    df_filtrado = df.copy()
    
    # Filtro de Status Tratativa
    if 'Status_Tratativa' in df_filtrado.columns:
        status_options = ['Todos'] + sorted(df_filtrado['Status_Tratativa'].dropna().unique().tolist())
        status_selecionado = st.sidebar.selectbox("📋 **Status Tratativa**", status_options)
        
        if status_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Status_Tratativa'] == status_selecionado]
    
    # Filtro de Polos
    if 'Provider' in df_filtrado.columns:
        provider_options = ['Todos'] + sorted(df_filtrado['Provider'].dropna().unique().tolist())
        provider_selecionado = st.sidebar.selectbox("🏢 **Polo (Provider)**", provider_options)
        
        if provider_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Provider'] == provider_selecionado]
    
    # Filtro de Região
    if 'Região' in df_filtrado.columns:
        regiao_options = ['Todas'] + sorted(df_filtrado['Região'].dropna().unique().tolist())
        regiao_selecionada = st.sidebar.selectbox("🗺️ **Região**", regiao_options)
        
        if regiao_selecionada != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['Região'] == regiao_selecionada]
    
    return df_filtrado

def criar_metricas_principais(df):
    """Cria métricas principais"""
    st.markdown('<h2 class="section-header">📊 Métricas Principais</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_pedidos = len(df)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📦 Total de Pedidos</div>
            <div class="metric-value">{total_pedidos:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if 'Status_Tratativa' in df.columns:
            abertos = len(df[df['Status_Tratativa'] == 'Em Aberto'])
            perc_abertos = (abertos / total_pedidos * 100) if total_pedidos > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🔴 Ordens em Aberto</div>
                <div class="metric-value highlight-red">{abertos:,}</div>
                <div class="highlight-red">{perc_abertos:.1f}% do total</div>
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
            """, unsafe_allow_html=True)
    
    with col4:
        if 'Provider' in df.columns:
            polos_ativos = df['Provider'].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🏢 Polos Ativos</div>
                <div class="metric-value">{polos_ativos}</div>
            </div>
            """, unsafe_allow_html=True)

def criar_ranking_polos(df):
    """Cria ranking de polos por ordens em aberto"""
    if 'Provider' not in df.columns or 'Status_Tratativa' not in df.columns:
        return
    
    st.markdown('<h2 class="section-header">🏆 Ranking: Polos com Mais Ordens em Aberto</h2>', unsafe_allow_html=True)
    
    # Calcular ranking
    abertos_por_polo = df[df['Status_Tratativa'] == 'Em Aberto'].groupby('Provider').size().reset_index(name='Ordens_Aberto')
    total_por_polo = df.groupby('Provider').size().reset_index(name='Total_Ordens')
    
    ranking = total_por_polo.merge(abertos_por_polo, on='Provider', how='left').fillna(0)
    ranking['Percentual_Aberto'] = (ranking['Ordens_Aberto'] / ranking['Total_Ordens'] * 100).round(1)
    ranking = ranking.sort_values('Ordens_Aberto', ascending=False).head(10)
    
    # Gráfico de barras
    fig = px.bar(
        ranking,
        x='Ordens_Aberto',
        y='Provider',
        orientation='h',
        title='Top 10 Polos - Ordens em Aberto',
        text='Ordens_Aberto',
        color='Ordens_Aberto',
        color_continuous_scale='Reds'
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(height=500, showlegend=False)
    
    st.plotly_chart(fig, use_container_width=True)

def criar_grafico_pizza(df):
    """Cria gráfico de pizza de status"""
    if 'Status_Tratativa' not in df.columns:
        return
    
    status_counts = df['Status_Tratativa'].value_counts()
    
    cores = [CORES_STATUS.get(status, '#94A3B8') for status in status_counts.index]
    
    fig = go.Figure(data=[go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        hole=0.4,
        marker=dict(colors=cores),
        textinfo='label+percent+value'
    )])
    
    fig.update_layout(
        title='Distribuição por Status Tratativa',
        height=400
    )
    
    return fig

def criar_tabela_detalhada(df):
    """Cria tabela detalhada com download"""
    st.markdown('<h2 class="section-header">📋 Dados Detalhados</h2>', unsafe_allow_html=True)
    
    # Controles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        linhas = st.selectbox("Linhas por página", [25, 50, 100, 200], index=1)
    
    with col2:
        if not df.empty:
            ordenar_por = st.selectbox("Ordenar por", df.columns.tolist())
        else:
            ordenar_por = None
    
    with col3:
        ordem_desc = st.checkbox("Ordem decrescente", value=False)
    
    # Aplicar ordenação
    if ordenar_por:
        df_ordenado = df.sort_values(by=ordenar_por, ascending=not ordem_desc)
    else:
        df_ordenado = df
    
    # Mostrar tabela
    st.dataframe(df_ordenado.head(linhas), use_container_width=True, hide_index=True)
    
    # Download
    st.markdown("### 💾 Download dos Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Download CSV Completo",
            data=csv,
            file_name=f"safra_dados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if 'Status_Tratativa' in df.columns:
            df_abertos = df[df['Status_Tratativa'] == 'Em Aberto']
            if not df_abertos.empty:
                csv_abertos = df_abertos.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="🔴 Download Apenas Em Aberto",
                    data=csv_abertos,
                    file_name=f"safra_em_aberto_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )

def main():
    # Header
    st.markdown('<h1 class="main-header">📊 Dashboard Safra Corporativo</h1>', unsafe_allow_html=True)
    
    # Informações sobre os dados
    st.markdown("""
    <div class="data-info">
        <h3>📊 Dados Automaticamente Carregados</h3>
        <p>Este dashboard carrega automaticamente os dados do arquivo 
        <strong>Safra_Gerencial_Téc.Prop_17.06.xlsx</strong> localizado em 
        <strong>Projeto Safra/data/</strong></p>
        <p>Os colaboradores podem visualizar e analisar os dados sem necessidade de upload!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados automaticamente
    df = carregar_dados_automatico()
    
    if df.empty:
        st.error("❌ Não foi possível carregar os dados.")
        st.stop()
    
    # Aplicar filtros
    df_filtrado = criar_filtros_avancados(df)
    
    # Métricas principais
    criar_metricas_principais(df_filtrado)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pizza = criar_grafico_pizza(df_filtrado)
        if fig_pizza:
            st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col2:
        criar_ranking_polos(df_filtrado)
    
    st.markdown("---")
    
    # Tabela detalhada
    criar_tabela_detalhada(df_filtrado)
    
    # Sidebar com resumo
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 **Resumo**")
    
    total_registros = len(df_filtrado)
    if 'Status_Tratativa' in df_filtrado.columns:
        abertos = len(df_filtrado[df_filtrado['Status_Tratativa'] == 'Em Aberto'])
        perc_abertos = (abertos / total_registros * 100) if total_registros > 0 else 0
        
        st.sidebar.markdown(f"""
        **📈 Estatísticas:**
        - **Total:** {total_registros:,}
        - **Em aberto:** {abertos:,}
        - **% Aberto:** {perc_abertos:.1f}%
        """)

if __name__ == "__main__":
    main()
