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
st.write("Versão Cloud Protegida (Python 3.13) - Upload de Arquivo")

# --- FUNÇÃO DO DRIVER ---
def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # Caminho do Chromium no Streamlit Cloud (via packages.txt)
    options.binary_location = "/usr/bin/chromium"
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# --- INTERFACE DE UPLOAD ---
upload_file = st.file_uploader("📂 Suba sua lista de URLs (CSV ou TXT)", type=['csv', 'txt'])

if upload_file:
    # Lógica para extrair URLs
    if upload_file.name.endswith('.csv'):
        try:
            df_input = pd.read_csv(upload_file, sep=None, engine='python')
        except:
            df_input = pd.read_csv(upload_file, sep=';')
            
        coluna_url = st.selectbox("Selecione a coluna com as URLs:", df_input.columns.tolist())
        lista_final = df_input[coluna_url].dropna().tolist()
    else:
        stringio = upload_file.getvalue().decode("utf-8")
        lista_final = [line.strip() for line in stringio.splitlines() if line.strip()]

    st.info(f"📍 {len(lista_final)} URLs carregadas.")

    # Botão de ação
    if st.button("🚀 INICIAR AUDITORIA"):
        resultados = []
        
        try:
            with st.spinner("🤖 Abrindo navegador no servidor..."):
                driver = iniciar_driver()
            
            progresso = st.progress(0)
            status_msg = st.empty()
            
            for idx, url in enumerate(lista_final):
                url = url.strip()
                if not url.startswith('http'):
                    url = f"https://{url}"
                
                status_msg.markdown(f"🔍 **Analisando:** `{url}`")
                
                try:
                    driver.get(url)
                    time.sleep(2) 
                    
                    try:
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
                    
                    resultados.append({
                        "URL": url, 
                        "Status": status, 
                        "Descrição": conteudo,
                        "Caracteres": len(conteudo) if conteudo not in ["Vazia", "Não encontrada"] else 0
                    })
                except:
                    resultados.append({"URL": url, "Status": "⚠️ Erro de Acesso", "Descrição": "-", "Caracteres": 0})
                
                progresso.progress((idx + 1) / len(lista_final))
            
            driver.quit()
            
            # --- EXIBIÇÃO DOS RESULTADOS ---
            df_res = pd.DataFrame(resultados)
            st.divider()
            st.success("✅ Auditoria Finalizada!")
            
            # Tabela Interativa
            st.dataframe(
                df_res, 
                use_container_width=True,
                column_config={
                    "URL": st.column_config.LinkColumn("Link"),
                    "Caracteres": st.column_config.NumberColumn("Qtd Chars", format="%d ✍️")
                }
            )
            
            # Download do Relatório
            csv_output = df_res.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar Relatório SEO",
                data=csv_output,
                file_name=f"auditoria_seo_fgv.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Erro Crítico: {e}")
else:
    st.warning("Aguardando upload do arquivo para começar...")
