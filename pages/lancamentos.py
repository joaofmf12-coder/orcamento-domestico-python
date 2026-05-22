"""
Lançamentos de Receitas e Despesas
Com seleção de conta bancária e conciliação automática
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.connection import get_engine
from sqlalchemy import text
import calendar


def formatar_moeda(valor):
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

def get_contas():
    """Busca lista de contas bancárias ativas"""
    engine = get_engine()
    try:
        query = "SELECT id, nome FROM contas WHERE ativo = 1 ORDER BY nome"
        df = pd.read_sql(query, engine)
        return df.to_dict('records') if not df.empty else []
    except:
        return []


def get_conta_id_por_nome(nome):
    """Busca ID da conta pelo nome"""
    engine = get_engine()
    try:
        query = f"SELECT id FROM contas WHERE nome = '{nome}' LIMIT 1"
        df = pd.read_sql(query, engine)
        return df.iloc[0]['id'] if not df.empty else None
    except:
        return None


def get_categorias(tipo):
    """Busca categorias do banco de dados"""
    engine = get_engine()
    try:
        query = f"""
            SELECT DISTINCT categoria 
            FROM categorias 
            WHERE tipo = '{tipo}' AND ativo = 1
            ORDER BY categoria
        """
        df = pd.read_sql(query, engine)
        return df['categoria'].tolist() if not df.empty else []
    except:
        return []


@st.cache_data(ttl=60)
def get_subcategorias_cached(tipo, categoria):
    """Busca subcategorias com cache"""
    engine = get_engine()
    try:
        query = f"""
            SELECT DISTINCT subcategoria 
            FROM categorias 
            WHERE tipo = '{tipo}' AND categoria = '{categoria}' AND ativo = 1 AND subcategoria IS NOT NULL
            ORDER BY subcategoria
        """
        df = pd.read_sql(query, engine)
        return df['subcategoria'].tolist() if not df.empty else []
    except:
        return []

def get_subcategorias(tipo, categoria):
    """Busca subcategorias - wrapper para compatibilidade"""
    if not categoria:
        return []
    return get_subcategorias_cached(tipo, categoria)


def get_cartoes():
    """Busca lista de cartões ativos"""
    engine = get_engine()
    try:
        query = "SELECT id, nome FROM cartoes WHERE ativo = 1 ORDER BY nome"
        df = pd.read_sql(query, engine)
        return df['nome'].tolist() if not df.empty else []
    except:
        return []


def get_cartao_id(nome_cartao):
    """Busca ID do cartão pelo nome"""
    engine = get_engine()
    try:
        query = f"SELECT id FROM cartoes WHERE nome = '{nome_cartao}' LIMIT 1"
        df = pd.read_sql(query, engine)
        return df.iloc[0]['id'] if not df.empty else 1
    except:
        return 1


def buscar_previsoes_correspondentes(tipo, categoria, subcategoria, mes, ano):
    """Busca previsões correspondentes para conciliação"""
    engine = get_engine()
    try:
        query = f"""
            SELECT id, data, categoria, subcategoria, valor, descricao, status
            FROM previsoes
            WHERE tipo = '{tipo}'
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
        
        query2 = f"""
            SELECT id, data, categoria, subcategoria, valor, descricao, status
            FROM previsoes
            WHERE tipo = '{tipo}'
              AND categoria = '{categoria}'
              AND MONTH(data) = {mes}
              AND YEAR(data) = {ano}
              AND status = 'Ativa'
            ORDER BY data
        """
        df2 = pd.read_sql(query2, engine)
        return df2.to_dict('records') if not df2.empty else []
    except:
        return []


