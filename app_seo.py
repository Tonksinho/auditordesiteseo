import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urlparse
import streamlit.components.v1 as components

# Configuração inicial
st.set_page_config(page_title="MetaAuditor Pro", layout="wide", page_icon="🔍")

# --- LÓGICA DE AUDITORIA (Resumida para o exemplo) ---
def auditar_url(url):
    # Simulação de processamento (Mantenha sua função original aqui)
    time.sleep(0.1)
    status = random.choice(["Optimized", "Too Short", "Missing", "Too Long"])
    length = random.randint(0, 95) if status != "Missing" else 0
    return {
        "url": url,
        "status": status,
        "length": length,
        "title": f"Exemplo de Meta para {url}" if status != "Missing" else "N/A"
    }

# --- FUNÇÃO PARA GERAR O HTML DINÂMICO ---
def render_custom_dashboard(data_list):
    # Cálculos para os cards de métricas
    total = len(data_list)
    filled = len([d for d in data_list if d['status'] == "Optimized"])
    missing = len([d for d in data_list if d['status'] == "Missing"])
    errors = len([d for d in data_list if d['status'] in ["Too Short", "Too Long"]])
    ideal_pct = (filled / total * 100) if total > 0 else 0

    # Construção das linhas da tabela
    table_rows = ""
    for item in data_list:
        status_class = {
            "Optimized": "bg-secondary-container text-on-secondary-container",
            "Too Short": "bg-tertiary-fixed text-on-tertiary-fixed-variant",
            "Missing": "bg-error-container text-on-error-container",
            "Too Long": "bg-error-container text-on-error-container"
        }.get(item['status'], "bg-surface-variant")

        icon = "check_circle" if item['status'] == "Optimized" else "warning" if "Too" in item['status'] else "cancel"
        bar_color = "bg-secondary" if item['status'] == "Optimized" else "bg-tertiary-container" if "Short" in item['status'] else "bg-error"
        
        table_rows += f"""
        <tr class="hover:bg-surface-container-low transition-colors duration-150">
            <td class="px-6 py-4">
                <div class="flex flex-col">
                    <span class="font-data-mono text-[13px] text-primary">{item['url']}</span>
                    <span class="text-[10px] text-outline">{item['title']}</span>
                </div>
            </td>
            <td class="px-6 py-4">
                <span class="inline-flex items-center gap-1 {status_class} px-2 py-1 rounded-full text-[11px] font-bold">
                    <span class="material-symbols-outlined text-[14px]">{icon}</span> {item['status']}
                </span>
            </td>
            <td class="px-6 py-4">
                <div class="flex items-center gap-4">
                    <span class="font-body-sm text-body-sm text-on-surface">{item['length']} chars</span>
                    <div class="h-1.5 w-32 bg-surface-container rounded-full overflow-hidden">
                        <div class="h-full {bar_color}" style="width: {min(item['length'], 100)}%"></div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4">
                <button class="text-primary hover:underline font-label-bold text-[12px]">Detalhes</button>
            </td>
        </tr>
        """

    # O HTML completo (Baseado no seu template)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet"/>
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #f9f9ff; margin: 0; padding: 20px; }}
            .material-symbols-outlined {{ font-variation-settings: 'FILL' 1; }}
        </style>
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            primary: "#00305e", "on-primary": "#ffffff",
                            secondary: "#1b6d24", "secondary-container": "#a0f399",
                            error: "#ba1a1a", "error-container": "#ffdad6",
                            "surface-container-low": "#f3f3f9", "outline-variant": "#c2c6d2"
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <div class="max-w-7xl mx-auto space-y-6">
            <!-- Metricas -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="bg-white border border-outline-variant p-4 rounded-xl">
                    <p class="text-xs font-bold text-gray-500 uppercase">Preenchidas</p>
                    <h3 class="text-2xl font-bold text-secondary">{filled}</h3>
                </div>
                <div class="bg-white border border-outline-variant p-4 rounded-xl">
                    <p class="text-xs font-bold text-gray-500 uppercase">Ausentes</p>
                    <h3 class="text-2xl font-bold text-error">{missing}</h3>
                </div>
                <div class="bg-white border border-outline-variant p-4 rounded-xl">
                    <p class="text-xs font-bold text-gray-500 uppercase">Alertas</p>
                    <h3 class="text-2xl font-bold text-orange-600">{errors}</h3>
                </div>
                <div class="bg-white border border-outline-variant p-4 rounded-xl">
                    <p class="text-xs font-bold text-gray-500 uppercase">Saúde Meta</p>
                    <h3 class="text-2xl font-bold text-primary">{ideal_pct:.1f}%</h3>
                </div>
            </div>

            <!-- Tabela -->
            <div class="bg-white border border-outline-variant rounded-xl overflow-hidden">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-gray-50 border-b border-outline-variant">
                        <tr>
                            <th class="px-6 py-3 text-[11px] font-bold uppercase text-gray-500">URL Pathway</th>
                            <th class="px-6 py-3 text-[11px] font-bold uppercase text-gray-500">Status</th>
                            <th class="px-6 py-3 text-[11px] font-bold uppercase text-gray-500">Tamanho</th>
                            <th class="px-6 py-3 text-[11px] font-bold uppercase text-gray-500">Ação</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# --- INTERFACE STREAMLIT ---
st.title("MetaAuditor Engine")

arquivo = st.file_uploader("Suba sua lista", type=["txt", "xlsx"])

if arquivo:
    # Lógica de extração de URLs simplificada
    urls = ["exemplo.com/home", "exemplo.com/sobre", "exemplo.com/produto-erro", "exemplo.com/blog"]
    
    if st.button("Iniciar Auditoria"):
        resultados = []
        progresso = st.progress(0)
        
        for i, url in enumerate(urls):
            res = auditar_url(url)
            resultados.append(res)
            progresso.progress((i + 1) / len(urls))
        
        # EXIBIÇÃO DA UI CUSTOMIZADA
        st.subheader("Relatório de Auditoria")
        dashboard_html = render_custom_dashboard(resultados)
        components.html(dashboard_html, height=600, scrolling=True)
        
        # Download do CSV original
        df = pd.DataFrame(resultados)
        st.download_button("Exportar CSV", df.to_csv(index=False), "auditoria.csv")
