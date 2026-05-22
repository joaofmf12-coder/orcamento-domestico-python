import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime

# IMPORTAR DO MÓDULO CENTRAL
from services.financeiro_central import (
    get_dashboard_resumo,
    get_fluxo_caixa_mensal,
    get_despesas_por_categoria,
    get_receitas_por_categoria,
    get_saldo_inicial_ano,
    get_saldo_atual_contas
)


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


def mostrar_dashboard():
    st.title("Dashboard - Orcamento Domestico")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        ano = st.selectbox("Ano", options=[2024, 2025, 2026], index=2, key="dash_ano")
    
    with col2:
        mes_opcoes = {0: "Ano Completo"}
        for i in range(1, 13):
            mes_opcoes[i] = datetime(2000, i, 1).strftime("%B")
        mes = st.selectbox("Mes", options=list(mes_opcoes.keys()), format_func=lambda x: mes_opcoes[x], index=0, key="dash_mes")
    
    st.markdown("---")
    
    # USAR MÓDULO CENTRAL
    try:
        resumo = get_dashboard_resumo(ano, mes if mes > 0 else None)
    except Exception as e:
        st.warning(f"Nao foi possivel carregar os dados: {e}")
        resumo = {'receitas': 0, 'despesas': 0, 'saldo': 0, 'investimentos': 0, 'economia_percentual': 0, 'saldo_contas': 0}
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Receitas", formatar_moeda(resumo['receitas']))
    col2.metric("Despesas", formatar_moeda(resumo['despesas']))
    col3.metric("Saldo", formatar_moeda(resumo['saldo']), delta=f"{resumo['economia_percentual']}%")
    col4.metric("Investimentos", formatar_moeda(resumo['investimentos']))
    col5.metric("Taxa Economia", f"{resumo['economia_percentual']}%")
    
    # Mostrar saldo atual das contas
    st.info(f"💰 **Saldo Atual das Contas Bancárias:** {formatar_moeda(resumo.get('saldo_contas', 0))}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Despesas por Categoria")
        try:
            despesas_cat = get_despesas_por_categoria(ano, mes if mes > 0 else None)
            if despesas_cat:
                df = pd.DataFrame([{"Categoria": k, "Valor": v} for k, v in despesas_cat.items()])
                fig = px.pie(df, values='Valor', names='Categoria', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma despesa encontrada.")
        except Exception as e:
            st.warning(f"Erro: {e}")
    
    with col2:
        st.subheader("Receitas por Categoria")
        try:
            receitas_cat = get_receitas_por_categoria(ano, mes if mes > 0 else None)
            if receitas_cat:
                df = pd.DataFrame([{"Categoria": k, "Valor": v} for k, v in receitas_cat.items()])
                fig = px.bar(df, x='Categoria', y='Valor', color='Categoria')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma receita encontrada.")
        except Exception as e:
            st.warning(f"Erro: {e}")
    
    st.markdown("---")
    st.subheader("Fluxo de Caixa Mensal")
    
    # Mostrar saldo inicial usado
    saldo_inicial = get_saldo_inicial_ano(ano)
    st.caption(f"💰 Saldo em 01/01/{ano}: {formatar_moeda(saldo_inicial)}")
    
    try:
        # USAR MÓDULO CENTRAL
        fluxo = get_fluxo_caixa_mensal(ano)
        
        if fluxo:
            df_fluxo = pd.DataFrame(fluxo)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_fluxo['mes_nome'], y=df_fluxo['entradas_total'], name='Entradas', marker_color='#2ecc71'))
            fig.add_trace(go.Bar(x=df_fluxo['mes_nome'], y=df_fluxo['saidas_total'], name='Saidas', marker_color='#e74c3c'))
            fig.add_trace(go.Scatter(x=df_fluxo['mes_nome'], y=df_fluxo['saldo_acumulado'], name='Saldo Acumulado', mode='lines+markers', line=dict(color='#3498db', width=3), yaxis='y2'))
            fig.update_layout(barmode='group', yaxis=dict(title='Valores (R$)'), yaxis2=dict(title='Saldo Acumulado', overlaying='y', side='right'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")
    except Exception as e:
        st.warning(f"Erro: {e}")
