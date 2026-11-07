import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
import psycopg2
import hashlib
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import openpyxl
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import PatternFill, Font

# Configuração da página e Título do Navegador
st.set_page_config(
    page_title="Calculadora ETE | Gestão & Auditoria",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# BANCO DE DADOS POSTGRESQL (SUPABASE) E AUTENTICAÇÃO
# =========================================================
def get_db_connection():
    """Cria uma ligação segura e robusta com o PostgreSQL no Supabase."""
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=int(st.secrets["postgres"]["port"]),
        sslmode="require"
    )

def init_db():
    """Inicializa as tabelas de utilizadores e lançamentos operacionais."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de Utilizadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de Lançamentos Operacionais
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            dbo_permeado REAL, dbo_limite REAL,
            dqo_permeado REAL, dqo_limite REAL,
            og_permeado REAL, og_limite REAL,
            n_permeado REAL, n_limite REAL,
            p_permeado REAL, p_limite REAL,
            vazao_sanitario REAL, vazao_ind_bruto REAL,
            vazao_ind_tratado REAL, vazao_permeado REAL,
            carga_dbo_entrada REAL, rem_dqo REAL, rem_dbo REAL,
            rem_og REAL, rem_n REAL, rem_p REAL,
            balanco_n REAL, balanco_p REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

init_db()

def hash_senha(senha):
    """Gera um Hash seguro para a senha."""
    return hashlib.sha256(senha.encode()).hexdigest()

def cadastrar_utilizador(nome, email, senha):
    """Cadastra um novo utilizador no Supabase."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)",
            (nome, email.lower().strip(), hash_senha(senha))
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True, "✅ Conta criada com sucesso! Faça login para aceder ao sistema."
    except Exception as e:
        return False, f"⚠️ Este e-mail já está registado no sistema."

