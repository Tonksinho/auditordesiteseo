import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

# --- CONFIGURAÇÕES ---
PASTA_TRABALHO = r'C:\Users\felip\Downloads\Python script teste'
NOME_ARQUIVO = os.path.join(PASTA_TRABALHO, 'Páginas sem meta description(Educação executiva).csv')
ARQUIVO_VERIFICACAO = os.path.join(PASTA_TRABALHO, 'verificacao_final.csv')

options = Options()
options.add_argument("--headless") # Roda sem abrir a janela do navegador (mais rápido)
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    df = pd.read_csv(NOME_ARQUIVO, sep=';', encoding='utf-8')
    
    # Intervalo solicitado: Linha 1 até 158 (índices 0 a 157)
    inicio = 0
    fim = 599 
    
    resultados = []

    print(f"🔍 Iniciando varredura de SEO em {fim} links...")

    for i in range(inicio, fim):
        url = str(df.loc[i, 'Page URL']).strip()
        print(f"🌐 Verificando [{i+1}/{fim}]: {url}")
        
        try:
            driver.get(url)
            time.sleep(1) # Espera rápida para carregar o head
            
            # Tenta encontrar a meta tag description no HTML
            try:
                meta_desc = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
                status = "✅ COM DESCRIÇÃO" if meta_desc.strip() else "⚠️ TAG VAZIA"
            except:
                meta_desc = "NÃO ENCONTRADA"
                status = "❌ SEM TAG"

            resultados.append({
                'Linha Excel': i + 2,
                'URL': url,
                'Status': status,
                'Conteúdo Encontrado': meta_desc[:50] + "..." if len(meta_desc) > 50 else meta_desc
            })

        except Exception as e:
            resultados.append({'Linha Excel': i + 2, 'URL': url, 'Status': f"ERRO: {str(e)[:30]}", 'Conteúdo Encontrado': ""})

    # Salva o resultado em um novo CSV
    df_resumo = pd.DataFrame(resultados)
    df_resumo.to_csv(ARQUIVO_VERIFICACAO, index=False, sep=';', encoding='utf-8-sig')
    
    print(f"\n🏁 Verificação concluída! Confira o arquivo: {ARQUIVO_VERIFICACAO}")

except Exception as e:
    print(f"❌ Erro ao processar planilha: {e}")
finally:
    driver.quit()