def cancelar_previsao(id_previsao):
    """Cancela uma previsão"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("UPDATE previsoes SET status = 'Cancelada' WHERE id = :id")
        conn.execute(query, {"id": id_previsao})
        conn.commit()


def salvar_receita(data, categoria, subcategoria, valor, observacao, conta_id, status='Realizado'):
    """Salva uma receita no banco"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("""
            INSERT INTO receitas (data, categoria, subcategoria, valor, descricao, status, conta_id, conciliado)
            VALUES (:data, :categoria, :subcategoria, :valor, :descricao, :status, :conta_id, 0)
        """)
        conn.execute(query, {
            "data": data, "categoria": categoria, "subcategoria": subcategoria,
            "valor": valor, "descricao": observacao, "status": status, "conta_id": conta_id
        })
        conn.commit()
    return True


def salvar_despesa(data, categoria, subcategoria, valor, observacao, conta_id, status='Realizado'):
    """Salva uma despesa no banco"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("""
            INSERT INTO despesas (data, categoria, subcategoria, valor, descricao, status, conta_id, conciliado)
            VALUES (:data, :categoria, :subcategoria, :valor, :descricao, :status, :conta_id, 0)
        """)
        conn.execute(query, {
            "data": data, "categoria": categoria, "subcategoria": subcategoria,
            "valor": valor, "descricao": observacao, "status": status, "conta_id": conta_id
        })
        conn.commit()
    return True


def salvar_compra_cartao(data_compra, categoria, subcategoria, descricao, valor_total, num_parcelas, cartao):
    """Salva compra no cartão e gera parcelas"""
    engine = get_engine()
    cartao_id = get_cartao_id(cartao)
    
    try:
        query_cartao = f"SELECT dia_vencimento FROM cartoes WHERE nome = '{cartao}' LIMIT 1"
        df_cartao = pd.read_sql(query_cartao, engine)
        dia_venc = df_cartao.iloc[0]['dia_vencimento'] if not df_cartao.empty else 15
    except:
        dia_venc = 15
    
    with engine.connect() as conn:
        query = text("""
            INSERT INTO compras_cartao (data_compra, categoria, subcategoria, descricao, valor_total, num_parcelas, cartao_id)
            VALUES (:data_compra, :categoria, :subcategoria, :descricao, :valor_total, :num_parcelas, :cartao_id)
        """)
        result = conn.execute(query, {
            "data_compra": data_compra, "categoria": categoria, "subcategoria": subcategoria,
            "descricao": descricao, "valor_total": valor_total, "num_parcelas": num_parcelas, 
            "cartao_id": cartao_id
        })
        compra_id = result.lastrowid
        
        valor_parcela = valor_total / num_parcelas
        for i in range(num_parcelas):
            mes_parcela = data_compra.month + i + 1
            ano_parcela = data_compra.year
            while mes_parcela > 12:
                mes_parcela -= 12
                ano_parcela += 1
            
            ultimo_dia = calendar.monthrange(ano_parcela, mes_parcela)[1]
            dia_venc_ajustado = min(dia_venc, ultimo_dia)
            data_vencimento = date(ano_parcela, mes_parcela, dia_venc_ajustado)
            
        query_parcela = text("""
            INSERT INTO parcelas (compra_id, num_parcela, valor, data_vencimento, fatura_mes_ano)
            VALUES (:compra_id, :num_parcela, :valor, :data_vencimento, :fatura_mes_ano)
        """)
        conn.execute(query_parcela, {
            "compra_id": compra_id, 
            "num_parcela": i + 1,
            "valor": valor_parcela, 
            "data_vencimento": data_vencimento,
            "fatura_mes_ano": data_vencimento.strftime('%m/%Y')
        })
        conn.commit()
    return compra_id


def get_despesas_recentes(limite=30):
    """Busca despesas recentes"""
    engine = get_engine()
    query = f"""
        SELECT d.id, d.data, d.categoria, d.subcategoria, d.valor, d.descricao, d.status,
               COALESCE(c.nome, 'Não informado') as conta
        FROM despesas d
        LEFT JOIN contas c ON d.conta_id = c.id
        ORDER BY d.data DESC, d.id DESC
        LIMIT {limite}
    """
    return pd.read_sql(query, engine)


def get_receitas_recentes(limite=30):
    """Busca receitas recentes"""
    engine = get_engine()
    query = f"""
        SELECT r.id, r.data, r.categoria, r.subcategoria, r.valor, r.descricao, r.status,
               COALESCE(c.nome, 'Não informado') as conta
        FROM receitas r
        LEFT JOIN contas c ON r.conta_id = c.id
        ORDER BY r.data DESC, r.id DESC
        LIMIT {limite}
    """
    return pd.read_sql(query, engine)


def get_cartoes_recentes(limite=20):
    """Busca compras recentes no cartão"""
    engine = get_engine()
    try:
        query = f"""
            SELECT c.id, c.data_compra as data, c.categoria, c.subcategoria, c.valor_total as valor, 
                   c.descricao, c.num_parcelas, ca.nome as cartao
            FROM compras_cartao c
            LEFT JOIN cartoes ca ON c.cartao_id = ca.id
            ORDER BY c.data_compra DESC, c.id DESC
            LIMIT {limite}
        """
        return pd.read_sql(query, engine)
    except:
        return pd.DataFrame()


def atualizar_despesa(id_despesa, data, categoria, subcategoria, valor, descricao, status, conta_id):
    """Atualiza uma despesa"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("""
            UPDATE despesas 
            SET data = :data, categoria = :categoria, subcategoria = :subcategoria, 
                valor = :valor, descricao = :descricao, status = :status, conta_id = :conta_id
            WHERE id = :id
        """)
        conn.execute(query, {
            "id": id_despesa, "data": data, "categoria": categoria, 
            "subcategoria": subcategoria, "valor": valor, "descricao": descricao, 
            "status": status, "conta_id": conta_id
        })
        conn.commit()


def atualizar_receita(id_receita, data, categoria, subcategoria, valor, descricao, status, conta_id):
    """Atualiza uma receita"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("""
            UPDATE receitas 
            SET data = :data, categoria = :categoria, subcategoria = :subcategoria, 
                valor = :valor, descricao = :descricao, status = :status, conta_id = :conta_id
            WHERE id = :id
        """)
        conn.execute(query, {
            "id": id_receita, "data": data, "categoria": categoria, 
            "subcategoria": subcategoria, "valor": valor, "descricao": descricao, 
            "status": status, "conta_id": conta_id
        })
        conn.commit()


def excluir_despesa(id_despesa):
    """Exclui uma despesa"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("DELETE FROM despesas WHERE id = :id")
        conn.execute(query, {"id": id_despesa})
        conn.commit()


