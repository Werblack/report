import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config.email_config import EMAIL_CONFIG

def testar_configuracao_email():
    """Testa se a configuração de email está funcionando"""
    
    try:
        # Criar mensagem de teste
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['email_remetente']
        msg['To'] = EMAIL_CONFIG['email_destinatario']
        msg['Subject'] = "🧪 Teste - Dashboard Safra"
        
        corpo_teste = """
        📧 TESTE DE CONFIGURAÇÃO DE EMAIL
        
        Se você recebeu este email, a configuração está funcionando corretamente!
        
        ✅ SMTP Server: Conectado
        ✅ Autenticação: OK
        ✅ Envio: Sucesso
        
        ---
        Dashboard Safra - Sistema de Testes
        """
        
        msg.attach(MIMEText(corpo_teste, 'plain'))
        
        # Conectar e enviar
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email_remetente'], EMAIL_CONFIG['senha_remetente'])
        
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['email_remetente'], EMAIL_CONFIG['email_destinatario'], text)
        server.quit()
        
        print("✅ Teste de email SUCESSO!")
        print(f"📧 Email enviado para: {EMAIL_CONFIG['email_destinatario']}")
        return True
        
    except Exception as e:
        print(f"❌ Teste de email FALHOU: {e}")
        print("\n🔧 Verifique:")
        print("1. Configurações em config/email_config.py")
        print("2. Senha de app do Gmail (se usando Gmail)")
        print("3. Permissões de firewall/antivírus")
        return False

if __name__ == "__main__":
    testar_configuracao_email()
