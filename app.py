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

# Configuração da página
st.set_page_config(
    page_title="Calculadora ETE | Gestão & Auditoria",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# BANCO DE DADOS SQLITE LOCAL (ZERO ERROS DE REDE)
# =========================================================
def get_db_connection():
    """Cria uma ligação local com o SQLite."""
    conn = sqlite3.connect("calculadora_ete.db", check_same_thread=False)
    return conn

def init_db():
    """Inicializa as tabelas de utilizadores e lançamentos operacionais."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de Utilizadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de Lançamentos Operacionais
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

init_db()
