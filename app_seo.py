import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

st.set_page_config(page_title="Auditor SEO Flex", layout="centered", page_icon="🔍")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; max-width: 700px; }
    h1 { text-align: center; color: #004685; font-size: 24px !important; }
    .stButton>button { width: 100%; background-color: #004685; color: white; height: 3em; }
    .card-ok { background-color: #f0fff4; border-left: 4px solid #00a854; padding: 10px; margin: 5px 0; border-radius: 4px; font-size: 13px; }
    .card-erro { background-color: #fff0f0; border-left: 4px solid #cc0000; padding: 10px; margin: 5px 0; border-radius: 4px; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 Auditor de Meta Tags Flexível")


def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)


def normalizar(texto):
    return str(texto).strip().lower() if texto and str(texto).lower() != "nan" else ""


arquivo = st.file_uploader("📂 Suba qualquer planilha Excel (.xlsx)", type=["xlsx"])

if arquivo:
    df_raw = pd.read_excel(arquivo)
    cols = list(df_raw.columns)

    st.divider()
    st.subheader("⚙️ Mapeamento de Colunas")

    # --- URL (obrigatório) ---
    c_url = st.selectbox("Coluna de URL *", cols, index=0)

    # --- Título (opcional) ---
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        usar_titulo = st.checkbox("", value=False, key="chk_titulo")
    with col2:
        idx_t = next((i for i, c in enumerate(cols) if "tit" in c.lower()), 1 if len(cols) > 1 else 0)
        c_tit = st.selectbox(
            "Verificar Título (opcional)",
            cols,
            index=idx_t,
            disabled=not usar_titulo,
        )

    # --- Meta Description (opcional) ---
    col3, col4 = st.columns([0.15, 0.85])
    with col3:
        usar_meta = st.checkbox("", value=True, key="chk_meta")
    with col4:
        idx_m = next((i for i, c in enumerate(cols) if "meta" in c.lower() or "desc" in c.lower()), 2 if len(cols) > 2 else 0)
        c_meta = st.selectbox(
            "Verificar Meta Description (opcional)",
            cols,
            index=idx_m,
            disabled=not usar_meta,
        )

    if not usar_titulo and not usar_meta:
        st.warning("Selecione ao menos uma coluna para verificar (Título ou Meta).")
    else:
        st.info(f"Total de linhas para processar: **{len(df_raw)}**")

        if st.button("🚀 INICIAR AUDITORIA"):
            resultados = []
            progresso = st.progress(0)
            status_txt = st.empty()

            driver = iniciar_driver()

            for idx, row in df_raw.iterrows():
                url = str(row[c_url]).strip()
                if not url.startswith("http"):
                    url = "https://" + url

                status_txt.text(f"Analisando ({idx+1}/{len(df_raw)}): {url}")
                res = {"URL": url, "Resultado": "", "Detalhes": ""}

                try:
                    driver.get(url)
                    time.sleep(2)

                    erros = []

                    # --- Verifica título (se ativado) ---
                    if usar_titulo:
                        site_tit = driver.title
                        if normalizar(site_tit) != normalizar(row[c_tit]):
                            erros.append(
                                f"Título diverge | Esperado: '{normalizar(row[c_tit])}' | Encontrado: '{normalizar(site_tit)}'"
                            )

                    # --- Verifica meta description (se ativado) ---
                    if usar_meta:
                        try:
                            # Busca explicitamente pelo atributo name="description" no HTML
                            meta_el = driver.find_element(
                                By.XPATH, "//meta[@name='description']"
                            )
                            site_meta = meta_el.get_attribute("content") or ""
                        except:
                            site_meta = ""

                        meta_esperada = normalizar(row[c_meta])
                        meta_encontrada = normalizar(site_meta)

                        if meta_esperada == "":
                            erros.append("Meta description: valor esperado vazio na planilha")
                        elif site_meta == "":
                            erros.append("Meta description: não encontrada na página")
                        elif meta_esperada != meta_encontrada:
                            erros.append(
                                f"Meta diverge | Esperado: '{meta_esperada[:60]}...' | Encontrado: '{meta_encontrada[:60]}...'"
                            )

                    # --- Resultado final ---
                    if not erros:
                        res["Resultado"] = "✅ OK"
                    else:
                        res["Resultado"] = "❌ Divergente"
                        res["Detalhes"] = " | ".join(erros)

                except Exception as e:
                    res["Resultado"] = "⚠️ Erro"
                    res["Detalhes"] = str(e)[:80]

                resultados.append(res)
                progresso.progress((idx + 1) / len(df_raw))

            driver.quit()
            status_txt.success("Auditoria concluída!")

            df_final = pd.DataFrame(resultados)
            st.dataframe(df_final)

            # Download do resultado
            csv = df_final.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar resultado CSV",
                data=csv,
                file_name="auditoria_seo.csv",
                mime="text/csv",
            )
