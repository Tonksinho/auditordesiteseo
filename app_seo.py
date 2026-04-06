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
    .url-link { color: #004685; text-decoration: none; font-weight: bold; }
    .url-link:hover { text-decoration: underline; }
    </style>
""", unsafe_allow_html=True)

# --- LOGO ---
if os.path.exists("fgv-logo-0.png"):
    st.image("fgv-logo-0.png", width=120)
else:
    st.markdown("<h2 style='text-align:center;color:#004685;'>FGV</h2>", unsafe_allow_html=True)

st.title("Auditor de Meta Tags")

# --- COLUNAS ESPERADAS ---
COL_URL       = "URL"
COL_TITULO    = "Título da Página (até 60 caracteres)"
COL_META_DESC = "Meta Description (até 160 caracteres)"

def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # Configurações para rodar no Streamlit Cloud/Linux
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

def normalizar(texto: str) -> str:
    return str(texto).strip().lower() if texto else ""

# --- INTERFACE DE UPLOAD ---
st.divider()
arquivo = st.file_uploader("📂 Suba sua planilha EPPG (.xlsx)", type=["xlsx"])

if arquivo:
    df_input = pd.read_excel(arquivo)
    df_input.columns = df_input.columns.str.strip()

    colunas_faltando = [c for c in [COL_URL, COL_TITULO, COL_META_DESC] if c not in df_input.columns]
    if colunas_faltando:
        st.error(f"Colunas não encontradas: {colunas_faltando}")
        st.stop()

    # Limpeza inicial e correção de URL (adicionando o E se faltar)
    df_input[COL_URL] = df_input[COL_URL].apply(lambda x: str(x).replace("eppg.fgv.br", "eppge.fgv.br").strip())
    df_input = df_input[[COL_URL, COL_TITULO, COL_META_DESC]].dropna(subset=[COL_URL])
    
    st.success(f"✅ Planilha pronta — **{len(df_input)}** URLs para validar.")

    opcao = st.radio("O que deseja comparar?", ["Meta Description + Título", "Só Meta Description", "Só Título"], horizontal=True)
    ver_titulo = "Título" in opcao
    ver_meta = "Meta" in opcao

    if st.button("🚀 INICIAR AUDITORIA"):
        resultados = []
        try:
            with st.spinner("🤖 Abrindo navegador..."):
                driver = iniciar_driver()

            progresso = st.progress(0)
            status_txt = st.empty()
            
            for idx, row in df_input.iterrows():
                url = row[COL_URL].rstrip("/")
                status_txt.markdown(f"🔍 Analisando: `{url}`")
                
                res = {
                    "URL": url, "Status Título": "—", "Título Esperado": str(row[COL_TITULO]), "Título Site": "",
                    "Status Meta": "—", "Meta Esperada": str(row[COL_META_DESC]), "Meta Site": "", "Resultado": ""
                }

                try:
                    driver.get(url)
                    time.sleep(2)
                    
                    # Verificação de erro 404/Acesso
                    if any(x in driver.title.lower() for x in ["404", "não encontrada", "denied"]):
                        res["Resultado"] = "🔴 Erro de Acesso"
                    else:
                        # Validação Título
                        if ver_titulo:
                            t_site = driver.title.strip()
                            res["Título Site"] = t_site
                            res["Status Título"] = "✅ Igual" if normalizar(row[COL_TITULO]) == normalizar(t_site) else ("❌ Ausente" if not t_site else "⚠️ Diferente")
                        
                        # Validação Meta
                        if ver_meta:
                            try:
                                m_site = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content").strip()
                            except: m_site = ""
                            res["Meta Site"] = m_site
                            res["Status Meta"] = "✅ Igual" if normalizar(row[COL_META_DESC]) == normalizar(m_site) else ("❌ Ausente" if not m_site else "⚠️ Diferente")
                        
                        # Resultado Geral
                        checks = []
                        if ver_titulo: checks.append(res["Status Título"])
                        if ver_meta: checks.append(res["Status Meta"])
                        
                        if all("✅" in s for s in checks): res["Resultado"] = "✅ Tudo certo"
                        elif any("❌" in s for s in checks): res["Resultado"] = "❌ Problemas"
                        else: res["Resultado"] = "⚠️ Divergência"

                except Exception as e:
                    res["Resultado"] = f"⚠️ Erro: {str(e)[:30]}"
                
                resultados.append(res)
                progresso.progress((idx + 1) / len(df_input))

            driver.quit()
            status_txt.empty()
            # Salva na sessão para permitir filtros sem re-executar
            st.session_state['res_audit'] = pd.DataFrame(resultados)
            st.session_state['ver_t'] = ver_titulo
            st.session_state['ver_m'] = ver_meta

        except Exception as e:
            st.error(f"Erro fatal: {e}")

# --- EXIBIÇÃO E FILTROS ---
if 'res_audit' in st.session_state:
    df_res = st.session_state['res_audit']
    
    # Métricas
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", len(df_res))
    m2.metric("✅ Ok", len(df_res[df_res["Resultado"] == "✅ Tudo certo"]))
    m3.metric("⚠️ Div.", len(df_res[df_res["Resultado"] == "⚠️ Divergência"]))
    m4.metric("❌ Erros", len(df_res[df_res["Resultado"].str.contains("❌|🔴")]))

    # FILTRO DINÂMICO
    filtro = st.pills("Filtrar visualização:", ["Todos", "✅ Tudo certo", "⚠️ Divergência", "❌ Problemas"], default="Todos")
    
    df_view = df_res.copy()
    if filtro == "✅ Tudo certo": df_view = df_res[df_res["Resultado"] == "✅ Tudo certo"]
    elif filtro == "⚠️ Divergência": df_view = df_res[df_res["Resultado"] == "⚠️ Divergência"]
    elif filtro == "❌ Problemas": df_view = df_res[df_res["Resultado"].str.contains("❌|🔴")]

    # Cards
    for _, r in df_view.iterrows():
        tipo = "card-ok" if "✅" in r["Resultado"] else ("card-erro" if "❌" in r["Resultado"] or "🔴" in r["Resultado"] else "card-aviso")
        
        detalhes = f"<div class='label'>🔗 <a href='{r['URL']}' target='_blank' class='url-link'>{r['URL']}</a></div>"
        if st.session_state['ver_t']:
            detalhes += f"<div class='label'>📌 Título: {r['Status Título']} | Site: <i>{r['Título Site']}</i></div>"
        if st.session_state['ver_m']:
            detalhes += f"<div class='label'>📝 Meta: {r['Status Meta']} | Site: <i>{r['Meta Site']}</i></div>"

        st.markdown(f"<div class='{tipo}'><b>{r['Resultado']}</b>{detalhes}</div>", unsafe_allow_html=True)

    # Exportação
    csv = df_res.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("📥 Baixar Relatório Completo", csv, "auditoria.csv", "text/csv")
