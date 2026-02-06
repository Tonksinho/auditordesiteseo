import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Auditor SEO | FGV", page_icon="🔍", layout="wide")

# --- CSS CUSTOMIZADO (IDENTIDADE FGV) ---
st.markdown("""
    <style>
    /* Cor do botão principal */
    .stButton>button {
        background-color: #004685;
        color: white;
        border-radius: 5px;
        border: None;
    }
    .stButton>button:hover {
        background-color: #003366;
        color: white;
    }
    /* Estilo do título */
    h1 {
        color: #004685;
        font-weight: bold;
    }
    /* Ajuste da Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO COM LOGO ---
col1, col2 = st.columns([1, 4])
with col1:
    # Usando a logo que você enviou (suba o arquivo fgv-logo-0.png para o GitHub)
    if os.path.exists("fgv-logo-0.png"):
        st.image("fgv-logo-0.png", width=150)
    else:
        st.write("### FGV") # Fallback caso a imagem não carregue

with col2:
    st.title("Verificador de Meta Description")
    st.write("Ferramenta interna FGV")

st.divider()

# --- SIDEBAR / CONFIGURAÇÕES ---
with st.sidebar:
    st.header("⚙️ Configurações")
    delay = st.slider("Tempo de espera por página (segundos)", 1, 5, 2)
    st.info("O tempo de espera ajuda a garantir que o site carregue antes do robô ler a tag.")
    
    upload_file = st.file_uploader("Suba sua lista (.csv ou .txt)", type=['csv', 'txt'])
    st.divider()
    st.caption("Desenvolvido para uso interno - FGV")

# --- FUNÇÃO DO ROBÔ ---
def rodar_auditoria(lista_urls):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = "/usr/bin/chromium"
    
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)  
    
    resultados = []
    progresso = st.progress(0)
    status_text = st.empty()
    
    total = len(lista_urls)
    
    for idx, url in enumerate(lista_urls):
        url = url.strip()
        if not url: continue
        
        status_text.text(f"📊 Processando {idx+1} de {total}: {url}")
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
            resultados.append({'URL': url, 'Status': f"⚠️ ERRO DE ACESSO", 'Conteúdo': str(e)[:30]})
            
    driver.quit()
    return pd.DataFrame(resultados)

# --- LÓGICA DE EXECUÇÃO ---
if upload_file is not None:
    if upload_file.name.endswith('.csv'):
        df_input = pd.read_csv(upload_file, sep=';')
        coluna_url = st.selectbox("Selecione a coluna das URLs:", df_input.columns.tolist())
        lista_final = df_input[coluna_url].tolist()
    else:
        stringio = upload_file.getvalue().decode("utf-8")
        lista_final = stringio.splitlines()

    if st.button("🚀 Iniciar Auditoria"):
        with st.spinner("O robô da FGV está verificando os sites..."):
            df_final = rodar_auditoria(lista_final)
            
        st.success("🏁 Auditoria Concluída!")
        
        # Exibição dos resultados em tabela bonita
        st.dataframe(df_final, use_container_width=True)

        # Métricas rápidas
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Verificado", len(df_final))
        c2.metric("Com Descrição", len(df_final[df_final['Status'] == "✅ COM DESCRIÇÃO"]))
        c3.metric("Faltantes/Erro", len(df_final[df_final['Status'] != "✅ COM DESCRIÇÃO"]))

        # Botão de Download estilizado
        csv = df_final.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Relatório Completo",
            data=csv,
            file_name=f"auditoria_seo_fgv_{int(time.time())}.csv",
            mime="text/csv",
        )

