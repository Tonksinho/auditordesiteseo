import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- CONFIGURAÇÃO DO NAVEGADOR ---
def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/chromium" # Caminho do Streamlit Cloud
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

st.title("🔍 Verificador de Meta Description")

# --- UPLOAD ---
arquivo = st.file_uploader("Suba seu arquivo (TXT ou CSV)", type=['csv', 'txt'])

if arquivo:
    # Transforma o arquivo em lista de URLs
    if arquivo.name.endswith('.csv'):
        df_input = pd.read_csv(arquivo)
        # Pega a primeira coluna do CSV como URL
        urls = df_input.iloc[:, 0].tolist()
    else:
        urls = arquivo.read().decode().splitlines()

    if st.button("🚀 Rodar Verificação"):
        resultados = []
        driver = iniciar_driver()
        barra = st.progress(0)
        
        for i, url in enumerate(urls):
            url = url.strip()
            if not url.startswith('http'): url = "https://" + url
            
            try:
                driver.get(url)
                time.sleep(2)
                try:
                    meta = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
                    status = "✅ Tem"
                except:
                    meta = "Vazio/Não existe"
                    status = "❌ Sem"
                resultados.append({"URL": url, "Status": status, "Conteúdo": meta})
            except:
                resultados.append({"URL": url, "Status": "⚠️ Erro", "Conteúdo": "Erro ao acessar"})
            
            barra.progress((i + 1) / len(urls))
        
        driver.quit()
        
        # --- RESULTADO ---
        df_final = pd.DataFrame(resultados)
        st.dataframe(df_final)
        st.download_button("📥 Baixar CSV", df_final.to_csv(index=False), "resultado.csv")
