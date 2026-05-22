"""
📋 ORÇADO vs REALIZADO
Igual à aba ORCAMENTO do Excel - Agrupado por CATEGORIA
USA REGIME DE COMPETÊNCIA (data da compra, não data do pagamento)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database.connection import get_engine

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

def get_orcamento_previsto(ano):
    """Busca orçamento previsto agrupado por CATEGORIA"""
    engine = get_engine()
    query = f"""
        SELECT 
            tipo, 
            categoria,
            SUM(jan) as jan, SUM(fev) as fev, SUM(mar) as mar, SUM(abr) as abr,
            SUM(mai) as mai, SUM(jun) as jun, SUM(jul) as jul, SUM(ago) as ago,
            SUM(`set`) as `set`, SUM(`out`) as `out`, SUM(nov) as nov, SUM(dez) as dez
        FROM orcamento_previsto
        WHERE ano = {ano}
        GROUP BY tipo, categoria
        ORDER BY tipo DESC, categoria
    """
    df = pd.read_sql(query, engine)
    return df

def get_realizado_receitas_por_categoria(ano):
    """Busca receitas realizadas agrupadas por CATEGORIA e MÊS"""
    engine = get_engine()
    query = f"""
        SELECT 
            categoria,
            MONTH(data) as mes,
            SUM(valor) as valor
        FROM receitas
        WHERE YEAR(data) = {ano} AND status = 'Realizado'
        GROUP BY categoria, MONTH(data)
    """
    df = pd.read_sql(query, engine)
    return df

def get_realizado_despesas_por_categoria(ano):
    """
    Busca despesas realizadas agrupadas por CATEGORIA e MÊS.
    
    ⚠️ REGIME DE COMPETÊNCIA:
    - Despesas normais: usa data da despesa
    - Compras de cartão: usa DATA DA COMPRA (não data de vencimento da parcela)
    - O valor total da compra é lançado no MÊS DA COMPRA
    """
    engine = get_engine()
    
    # Query com REGIME DE COMPETÊNCIA
    # Para cartões: usa data_compra e valor_total (não parcelas individuais)
    query = f"""
        SELECT categoria, mes, SUM(valor) as valor
        FROM (
            -- Despesas normais (à vista/débito/PIX)
            SELECT categoria, MONTH(data) as mes, valor 
            FROM despesas 
            WHERE YEAR(data) = {ano} AND status = 'Realizado'
            
            UNION ALL
            
            -- Compras de cartão: REGIME DE COMPETÊNCIA
            -- Usa data_compra e valor_total (não data_vencimento das parcelas)
            SELECT categoria, MONTH(data_compra) as mes, valor_total as valor
            FROM compras_cartao
            WHERE YEAR(data_compra) = {ano}
            
        ) combined
        GROUP BY categoria, mes
    """
    df = pd.read_sql(query, engine)
    return df

def mostrar_orcamento():
    st.title("📋 Orçamento - Previsto vs Realizado")
    st.markdown("*Regime de Competência: gastos são contabilizados na data da compra*")
    
    # Filtro de ano
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        ano = st.selectbox("📅 ANO:", [2025, 2026, 2027], index=1)
    
    # Buscar dados
    df_orcamento = get_orcamento_previsto(ano)
    df_real_rec = get_realizado_receitas_por_categoria(ano)
    df_real_desp = get_realizado_despesas_por_categoria(ano)
    
    if df_orcamento.empty:
        st.warning("⚠️ Nenhum orçamento cadastrado para este ano.")
        return
    
    # Meses
    meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    meses_num = {m: i+1 for i, m in enumerate(meses)}
    
    # Processar dados
    resultados = []
    
    for _, row in df_orcamento.iterrows():
        tipo = row['tipo']
        categoria = row['categoria']
        
        # Selecionar DataFrame correto
        df_real = df_real_rec if tipo == 'Receita' else df_real_desp
        
        # Calcular Prev.Mensal (média do orçamento anual)
        total_orc = sum([float(row[m]) if pd.notna(row[m]) else 0 for m in meses])
        prev_mensal = total_orc / 12
        
        linha = {
            'Tipo': tipo,
            'Categoria': categoria,
            'Prev.Mensal': prev_mensal
        }
        
        total_real = 0
        
        for mes in meses:
            mes_num = meses_num[mes]
            
            # Buscar realizado
            if df_real.empty:
                real = 0
            else:
                mask = (df_real['categoria'] == categoria) & (df_real['mes'] == mes_num)
                real = df_real[mask]['valor'].sum() if len(df_real[mask]) > 0 else 0
            
            linha[mes.capitalize()] = real
            total_real += real
        
        linha['Total Anual'] = total_real
        linha['Variação'] = total_real - total_orc
        
        resultados.append(linha)
    
    df_resultado = pd.DataFrame(resultados)
    
    # =====================================
    # RECEITAS
    # =====================================
    st.subheader("💰 RECEITAS")
    df_receitas = df_resultado[df_resultado['Tipo'] == 'Receita'].copy()
    
    if not df_receitas.empty:
        # Totais
        total_rec_prev = df_receitas['Prev.Mensal'].sum()
        total_rec_real = df_receitas['Total Anual'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Prev.Mensal", formatar_moeda(total_rec_prev))
        with col2:
            st.metric("✅ Total Realizado", formatar_moeda(total_rec_real))
        with col3:
            # Calcular média apenas dos meses com dados
            meses_com_dados = sum(1 for m in meses if df_receitas[m.capitalize()].sum() > 0)
            media = total_rec_real / meses_com_dados if meses_com_dados > 0 else 0
            st.metric("📊 Média Mensal", formatar_moeda(media))
        
        # Tabela
        cols_exibir = ['Categoria', 'Prev.Mensal'] + [m.capitalize() for m in meses] + ['Total Anual']
        df_exibir = df_receitas[cols_exibir].copy()
        
        # Formatação
        cols_formato = ['Prev.Mensal'] + [m.capitalize() for m in meses] + ['Total Anual']
        for col in cols_formato:
            df_exibir[col] = df_exibir[col].apply(formatar_moeda)
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # =====================================
    # DESPESAS
    # =====================================
    st.subheader("📉 DESPESAS")
    df_despesas = df_resultado[df_resultado['Tipo'] == 'Despesa'].copy()
    
    if not df_despesas.empty:
        # Totais
        total_desp_prev = df_despesas['Prev.Mensal'].sum()
        total_desp_real = df_despesas['Total Anual'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Prev.Mensal", formatar_moeda(total_desp_prev))
        with col2:
            st.metric("✅ Total Realizado", formatar_moeda(total_desp_real))
        with col3:
            # Calcular média apenas dos meses com dados
            meses_com_dados = sum(1 for m in meses if df_despesas[m.capitalize()].sum() > 0)
            media = total_desp_real / meses_com_dados if meses_com_dados > 0 else 0
            st.metric("📊 Média Mensal", formatar_moeda(media))
        
        # Tabela
        cols_exibir = ['Categoria', 'Prev.Mensal'] + [m.capitalize() for m in meses] + ['Total Anual']
        df_exibir = df_despesas[cols_exibir].copy()
        
        # Formatação
        cols_formato = ['Prev.Mensal'] + [m.capitalize() for m in meses] + ['Total Anual']
        for col in cols_formato:
            df_exibir[col] = df_exibir[col].apply(formatar_moeda)
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # =====================================
    # RESULTADO
    # =====================================
    st.subheader("📊 RESULTADO OPERACIONAL")
    
    total_rec = df_receitas['Total Anual'].sum() if not df_receitas.empty else 0
    total_desp = df_despesas['Total Anual'].sum() if not df_despesas.empty else 0
    resultado = total_rec - total_desp
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Receitas", formatar_moeda(total_rec))
    with col2:
        st.metric("📉 Despesas", formatar_moeda(total_desp))
    with col3:
        cor = "normal" if resultado >= 0 else "inverse"
        st.metric("💵 Resultado", formatar_moeda(resultado), delta_color=cor)
    with col4:
        pct = (resultado / total_rec * 100) if total_rec > 0 else 0
        st.metric("📊 % Economia", f"{pct:.1f}%")
    
    # Legenda explicativa
    st.markdown("---")
    st.markdown("""
    **📋 REGIME DE COMPETÊNCIA:**
    - Os gastos são contabilizados no **mês em que a compra foi realizada**
    - Compras parceladas no cartão: o **valor total** entra no mês da compra
    - Diferente do Fluxo de Caixa, que usa o mês do pagamento (Regime de Caixa)
    """)