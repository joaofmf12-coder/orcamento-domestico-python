"""
╔══════════════════════════════════════════════════════════════╗
║                  🔮 PREVISÕES FINANCEIRAS                    ║
║                                                              ║
║  Gestão de receitas e despesas previstas                     ║
║  Com suporte a previsões recorrentes (mensais)               ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from database.connection import get_engine
from sqlalchemy import text
import calendar


def formatar_moeda(valor):
    """Formata valor para R$ brasileiro"""
    if pd.isna(valor) or valor is None:
        return "R$ 0,00"
    try:
        valor = float(valor)
        if valor < 0:
            return f"-R$ {abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


# ==========================================
# FUNÇÕES DE BANCO DE DADOS
# ==========================================

def get_previsoes(ano, mes=None, status=None, tipo=None):
    """Busca previsões do banco de dados"""
    engine = get_engine()
    
    filtros = [f"YEAR(data) = {ano}"]
    if mes and mes > 0:
        filtros.append(f"MONTH(data) = {mes}")
    if status and status != "Todas":
        filtros.append(f"status = '{status}'")
    if tipo and tipo != "Todos":
        filtros.append(f"tipo = '{tipo}'")
    
    where_clause = " AND ".join(filtros)
    
    query = f"""
        SELECT id, data, tipo, categoria, subcategoria, valor, descricao, status
        FROM previsoes
        WHERE {where_clause}
        ORDER BY data, tipo, categoria
    """
    return pd.read_sql(query, engine)


def atualizar_status_previsao(id_previsao, novo_status):
    """Atualiza o status de uma previsão"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("UPDATE previsoes SET status = :status WHERE id = :id")
        conn.execute(query, {"status": novo_status, "id": id_previsao})
        conn.commit()


def criar_previsao(data, tipo, categoria, subcategoria, valor, descricao):
    """Cria uma nova previsão única"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("""
            INSERT INTO previsoes (data, tipo, categoria, subcategoria, valor, descricao, status)
            VALUES (:data, :tipo, :categoria, :subcategoria, :valor, :descricao, 'Ativa')
        """)
        conn.execute(query, {
            "data": data, "tipo": tipo, "categoria": categoria,
            "subcategoria": subcategoria, "valor": valor, "descricao": descricao
        })
        conn.commit()


def criar_previsoes_recorrentes(data_inicio, data_fim, dia_vencimento, tipo, categoria, subcategoria, valor, descricao_base):
    """Cria previsões recorrentes para um período (igual ao Excel)"""
    engine = get_engine()
    
    meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    previsoes_criadas = 0
    data_atual = date(data_inicio.year, data_inicio.month, 1)
    data_final = date(data_fim.year, data_fim.month, 1)
    
    with engine.connect() as conn:
        while data_atual <= data_final:
            # Ajustar o dia do mês
            ultimo_dia = calendar.monthrange(data_atual.year, data_atual.month)[1]
            dia_ajustado = min(dia_vencimento, ultimo_dia)
            data_previsao = date(data_atual.year, data_atual.month, dia_ajustado)
            
            # Gerar descrição com mês/ano (igual ao Excel)
            mes_nome = meses_pt[data_previsao.month - 1]
            descricao = f"{descricao_base} - {mes_nome}/{data_previsao.year}"
            
            query = text("""
                INSERT INTO previsoes (data, tipo, categoria, subcategoria, valor, descricao, status)
                VALUES (:data, :tipo, :categoria, :subcategoria, :valor, :descricao, 'Ativa')
            """)
            conn.execute(query, {
                "data": data_previsao, "tipo": tipo, "categoria": categoria,
                "subcategoria": subcategoria, "valor": valor, "descricao": descricao
            })
            
            previsoes_criadas += 1
            # Avançar para o próximo mês
            if data_atual.month == 12:
                data_atual = date(data_atual.year + 1, 1, 1)
            else:
                data_atual = date(data_atual.year, data_atual.month + 1, 1)
        
        conn.commit()
    
    return previsoes_criadas


def get_categorias(tipo):
    """Busca categorias por tipo"""
    engine = get_engine()
    query = f"""
        SELECT DISTINCT categoria 
        FROM categorias 
        WHERE tipo = '{tipo}' AND ativo = 1
        ORDER BY categoria
    """
    df = pd.read_sql(query, engine)
    return df['categoria'].tolist() if not df.empty else []


def get_subcategorias(tipo, categoria):
    """Busca subcategorias"""
    engine = get_engine()
    query = f"""
        SELECT DISTINCT subcategoria 
        FROM categorias 
        WHERE tipo = '{tipo}' AND categoria = '{categoria}' AND ativo = 1 AND subcategoria IS NOT NULL
        ORDER BY subcategoria
    """
    df = pd.read_sql(query, engine)
    return df['subcategoria'].tolist() if not df.empty else []


def excluir_previsao(id_previsao):
    """Exclui uma previsão"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("DELETE FROM previsoes WHERE id = :id")
        conn.execute(query, {"id": id_previsao})
        conn.commit()


