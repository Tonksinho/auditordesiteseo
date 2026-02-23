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
st.set_page_config(page_title="Auditor SEO | FGV", page_icon="🔍", layout="centered")

# --- CSS MODERNO E CENTRALIZADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Reset de Fonte */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Estilização dos Cards de Métrica */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e6ed;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }

    /* Botão Principal FGV */
    .stButton>button {
        width: 100%;
        background-color: #004685;
        color: white;
        border-radius: 8px;
        padding: 10px;
        font-weight: 600;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #002d56;
        box-shadow: 0 4px 12px rgba(0,70,133,0.3);
    }

    /* Estilo do File Uploader */
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed #004685;
        border-radius: 12px;
        background-color: #f8faff;
    }

    /* Títulos */
    h1 {
        color: #004685;
        font-weight: 800 !important;
        letter-spacing: -1px;
    }
    
    /* Ajuste da Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO CENTRALIZADO ---
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
if os.path.exists("fgv-logo-0.png"):
    st.image("fgv-logo-0.png", width=180)
else:
    st.markdown("<h2 style='color: #004685;'>FGV</h2>", unsafe_allow_html=True)

st.title("Auditor de Meta Description")
st.write("Otimização de SEO para Portais Institucionais")
st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Parâmetros")
    delay = st.slider("Delay de carregamento (s)", 1, 5, 2)
    st.divider()
    st.caption("v2.0 - Dashboard Modernizado")

# --- LÓGICA DO ROBÔ (Otimizada) ---
def rodar_auditoria(lista_urls):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Identificando como navegador real para evitar bloqueios
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Nota: Em produção/Streamlit Cloud, ajuste os caminhos do driver se necessário
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)  
    
    resultados = []
    progresso_bar = st.progress(0)
    status_msg = st.empty()
    
    total = len(lista_urls)
    
    for idx, url in enumerate(lista_urls):
        url = url.strip()
        if not url: continue
        
        status_msg.markdown(f"🔍 **Analisando:** `{url}`")
        progresso_bar.progress((idx + 1) / total)
        
        try:
            driver.get(url)
            time.sleep(delay)
            
            try:
                meta_desc = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
                status = "✅ COM DESCRIÇÃO" if meta_desc.strip() else "⚠️ TAG VAZIA"
            except:
                meta_desc = "Não encontrada no HTML"
                status = "❌ SEM TAG"

            resultados.append({'URL': url, 'Status': status, 'Conteúdo': meta_desc})
        except Exception as e:
            resultados.append({'URL': url, 'Status': "⚠️ ERRO DE ACESSO", 'Conteúdo': str(e)[:40]})
            
    driver.quit()
    return pd.DataFrame(resultados)

# --- ÁREA PRINCIPAL ---
upload_file = st.file_uploader("Suba sua lista de URLs (CSV ou TXT)", type=['csv', 'txt'])

if upload_file:
    # Processamento do arquivo
    if upload_file.name.endswith('.csv'):
        df_input = pd.read_csv(upload_file, sep=';')
        coluna_url = st.selectbox("Em qual coluna estão as URLs?", df_input.columns.tolist())
        lista_final = df_input[coluna_url].dropna().tolist()
    else:
        stringio = upload_file.getvalue().decode("utf-8")
        lista_final = [line for line in stringio.splitlines() if line.strip()]

    # Botão de ação centralizado
    if st.button("🚀 INICIAR AUDITORIA"):
        df_final = rodar_auditoria(lista_final)
        
        st.divider()
        st.subheader("📊 Resultados da Análise")
        
        # Métricas em colunas com estilo de card
        m1, m2, m3 = st.columns(3)
        m1.metric("Total", len(df_final))
        m2.metric("OK", len(df_final[df_final['Status'] == "✅ COM DESCRIÇÃO"]))
        m3.metric("Falhas", len(df_final[df_final['Status'] != "✅ COM DESCRIÇÃO"]))

        # Tabela interativa com configuração de colunas
        st.dataframe(
            df_final,
            use_container_width=True,
            column_config={
                "URL": st.column_config.LinkColumn("Link Analisado"),
                "Status": st.column_config.TextColumn("Diagnóstico"),
                "Conteúdo": st.column_config.TextColumn("Meta Description Encontrada")
            },
            hide_index=True
        )

        # Download centralizado
        csv = df_final.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Relatório Completo (CSV)",
            data=csv,
            file_name=f"auditoria_fgv_{int(time.time())}.csv",
            mime="text/csv",
        )
else:
    # Estado inicial "vazio" para não poluir a tela
    st.info("💡 Dica: O arquivo deve conter uma lista de URLs completas (com https://).")
