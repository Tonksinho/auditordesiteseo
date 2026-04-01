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

# --- CSS ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        max-width: 600px;
    }
    h1 {
        text-align: center;
        color: #004685;
        font-size: 24px !important;
        margin-bottom: 0px;
    }
    .stImage {
        display: flex;
        justify-content: center;
        margin-bottom: -10px;
    }
    .stButton>button {
        width: 100%;
        background-color: #004685;
        color: white;
        border-radius: 5px;
        height: 3em;
    }
    /* Cards de URL com erro */
    .url-erro {
        background-color: #fff0f0;
        border-left: 4px solid #cc0000;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 13px;
        color: #cc0000;
        font-family: monospace;
    }
    .url-ok {
        background-color: #f0fff4;
        border-left: 4px solid #00a854;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 13px;
        color: #007a3d;
        font-family: monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO COM LOGO ---
if os.path.exists("fgv-logo-0.png"):
    st.image("fgv-logo-0.png", width=120)
else:
    st.markdown("<h2 style='text-align: center; color: #004685;'>FGV</h2>", unsafe_allow_html=True)

st.title("Auditor de Meta Tags")
st.markdown("<p style='text-align: center; font-size: 14px;'>Versão Cloud Protegida</p>", unsafe_allow_html=True)

# --- DRIVER ---
def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = "/usr/bin/chromium"
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
        urls_com_erro = []

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

                    # Verifica se a página existe (404, erro de rota, etc.)
                    page_title = driver.title.lower()
                    current_url = driver.current_url

                    pagina_inexistente = (
                        "404" in page_title or
                        "não encontrada" in page_title or
                        "page not found" in page_title or
                        "access denied" in page_title
                    )

                    if pagina_inexistente:
                        resultados.append({
                            "URL": url,
                            "Status": "🔴 Página inexistente",
                            "Descrição": "URL inválida ou página removida"
                        })
                        urls_com_erro.append((url, "Página inexistente / 404"))
                    else:
                        try:
                            meta = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
                            if meta and meta.strip():
                                status = "✅ OK"
                                descricao = meta
                            else:
                                status = "❌ Sem Tag"
                                descricao = "Meta description vazia"
                                urls_com_erro.append((url, "Meta description vazia"))
                        except:
                            status = "❌ Sem Tag"
                            descricao = "Não encontrada"
                            urls_com_erro.append((url, "Meta description ausente"))

                        resultados.append({"URL": url, "Status": status, "Descrição": descricao})

                except Exception as e:
                    resultados.append({
                        "URL": url,
                        "Status": "⚠️ Falha de conexão",
                        "Descrição": str(e)[:80]
                    })
                    urls_com_erro.append((url, "Falha de conexão"))

                progresso.progress((idx + 1) / len(lista_urls))

            driver.quit()
            status_txt.empty()

            # --- RESULTADOS ---
            df_res = pd.DataFrame(resultados)

            total = len(df_res)
            total_ok = len(df_res[df_res["Status"] == "✅ OK"])
            total_erro = total - total_ok

            col1, col2, col3 = st.columns(3)
            col1.metric("Total", total)
            col2.metric("✅ Com meta", total_ok)
            col3.metric("❌ Com problema", total_erro)

            st.success("Auditoria concluída!")
            st.dataframe(df_res, use_container_width=True, hide_index=True)

            # --- SEÇÃO DE ERROS EM VERMELHO ---
            if urls_com_erro:
                st.divider()
                st.markdown("### 🔴 Sites com problema")
                st.markdown(f"<p style='font-size:13px; color:#888;'>{len(urls_com_erro)} URL(s) precisam de atenção:</p>", unsafe_allow_html=True)
                for url_err, motivo in urls_com_erro:
                    st.markdown(
                        f"<div class='url-erro'>❌ <strong>{url_err}</strong><br><span style='font-size:11px;'>{motivo}</span></div>",
                        unsafe_allow_html=True
                    )

            # --- DOWNLOAD ---
            st.divider()
            csv = df_res.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 Baixar Relatório Completo (CSV)", csv, "auditoria_fgv.csv", "text/csv")

            # Download separado só dos erros
            if urls_com_erro:
                df_erros = pd.DataFrame(urls_com_erro, columns=["URL", "Motivo do Erro"])
                csv_erros = df_erros.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("🔴 Baixar Apenas os Erros (CSV)", csv_erros, "erros_fgv.csv", "text/csv")

        except Exception as e:
            st.error(f"Erro no Servidor: {e}")
