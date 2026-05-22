"""
╔══════════════════════════════════════════════════════════════╗
║                        RELATÓRIOS                            ║
║                                                              ║
║  INTEGRADO com Módulo Financeiro Central                     ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime

# IMPORTAR DO MÓDULO CENTRAL - ÚNICA FONTE DE VERDADE
from services.financeiro_central import (
    get_fluxo_caixa_mensal,
    get_orcado_vs_realizado,
    get_despesas_por_categoria,
    get_receitas_por_categoria,
    get_saldo_inicial_ano
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


def mostrar_relatorios():
    """Renderiza a página de Relatórios."""
    
    st.title("📊 Relatórios")
    st.markdown("*Dados integrados com o módulo financeiro central*")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs([
        "📈 Fluxo de Caixa",
        "📊 Orçado vs Realizado",
        "📋 Análise por Categoria"
    ])
    
    # --------------------------------------------
    # TAB 1: FLUXO DE CAIXA
    # --------------------------------------------
    with tab1:
        st.subheader("📈 Fluxo de Caixa Anual")
        
        ano = st.selectbox("📅 Ano", [2024, 2025, 2026], index=2, key="rel_fc_ano")
        
        # Mostrar saldo inicial (SOMENTE LEITURA - vem do módulo central)
        saldo_inicial = get_saldo_inicial_ano(ano)
        st.info(f"💰 **Saldo em 01/01/{ano}:** {formatar_moeda(saldo_inicial)} *(fonte: configurações do sistema)*")
        
        try:
            # USAR MÓDULO CENTRAL - MESMA FONTE DO DASHBOARD E FLUXO_CAIXA
            fluxo = get_fluxo_caixa_mensal(ano)
            
            if fluxo:
                df = pd.DataFrame(fluxo)
                
                # Gráfico
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df['mes_nome'],
                    y=df['entradas_total'],
                    name='Entradas',
                    marker_color='#27ae60'
                ))
                
                fig.add_trace(go.Bar(
                    x=df['mes_nome'],
                    y=df['saidas_total'],
                    name='Saídas',
                    marker_color='#e74c3c'
                ))
                
                fig.add_trace(go.Scatter(
                    x=df['mes_nome'],
                    y=df['saldo_acumulado'],
                    name='Saldo Acumulado',
                    mode='lines+markers',
                    line=dict(color='#3498db', width=3),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    barmode='group',
                    yaxis=dict(title='Valores (R$)'),
                    yaxis2=dict(title='Saldo Acumulado', overlaying='y', side='right'),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela
                df_exibir = df.copy()
                for col in ['entradas_total', 'saidas_total', 'saldo_mes', 'saldo_acumulado']:
                    df_exibir[col] = df_exibir[col].apply(formatar_moeda)
                
                df_exibir = df_exibir.rename(columns={
                    'mes_nome': 'Mês',
                    'entradas_total': 'Entradas',
                    'saidas_total': 'Saídas',
                    'saldo_mes': 'Saldo Mês',
                    'saldo_acumulado': 'Saldo Acum.'
                })
                
                st.dataframe(df_exibir[['Mês', 'Entradas', 'Saídas', 'Saldo Mês', 'Saldo Acum.']], 
                           use_container_width=True, hide_index=True)
            else:
                st.info("📭 Nenhum dado encontrado.")
        
        except Exception as e:
            st.warning(f"⚠️ Erro: {e}")
    
    # --------------------------------------------
    # TAB 2: ORÇADO VS REALIZADO
    # --------------------------------------------
    with tab2:
        st.subheader("📊 Orçado vs Realizado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ano = st.selectbox("📅 Ano", [2024, 2025, 2026], index=2, key="rel_or_ano")
        
        with col2:
            mes_opcoes = {0: "Ano Completo"} | {i: datetime(2000, i, 1).strftime("%B") for i in range(1, 13)}
            mes = st.selectbox(
                "📆 Mês",
                options=list(mes_opcoes.keys()),
                format_func=lambda x: mes_opcoes[x],
                key="rel_or_mes"
            )
        
        orcamento = {
            'Habitação': 4800,
            'Alimentação': 2000,
            'Transporte': 1200,
            'Saúde': 800,
            'Educação': 1500,
            'Vestuário': 300,
            'Lazer': 600,
            'Caridade': 100,
            'Trabalho': 200,
            'Outros': 1000
        }
        
        try:
            # USAR MÓDULO CENTRAL
            comparativo = get_orcado_vs_realizado(ano, mes if mes > 0 else None, orcamento)
            
            if comparativo:
                df = pd.DataFrame(comparativo)
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df['categoria'],
                    y=df['orcado'],
                    name='Orçado',
                    marker_color='#3498db'
                ))
                
                fig.add_trace(go.Bar(
                    x=df['categoria'],
                    y=df['realizado'],
                    name='Realizado',
                    marker_color='#e74c3c'
                ))
                
                fig.update_layout(
                    barmode='group',
                    xaxis_tickangle=-45,
                    legend=dict(orientation='h', yanchor='bottom', y=1.02)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                df_exibir = df.copy()
                df_exibir['orcado'] = df_exibir['orcado'].apply(formatar_moeda)
                df_exibir['realizado'] = df_exibir['realizado'].apply(formatar_moeda)
                df_exibir['variacao'] = df_exibir['variacao'].apply(formatar_moeda)
                
                df_exibir = df_exibir.rename(columns={
                    'categoria': 'Categoria',
                    'orcado': 'Orçado',
                    'realizado': 'Realizado',
                    'variacao': 'Variação',
                    'variacao_percentual': '% Variação',
                    'status': 'Status'
                })
                
                st.dataframe(df_exibir, use_container_width=True, hide_index=True)
            else:
                st.info("📭 Nenhum dado encontrado.")
        
        except Exception as e:
            st.warning(f"⚠️ Erro: {e}")
    
    # --------------------------------------------
    # TAB 3: ANÁLISE POR CATEGORIA
    # --------------------------------------------
    with tab3:
        st.subheader("📋 Análise por Categoria")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ano = st.selectbox("📅 Ano", [2024, 2025, 2026], index=2, key="rel_cat_ano")
        
        with col2:
            tipo = st.selectbox("📂 Tipo", ["Despesas", "Receitas"], key="rel_cat_tipo")
        
        try:
            # USAR MÓDULO CENTRAL
            if tipo == "Despesas":
                dados = get_despesas_por_categoria(ano)
                titulo = "📉 Despesas por Categoria"
                cor = px.colors.sequential.Reds_r
            else:
                dados = get_receitas_por_categoria(ano)
                titulo = "📈 Receitas por Categoria"
                cor = px.colors.sequential.Greens_r
            
            if dados:
                df = pd.DataFrame([
                    {'Categoria': k, 'Valor': v}
                    for k, v in sorted(dados.items(), key=lambda x: x[1], reverse=True)
                ])
                
                total = df['Valor'].sum()
                df['Percentual'] = (df['Valor'] / total * 100).round(1)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.pie(
                        df,
                        values='Valor',
                        names='Categoria',
                        title=titulo,
                        color_discrete_sequence=cor
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    df_exibir = df.copy()
                    df_exibir['Valor'] = df_exibir['Valor'].apply(formatar_moeda)
                    df_exibir['Percentual'] = df_exibir['Percentual'].apply(lambda x: f"{x}%")
                    
                    st.dataframe(df_exibir, use_container_width=True, hide_index=True)
                    
                    st.metric(f"💰 Total {tipo}", formatar_moeda(total))
            else:
                st.info("📭 Nenhum dado encontrado.")
        
        except Exception as e:
            st.warning(f"⚠️ Erro: {e}")