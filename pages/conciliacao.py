"""
Conciliação Bancária - Extrato por Conta e Verificação de Saldos
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database.connection import get_engine
from sqlalchemy import text


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


def get_contas():
    """Busca lista de contas bancárias"""
    engine = get_engine()
    query = "SELECT id, nome, banco, tipo, saldo_inicial, data_saldo_inicial FROM contas WHERE ativo = 1 ORDER BY nome"
    return pd.read_sql(query, engine)


def get_extrato_conta(conta_id, data_inicio, data_fim):
    """Busca extrato de uma conta específica"""
    engine = get_engine()
    
    # Receitas
    query_rec = f"""
        SELECT data, 'Entrada' as tipo, categoria, subcategoria, valor, descricao, status, conciliado
        FROM receitas
        WHERE conta_id = {conta_id} 
          AND data BETWEEN '{data_inicio}' AND '{data_fim}'
          AND status = 'Realizado'
        ORDER BY data, id
    """
    df_rec = pd.read_sql(query_rec, engine)
    
    # Despesas
    query_desp = f"""
        SELECT data, 'Saída' as tipo, categoria, subcategoria, valor * -1 as valor, descricao, status, conciliado
        FROM despesas
        WHERE conta_id = {conta_id} 
          AND data BETWEEN '{data_inicio}' AND '{data_fim}'
          AND status = 'Realizado'
        ORDER BY data, id
    """
    df_desp = pd.read_sql(query_desp, engine)
    
    # Combinar
    df = pd.concat([df_rec, df_desp], ignore_index=True)
    df = df.sort_values('data').reset_index(drop=True)
    
    return df


def get_saldo_anterior(conta_id, data_referencia):
    """Calcula saldo anterior a uma data"""
    engine = get_engine()
    
    # Buscar saldo inicial da conta
    query_conta = f"SELECT saldo_inicial, data_saldo_inicial FROM contas WHERE id = {conta_id}"
    df_conta = pd.read_sql(query_conta, engine)
    
    if df_conta.empty:
        return 0.0
    
    saldo_inicial = float(df_conta.iloc[0]['saldo_inicial'])
    data_saldo = df_conta.iloc[0]['data_saldo_inicial']
    
    # Receitas anteriores
    query_rec = f"""
        SELECT COALESCE(SUM(valor), 0) as total
        FROM receitas
        WHERE conta_id = {conta_id} 
          AND data >= '{data_saldo}' AND data < '{data_referencia}'
          AND status = 'Realizado'
    """
    df_rec = pd.read_sql(query_rec, engine)
    total_rec = float(df_rec.iloc[0]['total']) if not df_rec.empty else 0
    
    # Despesas anteriores
    query_desp = f"""
        SELECT COALESCE(SUM(valor), 0) as total
        FROM despesas
        WHERE conta_id = {conta_id} 
          AND data >= '{data_saldo}' AND data < '{data_referencia}'
          AND status = 'Realizado'
    """
    df_desp = pd.read_sql(query_desp, engine)
    total_desp = float(df_desp.iloc[0]['total']) if not df_desp.empty else 0
    
    return saldo_inicial + total_rec - total_desp


def get_saldo_atual(conta_id):
    """Calcula saldo atual da conta"""
    engine = get_engine()
    
    # Buscar saldo inicial
    query_conta = f"SELECT saldo_inicial, data_saldo_inicial FROM contas WHERE id = {conta_id}"
    df_conta = pd.read_sql(query_conta, engine)
    
    if df_conta.empty:
        return 0.0
    
    saldo_inicial = float(df_conta.iloc[0]['saldo_inicial'])
    data_saldo = df_conta.iloc[0]['data_saldo_inicial']
    
    # Total receitas realizadas
    query_rec = f"""
        SELECT COALESCE(SUM(valor), 0) as total
        FROM receitas
        WHERE conta_id = {conta_id} AND status = 'Realizado' AND data >= '{data_saldo}'
    """
    df_rec = pd.read_sql(query_rec, engine)
    total_rec = float(df_rec.iloc[0]['total']) if not df_rec.empty else 0
    
    # Total despesas realizadas
    query_desp = f"""
        SELECT COALESCE(SUM(valor), 0) as total
        FROM despesas
        WHERE conta_id = {conta_id} AND status = 'Realizado' AND data >= '{data_saldo}'
    """
    df_desp = pd.read_sql(query_desp, engine)
    total_desp = float(df_desp.iloc[0]['total']) if not df_desp.empty else 0
    
    return saldo_inicial + total_rec - total_desp


def atualizar_saldo_inicial_conta(conta_id, novo_saldo, data_saldo):
    """Atualiza saldo inicial da conta"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("""
            UPDATE contas 
            SET saldo_inicial = :saldo, data_saldo_inicial = :data
            WHERE id = :id
        """)
        conn.execute(query, {"saldo": novo_saldo, "data": data_saldo, "id": conta_id})
        conn.commit()


def marcar_conciliado(tabela, id_registro, conciliado):
    """Marca um registro como conciliado ou não"""
    engine = get_engine()
    with engine.connect() as conn:
        query = text(f"UPDATE {tabela} SET conciliado = :conciliado WHERE id = :id")
        conn.execute(query, {"conciliado": 1 if conciliado else 0, "id": id_registro})
        conn.commit()


def mostrar_conciliacao():
    """Renderiza a página de Conciliação Bancária."""
    
    st.title("🏦 Conciliação Bancária")
    st.markdown("*Extrato por conta e verificação de saldos*")
    
    tab1, tab2, tab3 = st.tabs(["📊 Extrato por Conta", "💰 Saldos das Contas", "⚙️ Ajustar Saldo"])
    
    # ------------------------------------------
    # TAB 1: EXTRATO POR CONTA
    # ------------------------------------------
    with tab1:
        st.subheader("📊 Extrato Bancário por Conta")
        
        df_contas = get_contas()
        
        if df_contas.empty:
            st.warning("⚠️ Nenhuma conta cadastrada!")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            contas_dict = {row['id']: row['nome'] for _, row in df_contas.iterrows()}
            conta_selecionada = st.selectbox(
                "🏦 Selecione a Conta:",
                options=list(contas_dict.keys()),
                format_func=lambda x: contas_dict[x],
                key="extrato_conta"
            )
        with col2:
            data_inicio = st.date_input("📅 Data Inicial:", value=date.today().replace(day=1), key="extrato_ini")
        with col3:
            data_fim = st.date_input("📅 Data Final:", value=date.today(), key="extrato_fim")
        
        # Buscar extrato
        df_extrato = get_extrato_conta(conta_selecionada, data_inicio, data_fim)
        saldo_anterior = get_saldo_anterior(conta_selecionada, data_inicio)
        
        # KPIs
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        total_entradas = df_extrato[df_extrato['tipo'] == 'Entrada']['valor'].sum() if not df_extrato.empty else 0
        total_saidas = abs(df_extrato[df_extrato['tipo'] == 'Saída']['valor'].sum()) if not df_extrato.empty else 0
        saldo_periodo = total_entradas - total_saidas
        saldo_final = saldo_anterior + saldo_periodo
        
        with col1:
            st.metric("💵 Saldo Anterior", formatar_moeda(saldo_anterior))
        with col2:
            st.metric("📥 Entradas", formatar_moeda(total_entradas))
        with col3:
            st.metric("📤 Saídas", formatar_moeda(total_saidas))
        with col4:
            st.metric("🏦 Saldo Final", formatar_moeda(saldo_final))
        
        st.markdown("---")
        
        # Exibir extrato
        if not df_extrato.empty:
            df_display = df_extrato.copy()
            
            # Calcular saldo acumulado
            df_display['saldo'] = saldo_anterior + df_display['valor'].cumsum()
            
            # Formatar
            df_display['data'] = pd.to_datetime(df_display['data']).dt.strftime('%d/%m/%Y')
            df_display['valor_fmt'] = df_display['valor'].apply(formatar_moeda)
            df_display['saldo_fmt'] = df_display['saldo'].apply(formatar_moeda)
            df_display['tipo_emoji'] = df_display['tipo'].apply(lambda x: '📥' if x == 'Entrada' else '📤')
            
            df_show = df_display[['data', 'tipo_emoji', 'categoria', 'subcategoria', 'valor_fmt', 'saldo_fmt', 'descricao']]
            df_show.columns = ['📅 Data', '↕️', '📁 Categoria', '📋 Subcategoria', '💰 Valor', '🏦 Saldo', '📝 Descrição']
            
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=400)
            
            # Totais
            st.info(f"📊 **{len(df_extrato)} lançamentos** | Entradas: {formatar_moeda(total_entradas)} | Saídas: {formatar_moeda(total_saidas)}")
        else:
            st.info("📭 Nenhum lançamento encontrado no período.")
    
    # ------------------------------------------
    # TAB 2: SALDOS DAS CONTAS
    # ------------------------------------------
    with tab2:
        st.subheader("💰 Saldos de Todas as Contas")
        
        df_contas = get_contas()
        
        if not df_contas.empty:
            dados = []
            total_geral = 0
            
            for _, conta in df_contas.iterrows():
                saldo = get_saldo_atual(conta['id'])
                total_geral += saldo
                
                dados.append({
                    'Conta': conta['nome'],
                    'Banco': conta['banco'] or "-",
                    'Tipo': conta['tipo'],
                    'Saldo Sistema': formatar_moeda(saldo),
                    'Saldo_Num': saldo
                })
            
            df_saldos = pd.DataFrame(dados)
            
            # Exibir
            df_show = df_saldos[['Conta', 'Banco', 'Tipo', 'Saldo Sistema']]
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.metric("💰 TOTAL GERAL", formatar_moeda(total_geral))
            
            # Comparar com saldo real
            st.markdown("---")
            st.markdown("##### 🔍 Comparar com Saldo Real do Banco")
            
            col1, col2 = st.columns(2)
            with col1:
                conta_comparar = st.selectbox(
                    "Conta:",
                    options=[d['Conta'] for d in dados],
                    key="conta_comparar"
                )
                saldo_sistema = next((d['Saldo_Num'] for d in dados if d['Conta'] == conta_comparar), 0)
            with col2:
                saldo_real = st.number_input("Saldo Real no Banco:", value=0.0, step=100.0, key="saldo_real_input")
            
            if saldo_real > 0:
                diferenca = saldo_real - saldo_sistema
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Sistema", formatar_moeda(saldo_sistema))
                with col2:
                    st.metric("Banco", formatar_moeda(saldo_real))
                with col3:
                    cor = "🟢" if abs(diferenca) < 1 else "🔴"
                    st.metric(f"{cor} Diferença", formatar_moeda(diferenca))
                
                if abs(diferenca) > 1:
                    if diferenca > 0:
                        st.warning(f"""
                        **O banco tem {formatar_moeda(diferenca)} A MAIS que o sistema.**
                        
                        Possíveis causas:
                        - Receitas não lançadas no sistema
                        - Despesas lançadas mas não pagas
                        """)
                    else:
                        st.warning(f"""
                        **O banco tem {formatar_moeda(abs(diferenca))} A MENOS que o sistema.**
                        
                        Possíveis causas:
                        - Despesas pagas mas não lançadas
                        - Receitas lançadas mas não recebidas
                        """)
        else:
            st.info("📭 Nenhuma conta cadastrada.")
    
    # ------------------------------------------
    # TAB 3: AJUSTAR SALDO
    # ------------------------------------------
    with tab3:
        st.subheader("⚙️ Ajustar Saldo Inicial da Conta")
        st.info("💡 Use para corrigir o saldo inicial de uma conta, ajustando a data de referência.")
        
        df_contas = get_contas()
        
        if not df_contas.empty:
            contas_dict = {row['id']: row['nome'] for _, row in df_contas.iterrows()}
            
            conta_ajuste = st.selectbox(
                "🏦 Conta:",
                options=list(contas_dict.keys()),
                format_func=lambda x: contas_dict[x],
                key="ajuste_conta"
            )
            
            # Dados atuais
            conta_info = df_contas[df_contas['id'] == conta_ajuste].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Saldo Inicial Atual", formatar_moeda(conta_info['saldo_inicial']))
                st.write(f"📅 Data de Referência: {pd.to_datetime(conta_info['data_saldo_inicial']).strftime('%d/%m/%Y') if conta_info['data_saldo_inicial'] else 'Não definida'}")
            
            with col2:
                saldo_atual = get_saldo_atual(conta_ajuste)
                st.metric("Saldo Atual Calculado", formatar_moeda(saldo_atual))
            
            st.markdown("---")
            st.markdown("##### 📝 Novo Saldo")
            
            col1, col2 = st.columns(2)
            with col1:
                novo_saldo = st.number_input("💰 Novo Saldo Inicial:", value=float(conta_info['saldo_inicial']), step=100.0, key="novo_saldo")
            with col2:
                nova_data = st.date_input("📅 Data de Referência:", value=date.today(), key="nova_data_saldo")
            
            if st.button("💾 Salvar Ajuste", type="primary", key="btn_salvar_ajuste"):
                atualizar_saldo_inicial_conta(conta_ajuste, novo_saldo, nova_data)
                st.success(f"✅ Saldo da conta '{contas_dict[conta_ajuste]}' ajustado para {formatar_moeda(novo_saldo)} em {nova_data.strftime('%d/%m/%Y')}")
                st.rerun()
        else:
            st.info("📭 Nenhuma conta cadastrada.")