import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
import sqlite3
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
# BANCO DE DADOS E AUTENTICAÇÃO (SISTEMA MULTI-USUÁRIO)
# =========================================================
DB_NAME = "ete_database.db"

def init_db():
    """Inicializa as tabelas de usuários e lançamentos operacionais no banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de Usuários (Contas individuais)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de Lançamentos Operacionais (Vinculados por usuario_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def hash_senha(senha):
    """Gera um Hash seguro para a senha."""
    return hashlib.sha256(senha.encode()).hexdigest()

def cadastrar_usuario(nome, email, senha):
    """Cadastra um novo usuário de forma única no banco de dados."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
            (nome, email.lower().strip(), hash_senha(senha))
        )
        conn.commit()
        conn.close()
        return True, "✅ Conta criada com sucesso! Faça login para acessar o sistema."
    except sqlite3.IntegrityError:
        return False, "⚠️ Este e-mail já está cadastrado no sistema."
    except Exception as e:
        return False, f"❌ Erro ao cadastrar: {str(e)}"

def autenticar_usuario(email, senha):
    """Valida o e-mail e a senha do usuário."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, email FROM usuarios WHERE email = ? AND senha_hash = ?",
        (email.lower().strip(), hash_senha(senha))
    )
    user = cursor.fetchone()
    conn.close()
    return user

def verificar_email_existe(email):
    """Verifica se o e-mail existe no banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM usuarios WHERE email = ?", (email.lower().strip(),))
    user = cursor.fetchone()
    conn.close()
    return user

