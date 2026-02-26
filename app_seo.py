# --- LÓGICA DO ROBÔ (Ajustada para Cloud) ---
def rodar_auditoria(lista_urls):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Este caminho é o padrão onde o packages.txt instala o Chromium no Streamlit
    options.binary_location = "/usr/bin/chromium" 
    
    # Identidade visual para o site não bloquear
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # ... resto do seu código de loop ...
    
    # MUITO IMPORTANTE: Define o caminho do Chromium no Linux do Streamlit
    options.binary_location = "/usr/bin/chromium" 
    
    # Identificando como navegador real para evitar bloqueios
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Instala o driver compatível automaticamente
    service = Service(ChromeDriverManager().install())
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        st.error(f"Erro ao iniciar o Navegador: {e}")
        return pd.DataFrame()

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
                # Busca a meta description
                meta_desc = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
                status = "✅ COM DESCRIÇÃO" if meta_desc.strip() else "⚠️ TAG VAZIA"
            except:
                meta_desc = "Não encontrada no HTML"
                status = "❌ SEM TAG"

            resultados.append({'URL': url, 'Status': status, 'Conteúdo': meta_desc})
        except Exception as e:
            resultados.append({'URL': url, 'Status': "⚠️ ERRO DE ACESSO", 'Conteúdo': "Falha ao carregar página"})
            
    driver.quit()
    return pd.DataFrame(resultados)

