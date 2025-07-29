import streamlit as st
import pandas as pd
import io
from pathlib import Path
import sys
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import unicodedata

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import config

def aplicar_estilo_formulario():
    """CSS específico para o formulário"""
    st.markdown("""
    <style>
    .formulario-header {
        background: linear-gradient(135deg, rgb(255, 99, 99) 0%, rgb(255, 182, 193) 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .polo-card {
        background: linear-gradient(135deg, rgb(255, 255, 255) 0%, rgb(248, 249, 250) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid rgb(255, 231, 45);
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .polo-card-critico {
        border-left-color: rgb(255, 99, 99) !important;
    }
    
    .polo-card-atencao {
        border-left-color: rgb(255, 231, 45) !important;
    }
    
    .polo-card-ok {
        border-left-color: rgb(158, 213, 158) !important;
    }
    
    .metrica-polo {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid rgb(240, 240, 240);
    }
    
    .metrica-polo:last-child {
        border-bottom: none;
    }
    
    .campo-obrigatorio {
        color: rgb(255, 99, 99);
        font-weight: bold;
    }
    
    .info-semana {
        background: linear-gradient(135deg, rgb(158, 213, 158) 0%, rgb(212, 225, 103) 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

def calcular_semana_ano(data=None):
    """Calcula semana do ano e período"""
    if data is None:
        data = datetime.now()
    
    semana = data.isocalendar()[1]
    ano = data.year
    
    # Calcular início e fim da semana
    inicio_semana = data - timedelta(days=data.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    
    periodo = f"{inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m')}"
    
    return semana, ano, periodo

def remover_acentos(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto)
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('ascii')

def normalizar_provider(provider):
    if pd.isna(provider):
        return ""
    provider_str = str(provider).strip().upper()
    if provider_str.startswith('POLO '):
        provider_str = provider_str[5:]
    provider_str = remover_acentos(provider_str)
    return provider_str

def normalizar_polo_sap(polo_sap):
    if pd.isna(polo_sap):
        return ""
    polo_str = str(polo_sap).strip().upper()
    polo_str = remover_acentos(polo_str)
    return polo_str

def calcular_metricas_polo(df_polo):
    """Calcula métricas de um polo específico"""
    if df_polo.empty:
        return {
            'total_em_aberto': 0,
            'em_atraso': 0,
            'perc_atraso': 0.0
        }
    
    total_em_aberto = len(df_polo)
    
    if 'SLA Cliente' in df_polo.columns:
        sla_validos = pd.to_numeric(df_polo['SLA Cliente'], errors='coerce').dropna()
        if not sla_validos.empty:
            em_atraso = len(sla_validos[sla_validos >= 2])
            perc_atraso = round((em_atraso / total_em_aberto * 100), 1) if total_em_aberto > 0 else 0.0
        else:
            em_atraso = 0
            perc_atraso = 0.0
    else:
        em_atraso = 0
        perc_atraso = 0.0
    
    return {
        'total_em_aberto': total_em_aberto,
        'em_atraso': em_atraso,
        'perc_atraso': perc_atraso
    }

def salvar_justificativas_excel(dados_formulario):
    """Salva justificativas em Excel na pasta compartilhada"""
    
    # Criar pasta se não existir
    pasta_justificativas = Path("data/justificativas")
    pasta_justificativas.mkdir(parents=True, exist_ok=True)
    
    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    nome_arquivo = f"{timestamp}_{dados_formulario['lider'].replace(' ', '_')}_S{dados_formulario['semana']}.xlsx"
    
    caminho_arquivo = pasta_justificativas / nome_arquivo
    
    # Preparar dados para Excel
    dados_excel = []
    
    for polo_info in dados_formulario['polos']:
        dados_excel.append({
            'Data': dados_formulario['data'],
            'Semana': dados_formulario['semana'],
            'Lider': dados_formulario['lider'],
            'Polo': polo_info['nome'],
            'Ordens_Em_Aberto': polo_info['metricas']['total_em_aberto'],
            'Ordens_Em_Atraso': polo_info['metricas']['em_atraso'],
            'Perc_Atraso': polo_info['metricas']['perc_atraso'],
            'Justificativa': polo_info['justificativa'],
            'Acao_Corretiva': polo_info['acao_corretiva'],
            'Observacoes': dados_formulario['observacoes']
        })
    
    # Salvar em Excel
    df_excel = pd.DataFrame(dados_excel)
    df_excel.to_excel(caminho_arquivo, index=False)
    
    return caminho_arquivo

def enviar_notificacao_email(dados_formulario, caminho_arquivo):
    """Envia notificação por email (configurar conforme seu ambiente)"""
    
    try:
        # Configurações do email (AJUSTAR CONFORME SEU AMBIENTE)
        smtp_server = "smtp.gmail.com"  # ou servidor da empresa
        smtp_port = 587
        email_remetente = "dashboard.safra@empresa.com"  # CONFIGURAR
        senha_remetente = "sua_senha_app"  # CONFIGURAR
        email_destinatario = "seu.email@empresa.com"  # SEU EMAIL
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_remetente
        msg['To'] = email_destinatario
        msg['Subject'] = f"📋 Justificativas - {dados_formulario['lider']} - Semana {dados_formulario['semana']}"
        
        # Resumo dos polos
        resumo_polos = "\n".join([
            f"• {polo['nome']}: {polo['metricas']['em_atraso']} atrasos ({polo['metricas']['perc_atraso']:.1f}%)"
            for polo in dados_formulario['polos']
            if polo['metricas']['perc_atraso'] > 0
        ])
        
        # Corpo do email
        corpo_email = f"""
📋 NOVA JUSTIFICATIVA RECEBIDA

👤 Líder: {dados_formulario['lider']}
📅 Data: {dados_formulario['data']}
📊 Semana: {dados_formulario['semana']} ({dados_formulario['periodo']})
🏢 Polos: {len(dados_formulario['polos'])} polos analisados

⚠️ Polos com Atraso:
{resumo_polos}

📁 Arquivo: {caminho_arquivo.name}
📂 Pasta: {caminho_arquivo.parent}

💬 Observações: {dados_formulario['observacoes']}

---
Dashboard Safra - Sistema Automático
        """
        
        msg.attach(MIMEText(corpo_email, 'plain'))
        
        # Anexar Excel
        with open(caminho_arquivo, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= "{caminho_arquivo.name}"'
        )
        msg.attach(part)
        
        # Enviar email (DESCOMENTE E CONFIGURE)
        # server = smtplib.SMTP(smtp_server, smtp_port)
        # server.starttls()
        # server.login(email_remetente, senha_remetente)
        # text = msg.as_string()
        # server.sendmail(email_remetente, email_destinatario, text)
        # server.quit()
        
        return True
        
    except Exception as e:
        st.error(f"Erro ao enviar email: {e}")
        return False

def carregar_dados_dashboard():
    """Carrega dados do dashboard ou arquivos diretos"""
    
    # Tentar usar dados do session_state primeiro
    if 'dados_dashboard' in st.session_state:
        return st.session_state['dados_dashboard']
    
    # Fallback: carregar dados diretamente
    try:
        df_hoje = pd.read_excel('data/input/Relatorio_Diario1.xlsx')
        df_mapeamento = pd.read_excel('data/input/pagresolve_regionais.xlsx')
        
        # Excluir TEFTI
        df_hoje = df_hoje[df_hoje['Provider'] != 'TEFTI'].copy()
        
        # Processar com líder
        df_hoje['Provider_Normalizado'] = df_hoje['Provider'].apply(normalizar_provider)
        df_mapeamento['Polo_SAP_Normalizado'] = df_mapeamento['Polo + SAP'].apply(normalizar_polo_sap)
        
        df_hoje_com_lider = df_hoje.merge(
            df_mapeamento[['Polo_SAP_Normalizado', 'Líder PagResolve']],
            left_on='Provider_Normalizado',
            right_on='Polo_SAP_Normalizado',
            how='left'
        ).rename(columns={'Líder PagResolve': 'Lider'})
        
        return {
            'df_hoje_com_lider': df_hoje_com_lider,
            'df_mapeamento': df_mapeamento,
            'metricas_hoje': {}
        }
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# Configuração da página
st.set_page_config(
    page_title="Formulário de Justificativas", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

aplicar_estilo_formulario()

# Header do formulário
semana, ano, periodo = calcular_semana_ano()

st.markdown(f"""
<div class="formulario-header">
    <h1>📋 Formulário de Justificativas</h1>
    <p>Sistema de Accountability para Líderes Safra</p>
</div>
""", unsafe_allow_html=True)

# Informações da semana
st.markdown(f"""
<div class="info-semana">
    <h3>📅 Informações do Período</h3>
    <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y')}</p>
    <p><strong>Semana:</strong> Semana {semana} de {ano} ({periodo})</p>
</div>
""", unsafe_allow_html=True)

# Carregar dados
dados_dashboard = carregar_dados_dashboard()

if dados_dashboard is None:
    st.error("❌ Não foi possível carregar os dados do dashboard")
    st.stop()

df_hoje_com_lider = dados_dashboard['df_hoje_com_lider']
df_mapeamento = dados_dashboard['df_mapeamento']

# Verificar se há líderes
lideres_disponiveis = sorted(df_hoje_com_lider['Lider'].dropna().unique().tolist())

if not lideres_disponiveis:
    st.error("❌ Nenhum líder encontrado nos dados")
    st.stop()

# SEÇÃO 1: Seleção do Líder
st.markdown('<h3>👤 Identificação do Líder</h3>', unsafe_allow_html=True)

lider_selecionado = st.selectbox(
    "Selecione seu nome:",
    lideres_disponiveis,
    help="Selecione o líder responsável pelas justificativas"
)

if lider_selecionado:
    # Filtrar dados do líder
    df_lider = df_hoje_com_lider[df_hoje_com_lider['Lider'] == lider_selecionado].copy()
    
    if df_lider.empty:
        st.warning("⚠️ Nenhum polo encontrado para este líder")
        st.stop()
    
    # Obter polos do líder
    polos_lider = df_lider['Provider'].unique()
    
    st.success(f"✅ Líder selecionado: **{lider_selecionado}**")
    st.info(f"🏢 Polos sob sua responsabilidade: **{len(polos_lider)}** polos")
    
    # SEÇÃO 2: Polos e Métricas
    st.markdown('<h3>🏢 Polos e Justificativas</h3>', unsafe_allow_html=True)
    
    # Inicializar dados do formulário
    dados_formulario = {
        'data': datetime.now().strftime('%d/%m/%Y'),
        'semana': semana,
        'periodo': periodo,
        'lider': lider_selecionado,
        'polos': []
    }
    
    # Para cada polo do líder
    for i, polo in enumerate(polos_lider):
        # Filtrar dados do polo
        df_polo = df_lider[df_lider['Provider'] == polo].copy()
        
        # Calcular métricas do polo
        metricas_polo = calcular_metricas_polo(df_polo)
        
        # Determinar criticidade
        if metricas_polo['perc_atraso'] >= 30:
            classe_card = "polo-card-critico"
            emoji_status = "🔴"
        elif metricas_polo['perc_atraso'] >= 20:
            classe_card = "polo-card-atencao"
            emoji_status = "🟡"
        else:
            classe_card = "polo-card-ok"
            emoji_status = "🟢"
        
        # Card do polo
        st.markdown(f"""
        <div class="polo-card {classe_card}">
            <h4>{emoji_status} {polo}</h4>
            <div class="metrica-polo">
                <span>📊 Ordens em Aberto:</span>
                <span><strong>{metricas_polo['total_em_aberto']:,}</strong></span>
            </div>
            <div class="metrica-polo">
                <span>⚠️ Em Atraso (≥2 dias):</span>
                <span><strong>{metricas_polo['em_atraso']:,} ({metricas_polo['perc_atraso']:.1f}%)</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Campos de justificativa
        col1, col2 = st.columns(2)
        
        with col1:
            # Justificativa (obrigatória se % > 20%)
            obrigatorio_justificativa = metricas_polo['perc_atraso'] >= 20
            label_justificativa = f"📝 Justificativa para {polo}"
            if obrigatorio_justificativa:
                label_justificativa += " *"
            
            justificativa = st.text_area(
                label_justificativa,
                key=f"justificativa_{i}",
                height=100,
                help="Explique os motivos dos atrasos ou desvios operacionais" + 
                     (" (OBRIGATÓRIO - % atraso ≥ 20%)" if obrigatorio_justificativa else "")
            )
        
        with col2:
            # Ação corretiva (obrigatória se % > 20%)
            obrigatorio_acao = metricas_polo['perc_atraso'] >= 20
            label_acao = f"🔧 Ação Corretiva para {polo}"
            if obrigatorio_acao:
                label_acao += " *"
            
            acao_corretiva = st.text_area(
                label_acao,
                key=f"acao_{i}",
                height=100,
                help="Descreva as ações corretivas ou suporte necessário" + 
                     (" (OBRIGATÓRIO - % atraso ≥ 20%)" if obrigatorio_acao else "")
            )
        
        # Adicionar aos dados do formulário
        dados_formulario['polos'].append({
            'nome': polo,
            'metricas': metricas_polo,
            'justificativa': justificativa,
            'acao_corretiva': acao_corretiva,
            'obrigatorio_justificativa': obrigatorio_justificativa,
            'obrigatorio_acao': obrigatorio_acao
        })
        
        st.markdown("---")
    
    # SEÇÃO 3: Observações Gerais
    st.markdown('<h3>💬 Observações Gerais</h3>', unsafe_allow_html=True)
    
    observacoes = st.text_area(
        "Comentários adicionais (opcional):",
        height=100,
        help="Campo livre para observações gerais sobre a semana"
    )
    
    dados_formulario['observacoes'] = observacoes
    
    # SEÇÃO 4: Validação e Envio
    st.markdown('<h3>📤 Envio das Justificativas</h3>', unsafe_allow_html=True)
    
    # Validar formulário
    def validar_formulario():
        erros = []
        
        for polo_info in dados_formulario['polos']:
            if polo_info['obrigatorio_justificativa'] and not polo_info['justificativa'].strip():
                erros.append(f"Justificativa obrigatória para {polo_info['nome']} (% atraso ≥ 20%)")
            
            if polo_info['obrigatorio_acao'] and not polo_info['acao_corretiva'].strip():
                erros.append(f"Ação corretiva obrigatória para {polo_info['nome']} (% atraso ≥ 20%)")
        
        return erros
    
    # Mostrar resumo antes do envio
    with st.expander("📋 Resumo das Justificativas", expanded=False):
        st.write(f"**Líder:** {lider_selecionado}")
        st.write(f"**Data:** {dados_formulario['data']}")
        st.write(f"**Semana:** {dados_formulario['semana']} ({dados_formulario['periodo']})")
        st.write(f"**Polos analisados:** {len(dados_formulario['polos'])}")
        
        polos_com_atraso = [p for p in dados_formulario['polos'] if p['metricas']['perc_atraso'] > 0]
        st.write(f"**Polos com atraso:** {len(polos_com_atraso)}")
        
        if polos_com_atraso:
            for polo in polos_com_atraso:
                st.write(f"• {polo['nome']}: {polo['metricas']['em_atraso']} atrasos ({polo['metricas']['perc_atraso']:.1f}%)")
    
    # Botões de ação
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📤 Enviar Justificativas", type="primary"):
            # Validar formulário
            erros = validar_formulario()
            
            if erros:
                st.error("❌ Corrija os seguintes erros:")
                for erro in erros:
                    st.error(f"• {erro}")
            else:
                try:
                    # Salvar em Excel
                    caminho_arquivo = salvar_justificativas_excel(dados_formulario)
                    
                    # Enviar notificação por email
                    email_enviado = enviar_notificacao_email(dados_formulario, caminho_arquivo)
                    
                    # Feedback de sucesso
                    st.success("✅ Justificativas enviadas com sucesso!")
                    st.info(f"📁 Arquivo salvo: {caminho_arquivo.name}")
                    
                    if email_enviado:
                        st.success("📧 Notificação enviada por email!")
                    else:
                        st.warning("⚠️ Arquivo salvo, mas email não configurado")
                    
                    # Mostrar informações do arquivo
                    st.markdown(f"""
                    **📋 Detalhes do Envio:**
                    - **Arquivo:** {caminho_arquivo.name}
                    - **Localização:** {caminho_arquivo.parent}
                    - **Tamanho:** {caminho_arquivo.stat().st_size} bytes
                    - **Data/Hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                    """)
                    
                    # Limpar formulário após 3 segundos
                    import time
                    time.sleep(3)
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao enviar justificativas: {e}")
    
    with col2:
        if st.button("🔄 Limpar Formulário"):
            st.experimental_rerun()
    
    with col3:
        st.info("💡 Campos marcados com * são obrigatórios para polos com % atraso ≥ 20%")
    
    # SEÇÃO 5: Instruções e Ajuda
    with st.expander("❓ Instruções de Preenchimento", expanded=False):
        st.markdown("""
        ### 📋 Como Preencher o Formulário
        
        **1. Identificação**
        - Selecione seu nome na lista de líderes
        - O sistema carregará automaticamente seus polos
        
        **2. Justificativas por Polo**
        - **Justificativa:** Explique os motivos dos atrasos (obrigatório se % ≥ 20%)
        - **Ação Corretiva:** Descreva as ações para resolver (obrigatório se % ≥ 20%)
        
        **3. Observações Gerais**
        - Campo livre para comentários adicionais sobre a semana
        
        **4. Envio**
        - Revise o resumo antes de enviar
        - O sistema salvará em Excel e enviará notificação
        
        ### 🎯 Critérios de Obrigatoriedade
        - **🔴 Crítico (≥30%):** Justificativa e ação obrigatórias
        - **🟡 Atenção (≥20%):** Justificativa e ação obrigatórias  
        - **🟢 Normal (<20%):** Justificativa opcional
        
        ### 📧 Notificações
        - Email automático será enviado para a gestão
        - Arquivo Excel anexado com todos os detalhes
        - Histórico preservado na pasta compartilhada
        """)
    
    # SEÇÃO 6: Histórico (se disponível)
    with st.expander("📚 Histórico de Justificativas", expanded=False):
        try:
            pasta_justificativas = Path("data/justificativas")
            if pasta_justificativas.exists():
                arquivos_historico = list(pasta_justificativas.glob("*.xlsx"))
                
                if arquivos_historico:
                    st.write("**Últimas justificativas enviadas:**")
                    
                    # Mostrar últimos 10 arquivos
                    arquivos_recentes = sorted(arquivos_historico, key=lambda x: x.stat().st_mtime, reverse=True)[:10]
                    
                    for arquivo in arquivos_recentes:
                        # Extrair informações do nome do arquivo
                        nome_parts = arquivo.stem.split('_')
                        if len(nome_parts) >= 3:
                            data_envio = nome_parts[0]
                            hora_envio = nome_parts[1]
                            lider_nome = ' '.join(nome_parts[2:-1])
                            semana_info = nome_parts[-1]
                            
                            data_formatada = f"{data_envio[:2]}/{data_envio[2:4]}/{data_envio[4:8]}"
                            hora_formatada = f"{hora_envio[:2]}:{hora_envio[2:4]}"
                            
                            st.write(f"• {data_formatada} {hora_formatada} - {lider_nome} - {semana_info}")
                else:
                    st.info("Nenhuma justificativa anterior encontrada")
            else:
                st.info("Pasta de histórico não encontrada")
                
        except Exception as e:
            st.warning(f"Não foi possível carregar histórico: {e}")

else:
    st.warning("⚠️ Selecione um líder para continuar")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: rgb(51, 51, 51); opacity: 0.7; margin-top: 2rem;">'
    'Formulário de Justificativas Safra • Sistema de Accountability • Julho/2025'
    '</div>', 
    unsafe_allow_html=True
)

# Botão para voltar ao dashboard
st.markdown('<br>', unsafe_allow_html=True)
if st.button("🔙 Voltar ao Dashboard"):
    st.switch_page("dashboard/app_dashboard.py")

