import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- CONFIGURAÇÃO DA PÁGINA WEB ---
st.set_page_config(page_title="Auditor de SEO - FGV", page_icon="🔍")
st.title("🔍 Verificador de Meta Description")
st.markdown("Suba sua lista de URLs e eu verifico quais possuem Meta Description.")

# --- SIDEBAR / CONFIGURAÇÕES ---
with st.sidebar:
    st.header("Configurações")
    delay = st.slider("Tempo de espera (segundos)", 1, 5, 2)
    upload_file = st.file_uploader("Escolha o arquivo (.csv ou .txt)", type=['csv', 'txt'])

# --- FUNÇÃO DO ROBÔ ---
def rodar_auditoria(lista_urls):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    resultados = []
    progresso = st.progress(0)
    status_text = st.empty()
    
    total = len(lista_urls)
    
    for idx, url in enumerate(lista_urls):
        url = url.strip()
        if not url: continue
        
        status_text.text(f"Verificando {idx+1}/{total}: {url}")
        progresso.progress((idx + 1) / total)
        
        try:
            driver.get(url)
            time.sleep(delay)
            
            try:
                meta_desc = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
                status = "✅ COM DESCRIÇÃO" if meta_desc.strip() else "⚠️ TAG VAZIA"
            except:
                meta_desc = "NÃO ENCONTRADA"
                status = "❌ SEM TAG"

            resultados.append({
                'URL': url,
                'Status': status,
                'Conteúdo': meta_desc
            })
        except Exception as e:
            resultados.append({'URL': url, 'Status': f"ERRO: {str(e)[:20]}", 'Conteúdo': ""})
            
    driver.quit()
    return pd.DataFrame(resultados)

# --- LÓGICA DE EXECUÇÃO ---
if upload_file is not None:
    # Lendo o arquivo (suporta CSV ou TXT linha por linha)
    if upload_file.name.endswith('.csv'):
        df_input = pd.read_csv(upload_file, sep=';')
        # Tenta achar a coluna de URL
        colunas = df_input.columns.tolist()
        coluna_url = st.selectbox("Selecione a coluna das URLs:", colunas)
        lista_final = df_input[coluna_url].tolist()
    else:
        stringio = upload_file.getvalue().decode("utf-8")
        lista_final = stringio.splitlines()

    if st.button("🚀 Iniciar Verificação"):
        with st.spinner("O robô está trabalhando..."):
            df_final = rodar_auditoria(lista_final)
            
        st.success("🏁 Verificação Concluída!")
        st.dataframe(df_final)

        # Botão de Download
        csv = df_final.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Relatório em CSV",
            data=csv,
            file_name="relatorio_seo_final.csv",
            mime="text/csv",
        )