def excluir_previsoes_em_lote(ids):
    """Exclui múltiplas previsões"""
    engine = get_engine()
    with engine.connect() as conn:
        for id_prev in ids:
            query = text("DELETE FROM previsoes WHERE id = :id")
            conn.execute(query, {"id": id_prev})
        conn.commit()


# ==========================================
# INTERFACE STREAMLIT
# ==========================================

def mostrar_previsoes():
    st.title("🔮 Previsões Financeiras")
    st.markdown("*Gestão de Receitas e Despesas Previstas - Com suporte a previsões recorrentes*")
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Visualizar", 
        "➕ Nova Previsão", 
        "🔄 Previsão Recorrente",
        "✏️ Gerenciar"
    ])
    
    # ------------------------------------------
    # TAB 1: VISUALIZAR PREVISÕES
    # ------------------------------------------
    with tab1:
        st.subheader("📋 Visualizar Previsões")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ano = st.selectbox("📅 Ano:", [2025, 2026, 2027], index=1, key="v_ano")
        with col2:
            meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                     "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_nome = st.selectbox("📆 Mês:", meses, key="v_mes")
            mes = meses.index(mes_nome) if mes_nome != "Todos" else 0
        with col3:
            status_filtro = st.selectbox("✅ Status:", ["Todas", "Ativa", "Cancelada", "Realizada"], key="v_status")
        with col4:
            tipo_filtro = st.selectbox("📂 Tipo:", ["Todos", "Receita", "Despesa"], key="v_tipo")
        
        # Buscar dados
        df_prev = get_previsoes(ano, mes, status_filtro, tipo_filtro)
        
        # KPIs
        st.markdown("---")
        df_ativas = df_prev[df_prev['status'] == 'Ativa'] if not df_prev.empty else pd.DataFrame()
        
        total_rec = df_ativas[df_ativas['tipo'] == 'Receita']['valor'].sum() if not df_ativas.empty else 0
        total_desp = df_ativas[df_ativas['tipo'] == 'Despesa']['valor'].sum() if not df_ativas.empty else 0
        saldo = total_rec - total_desp
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📥 Receitas Ativas", formatar_moeda(total_rec))
        with col2:
            st.metric("📤 Despesas Ativas", formatar_moeda(total_desp))
        with col3:
            st.metric("💵 Saldo Previsto", formatar_moeda(saldo), delta_color="normal" if saldo >= 0 else "inverse")
        with col4:
            st.metric("📊 Total Previsões", len(df_prev))
        
        # Tabela
        if not df_prev.empty:
            df_display = df_prev.copy()
            df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
            df_display['valor'] = df_display['valor'].apply(formatar_moeda)
            df_display['status'] = df_display['status'].apply(
                lambda s: '🟢 Ativa' if s == 'Ativa' else ('❌ Cancelada' if s == 'Cancelada' else '✅ Realizada')
            )
            df_display['tipo'] = df_display['tipo'].apply(lambda t: '📥 Receita' if t == 'Receita' else '📤 Despesa')
            
            df_show = df_display[['data', 'tipo', 'categoria', 'subcategoria', 'valor', 'descricao', 'status']]
            df_show.columns = ['📅 Data', '📂 Tipo', '📁 Categoria', '📋 Subcategoria', '💰 Valor', '📝 Descrição', '✅ Status']
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=400)
            
            # Contadores
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🟢 Ativas", len(df_prev[df_prev['status'] == 'Ativa']))
            with col2:
                st.metric("❌ Canceladas", len(df_prev[df_prev['status'] == 'Cancelada']))
            with col3:
                st.metric("✅ Realizadas", len(df_prev[df_prev['status'] == 'Realizada']))
        else:
            st.info("📭 Nenhuma previsão encontrada.")
    
     # ------------------------------------------
    # TAB 2: NOVA PREVISÃO (ÚNICA) - CORRIGIDO
    # ------------------------------------------
    with tab2:
        st.subheader("➕ Criar Nova Previsão (Única)")
        st.info("💡 Cria uma previsão para uma data específica")
        
        # FORA DO FORMULÁRIO: Tipo e Categoria para atualização dinâmica
        col_tipo, col_cat = st.columns(2)
        
        with col_tipo:
            tipo_prev = st.selectbox("📂 Tipo:", ["Despesa", "Receita"], key="n_tipo_fora")
        
        with col_cat:
            # Buscar categorias baseado no tipo selecionado
            categorias = get_categorias(tipo_prev)
            categoria_prev = st.selectbox("📁 Categoria:", categorias if categorias else [""], key="n_cat_fora")
        
        # Buscar subcategorias baseado no tipo e categoria
        subcategorias = get_subcategorias(tipo_prev, categoria_prev) if categoria_prev else []
        
        with st.form("form_nova_prev", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                data_prev = st.date_input("📅 Data:", value=date.today(), key="n_data")
                # Mostrar tipo e categoria selecionados (somente leitura)
                st.info(f"📂 Tipo: **{tipo_prev}** | 📁 Categoria: **{categoria_prev}**")
            
            with col2:
                # Subcategoria agora atualiza corretamente
                subcategoria_prev = st.selectbox("📋 Subcategoria:", subcategorias if subcategorias else [""], key="n_subcat")
                valor_prev = st.number_input("💰 Valor:", min_value=0.0, step=100.0, format="%.2f", key="n_valor")
                descricao_prev = st.text_input("📝 Descrição:", key="n_desc")
            
            if st.form_submit_button("💾 Salvar Previsão", type="primary"):
                if categoria_prev and subcategoria_prev and valor_prev > 0:
                    criar_previsao(data_prev, tipo_prev, categoria_prev, subcategoria_prev, valor_prev, descricao_prev)
                    st.success("✅ Previsão criada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos!")
    
    # ------------------------------------------
    # TAB 3: PREVISÃO RECORRENTE - CORRIGIDO
    # ------------------------------------------
    with tab3:
        st.subheader("🔄 Criar Previsão Recorrente (Mensal)")
        st.info("💡 Cria automaticamente previsões para vários meses - Igual à aba PREVISOES do Excel!")
        
        # FORA DO FORMULÁRIO: Tipo e Categoria para atualização dinâmica
        col_tipo_r, col_cat_r = st.columns(2)
        
        with col_tipo_r:
            tipo_rec = st.selectbox("📂 Tipo:", ["Despesa", "Receita"], key="r_tipo_fora")
        
        with col_cat_r:
            # Buscar categorias baseado no tipo selecionado
            categorias_rec = get_categorias(tipo_rec)
            categoria_rec = st.selectbox("📁 Categoria:", categorias_rec if categorias_rec else [""], key="r_cat_fora")
        
        # Buscar subcategorias baseado no tipo e categoria
        subcategorias_rec = get_subcategorias(tipo_rec, categoria_rec) if categoria_rec else []
        
        with st.form("form_prev_recorrente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 📂 Dados da Previsão")
                # Mostrar tipo e categoria selecionados (somente leitura)
                st.info(f"📂 Tipo: **{tipo_rec}** | 📁 Categoria: **{categoria_rec}**")
                subcategoria_rec = st.selectbox("Subcategoria:", subcategorias_rec if subcategorias_rec else [""], key="r_subcat")
                valor_rec = st.number_input("💰 Valor Mensal:", min_value=0.0, step=100.0, format="%.2f", key="r_valor")
                descricao_rec = st.text_input("📝 Descrição Base:", placeholder="Ex: Energia Elétrica", key="r_desc")
            
            with col2:
                st.markdown("##### 📅 Período de Recorrência")
                hoje = date.today()
                
                col_inicio, col_fim = st.columns(2)
                with col_inicio:
                    mes_inicio = st.selectbox("Mês Inicial:", list(range(1, 13)), index=hoje.month - 1, key="r_mes_ini")
                    ano_inicio = st.selectbox("Ano Inicial:", [2025, 2026, 2027], index=1, key="r_ano_ini")
                with col_fim:
                    mes_fim = st.selectbox("Mês Final:", list(range(1, 13)), index=11, key="r_mes_fim")
                    ano_fim = st.selectbox("Ano Final:", [2025, 2026, 2027], index=1, key="r_ano_fim")
                
                dia_vencimento = st.number_input("📆 Dia do Vencimento:", min_value=1, max_value=31, value=15, key="r_dia")
                
                # Calcular quantidade de meses
                data_inicio = date(ano_inicio, mes_inicio, 1)
                data_fim = date(ano_fim, mes_fim, 1)
                
                if data_fim >= data_inicio:
                    qtd_meses = (data_fim.year - data_inicio.year) * 12 + (data_fim.month - data_inicio.month) + 1
                    st.success(f"📊 Serão criadas **{qtd_meses}** previsões")
                else:
                    st.error("❌ Data final deve ser maior que inicial")
                    qtd_meses = 0
            
            if st.form_submit_button("🔄 Criar Previsões Recorrentes", type="primary"):
                if categoria_rec and subcategoria_rec and valor_rec > 0 and descricao_rec and qtd_meses > 0:
                    qtd = criar_previsoes_recorrentes(
                        data_inicio, data_fim, dia_vencimento,
                        tipo_rec, categoria_rec, subcategoria_rec, valor_rec, descricao_rec
                    )
                    st.success(f"✅ {qtd} previsões criadas com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos corretamente!")
        
        # Exemplo
        st.markdown("---")
        st.markdown("##### 📋 Exemplo de Uso")
        st.markdown("""
        **Cenário:** Criar previsão de Energia Elétrica de Junho a Dezembro de 2026
        
        | Campo | Valor |
        |-------|-------|
        | Tipo | Despesa |
        | Categoria | Habitação |
        | Subcategoria | Energia Elétrica |
        | Valor Mensal | R$ 800,00 |
        | Descrição Base | Energia Elétrica |
        | Período | Jun/2026 → Dez/2026 |
        | Dia Vencimento | 15 |
        
        **Resultado:** 7 previsões criadas automaticamente com descrições como:
        - "Energia Elétrica - Jun/2026" (15/06/2026)
        - "Energia Elétrica - Jul/2026" (15/07/2026)
        - ... até "Energia Elétrica - Dez/2026"
        """)
    
    # ------------------------------------------
    # TAB 4: GERENCIAR (Alterar Status / Excluir)
    # ------------------------------------------
    with tab4:
        st.subheader("✏️ Gerenciar Previsões")
        
        ano_ger = st.selectbox("📅 Ano:", [2025, 2026, 2027], index=1, key="g_ano")
        df_ger = get_previsoes(ano_ger, status="Ativa")
        
        if not df_ger.empty:
            # Alterar uma previsão
            st.markdown("##### 🔹 Alterar uma previsão específica")
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                opcoes = []
                for _, row in df_ger.iterrows():
                    data_fmt = pd.to_datetime(row['data']).strftime('%d/%m/%Y')
                    opcao = f"[{row['id']}] {data_fmt} | {row['tipo']} | {row['categoria']} - {row['subcategoria']} | {formatar_moeda(row['valor'])}"
                    opcoes.append(opcao)
                selecionado = st.selectbox("Selecione:", opcoes, key="g_select")
                id_selecionado = int(selecionado.split(']')[0].replace('[', ''))
            with col2:
                novo_status = st.selectbox("Novo Status:", ["Ativa", "Cancelada", "Realizada"], key="g_status")
            with col3:
                st.write("")
                st.write("")
                if st.button("💾 Atualizar", type="primary", key="g_btn_status"):
                    atualizar_status_previsao(id_selecionado, novo_status)
                    st.success(f"✅ Atualizado para '{novo_status}'!")
                    st.rerun()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Excluir Selecionada", type="secondary", key="g_btn_excluir"):
                    excluir_previsao(id_selecionado)
                    st.success("✅ Previsão excluída!")
                    st.rerun()
            
            st.markdown("---")
            
            # Operações em lote
            st.markdown("##### 🔹 Operações em Lote")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                categorias_lote = ["Todas"] + df_ger['categoria'].unique().tolist()
                cat_lote = st.selectbox("Categoria:", categorias_lote, key="g_cat_lote")
            with col2:
                meses_lote = ["Todos"] + list(range(1, 13))
                mes_lote = st.selectbox("Mês:", meses_lote, key="g_mes_lote")
            with col3:
                acao_lote = st.selectbox("Ação:", ["Cancelar", "Marcar Realizada", "Excluir"], key="g_acao_lote")
            
            # Filtrar
            df_lote = df_ger.copy()
            if cat_lote != "Todas":
                df_lote = df_lote[df_lote['categoria'] == cat_lote]
            if mes_lote != "Todos":
                df_lote['mes'] = pd.to_datetime(df_lote['data']).dt.month
                df_lote = df_lote[df_lote['mes'] == mes_lote]
            
            st.info(f"📊 {len(df_lote)} previsão(ões) serão afetadas")
            
            if st.button(f"🔄 Aplicar '{acao_lote}' em Lote", type="secondary", key="g_btn_lote"):
                if not df_lote.empty:
                    ids = df_lote['id'].tolist()
                    if acao_lote == "Cancelar":
                        for id_p in ids:
                            atualizar_status_previsao(id_p, "Cancelada")
                        st.success(f"✅ {len(ids)} previsões canceladas!")
                    elif acao_lote == "Marcar Realizada":
                        for id_p in ids:
                            atualizar_status_previsao(id_p, "Realizada")
                        st.success(f"✅ {len(ids)} previsões marcadas como realizadas!")
                    else:  # Excluir
                        excluir_previsoes_em_lote(ids)
                        st.success(f"✅ {len(ids)} previsões excluídas!")
                    st.rerun()
        else:
            st.info("📭 Nenhuma previsão ativa encontrada.")