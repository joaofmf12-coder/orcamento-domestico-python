"""
💰 FLUXO DE CAIXA
Mensal + Próximos 30 dias
INTEGRADO com Módulo Financeiro Central - ÚNICA FONTE DE VERDADE
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.connection import get_engine

# IMPORTAR DO MÓDULO CENTRAL - ÚNICA FONTE DE VERDADE
from services.financeiro_central import (
    get_saldo_inicial_ano,
    get_saldo_atual_contas,
    get_fluxo_caixa_mensal,
    get_fluxo_caixa_diario
)


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


def mostrar_fluxo_caixa():
    st.title("💰 Fluxo de Caixa")
    st.markdown("*Integrado com Módulo Financeiro Central - Dados consistentes em todo o sistema*")
    
    # Calcular saldo atual das contas (ÚNICO PONTO DE VERDADE)
    saldo_atual_contas = get_saldo_atual_contas()
    
    # Filtros
    col1, col2 = st.columns([1, 5])
    with col1:
        ano = st.selectbox("📅 ANO:", [2025, 2026, 2027], index=1)
    
    # Mostrar saldo atual das contas em destaque
    st.success(f"💰 **SALDO ATUAL DAS CONTAS BANCÁRIAS:** {formatar_moeda(saldo_atual_contas)}")
    
    # Saldo inicial do ano (da configuração)
    saldo_inicial_ano = get_saldo_inicial_ano(ano)
    st.info(f"💰 **Saldo em 01/01/{ano}:** {formatar_moeda(saldo_inicial_ano)} *(fonte: tabela configurações)*")
    
    # =====================================
    # FLUXO MENSAL - USANDO MÓDULO CENTRAL
    # =====================================
    st.subheader("📊 FLUXO DE CAIXA MENSAL")
    
    # Buscar dados do módulo central
    fluxo_mensal = get_fluxo_caixa_mensal(ano)
    
    if fluxo_mensal:
        df_fluxo = pd.DataFrame(fluxo_mensal)
        
        # Criar cópia para exibição formatada
        df_display = df_fluxo.copy()
        colunas_moeda = ['entradas_reais', 'entradas_previstas', 'entradas_total', 
                         'saidas_reais', 'saidas_previstas', 'saidas_total', 
                         'saldo_mes', 'saldo_acumulado']
        
        for col in colunas_moeda:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(formatar_moeda)
        
        # Renomear colunas para exibição
        df_display = df_display.rename(columns={
            'mes_nome': 'Mês',
            'entradas_reais': 'Entradas Reais',
            'entradas_previstas': 'Entradas Prev.',
            'saidas_reais': 'Saídas Reais',
            'saidas_previstas': 'Saídas Prev.',
            'saldo_mes': 'Saldo Mês',
            'saldo_acumulado': 'Saldo Acum.',
            'status': 'Status'
        })
        
        # Selecionar colunas para exibição
        colunas_exibir = ['Mês', 'Entradas Reais', 'Entradas Prev.', 'Saídas Reais', 'Saídas Prev.', 'Saldo Mês', 'Saldo Acum.', 'Status']
        colunas_disponiveis = [c for c in colunas_exibir if c in df_display.columns]
        
        # Estilizar linhas negativas
        def highlight_negative(row):
            if '🔴' in str(row.get('Status', '')):
                return ['background-color: #ffcccc'] * len(row)
            return [''] * len(row)
        
        st.dataframe(
            df_display[colunas_disponiveis].style.apply(highlight_negative, axis=1),
            use_container_width=True,
            hide_index=True
        )
        
        # Totais
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        total_entradas = df_fluxo['entradas_total'].sum() if 'entradas_total' in df_fluxo.columns else 0
        total_saidas = df_fluxo['saidas_total'].sum() if 'saidas_total' in df_fluxo.columns else 0
        saldo_final = df_fluxo['saldo_acumulado'].iloc[-1] if 'saldo_acumulado' in df_fluxo.columns else 0
        
        with col1:
            st.metric("📥 Total Entradas", formatar_moeda(total_entradas))
        with col2:
            st.metric("📤 Total Saídas", formatar_moeda(total_saidas))
        with col3:
            st.metric("💵 Saldo Final Ano", formatar_moeda(saldo_final))
        with col4:
            meses_neg = len(df_fluxo[df_fluxo['saldo_acumulado'] < 0]) if 'saldo_acumulado' in df_fluxo.columns else 0
            if meses_neg > 0:
                st.metric("⚠️ Meses Negativos", meses_neg)
            else:
                st.metric("✅ Status", "Tudo OK!")
    else:
        st.info("📭 Nenhum dado encontrado para o fluxo mensal.")
    
    st.divider()
    
    # =====================================
    # FLUXO PRÓXIMOS 30 DIAS - USANDO MÓDULO CENTRAL
    # =====================================
    st.subheader("📅 FLUXO DE CAIXA - PRÓXIMOS 30 DIAS")
    
    # O saldo inicial do fluxo diário É o saldo atual das contas
    st.info(f"💰 **Saldo Inicial (hoje):** {formatar_moeda(saldo_atual_contas)} *(= Saldo Atual das Contas Bancárias)*")
    
    # Buscar dados do módulo central
    fluxo_diario = get_fluxo_caixa_diario(30)
    
    if fluxo_diario:
        df_30dias = pd.DataFrame(fluxo_diario)
        
        # Criar cópia para exibição formatada
        df_display_30 = df_30dias.copy()
        colunas_moeda_30 = ['entradas', 'saidas', 'saldo_dia', 'saldo_acumulado']
        
        for col in colunas_moeda_30:
            if col in df_display_30.columns:
                df_display_30[col] = df_display_30[col].apply(formatar_moeda)
        
        # Renomear colunas
        df_display_30 = df_display_30.rename(columns={
            'num': '#',
            'data_fmt': 'Data',
            'dia_semana': 'Dia',
            'entradas': 'Entradas',
            'saidas': 'Saídas',
            'saldo_dia': 'Saldo Dia',
            'saldo_acumulado': 'Saldo Acum.',
            'marcador': ''
        })
        
        # Selecionar colunas para exibição
        colunas_exibir_30 = ['#', 'Data', 'Dia', 'Entradas', 'Saídas', 'Saldo Dia', 'Saldo Acum.', '']
        colunas_disponiveis_30 = [c for c in colunas_exibir_30 if c in df_display_30.columns]
        
        st.dataframe(
            df_display_30[colunas_disponiveis_30],
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        # Totais 30 dias
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ent_30 = df_30dias['entradas'].sum() if 'entradas' in df_30dias.columns else 0
            st.metric("📥 Total Entradas", formatar_moeda(total_ent_30))
        with col2:
            total_sai_30 = df_30dias['saidas'].sum() if 'saidas' in df_30dias.columns else 0
            st.metric("📤 Total Saídas", formatar_moeda(total_sai_30))
        with col3:
            saldo_final_30 = df_30dias['saldo_acumulado'].iloc[-1] if 'saldo_acumulado' in df_30dias.columns else 0
            st.metric("💵 Saldo Final", formatar_moeda(saldo_final_30))
        
        # Alertas
        dias_negativos = df_30dias[df_30dias['saldo_acumulado'] < 0] if 'saldo_acumulado' in df_30dias.columns else pd.DataFrame()
        with col4:
            if not dias_negativos.empty:
                st.metric("⚠️ Dias Negativos", len(dias_negativos))
            else:
                st.metric("✅ Status", "Tudo OK!")
        
        if not dias_negativos.empty:
            st.error(f"⚠️ **ATENÇÃO:** {len(dias_negativos)} dias com saldo negativo nos próximos 30 dias!")
            
            # Mostrar apenas os dias negativos
            df_neg_display = dias_negativos[['num', 'data_fmt', 'dia_semana', 'saldo_acumulado']].copy()
            df_neg_display['saldo_acumulado'] = df_neg_display['saldo_acumulado'].apply(formatar_moeda)
            df_neg_display.columns = ['#', 'Data', 'Dia', 'Saldo Acum.']
            st.dataframe(df_neg_display, use_container_width=True, hide_index=True)
    else:
        st.info("📭 Nenhum dado encontrado para o fluxo diário.")
    
    # Legenda
    st.markdown("---")
    st.markdown("""
    **📋 LEGENDA:**
    - 📅 = Hoje
    - 🔶 = Primeiro dia do mês
    - 🔴 Fundo vermelho = Saldo negativo
    
    **💡 INTEGRAÇÃO DO SISTEMA:**
    - ✅ O **Saldo Atual das Contas** é calculado somando todas as contas bancárias
    - ✅ O **Fluxo Diário** usa o saldo atual como ponto de partida
    - ✅ O **Fluxo Mensal** usa o saldo configurado em 01/01 e projeta o ano todo
    - ✅ Ajustes na **Conciliação Bancária** afetam o saldo atual automaticamente
    - ✅ **Dashboard** e **Relatórios** usam os mesmos dados deste Fluxo de Caixa
    """)
