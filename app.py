import streamlit as st

# Configuração da página e Título Curto da Aba do Navegador
st.set_page_config(
    page_title="Calculadora ETE | Eficiência & Nutrientes",
    page_icon="🧪",
    layout="wide"
)
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Calculadora ETE | Eficiência & Nutrientes",
    page_icon="🧪",
    layout="wide"
)

# =========================================================
# SISTEMA DE PROTEÇÃO POR SENHA (HOTMART)
# =================================----------------========
SENHA_CORRETA = "ETECONTROLE"  # <- Altere aqui para a senha que desejar

def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        st.title("🔒 Acesso Restrito aos Alunos")
        st.write("Por favor, insira a senha fornecida na sua área de membros da Hotmart para liberar a calculadora.")
        
        senha_digitada = st.text_input("Senha de Acesso", type="password")
        
        if st.button("Entrar"):
            if senha_digitada == SENHA_CORRETA:
                st.session_state["autenticado"] = True
                st.rerun()  # Recarrega a página autenticado
            else:
                st.error("❌ Senha incorreta. Verifique a senha informada no curso da Hotmart.")
        return False
    return True

# Se a senha não estiver correta, interrompe a execução do resto do app
if not verificar_senha():
    st.stop()

# =========================================================
# RESTANTE DO SEU CÓDIGO (Só roda se a senha estiver correta)
# =========================================================
# (O banner, as vazões, análises e eficiências continuam aqui...)

# Estilo CSS Personalizado Profissional
st.markdown("""
<style>
    /* Banner do Cabeçalho Principal */
    .header-banner {
        background: linear-gradient(135deg, #0f4c81 0%, #1e88e5 100%);
        padding: 25px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .header-banner h1 {
        color: #ffffff !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        margin-bottom: 8px !important;
    }
    .header-banner p {
        color: #e0f2fe !important;
        font-size: 15px !important;
        margin-bottom: 0px !important;
    }

    /* Cartões KPI para os resultados de eficiência */
    .kpi-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        text-align: center;
        border-top: 5px solid #6c757d;
    }
    .kpi-title {
        font-size: 13px;
        color: #555555;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 2px;
    }
    .kpi-sub {
        font-size: 11px;
        color: #777777;
    }
    
    /* Cores de borda para os cartões */
    .card-blue { border-top-color: #1E88E5 !important; }
    .card-green { border-top-color: #2E7D32 !important; }
    .card-yellow { border-top-color: #F57F17 !important; }
    .card-red { border-top-color: #C62828 !important; }
</style>
""", unsafe_allow_html=True)