def autenticar_utilizador(email, senha):
    """Valida o e-mail e a senha do utilizador."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, email FROM usuarios WHERE email = %s AND senha_hash = %s",
        (email.lower().strip(), hash_senha(senha))
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def verificar_email_existe(email):
    """Verifica se o e-mail existe no Supabase."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM usuarios WHERE email = %s", (email.lower().strip(),))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def atualizar_senha(email, nova_senha):
    """Atualiza a senha do utilizador no Supabase."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET senha_hash = %s WHERE email = %s",
            (hash_senha(nova_senha), email.lower().strip())
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True, "✅ Senha alterada com sucesso! Faça login com a nova senha."
    except Exception as e:
        return False, f"❌ Erro ao atualizar senha: {str(e)}"

def enviar_email_real(email_destino, codigo_verificacao):
    """Envia o e-mail real com o código usando os dados SMTP."""
    try:
        smtp_server = st.secrets["smtp"]["server"]
        smtp_port = int(st.secrets["smtp"]["port"])
        smtp_user = st.secrets["smtp"]["user"]
        smtp_password = st.secrets["smtp"]["password"]

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email_destino
        msg['Subject'] = "🔒 Código de Recuperação de Senha - Calculadora ETE"

        corpo = f"""
        Olá,
        
        Recebemos uma solicitação de redefinição de senha para a sua conta na Plataforma Calculadora ETE.
        
        O seu código de verificação seguro é: {codigo_verificacao}
        
        Insira este código na tela de recuperação do aplicativo para cadastrar a sua nova senha.
        Caso não tenha solicitado esta alteração, ignore este e-mail.
        """
        msg.attach(MIMEText(corpo, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, email_destino, msg.as_string())
        server.quit()
        return True, "E-mail enviado com sucesso!"
    except Exception as e:
        return False, f"Erro SMTP: {str(e)}"

# Gerenciamento do estado da sessão
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "etapa_recuperacao" not in st.session_state:
    st.session_state["etapa_recuperacao"] = 1

if "email_recuperando" not in st.session_state:
    st.session_state["email_recuperando"] = ""

if "codigo_enviado" not in st.session_state:
    st.session_state["codigo_enviado"] = ""

# =========================================================
# TELA DE LOGIN, CADASTRO E RECUPERAÇÃO DE SENHA
# =========================================================
if st.session_state["usuario_logado"] is None:
    st.title("🔐 Acesso à Plataforma ETE Operacional")
    st.write("Bem-vindo! Faça login, crie a sua conta ou recupere o seu acesso de forma segura.")
    
    tab_login, tab_cadastro, tab_recuperar = st.tabs(["🔑 Entrar na Conta", "📝 Criar Nova Conta", "🔄 Esqueceu a Senha?"])
    
    with tab_login:
        email_login = st.text_input("E-mail de Acesso", key="login_email")
        senha_login = st.text_input("Senha", type="password", key="login_senha")
        
        if st.button("Entrar no Sistema", type="primary", use_container_width=True):
            user = autenticar_utilizador(email_login, senha_login)
            if user:
                st.session_state["usuario_logado"] = {"id": user[0], "nome": user[1], "email": user[2]}
                st.success(f"Bem-vindo, {user[1]}!")
                st.rerun()
            else:
                st.error("❌ E-mail ou senha incorretos. Tente novamente.")
                
    with tab_cadastro:
        nome_reg = st.text_input("Seu Nome Completo", key="reg_nome")
        email_reg = st.text_input("Seu E-mail (o mesmo da Hotmart)", key="reg_email")
        senha_reg = st.text_input("Crie uma Senha Forte", type="password", key="reg_senha")
        
        if st.button("Cadastrar e Liberar Acesso", use_container_width=True):
            if nome_reg and email_reg and senha_reg:
                sucesso, msg = cadastrar_utilizador(nome_reg, email_reg, senha_reg)
                if sucesso:
                    st.success(msg)
                else:
                    st.warning(msg)
            else:
                st.error("⚠️ Preencha todos os campos para se cadastrar.")

    with tab_recuperar:
        st.subheader("🔄 Recuperação Segura de Senha")
        
        if st.session_state["etapa_recuperacao"] == 1:
            st.write("Informe o seu e-mail cadastrado. Enviaremos um código de segurança exclusivo para a sua caixa de entrada.")
            email_rec = st.text_input("E-mail Cadastrado", key="rec_email_input")
            
            if st.button("📤 Enviar Código de Verificação por E-mail", type="primary", use_container_width=True):
                if email_rec:
                    user = verificar_email_existe(email_rec)
                    if user:
                        codigo_secreto = ''.join(random.choices(string.digits, k=6))
                        st.session_state["email_recuperando"] = email_rec.lower().strip()
                        st.session_state["codigo_enviado"] = codigo_secreto
                        
                        sucesso_envio, erro_msg = enviar_email_real(email_rec, codigo_secreto)
                        
                        if sucesso_envio:
                            st.success(f"✅ Código de segurança enviado para **{email_rec}**. Verifique sua caixa de entrada e spam!")
                            st.session_state["etapa_recuperacao"] = 2
                            st.rerun()
                        else:
                            st.error(f"❌ Falha ao enviar o e-mail. Detalhe: {erro_msg}")
                    else:
                        st.error("❌ Este e-mail não está registado no sistema.")
                else:
                    st.warning("⚠️ Insira o seu e-mail.")

        elif st.session_state["etapa_recuperacao"] == 2:
            st.info(f"Um código de segurança foi enviado para **{st.session_state['email_recuperando']}**.")
            
            codigo_digitado = st.text_input("Digite o Código de 6 Dígitos recebido no E-mail:", max_chars=6, key="input_cod_rec")
            nova_senha1 = st.text_input("Digite a Nova Senha:", type="password", key="nova_s1")
            nova_senha2 = st.text_input("Confirme a Nova Senha:", type="password", key="nova_s2")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("🔒 Redefinir Senha", type="primary", use_container_width=True):
                    if codigo_digitado.strip() == st.session_state["codigo_enviado"]:
                        if nova_senha1 and nova_senha1 == nova_senha2:
                            if len(nova_senha1) >= 4:
                                ok, mensagem = atualizar_senha(st.session_state["email_recuperando"], nova_senha1)
                                if ok:
                                    st.success(mensagem)
                                    st.session_state["etapa_recuperacao"] = 1
                                    st.session_state["email_recuperando"] = ""
                                    st.session_state["codigo_enviado"] = ""
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                            else:
                                st.warning("⚠️ A senha deve conter pelo menos 4 caracteres.")
                        else:
                            st.error("❌ As senhas não coincidem ou estão vazias.")
                    else:
                        st.error("❌ Código de verificação incorreto.")
            
            with col_b2:
                if st.button("Voltar / Reenviar", use_container_width=True):
                    st.session_state["etapa_recuperacao"] = 1
                    st.rerun()

    st.stop()

# =========================================================
# SISTEMA PRINCIPAL (APÓS LOGIN BEM-SUCEDIDO)
# =========================================================
user_id_atual = st.session_state["usuario_logado"]["id"]
nome_utilizador = st.session_state["usuario_logado"]["nome"]

st.markdown("""
<style>
    @media (max-width: 768px) {
        .main-title { font-size: 20px !important; }
        .kpi-value { font-size: 18px !important; }
        .kpi-title { font-size: 11px !important; }
    }
    
    .header-banner {
        background: linear-gradient(135deg, #0f4c81 0%, #1e88e5 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .kpi-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        text-align: center;
        border-top: 5px solid #6c757d;
    }
    .kpi-title { font-size: 12px; color: #555; font-weight: 600; }
    .kpi-value { font-size: 22px; font-weight: bold; }
    .kpi-sub { font-size: 10px; color: #777; }
    
    .card-blue { border-top-color: #1E88E5 !important; }
    .card-green { border-top-color: #2E7D32 !important; }
    .card-yellow { border-top-color: #F57F17 !important; }
    .card-red { border-top-color: #C62828 !important; }
</style>
""", unsafe_allow_html=True)

col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.markdown(f"""
    <div class="header-banner">
        <h1 class="main-title">🧪 Calculadora & Gestão Operacional ETE</h1>
        <p style="margin:0; font-size:13px;">PAINEL EXCLUSIVO: {nome_utilizador.upper()}</p>
    </div>
    """, unsafe_allow_html=True)

with col_head2:
    if st.button("🚪 Sair / Logout", use_container_width=True):
        st.session_state["usuario_logado"] = None
        st.rerun()

st.subheader("📅 Data do Lançamento Operacional")
data_lancamento = st.date_input("Selecione a Data das Análises:", value=date.today())

st.markdown("---")

st.header("💧 1. Vazões Diárias (m³/dia)")

col_v1, col_v2 = st.columns(2)
with col_v1:
    vazao_sanitario = st.number_input("🚿 Vazão Efluente Sanitário", min_value=0.0, value=87.14, step=5.0)
    vazao_ind_bruto = st.number_input("🏭 Vazão Ind. Bruto", min_value=0.0, value=371.57, step=5.0)

with col_v2:
    vazao_ind_tratado = st.number_input("⚙️ Vazão Ind. Tratado", min_value=0.0, value=320.0, step=5.0)
    vazao_permeado = st.number_input("🌊 Vazão Permeado (Saída)", min_value=0.0, value=479.0, step=5.0)

st.markdown("---")

st.header("🧪 2. Análises Físico-Químicas (mg/L)")

tab_dqo, tab_dbo, tab_nutrientes, tab_og, tab_ph = st.tabs([
    "🧪 DQO", "🧫 DBO", "🌱 Nutrientes", "🛢️ O&G", "