def excluir_receita(id_receita):
    """Exclui uma receita"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("DELETE FROM receitas WHERE id = :id")
        conn.execute(query, {"id": id_receita})
        conn.commit()


def get_despesa_por_id(id_despesa):
    """Busca despesa por ID"""
    engine = get_engine()
    query = f"""
        SELECT d.*, c.nome as conta_nome
        FROM despesas d
        LEFT JOIN contas c ON d.conta_id = c.id
        WHERE d.id = {id_despesa}
    """
    df = pd.read_sql(query, engine)
    return df.iloc[0] if not df.empty else None


def get_receita_por_id(id_receita):
    """Busca receita por ID"""
    engine = get_engine()
    query = f"""
        SELECT r.*, c.nome as conta_nome
        FROM receitas r
        LEFT JOIN contas c ON r.conta_id = c.id
        WHERE r.id = {id_receita}
    """
    df = pd.read_sql(query, engine)
    return df.iloc[0] if not df.empty else None


# ==========================================
# 📥 RECEITAS
# ==========================================

def mostrar_receitas():
    st.title("📥 Lançamento de Receitas")
    st.markdown("*Com seleção de conta bancária e conciliação automática*")
    
    if 'previsoes_receita' not in st.session_state:
        st.session_state.previsoes_receita = []
    if 'receita_salva' not in st.session_state:
        st.session_state.receita_salva = False
    
    tab1, tab2, tab3 = st.tabs(["💰 Nova Receita", "📋 Histórico", "✏️ Editar/Excluir"])
    
    # TAB 1: NOVA RECEITA
    with tab1:
        contas = get_contas()
        contas_nomes = [c['nome'] for c in contas] if contas else ["Conta não cadastrada"]
        
        col1, col2 = st.columns(2)
        with col1:
            data_rec = st.date_input("📅 Data:", value=date.today(), key="data_receita")
            categorias = get_categorias("Receita")
            categoria = st.selectbox("📁 Categoria:", categorias if categorias else [""], key="cat_receita")
            
            # Buscar subcategorias
            subcategorias = get_subcategorias("Receita", categoria) if categoria else []
            subcategoria = st.selectbox("📋 Subcategoria:", subcategorias if subcategorias else [""], key="subcat_receita")
        
        with col2:
            valor = st.number_input("💰 Valor:", min_value=0.0, step=100.0, format="%.2f", key="valor_receita")
            observacao = st.text_input("📝 Observação:", key="obs_receita")
            conta_selecionada = st.selectbox("🏦 Conta Destino:", contas_nomes, key="conta_receita")
            status_rec = st.selectbox("✅ Status:", ["Realizado", "Previsto"], key="status_receita")
        
        if categoria and subcategoria and valor > 0:
            previsoes = buscar_previsoes_correspondentes("Receita", categoria, subcategoria, data_rec.month, data_rec.year)
            if previsoes:
                st.markdown("---")
                st.warning(f"⚠️ **{len(previsoes)} Previsão(ões) encontrada(s):**")
                for prev in previsoes:
                    st.write(f"📋 {prev['descricao']} - {formatar_moeda(prev['valor'])}")
        
        if st.button("💾 Salvar Receita", type="primary", key="btn_salvar_receita"):
            if categoria and subcategoria and valor > 0:
                conta_id = get_conta_id_por_nome(conta_selecionada)
                salvar_receita(data_rec, categoria, subcategoria, valor, observacao, conta_id, status_rec)
                st.success(f"✅ Receita de {formatar_moeda(valor)} salva na conta '{conta_selecionada}'!")
                
                if status_rec == "Realizado":
                    previsoes = buscar_previsoes_correspondentes("Receita", categoria, subcategoria, data_rec.month, data_rec.year)
                    if previsoes:
                        st.session_state.previsoes_receita = previsoes
                        st.session_state.receita_salva = True
                        st.rerun()
            else:
                st.error("❌ Preencha todos os campos!")
        
        if st.session_state.receita_salva and st.session_state.previsoes_receita:
            st.markdown("---")
            st.subheader("🔄 Conciliar Previsões")
            for prev in st.session_state.previsoes_receita:
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    st.write(f"📋 **{prev['categoria']} - {prev['subcategoria']}**")
                with col2:
                    st.write(f"💰 {formatar_moeda(prev['valor'])}")
                with col3:
                    if st.button(f"❌ Cancelar", key=f"cancel_rec_{prev['id']}"):
                        cancelar_previsao(prev['id'])
                        st.success("✅ Previsão cancelada!")
                        st.session_state.previsoes_receita = [p for p in st.session_state.previsoes_receita if p['id'] != prev['id']]
                        st.rerun()
            if st.button("✅ Concluir", key="btn_concluir_receita"):
                st.session_state.previsoes_receita = []
                st.session_state.receita_salva = False
                st.rerun()
    
    # TAB 2: HISTÓRICO
    with tab2:
        st.subheader("📋 Últimas Receitas")
        df = get_receitas_recentes(30)
        if not df.empty:
            df_display = df.copy()
            df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
            df_display['valor'] = df_display['valor'].apply(formatar_moeda)
            df_show = df_display[['id', 'data', 'categoria', 'subcategoria', 'valor', 'conta', 'status']]
            df_show.columns = ['ID', '📅 Data', '📁 Categoria', '📋 Subcategoria', '💰 Valor', '🏦 Conta', '✅ Status']
            st.dataframe(df_show, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Nenhuma receita encontrada.")
    
    # TAB 3: EDITAR/EXCLUIR
    with tab3:
        st.subheader("✏️ Editar ou Excluir Receita")
        
        df_receitas = get_receitas_recentes(50)
        if not df_receitas.empty:
            opcoes = []
            for _, row in df_receitas.iterrows():
                data_fmt = pd.to_datetime(row['data']).strftime('%d/%m/%Y')
                opcao = f"[{row['id']}] {data_fmt} | {row['categoria']} | {formatar_moeda(row['valor'])} | {row['conta']}"
                opcoes.append(opcao)
            
            selecionado = st.selectbox("Selecione a receita:", opcoes, key="edit_rec_select")
            id_selecionado = int(selecionado.split(']')[0].replace('[', ''))
            
            receita = get_receita_por_id(id_selecionado)
            if receita is not None:
                st.markdown("---")
                st.markdown(f"##### 📝 Editando Receita ID: **{id_selecionado}**")
                
                contas = get_contas()
                contas_nomes = [c['nome'] for c in contas] if contas else ["Conta não cadastrada"]
                
                col1, col2 = st.columns(2)
                with col1:
                    nova_data = st.date_input("📅 Data:", value=pd.to_datetime(receita['data']).date(), key=f"edit_rec_data_{id_selecionado}")
                    categorias = get_categorias("Receita")
                    idx_cat = categorias.index(receita['categoria']) if receita['categoria'] in categorias else 0
                    nova_categoria = st.selectbox("📁 Categoria:", categorias, index=idx_cat, key=f"edit_rec_cat_{id_selecionado}")
                    
                    subcategorias = get_subcategorias("Receita", nova_categoria)
                    idx_subcat = subcategorias.index(receita['subcategoria']) if receita['subcategoria'] in subcategorias else 0
                    nova_subcategoria = st.selectbox("📋 Subcategoria:", subcategorias if subcategorias else [""], index=idx_subcat, key=f"edit_rec_subcat_{id_selecionado}")
                
                with col2:
                    novo_valor = st.number_input("💰 Valor:", value=float(receita['valor']), min_value=0.0, step=100.0, key=f"edit_rec_valor_{id_selecionado}")
                    nova_descricao = st.text_input("📝 Descrição:", value=receita['descricao'] if receita['descricao'] else "", key=f"edit_rec_desc_{id_selecionado}")
                    
                    idx_conta = 0
                    if receita['conta_nome'] and receita['conta_nome'] in contas_nomes:
                        idx_conta = contas_nomes.index(receita['conta_nome'])
                    nova_conta = st.selectbox("🏦 Conta:", contas_nomes, index=idx_conta, key=f"edit_rec_conta_{id_selecionado}")
                    
                    status_opcoes = ["Realizado", "Previsto", "Cancelado"]
                    idx_status = status_opcoes.index(receita['status']) if receita['status'] in status_opcoes else 0
                    novo_status = st.selectbox("✅ Status:", status_opcoes, index=idx_status, key=f"edit_rec_status_{id_selecionado}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Salvar Alterações", type="primary", key=f"btn_salvar_rec_{id_selecionado}"):
                        nova_conta_id = get_conta_id_por_nome(nova_conta)
                        atualizar_receita(id_selecionado, nova_data, nova_categoria, nova_subcategoria, novo_valor, nova_descricao, novo_status, nova_conta_id)
                        st.success("✅ Receita atualizada!")
                        st.rerun()
                with col2:
                    if st.button("🗑️ Excluir", type="secondary", key=f"btn_excluir_rec_{id_selecionado}"):
                        excluir_receita(id_selecionado)
                        st.success("✅ Receita excluída!")
                        st.rerun()


# ==========================================
# 📤 DESPESAS
# ==========================================

def mostrar_despesas():
    st.title("📤 Lançamento de Despesas")
    st.markdown("*Com seleção de conta bancária e conciliação automática*")
    
    if 'previsoes_despesa' not in st.session_state:
        st.session_state.previsoes_despesa = []
    if 'despesa_salva' not in st.session_state:
        st.session_state.despesa_salva = False
    
    tab1, tab2, tab3, tab4 = st.tabs(["💵 Despesa à Vista", "💳 Cartão de Crédito", "📋 Histórico", "✏️ Editar/Excluir"])
    
    # TAB 1: DESPESA À VISTA
    with tab1:
        st.subheader("💵 Despesa à Vista (Débito/PIX/Dinheiro)")
        
        contas = get_contas()
        contas_nomes = [c['nome'] for c in contas] if contas else ["Conta não cadastrada"]
        
        col1, col2 = st.columns(2)
        with col1:
            data_desp = st.date_input("📅 Data:", value=date.today(), key="data_avista")
            categorias = get_categorias("Despesa")
            categoria = st.selectbox("📁 Categoria:", categorias if categorias else [""], key="cat_avista")
            
            # Buscar subcategorias
            subcategorias = get_subcategorias("Despesa", categoria) if categoria else []
            subcategoria = st.selectbox("📋 Subcategoria:", subcategorias if subcategorias else [""], key="subcat_avista")
        
        with col2:
            valor = st.number_input("💰 Valor:", min_value=0.0, step=10.0, format="%.2f", key="valor_avista")
            observacao = st.text_input("📝 Observação:", key="obs_avista")
            conta_selecionada = st.selectbox("🏦 Conta/Meio de Pagamento:", contas_nomes, key="conta_avista")
            status_desp = st.selectbox("✅ Status:", ["Realizado", "Previsto"], key="status_avista")
        
        if categoria and subcategoria and valor > 0:
            previsoes = buscar_previsoes_correspondentes("Despesa", categoria, subcategoria, data_desp.month, data_desp.year)
            if previsoes:
                st.markdown("---")
                st.warning(f"⚠️ **{len(previsoes)} Previsão(ões) encontrada(s):**")
                for prev in previsoes:
                    st.write(f"📋 {prev['descricao']} - {formatar_moeda(prev['valor'])}")
        
        if st.button("💾 Salvar Despesa", type="primary", key="btn_salvar_avista"):
            if categoria and subcategoria and valor > 0:
                conta_id = get_conta_id_por_nome(conta_selecionada)
                salvar_despesa(data_desp, categoria, subcategoria, valor, observacao, conta_id, status_desp)
                st.success(f"✅ Despesa de {formatar_moeda(valor)} salva - {conta_selecionada}!")
                
                if status_desp == "Realizado":
                    previsoes = buscar_previsoes_correspondentes("Despesa", categoria, subcategoria, data_desp.month, data_desp.year)
                    if previsoes:
                        st.session_state.previsoes_despesa = previsoes
                        st.session_state.despesa_salva = True
                        st.rerun()
            else:
                st.error("❌ Preencha todos os campos!")
        
        if st.session_state.despesa_salva and st.session_state.previsoes_despesa:
            st.markdown("---")
            st.subheader("🔄 Conciliar Previsões")
            for prev in st.session_state.previsoes_despesa:
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    st.write(f"📋 **{prev['categoria']} - {prev['subcategoria']}**")
                with col2:
                    st.write(f"💰 {formatar_moeda(prev['valor'])}")
                with col3:
                    if st.button(f"❌ Cancelar", key=f"cancel_desp_{prev['id']}"):
                        cancelar_previsao(prev['id'])
                        st.success("✅ Previsão cancelada!")
                        st.session_state.previsoes_despesa = [p for p in st.session_state.previsoes_despesa if p['id'] != prev['id']]
                        st.rerun()
            if st.button("✅ Concluir", key="btn_concluir_desp"):
                st.session_state.previsoes_despesa = []
                st.session_state.despesa_salva = False
                st.rerun()
    
    # TAB 2: CARTÃO DE CRÉDITO - COM LISTAS FIXAS
    with tab2:
        st.subheader("💳 Compra no Cartão de Crédito")
        st.info("💡 Parcelas geradas automaticamente! Vai para a fatura do cartão.")
        
        # DICIONÁRIO FIXO DE SUBCATEGORIAS - GARANTIDO FUNCIONAR
        SUBCATEGORIAS_CARTAO = {
            "Alimentação": ["Supermercado", "Restaurantes", "Padaria", "Delivery", "Sacolão / Feira", "Almoço Escolar"],
            "Habitação": ["Manutenção Casa", "Cachorros", "Energia Elétrica", "Água", "Internet / TV", "Gás", "IPTU", "Faxineira", "Seguro Residencial", "Segurança", "Aquisições Casa", "Empregada Doméstica", "Impostos Empregada", "Salão / Beleza", "Limpeza Piscina", "Jardim/Área Externa"],
            "Transporte": ["Gasolina", "Manutenção Veículo", "Uber / Táxi", "Estacionamento", "IPVA", "Seguro Veículo"],
            "Saúde": ["Farmácia", "Plano de Saúde", "Consultas"],
            "Educação": ["Material Escolar", "Cursos", "Livros"],
            "Lazer": ["Saídas", "Viagens", "Streaming (Netflix/Spotify/Prime)", "Festas", "Esportes / Música"],
            "Vestuário": ["Roupas", "Acessórios", "Calçados"],
            "Trabalho": ["Gastos Trabalho Ana"],
            "Caridade": ["Doações", "Dízimo"],
            "Dívidas": ["Empréstimos", "Financiamentos"],
            "Outros": ["Presentes", "Aquisição de Bens", "Juros Conta"]
        }
        
        # Lista de categorias para o cartão
        categorias_cartao = list(SUBCATEGORIAS_CARTAO.keys())
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_compra = st.date_input("📅 Data da Compra:", value=date.today(), key="data_cartao_final")
            
            # Selectbox de categoria
            categoria_cartao = st.selectbox(
                "📁 Categoria:", 
                options=categorias_cartao,
                index=0,
                key="cat_cartao_final"
            )
            
            # Buscar subcategorias do dicionário fixo
            lista_subcategorias = SUBCATEGORIAS_CARTAO.get(categoria_cartao, ["Outros"])
            
            # Selectbox de subcategoria
            subcategoria_cartao = st.selectbox(
                "📋 Subcategoria:", 
                options=lista_subcategorias,
                index=0,
                key="subcat_cartao_final"
            )
            
            descricao_cartao = st.text_input("📝 Descrição:", key="desc_cartao_final")
        
        with col2:
            valor_total = st.number_input("💰 Valor Total:", min_value=0.0, step=10.0, format="%.2f", key="valor_cartao_final")
            num_parcelas = st.number_input("🔢 Nº de Parcelas:", min_value=1, max_value=24, value=1, step=1, key="parcelas_cartao_final")
            
            # Buscar cartões do banco
            cartoes = get_cartoes()
            if not cartoes:
                cartoes = ["Crédito INTER - João", "Crédito INTER - Ana", "Crédito Credicom Ana"]
            
            cartao = st.selectbox("💳 Cartão:", options=cartoes, key="cartao_select_final")
            
            if valor_total > 0 and num_parcelas > 0:
                st.metric("💵 Valor da Parcela", formatar_moeda(valor_total / num_parcelas))
        
        # Mostrar seleção atual
        st.success(f"📋 **{categoria_cartao}** → **{subcategoria_cartao}**")
        
        # Botão salvar
        if st.button("💾 Salvar Compra no Cartão", type="primary", key="btn_salvar_cartao_final"):
            if categoria_cartao and subcategoria_cartao and valor_total > 0:
                salvar_compra_cartao(data_compra, categoria_cartao, subcategoria_cartao, descricao_cartao, valor_total, num_parcelas, cartao)
                st.success(f"✅ Compra de {formatar_moeda(valor_total)} em {num_parcelas}x no cartão {cartao} salva!")
                st.balloons()
            else:
                st.error("❌ Preencha todos os campos!")
    
    # TAB 3: HISTÓRICO
    with tab3:
        st.subheader("📋 Últimos Lançamentos")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 💵 Despesas à Vista")
            df_avista = get_despesas_recentes(20)
            if not df_avista.empty:
                df_avista['data'] = pd.to_datetime(df_avista['data']).dt.strftime('%d/%m/%Y')
                df_avista['valor'] = df_avista['valor'].apply(formatar_moeda)
                df_show = df_avista[['id', 'data', 'categoria', 'valor', 'conta', 'status']]
                df_show.columns = ['ID', '📅', '📁 Cat', '💰', '🏦', '✅']
                st.dataframe(df_show, use_container_width=True, hide_index=True, height=400)
            else:
                st.info("📭 Nenhuma despesa encontrada.")
        
        with col2:
            st.markdown("##### 💳 Compras no Cartão")
            df_cartao = get_cartoes_recentes(20)
            if not df_cartao.empty:
                df_cartao['data'] = pd.to_datetime(df_cartao['data']).dt.strftime('%d/%m/%Y')
                df_cartao['valor'] = df_cartao['valor'].apply(formatar_moeda)
                df_show = df_cartao[['id', 'data', 'categoria', 'valor', 'cartao', 'num_parcelas']]
                df_show.columns = ['ID', '📅', '📁 Cat', '💰', '💳', '🔢']
                st.dataframe(df_show, use_container_width=True, hide_index=True, height=400)
            else:
                st.info("📭 Nenhuma compra encontrada.")
    
    # TAB 4: EDITAR/EXCLUIR
    with tab4:
        st.subheader("✏️ Editar ou Excluir Despesa")
        
        df_despesas = get_despesas_recentes(50)
        if not df_despesas.empty:
            opcoes = []
            for _, row in df_despesas.iterrows():
                data_fmt = pd.to_datetime(row['data']).strftime('%d/%m/%Y')
                status_emoji = "✅" if row['status'] == 'Realizado' else "⏳"
                opcao = f"[{row['id']}] {data_fmt} | {row['categoria']} | {formatar_moeda(row['valor'])} | {row['conta']} | {status_emoji}"
                opcoes.append(opcao)
            
            selecionado = st.selectbox("Selecione a despesa:", opcoes, key="edit_desp_select")
            id_selecionado = int(selecionado.split(']')[0].replace('[', ''))
            
            despesa = get_despesa_por_id(id_selecionado)
            if despesa is not None:
                st.markdown("---")
                st.markdown(f"##### 📝 Editando Despesa ID: **{id_selecionado}**")
                
                contas = get_contas()
                contas_nomes = [c['nome'] for c in contas] if contas else ["Conta não cadastrada"]
                
                col1, col2 = st.columns(2)
                with col1:
                    nova_data = st.date_input("📅 Data:", value=pd.to_datetime(despesa['data']).date(), key=f"edit_desp_data_{id_selecionado}")
                    categorias = get_categorias("Despesa")
                    idx_cat = categorias.index(despesa['categoria']) if despesa['categoria'] in categorias else 0
                    nova_categoria = st.selectbox("📁 Categoria:", categorias, index=idx_cat, key=f"edit_desp_cat_{id_selecionado}")
                    
                    subcategorias = get_subcategorias("Despesa", nova_categoria)
                    idx_subcat = 0
                    if despesa['subcategoria'] in subcategorias:
                        idx_subcat = subcategorias.index(despesa['subcategoria'])
                    nova_subcategoria = st.selectbox("📋 Subcategoria:", subcategorias if subcategorias else [""], index=idx_subcat, key=f"edit_desp_subcat_{id_selecionado}")
                
                with col2:
                    novo_valor = st.number_input("💰 Valor:", value=float(despesa['valor']), min_value=0.0, step=10.0, key=f"edit_desp_valor_{id_selecionado}")
                    nova_descricao = st.text_input("📝 Descrição:", value=despesa['descricao'] if despesa['descricao'] else "", key=f"edit_desp_desc_{id_selecionado}")
                    
                    idx_conta = 0
                    if despesa['conta_nome'] and despesa['conta_nome'] in contas_nomes:
                        idx_conta = contas_nomes.index(despesa['conta_nome'])
                    nova_conta = st.selectbox("🏦 Conta:", contas_nomes, index=idx_conta, key=f"edit_desp_conta_{id_selecionado}")
                    
                    status_opcoes = ["Realizado", "Previsto", "Cancelado"]
                    idx_status = status_opcoes.index(despesa['status']) if despesa['status'] in status_opcoes else 0
                    novo_status = st.selectbox("✅ Status:", status_opcoes, index=idx_status, key=f"edit_desp_status_{id_selecionado}")
                
                if nova_data > date.today() and novo_status == "Realizado":
                    st.warning("⚠️ Data futura com status 'Realizado'. Considere mudar para 'Previsto'.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Salvar Alterações", type="primary", key=f"btn_salvar_desp_{id_selecionado}"):
                        nova_conta_id = get_conta_id_por_nome(nova_conta)
                        atualizar_despesa(id_selecionado, nova_data, nova_categoria, nova_subcategoria, novo_valor, nova_descricao, novo_status, nova_conta_id)
                        st.success("✅ Despesa atualizada!")
                        st.rerun()
                with col2:
                    if st.button("🗑️ Excluir", type="secondary", key=f"btn_excluir_desp_{id_selecionado}"):
                        excluir_despesa(id_selecionado)
                        st.success("✅ Despesa excluída!")
                        st.rerun()