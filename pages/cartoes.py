import streamlit as st
import pandas as pd
from datetime import date, datetime

from services.cartoes import (
    criar_cartao, listar_cartoes, buscar_cartao, excluir_cartao,
    criar_compra_cartao, listar_compras_cartao, excluir_compra_cartao,
    listar_parcelas, calcular_fatura, total_parcelas_mes
)


def mostrar_cartoes():
    st.title("Cartoes de Credito")
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Meus Cartoes", "Nova Compra", "Compras Lancadas", "Faturas"])
    
    with tab1:
        st.subheader("Meus Cartoes de Credito")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            try:
                cartoes = listar_cartoes()
                if cartoes:
                    df = pd.DataFrame([{
                        'ID': c['id'],
                        'Nome': c['nome'],
                        'Banco': c['banco'] or "-",
                        'Dia Corte': c['dia_corte'],
                        'Dia Vencimento': c['dia_vencimento'],
                        'Limite': f"R$ {c['limite']:,.2f}"
                    } for c in cartoes])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum cartao cadastrado ainda.")
            except Exception as e:
                st.warning(f"Erro ao carregar cartoes: {e}")
        
        with col2:
            st.markdown("##### Cadastrar Novo Cartao")
            with st.form("form_cartao", clear_on_submit=True):
                nome = st.text_input("Nome do Cartao", placeholder="Ex: Credito Banco A")
                banco = st.text_input("Banco", placeholder="Ex: Banco A")
                col_a, col_b = st.columns(2)
                with col_a:
                    dia_corte = st.number_input("Dia Corte", min_value=1, max_value=31, value=7)
                with col_b:
                    dia_vencimento = st.number_input("Dia Venc.", min_value=1, max_value=31, value=15)
                limite = st.number_input("Limite", min_value=0.0, step=1000.0, format="%.2f")
                
                if st.form_submit_button("Cadastrar", type="primary"):
                    if nome:
                        try:
                            criar_cartao(nome=nome, banco=banco if banco else None, dia_corte=dia_corte, dia_vencimento=dia_vencimento, limite=limite)
                            st.success("Cartao cadastrado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                    else:
                        st.error("Informe o nome do cartao!")

    with tab2:
            st.subheader("Lancar Compra no Cartao")
            st.info("As parcelas serao geradas automaticamente!")

            try:
                cartoes = listar_cartoes()

                if not cartoes:
                    st.warning("Cadastre um cartao primeiro na aba Meus Cartoes")

                else:

                    # ==========================================
                    # CATEGORIAS E SUBCATEGORIAS (FORA DO FORM!)
                    # ==========================================

                    SUBCATEGORIAS = {
                        "Alimentacao": ["Supermercado", "Restaurante", "Delivery", "Padaria"],
                        "Vestuario": ["Roupas", "Calcados", "Acessorios"],
                        "Lazer": ["Festas", "Saídas", "Streaming", "Saídas"],
                        "Habitacao": ["Energia", "Agua", "Gás","Manutenção Casa", "IPTU", "Segurança", "Internet/TV/Celular", "Aquisições para Casa","Impostos Empregada", "Faxineira"],
                        "Saude": ["Farmacia", "Consultas", "Plano de Saude"],
                        "Educacao": ["Cursos", "Livros", "Material Escolar"],
                        "Transporte": ["Combustivel", "Uber/Taxi", "Estacionamento", "Manutencao", "Seguro Veicular", "IPVA"],
                        "Presentes": ["Aniversario", "Natal", "Datas Especiais"],
                        "Outros": ["Aquisição de bens", "Juros","Presentses", "Diversos"]
                    }

                    col1, col2 = st.columns(2)

                    with col1:
                        # FORA DO FORM - permite atualização dinâmica
                        categoria = st.selectbox(
                            "Categoria",
                            options=list(SUBCATEGORIAS.keys()),
                            key="cat_nova_compra"
                        )

                        subcategorias_disponiveis = SUBCATEGORIAS.get(categoria, ["Diversos"])

                        subcategoria = st.selectbox(
                            "Subcategoria",
                            options=subcategorias_disponiveis,
                            key="subcat_nova_compra"
                        )

                    # ==========================================
                    # FORMULÁRIO PARA OS DEMAIS CAMPOS
                    # ==========================================

                    with st.form("form_compra", clear_on_submit=True):

                        col1, col2 = st.columns(2)

                        with col1:
                            data_compra = st.date_input(
                                "Data da Compra",
                                value=date.today()
                            )

                            valor_total = st.number_input(
                                "Valor Total",
                                min_value=0.01,
                                step=50.0,
                                format="%.2f"
                            )

                        with col2:
                            cartao_opcoes = {c['id']: c['nome'] for c in cartoes}

                            cartao_id = st.selectbox(
                                "Cartao",
                                options=list(cartao_opcoes.keys()),
                                format_func=lambda x: cartao_opcoes[x]
                            )

                            num_parcelas = st.number_input(
                                "Numero de Parcelas",
                                min_value=1,
                                max_value=48,
                                value=1
                            )

                        descricao = st.text_input(
                            "Descricao",
                            placeholder="Ex: Jantar aniversario"
                        )

                        # Preview das parcelas
                        if valor_total > 0 and num_parcelas > 0:
                            valor_parcela = valor_total / num_parcelas
                            st.markdown(f"**Preview:** {num_parcelas}x de **R$ {valor_parcela:,.2f}**")

                        # Mostrar seleção atual
                        st.info(f"📋 Categoria: **{categoria}** → Subcategoria: **{subcategoria}**")

                        # Botão salvar
                        if st.form_submit_button("Lancar Compra", type="primary"):
                            if valor_total > 0 and descricao:
                                try:
                                    criar_compra_cartao(
                                        data_compra=data_compra,
                                        categoria=categoria,
                                        subcategoria=subcategoria,
                                        descricao=descricao,
                                        valor_total=valor_total,
                                        num_parcelas=num_parcelas,
                                        cartao_id=cartao_id
                                    )
                                    st.success(f"Compra lancada com sucesso! {num_parcelas} parcela(s) gerada(s).")
                                    st.balloons()
                                except Exception as e:
                                    st.error(f"Erro ao salvar compra: {e}")
                            else:
                                st.error("Preencha valor e descricao!")

            except Exception as e:
                st.error(f"Erro ao carregar formulario: {e}")
    
    with tab3:
        st.subheader("Compras Lancadas")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ano_filtro = st.selectbox("Ano", [2024, 2025, 2026], index=2, key="comp_ano")
        with col2:
            mes_opcoes = {0: "Todos"}
            for i in range(1, 13):
                mes_opcoes[i] = datetime(2000, i, 1).strftime("%B")
            mes_filtro = st.selectbox("Mes", options=list(mes_opcoes.keys()), format_func=lambda x: mes_opcoes[x], key="comp_mes")
        with col3:
            try:
                cartoes = listar_cartoes()
                cartao_opcoes = {0: "Todos"}
                for c in cartoes:
                    cartao_opcoes[c['id']] = c['nome']
                cartao_filtro = st.selectbox("Cartao", options=list(cartao_opcoes.keys()), format_func=lambda x: cartao_opcoes[x], key="comp_cartao")
            except:
                cartao_filtro = 0
        
        try:
            compras = listar_compras_cartao(cartao_id=cartao_filtro if cartao_filtro > 0 else None, ano=ano_filtro, mes=mes_filtro if mes_filtro > 0 else None)
            if compras:
                df = pd.DataFrame([{
                    'ID': c['id'],
                    'Data': c['data_compra'].strftime("%d/%m/%Y"),
                    'Descricao': c['descricao'],
                    'Categoria': c['categoria'],
                    'Valor Total': f"R$ {c['valor_total']:,.2f}",
                    'Parcelas': c['num_parcelas']
                } for c in compras])
                
                total = sum(c['valor_total'] for c in compras)
                st.metric("Total", f"R$ {total:,.2f}")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    id_excluir = st.number_input("ID para excluir", min_value=1, step=1, key="comp_excluir")
                with col2:
                    if st.button("Excluir", type="secondary", key="btn_excluir_comp"):
                        if excluir_compra_cartao(int(id_excluir)):
                            st.success("Compra e parcelas excluidas!")
                            st.rerun()
                        else:
                            st.error("Compra nao encontrada!")
            else:
                st.info("Nenhuma compra encontrada.")
        except Exception as e:
            st.warning(f"Erro ao carregar compras: {e}")
    
    with tab4:
        st.subheader("Faturas dos Cartoes")
        col1, col2 = st.columns(2)
        
        with col1:
            ano_fat = st.selectbox("Ano", [2024, 2025, 2026], index=2, key="fat_ano")
        with col2:
            mes_fat = st.selectbox("Mes", options=list(range(1, 13)), format_func=lambda x: datetime(2000, x, 1).strftime("%B"), index=datetime.now().month - 1, key="fat_mes")
        
        st.markdown("---")
        
        try:
            cartoes = listar_cartoes()
            total_geral = 0
            faturas_por_cartao = []
            
            # Calcular fatura de cada cartão
            for cartao in cartoes:
                fatura = calcular_fatura(cartao['id'], ano_fat, mes_fat)
                valor_fatura = fatura['total'] if fatura else 0
                total_geral += valor_fatura
                
                faturas_por_cartao.append({
                    'cartao': cartao,
                    'fatura': fatura,
                    'valor': valor_fatura
                })
            
            # Mostrar resumo geral
            st.subheader("Resumo das Faturas")
            
            col1, col2, col3 = st.columns(3)
            
            # Mostrar valor de cada cartão como métrica
            for i, item in enumerate(faturas_por_cartao):
                col = [col1, col2, col3][i % 3]
                with col:
                    st.metric(
                        label=item['cartao']['nome'],
                        value=f"R$ {item['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    )
            
            st.markdown("---")
            
            # Total geral em destaque
            st.metric(
                label="TOTAL GERAL - Todas as Faturas",
                value=f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                delta=f"{len([f for f in faturas_por_cartao if f['valor'] > 0])} cartao(s) com fatura"
            )
            
            st.markdown("---")
            
            # Detalhes por cartão (expansíveis)
            st.subheader("Detalhes por Cartao")
            
            for item in faturas_por_cartao:
                cartao = item['cartao']
                fatura = item['fatura']
                
                if fatura and fatura['total'] > 0:
                    with st.expander(f"{cartao['nome']} - R$ {fatura['total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), expanded=False):
                        st.markdown(f"**Vencimento:** Dia {cartao['dia_vencimento']} | **Lancamentos:** {fatura['qtd_lancamentos']}")
                        
                        if fatura['parcelas']:
                            df_parc = pd.DataFrame([{
                                'Descricao': p['descricao'],
                                'Parcela': f"{p['num_parcela']}/{p['total_parcelas']}",
                                'Valor': f"R$ {p['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            } for p in fatura['parcelas']])
                            st.dataframe(df_parc, use_container_width=True, hide_index=True)
                else:
                    with st.expander(f"{cartao['nome']} - Sem fatura", expanded=False):
                        st.info("Nenhum lancamento para este mes.")
        
        except Exception as e:
            st.warning(f"Erro ao carregar faturas: {e}")