# CABEÇALHO PROFISSIONAL
st.markdown("""
<div class="header-banner">
    <h1>🧪 Calculadora de Eficiência & Balanço de Nutrientes em ETE</h1>
    <p>SISTEMA OPERACIONAL DE APOIO AO TRATAMENTO DE EFLUENTES</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. ENTRADA DE DADOS: VAZÕES DIÁRIAS
# ---------------------------------------------------------
st.header("💧 1. Vazões Diárias (m³/dia)")

with st.container():
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.subheader("📥 Entrada (Efluentes Brutos / Processo)")
        vazao_sanitario = st.number_input("🚿 Vazão Efluente Sanitário (m³/dia)", min_value=0.0, value=87.14, step=10.0, help="Vazão diária proveniente do esgoto sanitário")
        vazao_ind_bruto = st.number_input("🏭 Vazão Ind. Bruto (m³/dia)", min_value=0.0, value=371.57, step=10.0, help="Vazão industrial bruta antes do pré-tratamento")

    with col_v2:
        st.subheader("🔄 Intermediário & Saída")
        vazao_ind_tratado = st.number_input("⚙️ Vazão Ind. Tratado (m³/dia)", min_value=0.0, value=320.0, step=10.0, help="Vazão industrial encaminhada ao reator biológico após pré-tratamento")
        vazao_permeado = st.number_input("🌊 Vazão Permeado / Saída Final (m³/dia)", min_value=0.0, value=479.0, step=10.0, help="Vazão total do efluente tratado final (saída)")

vazao_entrada_total = vazao_sanitario + vazao_ind_tratado

st.markdown("---")

# ---------------------------------------------------------
# 2. ENTRADA DE DADOS: ANÁLISES FÍSICO-QUÍMICAS
# ---------------------------------------------------------
st.header("🧪 2. Análises Físico-Químicas (mg/L)")

tab_dqo, tab_dbo, tab_nutrientes, tab_og, tab_ph = st.tabs([
    "🧪 DQO", 
    "🧫 DBO", 
    "🌱 Nutrientes (N e P)", 
    "🛢️ Óleos e Graxas (O&G)", 
    "⚗️ pH"
])

# ----- ABA DQO -----
with tab_dqo:
    st.caption("Insira as concentrações de Demanda Química de Oxigênio (DQO) em mg/L:")
    col_dqo1, col_dqo2 = st.columns(2)
    with col_dqo1:
        dqo_sanitario = st.number_input("DQO Sanitário (mg/L)", min_value=0.0, value=1209.0, key="dqo_san")
        dqo_ind_bruto = st.number_input("DQO Ind. Bruto (mg/L)", min_value=0.0, value=6980.0, key="dqo_bruto")
    with col_dqo2:
        dqo_ind_tratado = st.number_input("DQO Ind. Tratado (mg/L)", min_value=0.0, value=1391.0, key="dqo_trat")
        dqo_permeado = st.number_input("DQO Permeado / Efluente Final (mg/L)", min_value=0.0, value=73.5, key="dqo_perm")

# ----- ABA DBO -----
with tab_dbo:
    st.caption("Insira as concentrações de Demanda Bioquímica de Oxigênio (DBO) em mg/L:")
    col_dbo1, col_dbo2 = st.columns(2)
    with col_dbo1:
        dbo_sanitario = st.number_input("DBO Sanitário (mg/L)", min_value=0.0, value=650.0, key="dbo_san")
        dbo_ind_bruto = st.number_input("DBO Ind. Bruto (mg/L)", min_value=0.0, value=3100.0, key="dbo_bruto")
    with col_dbo2:
        dbo_ind_tratado = st.number_input("DBO Ind. Tratado (mg/L)", min_value=0.0, value=700.0, key="dbo_trat")
        dbo_permeado = st.number_input("DBO Permeado / Efluente Final (mg/L)", min_value=0.0, value=32.0, key="dbo_perm")

# ----- ABA NUTRIENTES -----
with tab_nutrientes:
    col_n, col_p = st.columns(2)
    
    with col_n:
        st.subheader("🔵 Nitrogênio Total (N)")
        n_sanitario = st.number_input("N Sanitário (mg/L)", min_value=0.0, value=93.1, key="n_san")
        n_ind_tratado = st.number_input("N Ind. Tratado (mg/L)", min_value=0.0, value=13.07, key="n_trat")
        n_permeado = st.number_input("N Permeado / Efluente Final (mg/L)", min_value=0.0, value=10.5, key="n_perm")

    with col_p:
        st.subheader("🟢 Fósforo Total (P)")
        p_sanitario = st.number_input("P Sanitário (mg/L)", min_value=0.0, value=43.6, key="p_san")
        p_ind_tratado = st.number_input("P Ind. Tratado (mg/L)", min_value=0.0, value=1.18, key="p_trat")
        p_permeado = st.number_input("P Permeado / Efluente Final (mg/L)", min_value=0.0, value=0.20, key="p_perm")

# ----- ABA O&G -----
with tab_og:
    st.caption("Insira as concentrações de Óleos e Graxas (O&G) em mg/L:")
    col_og1, col_og2 = st.columns(2)
    with col_og1:
        og_sanitario = st.number_input("O&G Sanitário (mg/L)", min_value=0.0, value=155.2, key="og_san")
        og_ind_bruto = st.number_input("O&G Ind. Bruto (mg/L)", min_value=0.0, value=2192.4, key="og_bruto")
    with col_og2:
        og_ind_tratado = st.number_input("O&G Ind. Tratado (mg/L)", min_value=0.0, value=283.8, key="og_trat")
        og_permeado = st.number_input("O&G Permeado / Efluente Final (mg/L)", min_value=0.0, value=49.4, key="og_perm")

# ----- ABA pH -----
with tab_ph:
    st.caption("Medições de pH ao longo do processo:")
    col_ph1, col_ph2 = st.columns(2)
    with col_ph1:
        ph_sanitario = st.number_input("pH Sanitário", min_value=0.0, max_value=14.0, value=7.6, key="ph_san")
        ph_ind_bruto = st.number_input("pH Ind. Bruto", min_value=0.0, max_value=14.0, value=9.7, key="ph_bruto")
    with col_ph2:
        ph_ind_tratado = st.number_input("pH Ind. Tratado", min_value=0.0, max_value=14.0, value=7.62, key="ph_trat")
        ph_permeado = st.number_input("pH Permeado", min_value=0.0, max_value=14.0, value=7.63, key="ph_perm")

st.markdown("---")

# ---------------------------------------------------------
# 3. CÁLCULOS MATEMÁTICOS E BALANÇO OPERACIONAL
# ---------------------------------------------------------
# Carga de DBO na entrada (Sanitário + Ind. Tratado em kg/dia)
carga_dbo_sanitario = (vazao_sanitario * dbo_sanitario) / 1000
carga_dbo_ind_tratado = (vazao_ind_tratado * dbo_ind_tratado) / 1000
carga_dbo_total_entrada = carga_dbo_sanitario + carga_dbo_ind_tratado

# Cargas Reais de Nutrientes na Entrada (kg/dia)
carga_n_real = ((vazao_sanitario * n_sanitario) + (vazao_ind_tratado * n_ind_tratado)) / 1000
carga_p_real = ((vazao_sanitario * p_sanitario) + (vazao_ind_tratado * p_ind_tratado)) / 1000

# Cargas Esperadas (Proporção 100 DBO : 5 N : 1 P)
carga_n_esperada = carga_dbo_total_entrada * 0.05
carga_p_esperada = carga_dbo_total_entrada * 0.01

# Desvios de Nutrientes (kg/dia)
desvio_n_kg = carga_n_real - carga_n_esperada
desvio_p_kg = carga_p_real - carga_p_esperada

# EFICIÊNCIAS DE REMOÇÃO GLOBAL (%)
def calcular_eficiencia(entrada_massa, saida_massa):
    if entrada_massa <= 0:
        return 0.0
    ef = ((entrada_massa - saida_massa) / entrada_massa) * 100
    return max(0.0, ef)

# Cálculo em massa de entradas e saídas
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

# Função auxiliar para cor dos cartões com base na eficiência
def get_color_class(valor):
    if valor >= 80:
        return "card-green", "#2E7D32"
    elif valor >= 50:
        return "card-yellow", "#F57F17"
    else:
        return "card-red", "#C62828"

# ---------------------------------------------------------
# 4. EXIBIÇÃO DOS RESULTADOS
# ---------------------------------------------------------
st.header("📊 Balanço Nutricional do Reator")
st.info("💡 **Relação teórica padrão para tratamento biológico:** 100 DBO : 5 N : 1 P")

col_res1, col_res2 = st.columns(2)

with col_res1:
    st.subheader("🔵 Nitrogênio (N)")
    st.metric("Carga Real Entrando", f"{carga_n_real:.2f} kg/dia")
    st.metric("Carga Esperada", f"{carga_n_esperada:.2f} kg/dia")
    
    if desvio_n_kg < 0:
        st.error(f"⚠️ **Falta Nutriente:** Dosar **{abs(desvio_n_kg):.2f} kg/dia** de N")
    else:
        st.success(f"✅ **Excesso Nutricional:** +{desvio_n_kg:.2f} kg/dia de N")

with col_res2:
    st.subheader("🟢 Fósforo (P)")
    st.metric("Carga Real Entrando", f"{carga_p_real:.2f} kg/dia")
    st.metric("Carga Esperada", f"{carga_p_esperada:.2f} kg/dia")
    
    if desvio_p_kg < 0:
        st.error(f"⚠️ **Falta Nutriente:** Dosar **{abs(desvio_p_kg):.2f} kg/dia** de P")
    else:
        st.success(f"✅ **Excesso Nutricional:** +{desvio_p_kg:.2f} kg/dia de P")

st.markdown("---")

# PAINEL ILUSTRATIVO DE EFICIÊNCIA GLOBAL
st.header("📈 Eficiência Global de Remoção")

col_c1, col_c2, col_c3, col_c4, col_c5, col_c6 = st.columns(6)

with col_c1:
    st.markdown(f"""
    <div class="kpi-card card-blue">
        <div class="kpi-title">Carga DBO Entrada</div>
        <div class="kpi-value" style="color:#1E88E5;">{carga_dbo_total_entrada:.1f}</div>
        <div class="kpi-sub">kg/dia</div>
    </div>
    """, unsafe_allow_html=True)

for col, titulo, val in [
    (col_c2, "Remoção DQO", efic_dqo),
    (col_c3, "Remoção DBO", efic_dbo),
    (col_c4, "Remoção O&G", efic_og),
    (col_c5, "Remoção N", efic_n),
    (col_c6, "Remoção P", efic_p),
]:
    card_class, color_hex = get_color_class(val)
    with col:
        st.markdown(f"""
        <div class="kpi-card {card_class}">
            <div class="kpi-title">{titulo}</div>
            <div class="kpi-value" style="color:{color_hex};">{val:.2f}%</div>
            <div class="kpi-sub">eficiência</div>
        </div>
        """, unsafe_allow_html=True)