import streamlit as st
import pandas as pd
from datetime import date

from services.contas import (
    criar_conta, listar_contas, buscar_conta, atualizar_conta,
    excluir_conta, calcular_saldo_conta, calcular_saldo_todas_contas
)
from services.receitas import listar_receitas
from services.despesas import listar_despesas


def mostrar_contas():
    st.title("Contas Bancarias")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["Saldos", "Nova Conta", "Extrato"])
    
    with tab1:
        st.subheader("Saldo das Contas")
        
        try:
            contas = listar_contas()
            
            if contas:
                dados = []
                total_geral = 0
                
                for conta in contas:
                    saldo = calcular_saldo_conta(conta['id'])
                    total_geral += saldo
                    
                    dados.append({
                        'ID': conta['id'],
                        'Conta': conta['nome'],
                        'Banco': conta['banco'] or "-",
                        'Tipo': conta['tipo'],
                        'Saldo Inicial': f"R$ {conta['saldo_inicial']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                        'Saldo Atual': f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    })
                
                df = pd.DataFrame(dados)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total de Contas", len(contas))
                with col2:
                    st.metric("Saldo Total", f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.markdown("---")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    id_excluir = st.number_input("ID para desativar", min_value=1, step=1, key="conta_excluir")
                with col2:
                    if st.button("Desativar", type="secondary"):
                        if excluir_conta(int(id_excluir)):
                            st.success("Conta desativada!")
                            st.rerun()
                        else:
                            st.error("Conta nao encontrada!")
            else:
                st.info("Nenhuma conta cadastrada ainda.")
                st.markdown("Va para a aba Nova Conta para cadastrar.")
        
        except Exception as e:
            st.warning(f"Erro ao carregar contas: {e}")
    
    with tab2:
        st.subheader("Cadastrar Nova Conta")
        
        with st.form("form_conta", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome da Conta", placeholder="Ex: Conta Corrente Banco A")
                banco = st.text_input("Banco", placeholder="Ex: Banco A")
                tipo = st.selectbox(
                    "Tipo de Conta",
                    options=["Corrente", "Poupanca", "Investimento", "Carteira"]
                )
            
            with col2:
                saldo_inicial = st.number_input(
                    "Saldo Inicial",
                    min_value=0.0,
                    step=1000.0,
                    format="%.2f",
                    help="Saldo da conta na data informada abaixo"
                )
                data_saldo = st.date_input(
                    "Data do Saldo Inicial",
                    value=date.today(),
                    help="Data de referencia do saldo inicial"
                )
            
            submitted = st.form_submit_button("Cadastrar Conta", type="primary")
            
            if submitted:
                if nome:
                    try:
                        criar_conta(
                            nome=nome,
                            banco=banco if banco else None,
                            tipo=tipo,
                            saldo_inicial=saldo_inicial,
                            data_saldo_inicial=data_saldo
                        )
                        st.success("Conta cadastrada com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {e}")
                else:
                    st.error("Informe o nome da conta!")
    
    with tab3:
        st.subheader("Extrato por Conta")
        
        try:
            contas = listar_contas()
            
            if not contas:
                st.warning("Cadastre uma conta primeiro.")
            else:
                conta_opcoes = {c['id']: c['nome'] for c in contas}
                conta_id = st.selectbox(
                    "Selecione a Conta",
                    options=list(conta_opcoes.keys()),
                    format_func=lambda x: conta_opcoes[x]
                )
                
                conta = buscar_conta(conta_id)
                
                if conta:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Banco", conta['banco'] or "-")
                    with col2:
                        st.metric("Tipo", conta['tipo'])
                    with col3:
                        saldo = calcular_saldo_conta(conta_id)
                        st.metric("Saldo Atual", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    
                    st.markdown("---")
                    
                    receitas = listar_receitas(conta_id=conta_id)
                    despesas = listar_despesas(conta_id=conta_id)
                    
                    movimentos = []
                    
                    for r in receitas:
                        movimentos.append({
                            'Data': r['data'],
                            'Tipo': 'Entrada',
                            'Categoria': r['categoria'],
                            'Descricao': r['descricao'] or "-",
                            'Valor': r['valor']
                        })
                    
                    for d in despesas:
                        movimentos.append({
                            'Data': d['data'],
                            'Tipo': 'Saida',
                            'Categoria': d['categoria'],
                            'Descricao': d['descricao'] or "-",
                            'Valor': -d['valor']
                        })
                    
                    if movimentos:
                        df = pd.DataFrame(movimentos)
                        df = df.sort_values('Data', ascending=False)
                        df['Data'] = df['Data'].apply(lambda x: x.strftime("%d/%m/%Y"))
                        df['Valor'] = df['Valor'].apply(
                            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        )
                        
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhum movimento encontrado para esta conta.")
        
        except Exception as e:
            st.warning(f"Erro ao carregar extrato: {e}")