def atualizar_senha(email, nova_senha):
    """Atualiza a senha do usuário no banco de dados."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET senha_hash = ? WHERE email = ?",
            (hash_senha(nova_senha), email.lower().strip())
        )
        conn.commit()
        conn.close()
        return True, "✅ Senha alterada com sucesso! Faça login com a nova senha."
    except Exception as e:
        return False, f"❌ Erro ao atualizar senha: {str(e)}"

def enviar_email_real(email_destino, codigo_verificacao):
    """Envia o e-mail real com o código usando os dados SMTP configurados."""
    try:
        # Lê as credenciais seguras configuradas no Streamlit Secrets (.streamlit/secrets.toml)
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

# Gerenciamento do estado da sessão do usuário
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "etapa_recuperacao" not in st.session_state:
    st.session_state["etapa_recuperacao"] = 1  # 1: Digitar email, 2: Digitar código e nova senha

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
            user = autenticar_usuario(email_login, senha_login)
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
                sucesso, msg = cadastrar_usuario(nome_reg, email_reg, senha_reg)
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
                        # Gera um código aleatório de 6 dígitos
                        codigo_secreto = ''.join(random.choices(string.digits, k=6))
                        st.session_state["email_recuperando"] = email_rec.lower().strip()
                        st.session_state["codigo_enviado"] = codigo_secreto
                        
                        # Dispara o e-mail real
                        sucesso_envio, erro_msg = enviar_email_real(email_rec, codigo_secreto)
                        
                        if sucesso_envio:
                            st.success(f"✅ Código de segurança enviado para **{email_rec}**. Verifique sua caixa de entrada e spam!")
                            st.session_state["etapa_recuperacao"] = 2
                            st.rerun()
                        else:
                            st.error(f"❌ Falha ao enviar o e-mail. Verifique se as configurações de SMTP estão ativas no servidor. Detalhe: {erro_msg}")
                    else:
                        st.error("❌ Este e-mail não está registado no sistema.")
                else:
                    st.warning("⚠️ Insira o seu e-mail.")

        elif st.session_state["etapa_recuperacao"] == 2:
            st.info(പരമായ(f"Um código de segurança foi enviado para **{st.session_state['email_recuperando']}**."))
            
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
                                    # Reseta o fluxo
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
                        st.error("❌ Código de verificação incorreto. Verifique o código enviado para o seu e-mail.")
            
            with col_b2:
                if st.button("Voltar / Reenviar", use_container_width=True):
                    st.session_state["etapa_recuperacao"] = 1
                    st.rerun()

    st.stop()  # Interrompe o script para quem não está logado

# =========================================================
# SISTEMA PRINCIPAL (APÓS LOGIN BEM-SUCEDIDO)
# =========================================================
user_id_atual = st.session_state["usuario_logado"]["id"]
nome_usuario = st.session_state["usuario_logado"]["nome"]

# Estilo CSS Personalizado
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

# CABEÇALHO PROFISSIONAL COM BOTÃO DE LOGOUT
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.markdown(f"""
    <div class="header-banner">
        <h1 class="main-title">🧪 Calculadora & Gestão Operacional ETE</h1>
        <p style="margin:0; font-size:13px;">PAINEL EXCLUSIVO: {nome_usuario.upper()}</p>
    </div>
    """, unsafe_allow_html=True)

with col_head2:
    if st.button("🚪 Sair / Logout", use_container_width=True):
        st.session_state["usuario_logado"] = None
        st.rerun()

# ---------------------------------------------------------
# DATA DE LANÇAMENTO
# ---------------------------------------------------------
st.subheader("📅 Data do Lançamento Operacional")
data_lancamento = st.date_input("Selecione a Data das Análises:", value=date.today())

st.markdown("---")

# ---------------------------------------------------------
# 1. ENTRADA DE DADOS: VAZÕES DIÁRIAS
# ---------------------------------------------------------
st.header("💧 1. Vazões Diárias (m³/dia)")

col_v1, col_v2 = st.columns(2)
with col_v1:
    vazao_sanitario = st.number_input("🚿 Vazão Efluente Sanitário", min_value=0.0, value=87.14, step=5.0)
    vazao_ind_bruto = st.number_input("🏭 Vazão Ind. Bruto", min_value=0.0, value=371.57, step=5.0)

with col_v2:
    vazao_ind_tratado = st.number_input("⚙️ Vazão Ind. Tratado", min_value=0.0, value=320.0, step=5.0)
    vazao_permeado = st.number_input("🌊 Vazão Permeado (Saída)", min_value=0.0, value=479.0, step=5.0)

st.markdown("---")

# ---------------------------------------------------------
# 2. ENTRADA DE DADOS: PARÂMETROS FÍSICO-QUÍMICOS
# ---------------------------------------------------------
st.header("🧪 2. Análises Físico-Químicas (mg/L)")

tab_dqo, tab_dbo, tab_nutrientes, tab_og, tab_ph = st.tabs([
    "🧪 DQO", "🧫 DBO", "🌱 Nutrientes", "🛢️ O&G", "⚗️ pH"
])

with tab_dqo:
    col1, col2 = st.columns(2)
    dqo_sanitario = col1.number_input("DQO Sanitário", min_value=0.0, value=1209.0, key="dqo_s")
    dqo_ind_bruto = col1.number_input("DQO Ind. Bruto", min_value=0.0, value=6980.0, key="dqo_b")
    dqo_ind_tratado = col2.number_input("DQO Ind. Tratado", min_value=0.0, value=1391.0, key="dqo_t")
    dqo_permeado = col2.number_input("DQO Permeado (Saída)", min_value=0.0, value=73.5, key="dqo_p")

with tab_dbo:
    col1, col2 = st.columns(2)
    dbo_sanitario = col1.number_input("DBO Sanitário", min_value=0.0, value=650.0, key="dbo_s")
    dbo_ind_bruto = col1.number_input("DBO Ind. Bruto", min_value=0.0, value=3100.0, key="dbo_b")
    dbo_ind_tratado = col2.number_input("DBO Ind. Tratado", min_value=0.0, value=700.0, key="dbo_t")
    dbo_permeado = col2.number_input("DBO Permeado (Saída)", min_value=0.0, value=32.0, key="dbo_p")

with tab_nutrientes:
    col1, col2 = st.columns(2)
    n_sanitario = col1.number_input("N Sanitário", min_value=0.0, value=93.1, key="n_s")
    n_ind_tratado = col1.number_input("N Ind. Tratado", min_value=0.0, value=13.07, key="n_t")
    n_permeado = col1.number_input("N Permeado (Saída)", min_value=0.0, value=10.5, key="n_p")
    
    p_sanitario = col2.number_input("P Sanitário", min_value=0.0, value=43.6, key="p_s")
    p_ind_tratado = col2.number_input("P Ind. Tratado", min_value=0.0, value=1.18, key="p_t")
    p_permeado = col2.number_input("P Permeado (Saída)", min_value=0.0, value=0.20, key="p_p")

with tab_og:
    col1, col2 = st.columns(2)
    og_sanitario = col1.number_input("O&G Sanitário", min_value=0.0, value=155.2, key="og_s")
    og_ind_bruto = col1.number_input("O&G Ind. Bruto", min_value=0.0, value=2192.4, key="og_b")
    og_ind_tratado = col2.number_input("O&G Ind. Tratado", min_value=0.0, value=283.8, key="og_t")
    og_permeado = col2.number_input("O&G Permeado (Saída)", min_value=0.0, value=49.4, key="og_p")

with tab_ph:
    col1, col2 = st.columns(2)
    ph_sanitario = col1.number_input("pH Sanitário", min_value=0.0, max_value=14.0, value=7.6, key="ph_s")
    ph_ind_bruto = col1.number_input("pH Ind. Bruto", min_value=0.0, max_value=14.0, value=9.7, key="ph_b")
    ph_ind_tratado = col2.number_input("pH Ind. Tratado", min_value=0.0, max_value=14.0, value=7.62, key="ph_t")
    ph_permeado = col2.number_input("pH Permeado (Saída)", min_value=0.0, max_value=14.0, value=7.63, key="ph_p")

st.markdown("---")

# ---------------------------------------------------------
# CÁLCULOS OPERACIONAIS
# ---------------------------------------------------------
carga_dbo_sanitario = (vazao_sanitario * dbo_sanitario) / 1000
carga_dbo_ind_tratado = (vazao_ind_tratado * dbo_ind_tratado) / 1000
carga_dbo_total_entrada = carga_dbo_sanitario + carga_dbo_ind_tratado

carga_n_real = ((vazao_sanitario * n_sanitario) + (vazao_ind_tratado * n_ind_tratado)) / 1000
carga_p_real = ((vazao_sanitario * p_sanitario) + (vazao_ind_tratado * p_ind_tratado)) / 1000

carga_n_esperada = carga_dbo_total_entrada * 0.05
carga_p_esperada = carga_dbo_total_entrada * 0.01

desvio_n_kg = carga_n_real - carga_n_esperada
desvio_p_kg = carga_p_real - carga_p_esperada

def calcular_eficiencia(entrada, saida):
    return max(0.0, ((entrada - saida) / entrada) * 100) if entrada > 0 else 0.0

m_dqo_in = (dqo_sanitario * vazao_sanitario) + (dqo_ind_bruto * vazao_ind_bruto)
m_dqo_out = dqo_permeado * vazao_permeado
efic_dqo = calcular_eficiencia(m_dqo_in, m_dqo_out)

m_dbo_in = (dbo_sanitario * vazao_sanitario) + (dbo_ind_bruto * vazao_ind_bruto)
m_dbo_out = dbo_permeado * vazao_permeado
efic_dbo = calcular_eficiencia(m_dbo_in, m_dbo_out)

m_og_in = (og_sanitario * vazao_sanitario) + (og_ind_bruto * vazao_ind_bruto)
m_og_out = og_permeado * vazao_permeado
efic_og = calcular_eficiencia(m_og_in, m_og_out)

m_n_in = (n_sanitario * vazao_sanitario) + (n_ind_tratado * vazao_ind_tratado)
m_n_out = n_permeado * vazao_permeado
efic_n = calcular_eficiencia(m_n_in, m_n_out)

m_p_in = (p_sanitario * vazao_sanitario) + (p_ind_tratado * vazao_ind_tratado)
m_p_out = p_permeado * vazao_permeado
efic_p = calcular_eficiencia(m_p_in, m_p_out)

def get_color_class(valor):
    if valor >= 80: return "card-green", "#2E7D32"
    elif valor >= 50: return "card-yellow", "#F57F17"
    else: return "card-red", "#C62828"

# ---------------------------------------------------------
# RESULTADOS DA TELA
# ---------------------------------------------------------
st.header("📊 Balanço Nutricional do Reator")
col_res1, col_res2 = st.columns(2)

with col_res1:
    st.subheader("🔵 Nitrogênio (N)")
    st.metric("Carga Real Entrando", f"{carga_n_real:.2f} kg/dia")
    st.metric("Carga Esperada", f"{carga_n_esperada:.2f} kg/dia")
    if desvio_n_kg < 0:
        st.error(f"⚠️ Dosar **{abs(desvio_n_kg):.2f} kg/dia** de N")
    else:
        st.success(f"✅ Excesso: +{desvio_n_kg:.2f} kg/dia de N")

with col_res2:
    st.subheader("🟢 Fósforo (P)")
    st.metric("Carga Real Entrando", f"{carga_p_real:.2f} kg/dia")
    st.metric("Carga Esperada", f"{carga_p_esperada:.2f} kg/dia")
    if desvio_p_kg < 0:
        st.error(f"⚠️ Dosar **{abs(desvio_p_kg):.2f} kg/dia** de P")
    else:
        st.success(f"✅ Excesso: +{desvio_p_kg:.2f} kg/dia de P")

st.markdown("---")

st.header("📈 Eficiência Global de Remoção")
c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,1,1,1])

with c1:
    st.markdown(f'<div class="kpi-card card-blue"><div class="kpi-title">Carga DBO Entrada</div><div class="kpi-value" style="color:#1E88E5;">{carga_dbo_total_entrada:.1f}</div><div class="kpi-sub">kg/dia</div></div>', unsafe_allow_html=True)

for col, titulo, val in [(c2, "Rem. DQO", efic_dqo), (c3, "Rem. DBO", efic_dbo), (c4, "Rem. O&G", efic_og), (c5, "Rem. N", efic_n), (c6, "Rem. P", efic_p)]:
    card_class, color_hex = get_color_class(val)
    with col:
        st.markdown(f'<div class="kpi-card {card_class}"><div class="kpi-title">{titulo}</div><div class="kpi-value" style="color:{color_hex};">{val:.1f}%</div><div class="kpi-sub">eficiência</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# GRAVAÇÃO PERMANENTE NO BANCO DE DADOS DA CONTA LOGADA
# ---------------------------------------------------------
st.header("💾 Salvar Lançamento & Extrair Relatórios")

if st.button("💾 Gravar Lançamento Permanente no Servidor", type="primary", use_container_width=True):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lancamentos (
            usuario_id, data, dbo_permeado, dbo_limite, dqo_permeado, dqo_limite,
            og_permeado, og_limite, n_permeado, n_limite, p_permeado, p_limite,
            vazao_sanitario, vazao_ind_bruto, vazao_ind_tratado, vazao_permeado,
            carga_dbo_entrada, rem_dqo, rem_dbo, rem_og, rem_n, rem_p,
            balanco_n, balanco_p
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id_atual, data_lancamento.strftime("%Y-%m-%d"),
        round(float(dbo_permeado), 2), 60.00,
        round(float(dqo_permeado), 2), 120.00,
        round(float(og_permeado), 2), 50.00,
        round(float(n_permeado), 2), 20.00,
        round(float(p_permeado), 2), 5.00,
        round(float(vazao_sanitario), 2), round(float(vazao_ind_bruto), 2),
        round(float(vazao_ind_tratado), 2), round(float(vazao_permeado), 2),
        round(float(carga_dbo_total_entrada), 2), round(float(efic_dqo), 2),
        round(float(efic_dbo), 2), round(float(efic_og), 2),
        round(float(efic_n), 2), round(float(efic_p), 2),
        round(float(desvio_n_kg), 2), round(float(desvio_p_kg), 2)
    ))
    conn.commit()
    conn.close()
    st.success(f"✅ Lançamento do dia {data_lancamento.strftime('%d/%m/%Y')} gravado permanentemente na sua conta!")

# ---------------------------------------------------------
# CARREGAR DADOS HISTÓRICOS APENAS DO USUÁRIO LOGADO
# ---------------------------------------------------------
conn = sqlite3.connect(DB_NAME)
query = """
    SELECT 
        data AS "Data",
        dbo_permeado AS "DBO Permeado (mg/L)", dbo_limite AS "DBO Limite (mg/L)",
        dqo_permeado AS "DQO Permeado (mg/L)", dqo_limite AS "DQO Limite (mg/L)",
        og_permeado AS "O&G Permeado (mg/L)", og_limite AS "O&G Limite (mg/L)",
        n_permeado AS "N Permeado (mg/L)", n_limite AS "N Limite (mg/L)",
        p_permeado AS "P Permeado (mg/L)", p_limite AS "P Limite (mg/L)",
        vazao_sanitario AS "Vazão Sanitário (m³/dia)", vazao_ind_bruto AS "Vazão Ind. Bruto (m³/dia)",
        vazao_ind_tratado AS "Vazão Ind. Tratado (m³/dia)", vazao_permeado AS "Vazão Permeado (m³/dia)",
        carga_dbo_entrada AS "Carga DBO Entrada (kg/dia)", rem_dqo AS "Remoção DQO (%)",
        rem_dbo AS "Remoção DBO (%)", rem_og AS "Remoção O&G (%)", rem_n AS "Remoção N (%)",
        rem_p AS "Remoção P (%)", balanco_n AS "Balanço N (kg/dia)", balanco_p AS "Balanço P (kg/dia)"
    FROM lancamentos 
    WHERE usuario_id = ?
    ORDER BY date(data) ASC
