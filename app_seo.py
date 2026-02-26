import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

# --- SETUP DA PÁGINA ---
st.set_page_config(page_title="Auditor SEO FGV", layout="wide")
st.title("🔍 Auditor de Meta Tags SEO")

# --- FUNÇÃO DO DRIVER (VERSÃO DIRETA) ---
def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # IMPORTANTE: Aponta para o Chromium instalado pelo packages.txt
    options.binary_location = "/usr/bin/chromium"
    
    # No Streamlit Cloud, o driver do Chromium fica neste caminho:
    service = Service("/usr/bin/chromedriver")
    
    return webdriver.Chrome(service=service, options=options)

# --- INTERFACE ---
arquivo = st.file_uploader("📂 Suba sua lista de URLs (CSV ou TXT)", type=['csv', 'txt'])

if arquivo:
    # Lógica simples de extração de URLs
    if arquivo.name.endswith('.csv'):
        df_in = pd.read_csv(arquivo)
        lista_urls = df_in.iloc[:, 0].tolist() # Pega a primeira coluna
    else:
        lista_urls = arquivo.read().decode().splitlines()

    if st.button("🚀 INICIAR AUDITORIA"):
        resultados = []
        try:
            with st.spinner("🤖 Iniciando Navegador..."):
                driver = iniciar_driver()
            
            progresso = st.progress(0)
            for idx, url in enumerate(lista_urls):
                url = url.strip()
                if not url: continue
                if not url.startswith('http'): url = f"https://{url}"
                
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
            
            # Exibição
            df_res = pd.DataFrame(resultados)
            st.success("Concluído!")
            st.dataframe(df_res, use_container_width=True)
            st.download_button("📥 Baixar CSV", df_res.to_csv(index=False), "auditoria.csv")
            
        except Exception as e:
            st.error(f"Erro no Servidor: {e}")
