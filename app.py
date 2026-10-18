import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
import openpyxl
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import PatternFill, Font

# Configuração da página e Título do Navegador
st.set_page_config(
    page_title="Calculadora ETE | Eficiência & Nutrientes",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# SISTEMA DE PROTEÇÃO POR SENHA (HOTMART)
# =========================================================
SENHA_CORRETA = "ETECONTROLE"  # <- Senha fornecida aos alunos na Hotmart

def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        st.title("🔒 Acesso Restrito aos Alunos")
        st.write("Por favor, insira a senha fornecida na sua área de membros da Hotmart para liberar o aplicativo.")
        
        senha_digitada = st.text_input("Senha de Acesso", type="password")
        
        if st.button("Entrar", type="primary", use_container_width=True):
            if senha_digitada == SENHA_CORRETA:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta. Verifique a senha informada no curso da Hotmart.")
        return False
    return True

if not verificar_senha():
    st.stop()

# =========================================================
# APLICAÇÃO PRINCIPAL
# =========================================================

# Estilo CSS Personalizado Otimizado para Telemóveis (Android)
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

if "historico_lancamentos" not in st.session_state:
    st.session_state["historico_lancamentos"] = pd.DataFrame()

# CABEÇALHO PROFISSIONAL
st.markdown("""
<div class="header-banner">
    <h1 class="main-title">🧪 Calculadora & Gestão Operacional ETE</h1>
    <p style="margin:0; font-size:13px;">SISTEMA DE CONTROLO DE EFICIÊNCIA E BALANÇO DE NUTRIENTES</p>
</div>
""", unsafe_allow_html=True)

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
# BOTÃO DE SALVAR LANÇAMENTO E EXTRAIR EXCEL
# ---------------------------------------------------------
st.header("💾 Salvar Lançamento & Extrair Relatórios")

if st.button("💾 Guardar Lançamento na Base de Dados", type="primary", use_container_width=True):
    novo_registro = {
        "Data": data_lancamento,
        "DBO Permeado (mg/L)": dbo_permeado,
        "DBO Limite (mg/L)": 60.0,
        "DQO Permeado (mg/L)": dqo_permeado,
        "DQO Limite (mg/L)": 120.0,
        "O&G Permeado (mg/L)": og_permeado,
        "O&G Limite (mg/L)": 50.0,
        "N Permeado (mg/L)": n_permeado,
        "N Limite (mg/L)": 20.0,
        "P Permeado (mg/L)": p_permeado,
        "P Limite (mg/L)": 5.0,
        "Vazão Sanitário (m³/dia)": vazao_sanitario,
        "Vazão Ind. Bruto (m³/dia)": vazao_ind_bruto,
        "Vazão Ind. Tratado (m³/dia)": vazao_ind_tratado,
        "Vazão Permeado (m³/dia)": vazao_permeado,
        "Carga DBO Entrada (kg/dia)": round(carga_dbo_total_entrada, 2),
        "Remoção DQO (%)": round(efic_dqo, 2),
        "Remoção DBO (%)": round(efic_dbo, 2),
        "Remoção O&G (%)": round(efic_og, 2),
        "Remoção N (%)": round(efic_n, 2),
        "Remoção P (%)": round(efic_p, 2),
        "Balanço N (kg/dia)": round(desvio_n_kg, 2),
        "Balanço P (kg/dia)": round(desvio_p_kg, 2)
    }
    
    df_novo = pd.DataFrame([novo_registro])
    st.session_state["historico_lancamentos"] = pd.concat([st.session_state["historico_lancamentos"], df_novo], ignore_index=True)
    st.success(f"✅ Lançamento do dia {data_lancamento.strftime('%d/%m/%Y')} guardado com sucesso!")

df_historico = st.session_state["historico_lancamentos"].copy()

if not df_historico.empty:
    # 1. Ordenação cronológica real por data
    df_historico['Data_Dt'] = pd.to_datetime(df_historico['Data'])
    df_historico = df_historico.sort_values(by="Data_Dt", ascending=True)

    # 2. Converte a coluna 'Data' para Texto Formatado (DD/MM/YYYY)
    df_historico['Data'] = df_historico['Data_Dt'].dt.strftime('%d/%m/%Y')
    df_excel = df_historico.drop(columns=['Data_Dt'])

    st.subheader("📋 Histórico de Lançamentos Guardados")
    
    # Exibição dos 5 últimos lançamentos com Destaque de Cor na Tela
    df_exibicao = df_excel.tail(5).copy()

    # Função para destacar o Streamlit (Verde se <= Limite, Vermelho se > Limite)
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

    st.dataframe(df_exibicao.style.apply(destacar_limites_streamlit, axis=None), use_container_width=True, height=210)

    # GERAÇÃO DO EXCEL
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Relatório ETE')
        
        wb = writer.book
        ws = writer.sheets['Relatório ETE']
        max_linha = len(df_excel) + 1
        
        # Formatando as células da coluna Data como texto
        for cell in ws['A'][1:]:
            cell.number_format = '@'

        # Estilos de Formatação Condicional no Excel
        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        green_font = Font(color="006100", bold=True)
        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        red_font = Font(color="9C0006", bold=True)

        # Mapeamento de Colunas do Excel (Letra Permeado, Letra Limite)
        # B: DBO Perm, C: DBO Lim
        # D: DQO Perm, E: DQO Lim
        # F: O&G Perm, G: O&G Lim
        # H: N Perm, I: N Lim
        # J: P Perm, K: P Lim
        mapeamento_colunas_excel = [
            ("B", "C"),
            ("D", "E"),
            ("F", "G"),
            ("H", "I"),
            ("J", "K")
        ]

        # Aplicar regras de formatação condicional dinâmicas no Excel
        for col_perm, col_lim in mapeamento_colunas_excel:
            intervalo = f"{col_perm}2:{col_perm}{max_linha}"
            regra_verde = FormulaRule(formula=[f"{col_perm}2<={col_lim}2"], stopIfTrue=True, fill=green_fill, font=green_font)
            regra_vermelha = FormulaRule(formula=[f"{col_perm}2>{col_lim}2"], stopIfTrue=True, fill=red_fill, font=red_font)
            ws.conditional_formatting.add(intervalo, regra_verde)
            ws.conditional_formatting.add(intervalo, regra_vermelha)

        # Se houver 5 ou mais lançamentos, cria os gráficos
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
            label="📥 Descarregar Relatório em Excel (.xlsx)",
            data=excel_data,
            file_name=f"Relatorio_Operacional_ETE_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_down2:
        csv_data = df_excel.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descarregar Relatório em CSV",
            data=csv_data,
            file_name=f"Relatorio_Operacional_ETE_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
else:
    st.info("Nenhum lançamento guardado na sessão atual. Preencha os dados e clique em 'Guardar Lançamento'.")