"""
df_historico = pd.read_sql_query(query, conn, params=(user_id_atual,))
conn.close()

if not df_historico.empty:
    st.subheader("📋 Histórico Permanente de Lançamentos do Usuário")
    
    # Converte 'Data' para Texto Formatado (DD/MM/YYYY)
    df_historico['Data_Dt'] = pd.to_datetime(df_historico['Data'])
    df_historico['Data'] = df_historico['Data_Dt'].dt.strftime('%d/%m/%Y')
    df_excel = df_historico.drop(columns=['Data_Dt'])

    df_exibicao = df_excel.tail(5).copy()

    # Função para destacar limites
    def destacar_limites_streamlit(df):
        style_df = pd.DataFrame('', index=df.index, columns=df.columns)
        pares_parametros = [
            ("DBO Permeado (mg/L)", "DBO Limite (mg/L)"),
            ("DQO Permeado (mg/L)", "DQO Limite (mg/L)"),
            ("O&G Permeado (mg/L)", "O&G Limite (mg/L)"),
            ("N Permeado (mg/L)", "N Limite (mg/L)"),
            ("P Permeado (mg/L)", "P Limite (mg/L)")
        ]
        for col_perm, col_lim in pares_parametros:
            if col_perm in df.columns and col_lim in df.columns:
                abaixo_ou_igual = df[col_perm] <= df[col_lim]
                style_df.loc[abaixo_ou_igual, col_perm] = 'background-color: #C6EFCE; color: #006100; font-weight: bold;'
                style_df.loc[~abaixo_ou_igual, col_perm] = 'background-color: #FFC7CE; color: #9C0006; font-weight: bold;'
        return style_df

    cols_numericas = [c for c in df_exibicao.columns if c != "Data"]
    st.dataframe(
        df_exibicao.style.apply(destacar_limites_streamlit, axis=None).format("{:.2f}", subset=cols_numericas),
        use_container_width=True,
        height=210
    )

    # GERAÇÃO DO EXCEL
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Relatório ETE')
        
        wb = writer.book
        ws = writer.sheets['Relatório ETE']
        max_linha = len(df_excel) + 1
        
        for cell in ws['A'][1:]:
            cell.number_format = '@'
            
        for row in ws.iter_rows(min_row=2, max_row=max_linha, min_col=2, max_col=ws.max_column):
            for cell in row:
                if isinstance(cell.value, (int, float)):
                    cell.number_format = '0.00'

        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        green_font = Font(color="006100", bold=True)
        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        red_font = Font(color="9C0006", bold=True)

        mapeamento_colunas_excel = [("B", "C"), ("D", "E"), ("F", "G"), ("H", "I"), ("J", "K")]

        for col_perm, col_lim in mapeamento_colunas_excel:
            intervalo = f"{col_perm}2:{col_perm}{max_linha}"
            regra_verde = FormulaRule(formula=[f"{col_perm}2<={col_lim}2"], stopIfTrue=True, fill=green_fill, font=green_font)
            regra_vermelha = FormulaRule(formula=[f"{col_perm}2>{col_lim}2"], stopIfTrue=True, fill=red_fill, font=red_font)
            ws.conditional_formatting.add(intervalo, regra_verde)
            ws.conditional_formatting.add(intervalo, regra_vermelha)

        if len(df_excel) >= 5:
            cats = Reference(ws, min_col=1, min_row=2, max_row=max_linha)
            graficos_config = [
                ("Acompanhamento DBO (Saída)", 2, 3, "W2"),
                ("Acompanhamento DQO (Saída)", 4, 5, "W18"),
                ("Acompanhamento O&G (Saída)", 6, 7, "W34"),
                ("Acompanhamento Nitrogênio - N (Saída)", 8, 9, "AF2"),
                ("Acompanhamento Fósforo - P (Saída)", 10, 11, "AF18")
            ]
            
            for titulo, col_real, col_limite, celula_excel in graficos_config:
                bar = BarChart()
                bar.title = titulo
                bar.style = 10
                bar.y_axis.title = "Concentração (mg/L)"
                bar.x_axis.title = "Data"
                bar.width = 15
                bar.height = 9
                
                bar.dataLabels = DataLabelList()
                bar.dataLabels.showVal = True
                bar.dataLabels.showSerName = False
                bar.dataLabels.showCatName = False
                bar.dataLabels.position = "ctr"
                
                dados_bar = Reference(ws, min_col=col_real, min_row=1, max_row=max_linha)
                bar.add_data(dados_bar, titles_from_data=True)
                bar.set_categories(cats)
                
                line = LineChart()
                dados_line = Reference(ws, min_col=col_limite, min_row=1, max_row=max_linha)
                line.add_data(dados_line, titles_from_data=True)
                line.set_categories(cats)
                
                bar += line
                ws.add_chart(bar, celula_excel)

    excel_data = output.getvalue()

    col_down1, col_down2 = st.columns(2)
    with col_down1:
        st.download_button(
            label="📥 Descarregar Relatório Completo em Excel (.xlsx)",
            data=excel_data,
            file_name=f"Relatorio_Auditoria_ETE_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_down2:
        csv_data = df_excel.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descarregar Relatório em CSV",
            data=csv_data,
            file_name=f"Relatorio_Auditoria_ETE_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
else:
    st.info("Nenhum lançamento gravado até o momento. Preencha os dados e clique em 'Gravar Lançamento Permanente'.")
