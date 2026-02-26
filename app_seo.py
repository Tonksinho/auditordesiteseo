import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- SETUP DA PÁGINA ---
st.set_page_config(page_title="Auditor SEO FGV", layout="wide", page_icon="🔍")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #004685; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 Auditor de Meta Tags SEO")
st.write("Versão Cloud Estável (Python 3.13) - Suporte a CSV e TXT")

# --- FUNÇÃO DO DRIVER (CONFIGURAÇÃO PARA STREAMLIT CLOUD) ---
def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # O caminho abaixo é onde o packages.txt instala o Chromium no Streamlit Cloud
    options.binary_location = "/usr/bin/chromium"
    
    # Identidade de navegador para evitar bloqueios de segurança dos sites
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# --- INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if 'lista_urls' not in st.session_state:
    st.session_state.lista_urls = []
if 'resultados' not in st.session_state:
    st.session_state.resultados = None

# --- INTERFACE DE UPLOAD ---
upload_file = st.file_uploader("📂 Suba sua lista de URLs (CSV ou TXT)", type=['csv', 'txt'])

if upload_file:
    # Lógica para processar o arquivo e salvar na sessão
    if upload_file.name.endswith('.csv'):
        try:
            df_input = pd.read_csv(upload_file, sep=None, engine='python')
        except:
            df_input = pd.read_csv(upload_file, sep=';')
            
        coluna_url = st.selectbox("Selecione a coluna que contém as URLs:", df_input.columns.tolist())
        st.session_state.lista_urls = df_input[coluna_url].dropna().tolist()
    else:
        stringio = upload_file.getvalue().decode("utf-8")
        st.session_state.lista_urls = [line.strip() for line in stringio.splitlines() if line.strip()]

    st.success(f"📍 {len(st.session_state.lista_urls)} URLs carregadas com sucesso!")

    # --- BOTÃO DE AÇÃO ---
    if st.button("🚀 INICIAR AUDITORIA"):
        resultados_temporarios = []
        
        try:
            with st.spinner("🤖 Inicializando navegador no servidor..."):
                driver = iniciar_driver()
            
            progresso = st.progress(0)
            status_msg = st.empty()
            
            total_urls = len(st.session_state.lista_urls)
            
            for idx, url in enumerate(st.session_state.lista_urls):
                url = url.strip()
                if not url.startswith('http'):
                    url = f"https://{url}"
                
                status_msg.markdown(f"🔍 **Analisando ({idx+1}/{total_urls}):** `{url}`")
                
                try:
                    driver.get(url)
                    time.sleep(2) # Espera o carregamento do DOM
                    
                    try:
                        # Busca a tag meta description
                        meta = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
                        conteudo = meta.strip() if meta else ""
                        
                        if not conteudo:
                            status = "⚠️ Tag Vazia"
                            conteudo = "Vazia"
                        else:
                            status = "✅ OK"
                    except:
                        status = "❌ Sem Tag"
                        conteudo = "Não encontrada"
                    
                    resultados_temporarios.append({
                        "URL": url, 
                        "Status": status, 
                        "Descrição": conteudo,
                        "Caracteres": len(conteudo) if conteudo not in ["Vazia", "Não encontrada"] else 0
                    })
                except:
                    resultados_temporarios.append({
                        "URL": url, 
                        "Status": "⚠️ Erro de Acesso", 
                        "Descrição": "Página inacessível", 
                        "Caracteres": 0
                    })
                
                progresso.progress((idx + 1) / total_urls)
            
            driver.quit()
            st.session_state.resultados = pd.DataFrame(resultados_temporarios)
            st.balloons()
            
        except Exception as e:
            st.error(f"Erro Crítico: {e}")

# --- EXIBIÇÃO DOS RESULTADOS (FORA DO LOOP) ---
if st.session_state.resultados is not None:
    st.divider()
    st.subheader("📊 Relatório de Auditoria")
    
    # Métricas Rápidas
    c1, c2, c3 = st.columns(3)
    df = st.session_state.resultados
    c1.metric("Analisados", len(df))
    c2.metric("Com Meta Tag", len(df[df['Status'] == "✅ OK"]))
    c3.metric("Falhas/Erros", len(df[df['Status'] != "✅ OK"]))

    # Tabela formatada
    st.dataframe(
        df, 
        use_container_width=True,
        column_config={
            "URL": st.column_config.LinkColumn("Link da Página"),
            "Status": st.column_config.TextColumn("Diagnóstico"),
            "Caracteres": st.column_config.NumberColumn("Caracteres", format="%d ✍️")
        },
        hide_index=True
    )
    
    # Download do CSV
    csv_output = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 Baixar Relatório Completo (CSV)",
        data=csv_output,
        file_name="auditoria_seo_fgv.csv",
        mime="text/csv"
    )
else:
    if not upload_file:
        st.info("Aguardando upload de arquivo para processar.")
