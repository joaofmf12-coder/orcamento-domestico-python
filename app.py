"""
╔══════════════════════════════════════════════════════════════╗
║           SISTEMA DE ORÇAMENTO DOMÉSTICO                     ║
║                                                              ║
║  Controle financeiro pessoal com:                            ║
║  - Receitas e Despesas                                       ║
║  - Cartões de Crédito (parcelas automáticas)                 ║
║  - Investimentos                                             ║
║  - Contas Bancárias e Conciliação                            ║
║  - Dashboard e Relatórios                                    ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st

# Configuração da página (DEVE ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="💰 Orçamento Doméstico",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importações do projeto
from database.connection import inicializar_banco
from database.models import criar_tabelas

# Inicializar o banco de dados
inicializar_banco()
criar_tabelas()

# ============================================
# SIDEBAR - MENU DE NAVEGAÇÃO
# ============================================
st.sidebar.title("💰 Orçamento Doméstico")
st.sidebar.markdown("---")

# Menu de navegação
pagina = st.sidebar.radio(
    "📋 Menu Principal",
    [
        "🏠 Dashboard",
        "📋 Orçado vs Realizado",      # ← NOVO
        "💰 Fluxo de Caixa",            # ← NOVO
        "📥 Receitas",
        "📤 Despesas",
        "💳 Cartões de Crédito",
        "🏦 Contas Bancárias",
        "📈 Investimentos",
        "🔮 Previsões",                 # ← NOVO (se não existir)
        "🔄 Conciliação Bancária",
        "📊 Relatórios",
        "⚙️ Configurações"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("📌 Versão 1.0.0")

# ============================================
# CONTEÚDO PRINCIPAL
# ============================================

if pagina == "🏠 Dashboard":
    from pages.dashboard import mostrar_dashboard
    mostrar_dashboard()

elif pagina == "📥 Receitas":
    from pages.lancamentos import mostrar_receitas
    mostrar_receitas()

elif pagina == "📤 Despesas":
    from pages.lancamentos import mostrar_despesas
    mostrar_despesas()

elif pagina == "💳 Cartões de Crédito":
    from pages.cartoes import mostrar_cartoes
    mostrar_cartoes()

elif pagina == "🏦 Contas Bancárias":
    from pages.contas import mostrar_contas
    mostrar_contas()

elif pagina == "📈 Investimentos":
    from pages.investimentos import mostrar_investimentos
    mostrar_investimentos()

elif pagina == "🔄 Conciliação Bancária":
    from pages.conciliacao import mostrar_conciliacao
    mostrar_conciliacao()

elif pagina == "📊 Relatórios":
    from pages.relatorios import mostrar_relatorios
    mostrar_relatorios()

elif pagina == "⚙️ Configurações":
    from pages.configuracoes import mostrar_configuracoes
    mostrar_configuracoes()
elif pagina == "📋 Orçado vs Realizado":
    from pages.orcamento import mostrar_orcamento
    mostrar_orcamento()

elif pagina == "💰 Fluxo de Caixa":
    from pages.fluxo_caixa import mostrar_fluxo_caixa
    mostrar_fluxo_caixa()
elif pagina == "🔮 Previsões":
    from pages.previsoes import mostrar_previsoes
    mostrar_previsoes()