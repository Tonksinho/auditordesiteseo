# --- INTERFACE DE UPLOAD ATUALIZADA ---
st.divider()
arquivo = st.file_uploader("📂 Suba qualquer planilha Excel (.xlsx)", type=["xlsx"])

if arquivo:
    df_input_raw = pd.read_excel(arquivo)
    colunas_disponiveis = list(df_input_raw.columns)
    
    st.info("🔍 Localizamos as colunas. Por favor, confirme o mapeamento:")
    
    col_selecao = st.columns(3)
    
    # Tentativa de pré-selecionar colunas comuns para facilitar sua vida
    def buscar_idx(lista, termos):
        for i, col in enumerate(lista):
            if any(t in col.lower() for t in termos): return i
        return 0

    with col_selecao[0]:
        col_url_web = st.selectbox("Coluna de URL:", colunas_disponiveis, index=buscar_idx(colunas_disponiveis, ["url", "link", "página"]))
    with col_selecao[1]:
        col_titulo_web = st.selectbox("Coluna de Título:", colunas_disponiveis, index=buscar_idx(colunas_disponiveis, ["titulo", "title", "nome"]))
    with col_selecao[2]:
        col_meta_web = st.selectbox("Coluna de Meta Description:", colunas_disponiveis, index=buscar_idx(colunas_disponiveis, ["meta", "description", "descrição"]))

    # Limpeza e Normalização
    df_input = df_input_raw.copy()
    df_input[col_url_web] = df_input[col_url_web].apply(lambda x: str(x).strip())
    df_input = df_input.dropna(subset=[col_url_web])
    
    st.success(f"✅ Pronto! **{len(df_input)}** URLs mapeadas para auditoria.")

    # --- O RESTANTE DO LOOP (Substitua as variáveis fixas pelas selecionadas) ---
    opcao = st.radio("O que deseja comparar?", ["Meta Description + Título", "Só Meta Description", "Só Título"], horizontal=True)
    st.session_state['ver_t'] = "Título" in opcao
    st.session_state['ver_m'] = "Meta" in opcao

    if st.button("🚀 INICIAR AUDITORIA"):
        resultados = []
        # ... (dentro do loop for idx, row in df_input.iterrows():)
        # Use row[col_url_web], row[col_titulo_web] e row[col_meta_web]
