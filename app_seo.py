import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import os

# --- SETUP DA PÁGINA ---
st.set_page_config(page_title="Auditor SEO FGV", layout="centered", page_icon="🔍")

# --- CSS PARA CENTRALIZAR E REDUZIR DESIGN ---
st.markdown("""
    <style>
    /* Centraliza tudo na tela */
    .block-container {
        padding-top: 2rem;
        max-width: 600px; /* Deixa o layout mais estreito e elegante */
    }
    /* Estiliza o título */
    h1 {
        text-align: center;
        color: #004685;
        font-size: 24px !important;
        margin-bottom: 0px;
    }
    /* Centraliza a logo */
    .stImage {
        display: flex;
        justify-content: center;
        margin-bottom: -10px;
    }
    /* Deixa o botão mais bonito */
    .stButton>button {
        width: 100%;
        background-color: #004685;
        color: white;
        border-radius: 5px;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO COM LOGO ---
if os.path.exists("fgv-logo-0.png"):
    st.image("fgv-logo-0.png", width=120) # Tamanho reduzido
else:
    st.markdown("<h2 style='text-align: center; color: #004685;'>FGV</h2>", unsafe_allow_html=True)

st.title("Auditor de Meta Tags")
st.markdown("<p style='text-align: center; font-size: 14px;'>Versão Cloud Protegida</p>", unsafe_allow_html=True)

# --- FUNÇÃO DO DRIVER (VERSÃO DIRETA - SEM BUG) ---
def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = "/usr/bin/chromium"
    
    # Usa o driver que o packages.txt instala no sistema
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

# --- INTERFACE ---
st.divider()
arquivo = st.file_uploader("📂 Suba sua lista de URLs (CSV ou TXT)", type=['csv', 'txt'])

if arquivo:
    if arquivo.name.endswith('.csv'):
        df_in = pd.read_csv(arquivo)
        lista_urls = df_in.iloc[:, 0].tolist()
    else:
        lista_urls = arquivo.read().decode().splitlines()

    st.write(f"📍 **{len(lista_urls)}** URLs carregadas.")

    if st.button("🚀 INICIAR AUDITORIA"):
        resultados = []
        try:
            with st.spinner("🤖 Iniciando Navegador..."):
                driver = iniciar_driver()
            
            progresso = st.progress(0)
            status_txt = st.empty()

            for idx, url in enumerate(lista_urls):
                url = url.strip()
                if not url: continue
                if not url.startswith('http'): url = f"https://{url}"
                
                status_txt.markdown(f"🔍 Analisando: `{url}`")
                
                try:
                    driver.get(url)
                    time.sleep(2)
                    try:
                        meta = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
                        status = "✅ OK"
                    except:
                        meta = "Não encontrada"
                        status = "❌ Sem Tag"
                    resultados.append({"URL": url, "Status": status, "Descrição": meta})
                except:
                    resultados.append({"URL": url, "Status": "⚠️ Erro", "Descrição": "Falha de conexão"})
                
                progresso.progress((idx + 1) / len(lista_urls))
            
            driver.quit()
            
            # Exibição compacta
            df_res = pd.DataFrame(resultados)
            st.success("Concluído!")
            st.dataframe(df_res, use_container_width=True, hide_index=True)
            
            # Download
            csv = df_res.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Baixar Relatório CSV", csv, "auditoria_fgv.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Erro no Servidor: {e}")
