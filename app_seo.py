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

# --- LOGO FGV ---
st.image("fgv-logo-0.png", width=150)

st.title("🔍 Auditor de Meta Description")


def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)


def carregar_urls(arquivo):
    nome = arquivo.name.lower()
    if nome.endswith(".txt"):
        linhas = arquivo.read().decode("utf-8").splitlines()
        urls = [l.strip() for l in linhas if l.strip()]
        return urls, None
    elif nome.endswith(".xlsx"):
        df = pd.read_excel(arquivo)
        return None, df


arquivo = st.file_uploader("📂 Suba a lista de URLs (.xlsx ou .txt)", type=["xlsx", "txt"])

if arquivo:
    urls_list, df_raw = carregar_urls(arquivo)

    if df_raw is not None:
        st.divider()
        cols = list(df_raw.columns)
        c_url = st.selectbox("Coluna de URL *", cols, index=0)
        urls_list = [str(r).strip() for r in df_raw[c_url] if str(r).strip()]

    st.info(f"Total de URLs para verificar: **{len(urls_list)}**")

    if st.button("🚀 INICIAR VERIFICAÇÃO"):
        resultados = []
        progresso = st.progress(0)
        status_txt = st.empty()

        driver = iniciar_driver()

        for idx, url in enumerate(urls_list):
            if not url.startswith("http"):
                url = "https://" + url

            status_txt.text(f"Verificando ({idx+1}/{len(urls_list)}): {url}")
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

            except Exception as e:
                res["Resultado"] = "⚠️ Erro ao acessar"
                res["Meta Description Encontrada"] = str(e)[:80]

            resultados.append(res)
            progresso.progress((idx + 1) / len(urls_list))

        driver.quit()
        status_txt.success("Verificação concluída!")

        df_final = pd.DataFrame(resultados)

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
