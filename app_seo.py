import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

st.set_page_config(page_title="Auditor SEO", layout="centered", page_icon="🔍")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; max-width: 700px; }
    h1 { text-align: center; color: #004685; font-size: 24px !important; }
    .stButton>button { width: 100%; background-color: #004685; color: white; height: 3em; }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 Auditor de Meta Description")


def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)


arquivo = st.file_uploader("📂 Suba a planilha com as URLs (.xlsx)", type=["xlsx"])

if arquivo:
    df_raw = pd.read_excel(arquivo)
    cols = list(df_raw.columns)

    st.divider()
    c_url = st.selectbox("Coluna de URL *", cols, index=0)
    st.info(f"Total de URLs para verificar: **{len(df_raw)}**")

    if st.button("🚀 INICIAR VERIFICAÇÃO"):
        resultados = []
        progresso = st.progress(0)
        status_txt = st.empty()

        driver = iniciar_driver()

        for idx, row in df_raw.iterrows():
            url = str(row[c_url]).strip()
            if not url.startswith("http"):
                url = "https://" + url

            status_txt.text(f"Verificando ({idx+1}/{len(df_raw)}): {url}")
            res = {"URL": url, "Resultado": "", "Meta Description Encontrada": ""}

            try:
                driver.get(url)
                time.sleep(2)

                try:
                    meta_el = driver.find_element(By.XPATH, "//meta[@name='description']")
                    conteudo = (meta_el.get_attribute("content") or "").strip()
                except:
                    conteudo = ""

                if conteudo:
                    res["Resultado"] = "✅ Preenchida"
                    res["Meta Description Encontrada"] = conteudo
                else:
                    res["Resultado"] = "❌ Ausente ou vazia"
                    res["Meta Description Encontrada"] = ""

            except Exception as e:
                res["Resultado"] = "⚠️ Erro ao acessar"
                res["Meta Description Encontrada"] = str(e)[:80]

            resultados.append(res)
            progresso.progress((idx + 1) / len(df_raw))

        driver.quit()
        status_txt.success("Verificação concluída!")

        df_final = pd.DataFrame(resultados)

        # Resumo rápido
        total = len(df_final)
        ok = len(df_final[df_final["Resultado"] == "✅ Preenchida"])
        nok = len(df_final[df_final["Resultado"] == "❌ Ausente ou vazia"])
        erro = len(df_final[df_final["Resultado"] == "⚠️ Erro ao acessar"])

        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Preenchidas", ok)
        col2.metric("❌ Ausentes", nok)
        col3.metric("⚠️ Erros", erro)

        st.dataframe(df_final)

        csv = df_final.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar resultado CSV",
            data=csv,
            file_name="auditoria_meta.csv",
            mime="text/csv",
        )
