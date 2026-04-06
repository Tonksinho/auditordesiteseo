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

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; max-width: 700px; }
    h1 { text-align: center; color: #004685; font-size: 24px !important; }
    .stButton>button {
        width: 100%;
        background-color: #004685;
        color: white;
        border-radius: 5px;
        height: 3em;
    }
    .card-ok {
        background-color: #f0fff4;
        border-left: 4px solid #00a854;
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 13px;
    }
    .card-erro {
        background-color: #fff0f0;
        border-left: 4px solid #cc0000;
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 13px;
    }
    .card-aviso {
        background-color: #fffbe6;
        border-left: 4px solid #faad14;
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 13px;
    }
    .label { font-size: 11px; color: #888; margin-top: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- LOGO ---
if os.path.exists("fgv-logo-0.png"):
    st.image("fgv-logo-0.png", width=120)
else:
    st.markdown("<h2 style='text-align:center;color:#004685;'>FGV</h2>", unsafe_allow_html=True)

st.title("Auditor de Meta Tags")
st.markdown("<p style='text-align:center;font-size:14px;color:#888;'>Compara o que está na planilha com o que está publicado no site</p>", unsafe_allow_html=True)

# --- COLUNAS ESPERADAS ---
COL_URL       = "URL"
COL_TITULO    = "Título da Página (até 60 caracteres)"
COL_META_DESC = "Meta Description (até 160 caracteres)"

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

def normalizar(texto: str) -> str:
    return str(texto).strip().lower() if texto else ""

# --- INTERFACE ---
st.divider()
arquivo = st.file_uploader("📂 Suba sua planilha EPPG (.xlsx)", type=["xlsx"])

if arquivo:
    df = pd.read_excel(arquivo)
    df.columns = df.columns.str.strip()

    colunas_faltando = [c for c in [COL_URL, COL_TITULO, COL_META_DESC] if c not in df.columns]
    if colunas_faltando:
        st.error(f"Colunas não encontradas na planilha: {colunas_faltando}")
        st.stop()

    df = df[[COL_URL, COL_TITULO, COL_META_DESC]].dropna(subset=[COL_URL])
    df.columns = ["url", "titulo_esperado", "meta_esperada"]
    df = df.fillna("")

    st.success(f"✅ Planilha carregada — **{len(df)}** URLs encontradas.")

    opcao = st.radio(
        "O que deseja comparar?",
        ["Meta Description + Título", "Só Meta Description", "Só Título"],
        horizontal=True,
    )

    verificar_titulo = opcao in ["Meta Description + Título", "Só Título"]
    verificar_meta   = opcao in ["Meta Description + Título", "Só Meta Description"]

    if st.button("🚀 INICIAR AUDITORIA"):
        resultados = []

        try:
            with st.spinner("🤖 Iniciando navegador..."):
                driver = iniciar_driver()

            progresso  = st.progress(0)
            status_txt = st.empty()
            total      = len(df)

            for idx, row in df.iterrows():
                url            = str(row["url"]).strip().rstrip("/")
                titulo_esp     = str(row["titulo_esperado"]).strip()
                meta_esp       = str(row["meta_esperada"]).strip()

                status_txt.markdown(f"🔍 Analisando `{url}`")

                resultado = {
                    "URL":               url,
                    "Status Título":     "—",
                    "Título Esperado":   titulo_esp,
                    "Título no Site":    "",
                    "Status Meta":       "—",
                    "Meta Esperada":     meta_esp,
                    "Meta no Site":      "",
                    "Resultado Geral":   "",
                }

                try:
                    driver.get(url)
                    time.sleep(2)

                    page_title_lower = driver.title.lower()
                    if any(x in page_title_lower for x in ["404", "não encontrada", "page not found", "access denied"]):
                        resultado["Resultado Geral"] = "🔴 Página inexistente"
                        resultados.append(resultado)
                        progresso.progress((idx + 1) / total)
                        continue

                    # ── Título ────────────────────────────────────────────────
                    if verificar_titulo:
                        titulo_site = driver.title.strip()
                        resultado["Título no Site"] = titulo_site
                        if normalizar(titulo_esp) == normalizar(titulo_site):
                            resultado["Status Título"] = "✅ Igual"
                        elif titulo_site == "":
                            resultado["Status Título"] = "❌ Ausente"
                        else:
                            resultado["Status Título"] = "⚠️ Diferente"

                    # ── Meta Description ──────────────────────────────────────
                    if verificar_meta:
                        try:
                            meta_site = driver.find_element(
                                By.XPATH, "//meta[@name='description']"
                            ).get_attribute("content") or ""
                            meta_site = meta_site.strip()
                        except Exception:
                            meta_site = ""

                        resultado["Meta no Site"] = meta_site
                        if normalizar(meta_esp) == normalizar(meta_site):
                            resultado["Status Meta"] = "✅ Igual"
                        elif meta_site == "":
                            resultado["Status Meta"] = "❌ Ausente"
                        else:
                            resultado["Status Meta"] = "⚠️ Diferente"

                    # ── Resultado geral ───────────────────────────────────────
                    status_vals = []
                    if verificar_titulo: status_vals.append(resultado["Status Título"])
                    if verificar_meta:   status_vals.append(resultado["Status Meta"])

                    if all("✅" in s for s in status_vals):
                        resultado["Resultado Geral"] = "✅ Tudo certo"
                    elif any("❌" in s for s in status_vals):
                        resultado["Resultado Geral"] = "❌ Com problema"
                    else:
                        resultado["Resultado Geral"] = "⚠️ Divergência"

                except Exception as e:
                    resultado["Resultado Geral"] = f"⚠️ Falha: {str(e)[:60]}"

                resultados.append(resultado)
                progresso.progress((idx + 1) / total)

            driver.quit()
            status_txt.empty()

            # --- RESULTADOS ---
            df_res = pd.DataFrame(resultados)

            total_ok    = len(df_res[df_res["Resultado Geral"] == "✅ Tudo certo"])
            total_div   = len(df_res[df_res["Resultado Geral"] == "⚠️ Divergência"])
            total_prob  = len(df_res[df_res["Resultado Geral"].str.contains("❌|🔴", na=False)])

            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total URLs", total)
            c2.metric("✅ Corretas",   total_ok)
            c3.metric("⚠️ Divergentes", total_div)
            c4.metric("❌ Problemas",  total_prob)

            st.success("Auditoria concluída!")

            # --- CARDS DETALHADOS ---
            st.divider()
            st.markdown("### 📋 Resultado por URL")

            for _, r in df_res.iterrows():
                geral = r["Resultado Geral"]
                css   = "card-ok" if "✅" in geral else ("card-erro" if "❌" in geral or "🔴" in geral else "card-aviso")

                linhas_detalhe = f"<div class='label'>🔗 {r['URL']}</div>"

                if verificar_titulo and r["Status Título"] != "—":
                    linhas_detalhe += f"""
                        <div class='label'>📌 <b>Título:</b> {r['Status Título']}</div>
                        <div class='label'>↳ Esperado: <i>{r['Título Esperado']}</i></div>
                        <div class='label'>↳ No site: <i>{r['Título no Site']}</i></div>
                    """
                if verificar_meta and r["Status Meta"] != "—":
                    linhas_detalhe += f"""
                        <div class='label'>📝 <b>Meta:</b> {r['Status Meta']}</div>
                        <div class='label'>↳ Esperada: <i>{r['Meta Esperada']}</i></div>
                        <div class='label'>↳ No site: <i>{r['Meta no Site']}</i></div>
                    """

                st.markdown(
                    f"<div class='{css}'><b>{geral}</b>{linhas_detalhe}</div>",
                    unsafe_allow_html=True,
                )

            # --- TABELA + DOWNLOAD ---
            st.divider()
            st.markdown("### 📊 Tabela Completa")

            colunas_exibir = ["URL", "Resultado Geral"]
            if verificar_titulo: colunas_exibir += ["Status Título", "Título Esperado", "Título no Site"]
            if verificar_meta:   colunas_exibir += ["Status Meta",   "Meta Esperada",   "Meta no Site"]

            st.dataframe(df_res[colunas_exibir], use_container_width=True, hide_index=True)

            csv = df_res[colunas_exibir].to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("📥 Baixar Relatório Completo (CSV)", csv, "auditoria_fgv.csv", "text/csv")

            df_prob = df_res[~df_res["Resultado Geral"].str.contains("✅", na=False)]
            if not df_prob.empty:
                csv_prob = df_prob[colunas_exibir].to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button("🔴 Baixar Apenas os Problemas (CSV)", csv_prob, "problemas_fgv.csv", "text/csv")

        except Exception as e:
            st.error(f"Erro no servidor: {e}")
