import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- SETUP DA PÁGINA ---
st.set_page_config(page_title="Auditor SEO FGV", layout="wide")

st.title("🔍 Auditor de Meta Tags SEO")
st.write("Versão Cloud Protegida (Python 3.13)")

# --- FUNÇÃO DO DRIVER (O SEGREDO TÁ AQUI) ---
def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # Caminho onde o 'packages.txt' instala o Chromium no Streamlit Cloud
    options.binary_location = "/usr/bin/chromium"
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# --- INTERFACE ---
urls_input = st.text_area("Insira as URLs (uma por linha):", placeholder="https://fgv.br")

if st.button("🚀 Iniciar Auditoria"):
    if not urls_input:
        st.warning("Adicione pelo menos uma URL.")
    else:
        lista_urls = urls_input.split('\n')
        resultados = []
        
        try:
            with st.spinner("🤖 Iniciando navegador no servidor..."):
                driver = iniciar_driver()
            
            progresso = st.progress(0)
            
            for idx, url in enumerate(lista_urls):
                url = url.strip()
                if not url: continue
                
                st.write(f"Analisando: {url}")
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
                    resultados.append({"URL": url, "Status": "⚠️ Erro de Conexão", "Descrição": "-"})
                
                progresso.progress((idx + 1) / len(lista_urls))
            
            driver.quit()
            
            # --- EXIBIÇÃO ---
            df = pd.DataFrame(resultados)
            st.success("Auditoria Concluída!")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV", csv, "auditoria_seo.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Erro Crítico no Servidor: {e}")
