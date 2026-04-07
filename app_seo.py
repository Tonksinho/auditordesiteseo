import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import os

# --- SETUP DA PÁGINA (Sempre o primeiro comando Streamlit) ---
st.set_page_config(page_title="Auditor SEO Flex", layout="centered", page_icon="🔍")

# Estilos CSS (Mantendo seu padrão visual)
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; max-width: 700px; }
    h1 { text-align: center; color: #004685; font-size: 24px !important; }
    .stButton>button { width: 100%; background-color: #004685; color: white; height: 3em; }
    .card-ok { background-color: #f0fff4; border-left: 4px solid #00a854; padding: 10px; margin: 5px 0; border-radius: 4px; font-size: 13px; }
    .card-erro { background-color: #fff0f0; border-left: 4px solid #cc0000; padding: 10px; margin: 5px 0; border-radius: 4px; font-size: 13px; }
    .label { font-size: 11px; color: #888; }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 Auditor de Meta Tags Flexível")

# --- FUNÇÕES DE APOIO ---
def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/chromium" # Ajuste conforme seu ambiente
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

def normalizar(texto):
    return str(texto).strip().lower() if texto and str(texto).lower() != 'nan' else ""

# --- INTERFACE DE UPLOAD ---
arquivo = st.file_uploader("📂 Suba qualquer planilha Excel (.xlsx)", type=["xlsx"])

if arquivo:
    df_raw = pd.read_excel(arquivo)
    cols = list(df_raw.columns)
    
    st.divider()
    st.subheader("⚙️ Mapeamento de Colunas")
    col1, col2, col3 = st.columns(3)
    
    # Seleção dinâmica de colunas
    with col1:
        c_url = st.selectbox("Coluna de URL", cols, index=0)
    with col2:
        # Tenta achar 'titulo' ou similar, se não, pega a segunda coluna
        idx_t = next((i for i, c in enumerate(cols) if "tit" in c.lower()), 1 if len(cols)>1 else 0)
        c_tit = st.selectbox("Coluna de Título", cols, index=idx_t)
    with col3:
        # Tenta achar 'meta' ou 'desc', se não, pega a terceira
        idx_m = next((i for i, c in enumerate(cols) if "meta" in c.lower() or "desc" in c.lower()), 2 if len(cols)>2 else 0)
        c_meta = st.selectbox("Coluna de Meta", cols, index=idx_m)

    st.info(f"Total de linhas para processar: **{len(df_raw)}**")
    
    if st.button("🚀 INICIAR AUDITORIA"):
        resultados = []
        progresso = st.progress(0)
        status_txt = st.empty()
        
        driver = iniciar_driver()
        
        for idx, row in df_raw.iterrows():
            url = str(row[c_url]).strip()
            if not url.startswith("http"): url = "https://" + url
            
            status_txt.text(f"Analisando ({idx+1}/{len(df_raw)}): {url}")
            
            res = {"URL": url, "Resultado": "", "Detalhes": ""}
            
            try:
                driver.get(url)
                time.sleep(2)
                
                # Coleta dados do site
                site_tit = driver.title
                try:
                    site_meta = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
                except:
                    site_meta = ""

                # Comparação
                erro_tit = normalizar(site_tit) != normalizar(row[c_tit])
                erro_meta = normalizar(site_meta) != normalizar(row[c_meta])

                if not erro_tit and not erro_meta:
                    res["Resultado"] = "✅ OK"
                else:
                    res["Resultado"] = "❌ Divergente"
                    res["Detalhes"] = f"Título OK: {not erro_tit} | Meta OK: {not erro_meta}"
                
            except Exception as e:
                res["Resultado"] = "⚠️ Erro"
                res["Detalhes"] = str(e)[:50]
            
            resultados.append(res)
            progresso.progress((idx + 1) / len(df_raw))

        driver.quit()
        status_txt.success("Auditoria concluída!")
        
        # Exibição básica dos resultados
        df_final = pd.DataFrame(resultados)
        st.dataframe(df_final)
