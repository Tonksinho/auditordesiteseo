import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import time
import random
from datetime import datetime

st.set_page_config(page_title="Auditor SEO", layout="centered", page_icon="🔍")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; max-width: 750px; }
    h1 { text-align: center; color: #004685; font-size: 24px !important; }
    .stButton>button { width: 100%; background-color: #004685; color: white; height: 3em; }
    .stButton>button:hover { background-color: #00336b; }
    .status-ok    { color: #2e7d32; font-weight: bold; }
    .status-nok   { color: #c62828; font-weight: bold; }
    .status-warn  { color: #f57c00; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- LOGO FGV ---
col_logo = st.columns([1, 2, 1])
with col_logo[1]:
    try:
        st.image("fgv-logo-0.png", use_container_width=True)
    except Exception:
        pass  # logo opcional

st.title("🔍 Auditor de Meta Description")

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

META_MIN = 120
META_MAX = 160

# Pool de User-Agents reais para rotacionar
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
]


def get_headers() -> dict:
    """Retorna headers completos com User-Agent aleatório a cada chamada."""
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "DNT": "1",
    }


def validar_url(url: str) -> str | None:
    """Normaliza e valida a URL. Retorna None se inválida."""
    url = url.strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
        return url
    except Exception:
        return None


def auditar_url(url: str, delay_min: float = 0.5, delay_max: float = 2.0) -> dict:
    """Audita uma única URL usando requests + BeautifulSoup."""
    res = {
        "URL": url,
        "Status HTTP": "",
        "Resultado Meta": "",
        "Meta Description": "",
        "og:description": "",
        "Tamanho (chars)": "",
        "Avaliação Tamanho": "",
        "Redirect Final": "",
    }

    # Delay aleatório para não parecer bot
    time.sleep(random.uniform(delay_min, delay_max))

    tentativas = 2
    for tentativa in range(tentativas):
        try:
            resp = requests.get(
                url,
                headers=get_headers(),  # headers novos a cada tentativa
                timeout=12,
                allow_redirects=True,
            )
            res["Status HTTP"] = resp.status_code

            # URL final após redirects
            if resp.url != url:
                res["Redirect Final"] = resp.url

            # Se bloqueado, espera mais e tenta de novo
            if resp.status_code in (403, 429) and tentativa < tentativas - 1:
                time.sleep(random.uniform(3.0, 6.0))
                continue

            if resp.status_code >= 400:
                res["Resultado Meta"] = f"⚠️ HTTP {resp.status_code}"
                return res

            soup = BeautifulSoup(resp.text, "html.parser")

            # Meta description
            meta_tag = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
            conteudo = ""
            if meta_tag:
                conteudo = (meta_tag.get("content") or "").strip()

            # og:description
            og_tag = soup.find("meta", property="og:description")
            og_desc = ""
            if og_tag:
                og_desc = (og_tag.get("content") or "").strip()

            res["og:description"] = og_desc

            if conteudo:
                tam = len(conteudo)
                res["Resultado Meta"] = "✅ Preenchida"
                res["Meta Description"] = conteudo
                res["Tamanho (chars)"] = tam
                if tam < META_MIN:
                    res["Avaliação Tamanho"] = f"⚠️ Curta ({tam} chars, mín. {META_MIN})"
                elif tam > META_MAX:
                    res["Avaliação Tamanho"] = f"⚠️ Longa ({tam} chars, máx. {META_MAX})"
                else:
                    res["Avaliação Tamanho"] = f"✅ Ideal ({tam} chars)"
            else:
                res["Resultado Meta"] = "❌ Ausente ou vazia"
                res["Tamanho (chars)"] = 0
                res["Avaliação Tamanho"] = "—"

            return res  # sucesso, sai do loop

        except requests.exceptions.Timeout:
            res["Resultado Meta"] = "⚠️ Timeout"
            res["Status HTTP"] = "Timeout"
        except requests.exceptions.ConnectionError:
            res["Resultado Meta"] = "⚠️ Erro de conexão"
            res["Status HTTP"] = "Conexão recusada"
        except Exception as e:
            res["Resultado Meta"] = "⚠️ Erro inesperado"
            res["Status HTTP"] = str(e)[:60]

    return res


def carregar_urls(arquivo) -> list[str]:
    nome = arquivo.name.lower()
    if nome.endswith(".txt"):
        linhas = arquivo.read().decode("utf-8").splitlines()
        return [l.strip() for l in linhas if l.strip()]
    elif nome.endswith(".xlsx"):
        return None  # tratado fora


def detectar_duplicatas(df: pd.DataFrame) -> pd.DataFrame:
    """Marca meta descriptions duplicadas."""
    mask = (
        df["Meta Description"].notna()
        & (df["Meta Description"] != "")
        & df["Meta Description"].duplicated(keep=False)
    )
    df["Duplicata?"] = mask.map({True: "⚠️ Duplicada", False: ""})
    return df


# ──────────────────────────────────────────────
# SESSION STATE — persiste resultados
# ──────────────────────────────────────────────
if "df_resultado" not in st.session_state:
    st.session_state["df_resultado"] = None
if "cancelar" not in st.session_state:
    st.session_state["cancelar"] = False

# ──────────────────────────────────────────────
# UPLOAD
# ──────────────────────────────────────────────
arquivo = st.file_uploader("📂 Suba a lista de URLs (.xlsx ou .txt)", type=["xlsx", "txt"])

urls_list = []

if arquivo:
    nome = arquivo.name.lower()
    if nome.endswith(".txt"):
        urls_list = carregar_urls(arquivo)
    elif nome.endswith(".xlsx"):
        df_raw = pd.read_excel(arquivo)
        st.divider()
        cols = list(df_raw.columns)
        c_url = st.selectbox("Coluna de URL *", cols, index=0)
        urls_list = [str(r).strip() for r in df_raw[c_url] if str(r).strip()]

    # Valida e normaliza
    urls_validas = []
    urls_invalidas = []
    for u in urls_list:
        v = validar_url(u)
        if v:
            urls_validas.append(v)
        else:
            urls_invalidas.append(u)

    if urls_invalidas:
        st.warning(f"⚠️ {len(urls_invalidas)} URL(s) inválida(s) foram ignoradas.")

    st.info(f"Total de URLs válidas para verificar: **{len(urls_validas)}**")

    workers = st.slider("⚡ Requisições paralelas", min_value=1, max_value=5, value=2,
                        help="Menos workers = menos chance de bloqueio. Recomendado: 2 ou 3.")

    delay_min, delay_max = st.select_slider(
        "⏱ Delay entre requisições (segundos)",
        options=[0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0],
        value=(1.0, 2.5),
        help="Delay aleatório entre cada requisição. Valores maiores evitam bloqueios.",
    )

    col_btn1, col_btn2 = st.columns(2)
    iniciar = col_btn1.button("🚀 INICIAR VERIFICAÇÃO")
    cancelar = col_btn2.button("🛑 CANCELAR")

    if cancelar:
        st.session_state["cancelar"] = True

    if iniciar and urls_validas:
        st.session_state["cancelar"] = False
        resultados = []
        total = len(urls_validas)

        progresso = st.progress(0)
        status_txt = st.empty()
        tempo_txt = st.empty()
        inicio = time.time()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(auditar_url, url, delay_min, delay_max): url
                for url in urls_validas
            }

            concluidos = 0
            for future in as_completed(futures):
                if st.session_state["cancelar"]:
                    executor.shutdown(wait=False, cancel_futures=True)
                    status_txt.warning("⛔ Verificação cancelada pelo usuário.")
                    break

                res = future.result()
                resultados.append(res)
                concluidos += 1

                elapsed = time.time() - inicio
                velocidade = concluidos / elapsed if elapsed > 0 else 1
                restante = (total - concluidos) / velocidade if velocidade > 0 else 0

                status_txt.text(f"Verificando… {concluidos}/{total} — {res['URL'][:60]}")
                tempo_txt.text(f"⏱ Tempo decorrido: {elapsed:.0f}s | Estimativa restante: {restante:.0f}s")
                progresso.progress(concluidos / total)

        if resultados:
            df_final = pd.DataFrame(resultados)
            df_final = detectar_duplicatas(df_final)
            st.session_state["df_resultado"] = df_final

            if not st.session_state["cancelar"]:
                status_txt.success(f"✅ Verificação concluída em {time.time() - inicio:.1f}s!")
                tempo_txt.empty()


# ──────────────────────────────────────────────
# EXIBIR RESULTADOS (persistidos no session_state)
# ──────────────────────────────────────────────
df_final = st.session_state.get("df_resultado")

if df_final is not None and not df_final.empty:
    st.divider()
    st.subheader("📊 Resultados")

    ok    = (df_final["Resultado Meta"] == "✅ Preenchida").sum()
    nok   = (df_final["Resultado Meta"] == "❌ Ausente ou vazia").sum()
    erro  = df_final["Resultado Meta"].str.startswith("⚠️").sum()
    ideal = (df_final["Avaliação Tamanho"].str.startswith("✅")).sum()
    dup   = (df_final.get("Duplicata?", pd.Series()) == "⚠️ Duplicada").sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("✅ Preenchidas", ok)
    col2.metric("❌ Ausentes", nok)
    col3.metric("⚠️ Erros/HTTP", erro)
    col4.metric("📏 Tamanho ideal", ideal)
    col5.metric("🔁 Duplicadas", dup)

    # Filtro rápido
    filtro = st.selectbox("Filtrar por resultado:", [
        "Todos",
        "✅ Preenchida",
        "❌ Ausente ou vazia",
        "⚠️ Erros",
        "⚠️ Duplicadas",
    ])

    df_view = df_final.copy()
    if filtro == "⚠️ Erros":
        df_view = df_view[df_view["Resultado Meta"].str.startswith("⚠️")]
    elif filtro == "⚠️ Duplicadas":
        df_view = df_view[df_view.get("Duplicata?", "") == "⚠️ Duplicada"]
    elif filtro != "Todos":
        df_view = df_view[df_view["Resultado Meta"] == filtro]

    st.dataframe(df_view, use_container_width=True)

    # Download
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    csv = df_final.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar resultado CSV",
        data=csv,
        file_name=f"auditoria_meta_{ts}.csv",
        mime="text/csv",
    )
