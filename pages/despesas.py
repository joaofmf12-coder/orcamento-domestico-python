"""
╔══════════════════════════════════════════════════════════════╗
║                    📤 LANÇAMENTO DE DESPESAS                 ║
║                                                              ║
║  Com conciliação automática de previsões                     ║
║  Igual às abas LAN_DESPESAS e LAN_CARTOES do Excel           ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.connection import get_engine
from sqlalchemy import text


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

def get_categorias_despesa():
    """Busca categorias de despesa"""
    engine = get_engine()
    query = """
        SELECT DISTINCT categoria 
        FROM categorias 
        WHERE tipo = 'Despesa' AND ativo = 1
        ORDER BY categoria
    """
    df = pd.read_sql(query, engine)
    return df['categoria'].tolist() if not df.empty else []


def get_subcategorias(categoria):
    """Busca subcategorias de uma categoria"""
    engine = get_engine()
    query = f"""
        SELECT DISTINCT subcategoria 
        FROM categorias 
        WHERE tipo = 'Despesa' AND categoria = '{categoria}' AND ativo = 1 AND subcategoria IS NOT NULL
        ORDER BY subcategoria
    """
    df = pd.read_sql(query, engine)
    return df['subcategoria'].tolist() if not df.empty else []


def get_cartoes():
    """Busca lista de cartões de crédito"""
    engine = get_engine()
    try:
        query = """SELECT DISTINCT cartao FROM compras_cartao ORDER BY cartao"""
        df = pd.read_sql(query, engine)
        cartoes = df['cartao'].tolist() if not df.empty else []
        # Adicionar cartões padrão se não existirem
        cartoes_padrao = ["Crédito INTER - Ana", "Crédito INTER - João", "Crédito Credicom Ana"]
        for c in cartoes_padrao:
            if c not in cartoes:
                cartoes.append(c)
        return sorted(cartoes)
    except:
        return ["Crédito INTER - Ana", "Crédito INTER - João", "Crédito Credicom Ana"]


def buscar_previsoes_correspondentes(categoria, subcategoria, mes, ano):
    """Busca previsões correspondentes (Ativas) para a despesa"""
    engine = get_engine()
    
    # Primeiro tenta buscar com subcategoria exata
    query = f"""
        SELECT id, data, categoria, subcategoria, valor, descricao, status
        FROM previsoes
        WHERE tipo = 'Despesa'
          AND categoria = '{categoria}'
          AND subcategoria = '{subcategoria}'
          AND MONTH(data) = {mes}
          AND YEAR(data) = {ano}
          AND status = 'Ativa'
        ORDER BY data
    """
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        return df.to_dict('records')
    
    # Se não encontrar, busca só por categoria
    query2 = f"""
        SELECT id, data, categoria, subcategoria, valor, descricao, status
        FROM previsoes
        WHERE tipo = 'Despesa'
          AND categoria = '{categoria}'
          AND MONTH(data) = {mes}
          AND YEAR(data) = {ano}
          AND status = 'Ativa'
        ORDER BY data
    """
    df2 = pd.read_sql(query2, engine)
    
    return df2.to_dict('records') if not df2.empty else []


def cancelar_previsao(id_previsao):
    """Atualiza status da previsão para Cancelada"""
    engine = get_engine()
    
    with engine.connect() as conn:
        query = text("UPDATE previsoes SET status = 'Cancelada' WHERE id = :id")
        conn.execute(query, {"id": id_previsao})
        conn.commit()


def salvar_despesa_avista(data, categoria, subcategoria, valor, observacao):
    """Salva despesa à vista (débito/PIX)"""
    engine = get_engine()
    
    with engine.connect() as conn:
        query = text("""
            INSERT INTO despesas (data, categoria, subcategoria, valor, observacao, status)
            VALUES (:data, :categoria, :subcategoria, :valor, :observacao, 'Realizado')
        """)
        conn.execute(query, {
            "data": data,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "valor": valor,
            "observacao": observacao
        })
        conn.commit()
    return True


def salvar_compra_cartao(data_compra, categoria, subcategoria, descricao, valor_total, num_parcelas, cartao):
    """Salva compra no cartão e gera parcelas"""
    engine = get_engine()
    
    with engine.connect() as conn:
        # 1. Inserir compra no cartão
        query = text("""
            INSERT INTO compras_cartao (data_compra, categoria, subcategoria, descricao, valor_total, num_parcelas, cartao)
            VALUES (:data_compra, :categoria, :subcategoria, :descricao, :valor_total, :num_parcelas, :cartao)
        """)
        result = conn.execute(query, {
            "data_compra": data_compra,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "descricao": descricao,
            "valor_total": valor_total,
            "num_parcelas": num_parcelas,
            "cartao": cartao
        })
        
        compra_id = result.lastrowid
        
        # 2. Gerar parcelas
        valor_parcela = valor_total / num_parcelas
        
        for i in range(num_parcelas):
            # Calcular data de vencimento da parcela
            mes_parcela = data_compra.month + i + 1
            ano_parcela = data_compra.year
            
            while mes_parcela > 12:
                mes_parcela -= 12
                ano_parcela += 1
            
            # Dia de vencimento baseado no cartão
            if "João" in cartao:
                dia_venc = 5
            elif "Credicom" in cartao:
                dia_venc = 19
            else:  # INTER Ana
                dia_venc = 15
            
            # Ajustar dia se necessário
            import calendar
            ultimo_dia = calendar.monthrange(ano_parcela, mes_parcela)[1]
            dia_venc = min(dia_venc, ultimo_dia)
            
            data_vencimento = date(ano_parcela, mes_parcela, dia_venc)
            
            query_parcela = text("""
                INSERT INTO parcelas (compra_id, num_parcela, valor, data_vencimento)
                VALUES (:compra_id, :num_parcela, :valor, :data_vencimento)
            """)
            conn.execute(query_parcela, {
                "compra_id": compra_id,
                "num_parcela": i + 1,
                "valor": valor_parcela,
                "data_vencimento": data_vencimento
            })
        
        conn.commit()
        
    return compra_id


def get_despesas_recentes(limite=20):
    """Busca despesas recentes"""
    engine = get_engine()
    query = f"""
        SELECT data, categoria, subcategoria, valor, observacao, status
        FROM despesas
        WHERE status = 'Realizado'
        ORDER BY data DESC, id DESC
        LIMIT {limite}
    """
    return pd.read_sql(query, engine)


def get_cartoes_recentes(limite=15):
    """Busca compras no cartão recentes"""
    engine = get_engine()
    query = f"""
        SELECT data_compra as data, categoria, subcategoria, valor_total as valor, 
               descricao, num_parcelas, cartao
        FROM compras_cartao
        ORDER BY data_compra DESC, id DESC
        LIMIT {limite}
    """
    return pd.read_sql(query, engine)


# ==========================================
# INTERFACE STREAMLIT
# ==========================================

def mostrar_despesas():
    st.title("📤 Lançamento de Despesas")
    st.markdown("*Com conciliação automática de previsões*")
    
    # Inicializar estado para previsões encontradas
    if 'previsoes_encontradas' not in st.session_state:
        st.session_state.previsoes_encontradas = []
    if 'despesa_salva' not in st.session_state:
        st.session_state.despesa_salva = False
    if 'cartao_salvo' not in st.session_state:
        st.session_state.cartao_salvo = False
    
    # ==========================================
    # ABAS: À VISTA | CARTÃO | HISTÓRICO
    # ==========================================
    tab1, tab2, tab3 = st.tabs(["💵 Despesa à Vista", "💳 Cartão de Crédito", "📋 Histórico"])
    
    # ------------------------------------------
    # TAB 1: DESPESA À VISTA (Débito/PIX)
    # ------------------------------------------
    with tab1:
        st.subheader("💵 Lançar Despesa à Vista (Débito/PIX)")
        st.info("💡 Igual à aba **LAN_DESPESAS** do Excel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_desp = st.date_input("📅 Data:", value=date.today(), key="data_avista")
            
            categorias = get_categorias_despesa()
            categoria = st.selectbox("📁 Categoria:", categorias if categorias else [""], key="cat_avista")
            
            subcategorias = get_subcategorias(categoria) if categoria else []
            subcategoria = st.selectbox(
                "📋 Subcategoria:", 
                subcategorias if subcategorias else [""], 
                key="subcat_avista"
            )
        
        with col2:
            valor = st.number_input("💰 Valor:", min_value=0.0, step=10.0, format="%.2f", key="valor_avista")
            observacao = st.text_input("📝 Observação:", key="obs_avista")
        
        # Mostrar previsões correspondentes ANTES de salvar
        if categoria and subcategoria and valor > 0:
            previsoes = buscar_previsoes_correspondentes(
                categoria, subcategoria, data_desp.month, data_desp.year
            )
            
            if previsoes:
                st.markdown("---")
                st.warning(f"⚠️ **{len(previsoes)} Previsão(ões) encontrada(s) para {categoria} - {subcategoria} em {data_desp.strftime('%m/%Y')}:**")
                
                for prev in previsoes:
                    col_p1, col_p2, col_p3 = st.columns([3, 1, 1])
                    with col_p1:
                        st.write(f"📋 {prev['descricao']} ({pd.to_datetime(prev['data']).strftime('%d/%m/%Y')})")
                    with col_p2:
                        st.write(f"💰 {formatar_moeda(prev['valor'])}")
                    with col_p3:
                        st.write(f"🟢 {prev['status']}")
        
        # Botão para salvar
        if st.button("💾 Salvar Despesa", type="primary", key="btn_salvar_avista"):
            if categoria and subcategoria and valor > 0:
                # Salvar despesa
                salvar_despesa_avista(data_desp, categoria, subcategoria, valor, observacao)
                st.success(f"✅ Despesa de {formatar_moeda(valor)} salva com sucesso!")
                
                # Buscar previsões para cancelar
                previsoes = buscar_previsoes_correspondentes(
                    categoria, subcategoria, data_desp.month, data_desp.year
                )
                
                if previsoes:
                    st.session_state.previsoes_encontradas = previsoes
                    st.session_state.despesa_salva = True
                    st.rerun()
            else:
                st.error("❌ Preencha categoria, subcategoria e valor!")
        
        # Mostrar opções de cancelamento após salvar
        if st.session_state.despesa_salva and st.session_state.previsoes_encontradas:
            st.markdown("---")
            st.subheader("🔄 Conciliar Previsões")
            st.info("Selecione as previsões que deseja **cancelar** (evita duplicação no Fluxo de Caixa)")
            
            for i, prev in enumerate(st.session_state.previsoes_encontradas):
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    st.write(f"📋 **{prev['categoria']} - {prev['subcategoria']}**")
                    st.write(f"   {prev['descricao']}")
                with col2:
                    st.write(f"💰 {formatar_moeda(prev['valor'])}")
                with col3:
                    if st.button(f"❌ Cancelar", key=f"cancel_prev_{prev['id']}"):
                        cancelar_previsao(prev['id'])
                        st.success(f"✅ Previsão #{prev['id']} cancelada!")
                        # Remover da lista
                        st.session_state.previsoes_encontradas = [
                            p for p in st.session_state.previsoes_encontradas if p['id'] != prev['id']
                        ]
                        st.rerun()
            
            if st.button("✅ Concluir (manter previsões restantes)", key="btn_concluir_avista"):
                st.session_state.previsoes_encontradas = []
                st.session_state.despesa_salva = False
                st.success("✅ Processo concluído!")
                st.rerun()
    
    # ------------------------------------------
    # TAB 2: CARTÃO DE CRÉDITO
    # ------------------------------------------
    with tab2:
        st.subheader("💳 Lançar Compra no Cartão de Crédito")
        st.info("💡 Igual à aba **LAN_CARTOES** do Excel - Parcelas geradas automaticamente!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_compra = st.date_input("📅 Data da Compra:", value=date.today(), key="data_cartao")
            
            categorias = get_categorias_despesa()
            categoria_cartao = st.selectbox("📁 Categoria:", categorias if categorias else [""], key="cat_cartao")
            
            subcategorias_cartao = get_subcategorias(categoria_cartao) if categoria_cartao else []
            subcategoria_cartao = st.selectbox(
                "📋 Subcategoria:", 
                subcategorias_cartao if subcategorias_cartao else [""], 
                key="subcat_cartao"
            )
            
            descricao_cartao = st.text_input("📝 Descrição:", key="desc_cartao")
        
        with col2:
            valor_total = st.number_input("💰 Valor Total:", min_value=0.0, step=10.0, format="%.2f", key="valor_cartao")
            num_parcelas = st.number_input("🔢 Nº de Parcelas:", min_value=1, max_value=24, value=1, step=1, key="parcelas_cartao")
            
            cartoes = get_cartoes()
            cartao = st.selectbox("💳 Cartão:", cartoes, key="cartao_select")
            
            # Mostrar valor da parcela
            if valor_total > 0 and num_parcelas > 0:
                valor_parcela = valor_total / num_parcelas
                st.metric("💵 Valor da Parcela", formatar_moeda(valor_parcela))
        
        # Mostrar previsões correspondentes
        if categoria_cartao and subcategoria_cartao and valor_total > 0:
            # Calcular mês da primeira parcela
            mes_primeira = data_compra.month + 1
            ano_primeira = data_compra.year
            if mes_primeira > 12:
                mes_primeira = 1
                ano_primeira += 1
            
            previsoes_cartao = buscar_previsoes_correspondentes(
                categoria_cartao, subcategoria_cartao, mes_primeira, ano_primeira
            )
            
            if previsoes_cartao:
                st.markdown("---")
                st.warning(f"⚠️ **Previsão encontrada para o mês da 1ª parcela ({mes_primeira:02d}/{ano_primeira}):**")
                for prev in previsoes_cartao:
                    st.write(f"📋 {prev['descricao']} - {formatar_moeda(prev['valor'])}")
        
        # Botão para salvar
        if st.button("💾 Salvar Compra no Cartão", type="primary", key="btn_salvar_cartao"):
            if categoria_cartao and subcategoria_cartao and valor_total > 0:
                # Salvar compra
                compra_id = salvar_compra_cartao(
                    data_compra, categoria_cartao, subcategoria_cartao,
                    descricao_cartao, valor_total, num_parcelas, cartao
                )
                st.success(f"✅ Compra de {formatar_moeda(valor_total)} em {num_parcelas}x salva! (ID: {compra_id})")
                st.info(f"📋 {num_parcelas} parcela(s) de {formatar_moeda(valor_total/num_parcelas)} gerada(s) automaticamente!")
                
                # Buscar previsões para cancelar
                mes_primeira = data_compra.month + 1
                ano_primeira = data_compra.year
                if mes_primeira > 12:
                    mes_primeira = 1
                    ano_primeira += 1
                
                previsoes_cartao = buscar_previsoes_correspondentes(
                    categoria_cartao, subcategoria_cartao, mes_primeira, ano_primeira
                )
                
                if previsoes_cartao:
                    st.session_state.previsoes_encontradas = previsoes_cartao
                    st.session_state.cartao_salvo = True
                    st.rerun()
            else:
                st.error("❌ Preencha categoria, subcategoria e valor!")
        
        # Mostrar opções de cancelamento após salvar cartão
        if st.session_state.cartao_salvo and st.session_state.previsoes_encontradas:
            st.markdown("---")
            st.subheader("🔄 Conciliar Previsões")
            
            for prev in st.session_state.previsoes_encontradas:
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    st.write(f"📋 **{prev['categoria']} - {prev['subcategoria']}**")
                with col2:
                    st.write(f"💰 {formatar_moeda(prev['valor'])}")
                with col3:
                    if st.button(f"❌ Cancelar", key=f"cancel_prev_cartao_{prev['id']}"):
                        cancelar_previsao(prev['id'])
                        st.success(f"✅ Previsão cancelada!")
                        st.session_state.previsoes_encontradas = []
                        st.session_state.cartao_salvo = False
                        st.rerun()
            
            if st.button("✅ Manter Previsão", key="btn_manter_cartao"):
                st.session_state.previsoes_encontradas = []
                st.session_state.cartao_salvo = False
                st.rerun()
    
    # ------------------------------------------
    # TAB 3: HISTÓRICO
    # ------------------------------------------
    with tab3:
        st.subheader("📋 Últimas Despesas Lançadas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 💵 Despesas à Vista (Últimas 20)")
            df_avista = get_despesas_recentes(20)
            if not df_avista.empty:
                df_display = df_avista.copy()
                df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
                df_display['valor'] = df_display['valor'].apply(formatar_moeda)
                df_display.columns = ['📅 Data', '📁 Categoria', '📋 Subcategoria', '💰 Valor', '📝 Obs', '✅ Status']
                st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
            else:
                st.info("📭 Nenhuma despesa à vista encontrada.")
        
        with col2:
            st.markdown("##### 💳 Compras no Cartão (Últimas 15)")
            df_cartao = get_cartoes_recentes(15)
            if not df_cartao.empty:
                df_display = df_cartao.copy()
                df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
                df_display['valor'] = df_display['valor'].apply(formatar_moeda)
                df_display['info'] = df_display['num_parcelas'].astype(str) + 'x - ' + df_display['cartao']
                df_show = df_display[['data', 'categoria', 'subcategoria', 'valor', 'descricao', 'info']]
                df_show.columns = ['📅 Data', '📁 Cat', '📋 Subcat', '💰 Valor', '📝 Desc', '💳 Cartão']
                st.dataframe(df_show, use_container_width=True, hide_index=True, height=400)
            else:
                st.info("📭 Nenhuma compra no cartão encontrada.")
