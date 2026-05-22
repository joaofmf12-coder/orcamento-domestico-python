import streamlit as st
import pandas as pd
from datetime import date, datetime

from services.investimentos import (
    criar_investimento, listar_investimentos, excluir_investimento,
    total_investimentos, investimentos_por_tipo, saldo_investimentos
)


def mostrar_investimentos():
    st.title("Investimentos")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["Novo Lancamento", "Historico", "Resumo"])
    
    with tab1:
        st.subheader("Novo Lancamento de Investimento")
        
        with st.form("form_investimento", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                data = st.date_input("Data", value=date.today())
                ativo = st.text_input("Ativo", placeholder="Ex: Tesouro Direto, ITUB4, ETF IVVB11")
                tipo_ativo = st.selectbox(
                    "Tipo de Ativo",
                    options=["Renda Fixa", "Renda Variavel", "Previdencia", "Alternativos"]
                )
            
            with col2:
                movimento = st.selectbox("Movimento", options=["Aporte", "Resgate"])
                valor = st.number_input("Valor", min_value=0.01, step=100.0, format="%.2f")
                observacao = st.text_input("Observacao", placeholder="Opcional")
            
            if st.form_submit_button("Registrar", type="primary"):
                if valor > 0 and ativo:
                    try:
                        criar_investimento(
                            data=data,
                            ativo=ativo,
                            tipo_ativo=tipo_ativo,
                            movimento=movimento,
                            valor=valor,
                            observacao=observacao if observacao else None
                        )
                        st.success("Investimento registrado com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.error("Preencha o ativo e o valor!")
    
    with tab2:
        st.subheader("Historico de Investimentos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ano = st.selectbox("Ano", [2024, 2025, 2026], index=2, key="inv_ano")
        with col2:
            mes_opcoes = {0: "Todos"}
            for i in range(1, 13):
                mes_opcoes[i] = datetime(2000, i, 1).strftime("%B")
            mes = st.selectbox("Mes", options=list(mes_opcoes.keys()), format_func=lambda x: mes_opcoes[x], key="inv_mes")
        with col3:
            mov_filtro = st.selectbox("Movimento", ["Todos", "Aporte", "Resgate"], key="inv_mov")
        
        try:
            investimentos = listar_investimentos(
                ano=ano,
                mes=mes if mes > 0 else None,
                movimento=mov_filtro if mov_filtro != "Todos" else None
            )
            
            if investimentos:
                df = pd.DataFrame([{
                    'ID': i['id'],
                    'Data': i['data'].strftime("%d/%m/%Y"),
                    'Ativo': i['ativo'],
                    'Tipo': i['tipo_ativo'],
                    'Movimento': i['movimento'],
                    'Valor': f"R$ {i['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                } for i in investimentos])
                
                total_aportes = sum(i['valor'] for i in investimentos if i['movimento'] == 'Aporte')
                total_resgates = sum(i['valor'] for i in investimentos if i['movimento'] == 'Resgate')
                saldo = total_aportes - total_resgates
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Aportes", f"R$ {total_aportes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                col2.metric("Resgates", f"R$ {total_resgates:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                col3.metric("Saldo", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    id_excluir = st.number_input("ID para excluir", min_value=1, step=1, key="inv_excluir")
                with col2:
                    if st.button("Excluir", type="secondary", key="btn_excluir_inv"):
                        if excluir_investimento(int(id_excluir)):
                            st.success("Investimento excluido!")
                            st.rerun()
                        else:
                            st.error("Investimento nao encontrado!")
            else:
                st.info("Nenhum investimento encontrado para o periodo.")
        except Exception as e:
            st.warning(f"Erro: {e}")
    
    with tab3:
        st.subheader("Resumo de Investimentos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ano_res = st.selectbox("Ano", [2024, 2025, 2026], index=2, key="inv_res_ano")
        with col2:
            mes_opcoes = {0: "Ano Completo"}
            for i in range(1, 13):
                mes_opcoes[i] = datetime(2000, i, 1).strftime("%B")
            mes_res = st.selectbox("Mes", options=list(mes_opcoes.keys()), format_func=lambda x: mes_opcoes[x], key="inv_res_mes")
        
        try:
            inv_por_tipo = investimentos_por_tipo(ano_res, mes_res if mes_res > 0 else None)
            
            if inv_por_tipo:
                dados = []
                total_aportes = 0
                total_resgates = 0
                
                for tipo, valores in inv_por_tipo.items():
                    saldo = valores['aportes'] - valores['resgates']
                    total_aportes += valores['aportes']
                    total_resgates += valores['resgates']
                    
                    dados.append({
                        'Tipo': tipo,
                        'Aportes': f"R$ {valores['aportes']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                        'Resgates': f"R$ {valores['resgates']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                        'Saldo': f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    })
                
                df = pd.DataFrame(dados)
                
                saldo_total = total_aportes - total_resgates
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Aportes", f"R$ {total_aportes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                col2.metric("Total Resgates", f"R$ {total_resgates:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                col3.metric("Saldo Liquido", f"R$ {saldo_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.markdown("---")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum investimento encontrado para o periodo.")
        except Exception as e:
            st.warning(f"Erro: {e}")