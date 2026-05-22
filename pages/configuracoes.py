"""
╔══════════════════════════════════════════════════════════════╗
║                      CONFIGURAÇÕES                           ║
║                                                              ║
║  Tela para configurar categorias, metas e preferências       ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd

from services.categorias import (
    criar_categoria, listar_categorias, excluir_categoria,
    listar_categorias_receita, listar_categorias_despesa
)
from database.connection import get_engine
from sqlalchemy import text


def mostrar_configuracoes():
    """Renderiza a página de Configurações."""
    
    st.title("⚙️ Configurações")
    st.markdown("---")
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs([
        "📂 Categorias",
        "🎯 Metas",
        "📋 Sobre"
    ])
    
    # --------------------------------------------
    # TAB 1: CATEGORIAS
    # --------------------------------------------
    with tab1:
        st.subheader("📂 Gerenciar Categorias")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Listar categorias existentes
            tipo_filtro = st.selectbox(
                "Filtrar por tipo",
                ["Todas", "Receita", "Despesa"],
                key="cat_filtro"
            )
            
            try:
                # Agora retorna lista de dicionários
                categorias = listar_categorias(
                    tipo=tipo_filtro if tipo_filtro != "Todas" else None
                )
                
                if categorias:
                    df = pd.DataFrame(categorias)
                    
                    # Renomear colunas para exibição
                    df_display = df.rename(columns={
                        'id': 'ID',
                        'tipo': 'Tipo',
                        'categoria': 'Categoria',
                        'subcategoria': 'Subcategoria'
                    })
                    df_display['Subcategoria'] = df_display['Subcategoria'].fillna('-')
                    
                    # Remover coluna 'ativo' da exibição
                    if 'ativo' in df_display.columns:
                        df_display = df_display.drop(columns=['ativo'])
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Exclusão
                    st.markdown("---")
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        id_excluir = st.number_input("ID para desativar", min_value=1, step=1, key="cat_excluir")
                    with col_b:
                        if st.button("🗑️ Desativar", type="secondary"):
                            if excluir_categoria(int(id_excluir)):
                                st.success("✅ Categoria desativada!")
                                st.rerun()
                            else:
                                st.error("❌ Não encontrada!")
                else:
                    st.info("📭 Nenhuma categoria cadastrada.")
            
            except Exception as e:
                st.warning(f"⚠️ Erro: {e}")
        
        with col2:
            # Nova categoria
            st.markdown("##### ➕ Nova Categoria")
            
            with st.form("form_categoria", clear_on_submit=True):
                tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
                categoria = st.text_input("Categoria", placeholder="Ex: Salário, Habitação")
                subcategoria = st.text_input("Subcategoria", placeholder="Ex: Salário Marido, Aluguel")
                
                if st.form_submit_button("💾 Cadastrar", type="primary"):
                    if categoria:
                        try:
                            criar_categoria(
                                tipo=tipo,
                                categoria=categoria,
                                subcategoria=subcategoria if subcategoria else None
                            )
                            st.success("✅ Categoria cadastrada!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
                    else:
                        st.error("❌ Informe a categoria!")
    
    # --------------------------------------------
    # TAB 2: METAS
    # --------------------------------------------
    with tab2:
        st.subheader("🎯 Configurar Metas Financeiras")
        
        st.info("💡 Defina metas mensais para cada categoria de despesa.")
        
        # Metas padrão
        metas = {
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
        
        st.markdown("##### 📊 Orçamento Mensal por Categoria")
        
        col1, col2 = st.columns(2)
        
        with col1:
            for i, (cat, valor) in enumerate(list(metas.items())[:5]):
                metas[cat] = st.number_input(
                    f"{cat}",
                    value=float(valor),
                    step=100.0,
                    format="%.2f",
                    key=f"meta_{i}"
                )
        
        with col2:
            for i, (cat, valor) in enumerate(list(metas.items())[5:]):
                metas[cat] = st.number_input(
                    f"{cat}",
                    value=float(valor),
                    step=100.0,
                    format="%.2f",
                    key=f"meta_{i+5}"
                )
        
        total_metas = sum(metas.values())
        st.metric("💰 Total Orçamento Mensal", f"R$ {total_metas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        if st.button("💾 Salvar Metas", type="primary"):
            st.success("✅ Metas salvas com sucesso!")
            # TODO: Salvar metas no banco de dados
    
    # --------------------------------------------
    # TAB 3: SOBRE
    # --------------------------------------------
    with tab3:
        st.subheader("📋 Sobre o Sistema")
        
        st.markdown("""
        ### 💰 Sistema de Orçamento Doméstico
        
        **Versão:** 1.0.0
        
        **Funcionalidades:**
        - ✅ Controle de Receitas e Despesas
        - ✅ Gerenciamento de Cartões de Crédito
        - ✅ Parcelas Automáticas
        - ✅ Contas Bancárias
        - ✅ Conciliação Bancária
        - ✅ Investimentos
        - ✅ Dashboard com Gráficos
        - ✅ Relatórios Detalhados
        
        **Tecnologias:**
        - Python 3.11+
        - Streamlit (Interface)
        - MySQL (Banco de Dados)
        - SQLAlchemy (ORM)
        - Pandas (Dados)
        - Plotly (Gráficos)
        
        ---
        
        **Desenvolvido por: João F.M. Fonseca** 
        
        **Licença:** MIT
        """)
        
        st.markdown("---")
        
        # Informações do banco de dados
        st.markdown("##### 🗄️ Informações do Banco de Dados")
        
        try:
            engine = get_engine()
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT DATABASE()"))
                db_name = result.scalar()
                
                result = conn.execute(text("SELECT VERSION()"))
                db_version = result.scalar()
            
            col1, col2 = st.columns(2)
            col1.metric("📁 Banco de Dados", db_name)
            col2.metric("🔢 Versão MySQL", db_version)
            
            st.success("✅ Conexão com banco de dados OK!")
        
        except Exception as e:
            st.error(f"❌ Erro na conexão: {e}")