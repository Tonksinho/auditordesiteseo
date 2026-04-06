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

# Estilos CSS Personalizados
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
    .url-link { color: #004685; text-decoration: none; font-weight: bold; font-size: 12px; }
    .url-link:hover { text-decoration: underline; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO ESTADO ---
if 'res_audit' not in st.session_state:
    st.session_state['res_audit'] = pd.DataFrame()
if 'ver_t' not in st.session_state:
    st.session_state['ver_t'] = True
if 'ver_m' not in st.session_state:
    st.session_state['ver_m'] = True

# --- LOGO ---
if os.path.exists("fgv-logo-0.png"):
    st.image("fgv-logo-0.png", width=120)
else:
    st.markdown("<h2 style='text-align:center;color:#004685;'>FGV</h2>", unsafe_allow_html=True)

st.title("Auditor de Meta Tags")

# --- CONFIGURAÇÕES DA PLANILHA ---
COL_URL       = "URL"
COL_TITULO    = "Título da Página (até 60 caracteres)"
COL_META_DESC = "Meta Description (até 160 caracteres)"

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

# --- INTERFACE DE UPLOAD ---
st.divider()
arquivo = st.file_uploader("📂 Suba sua planilha EPPG (.xlsx)", type=["xlsx"])

if arquivo:
    df_input = pd.read_excel(arquivo)
    df_input.columns = df_input.columns.str.strip()

    # Verifica colunas
    colunas_faltando = [c for c in [COL_URL, COL_TITULO, COL_META_DESC] if c not in df_input.columns]
    if colunas_faltando:
        st.error(f"Colunas não encontradas: {colunas_faltando}")
        st.stop()

    # Correção automática de EPPG -> EPPGE
    df_input[COL_URL] = df_input[COL_URL].apply(lambda x: str(x).replace("eppg.fgv.br", "eppge.fgv.br").replace("EPPG.fgv.br", "eppge.fgv.br").strip())
    df_input = df_input[[COL_URL, COL_TITULO, COL_META_DESC]].dropna(subset=[COL_URL])
    
    st.success(f"✅ Planilha carregada: **{len(df_input)}** URLs encontradas.")

    opcao = st.radio("O que deseja comparar?", ["Meta Description + Título", "Só Meta Description", "Só Título"], horizontal=True)
    st.session_state['ver_t'] = "Título" in opcao
    st.session_state['ver_m'] = "Meta" in opcao

    if st.button("🚀 INICIAR AUDITORIA"):
        resultados = []
        try:
            with st.spinner("🤖 Iniciando auditoria automatizada..."):
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
                        
                        if any(x in driver.title.lower() for x in ["404", "não encontrada", "denied", "forbidden"]):
                            res["Resultado"] = "🔴 Erro de Acesso / 404"
                        else:
                            # Validação Título
                            if st.session_state['ver_t']:
                                t_site = driver.title.strip()
                                res["Título Site"] = t_site
                                res["Status Título"] = "✅ Igual" if normalizar(row[COL_TITULO]) == normalizar(t_site) else ("❌ Ausente" if not t_site else "⚠️ Diferente")
                            
                            # Validação Meta
                            if st.session_state['ver_m']:
                                try:
                                    m_site = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content").strip()
                                except: m_site = ""
                                res["Meta Site"] = m_site
                                res["Status Meta"] = "✅ Igual" if normalizar(row[COL_META_DESC]) == normalizar(m_site) else ("❌ Ausente" if not m_site else "⚠️ Diferente")
                            
                            # Logica Resultado Geral
                            checks = []
                            if st.session_state['ver_t']: checks.append(res["Status Título"])
                            if st.session_state['ver_m']: checks.append(res["Status Meta"])
                            
                            if all("✅" in s for s in checks): res["Resultado"] = "✅ Tudo certo"
                            elif any("❌" in s for s in checks): res["Resultado"] = "❌ Problemas"
                            else: res["Resultado"] = "⚠️ Divergência"

                    except Exception as e:
                        res["Resultado"] = f"⚠️ Falha Técnica: {str(e)[:30]}"
                    
                    resultados.append(res)
                    progresso.progress((idx + 1) / len(df_input))

                driver.quit()
                status_txt.empty()
                st.session_state['res_audit'] = pd.DataFrame(resultados)
                st.balloons()

        except Exception as e:
            st.error(f"Erro ao iniciar driver: {e}")

# --- EXIBIÇÃO DE RESULTADOS E FILTROS ---
if not st.session_state['res_audit'].empty:
    df_res = st.session_state['res_audit']
    
    st.divider()
    st.subheader("📊 Resultados da Auditoria")
    
    # Métricas formatadas
    m1, m2, m3, m4 = st.columns(4)
    total_urls = len(df_res)
    total_ok = len(df_res[df_res["Resultado"] == "✅ Tudo certo"])
    total_div = len(df_res[df_res["Resultado"] == "⚠️ Divergência"])
    total_prob = len(df_res[df_res["Resultado"].str.contains("❌|🔴", na=False)])

    m1.metric("Total", total_urls)
    m2.metric("✅ Ok", total_ok)
    m3.metric("⚠️ Div.", total_div)
    m4.metric("❌ Erros", total_prob)

    # Filtro Dinâmico com Pills
    filtro = st.pills("Visualizar apenas:", ["Todos", "✅ Tudo certo", "⚠️ Divergência", "❌ Problemas"], default="Todos")
    
    df_view = df_res.copy()
    if filtro == "✅ Tudo certo": 
        df_view = df_res[df_res["Resultado"] == "✅ Tudo certo"]
    elif filtro == "⚠️ Divergência": 
        df_view = df_res[df_res["Resultado"] == "⚠️ Divergência"]
    elif filtro == "❌ Problemas": 
        df_view = df_res[df_res["Resultado"].str.contains("❌|🔴", na=False)]

    st.markdown(f"Exibindo **{len(df_view)}** itens filtrados.")

    # Renderização dos Cards
    for _, r in df_view.iterrows():
        tipo_css = "card-ok" if "✅" in r["Resultado"] else ("card-erro" if "❌" in r["Resultado"] or "🔴" in r["Resultado"] else "card-aviso")
        
        # URL clicável para conferência rápida
        info_html = f"<div class='label'>🔗 URL: <a href='{r['URL']}' target='_blank' class='url-link'>{r['URL']}</a></div>"
        
        if st.session_state.get('ver_t'):
            info_html += f"<div class='label'>📌 <b>Título:</b> {r['Status Título']} | No site: <i>{r['Título Site']}</i></div>"
        if st.session_state.get('ver_m'):
            info_html += f"<div class='label'>📝 <b>Meta:</b> {r['Status Meta']} | No site: <i>{r['Meta Site']}</i></div>"

        st.markdown(f"<div class='{tipo_css}'><b>{r['Resultado']}</b>{info_html}</div>", unsafe_allow_html=True)

    # Exportação de Dados
    st.divider()
    c_down1, c_down2 = st.columns(2)
    csv_completo = df_res.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
    c_down1.download_button("📥 Baixar Relatório Full (CSV)", csv_completo, "relatorio_seo_completo.csv", "text/csv")
    
    df_so_erros = df_res[df_res["Resultado"].str.contains("❌|🔴|⚠️", na=False)]
    if not df_so_erros.empty:
        csv_erros = df_so_erros.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
        c_down2.download_button("🔴 Baixar Apenas Erros/Div", csv_erros, "erros_seo.csv", "text/csv")

elif arquivo:
    st.info("Configurações prontas! Clique no botão **🚀 INICIAR AUDITORIA** para começar o processo.")
