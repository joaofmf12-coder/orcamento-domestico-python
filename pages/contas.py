"""
╔══════════════════════════════════════════════════════════════╗
║                 💰 CONTAS BANCÁRIAS                          ║
║                                                              ║
║  Gestão de contas e transferências entre contas              ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
from datetime import date
from services.contas import (
    listar_contas,
    criar_conta,
    calcular_saldo_conta,
    calcular_saldo_todas_contas,
    criar_transferencia,
    listar_transferencias,
    excluir_transferencia,
    atualizar_conta,
    excluir_conta
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


def mostrar_contas():
    st.title("💰 Contas Bancárias")
    st.markdown("*Gestão de contas e transferências entre contas*")
    
    # Abas
    tab1, tab2, tab3, tab4 = st.tabs([
        "💰 Saldos",
        "➕ Nova Conta",
        "🔄 Transferências",
        "✏️ Gerenciar"
    ])
    
    # ------------------------------------------
    # TAB 1: SALDOS
    # ------------------------------------------
    with tab1:
        st.subheader("💰 Saldos das Contas")
        
        contas = listar_contas()
        
        if contas:
            # KPI - Total
            total_geral = calcular_saldo_todas_contas()
            st.metric("💵 Saldo Total (Todas as Contas)", formatar_moeda(total_geral))
            
            st.markdown("---")
            
            # Tabela de saldos
            dados = []
            for conta in contas:
                saldo = calcular_saldo_conta(conta['id'])
                dados.append({
                    'Conta': conta['nome'],
                    'Banco': conta['banco'] or '-',
                    'Tipo': conta['tipo'],
                    'Saldo Inicial': conta['saldo_inicial'],
                    'Saldo Atual': saldo
                })
            
            df = pd.DataFrame(dados)
            
            # Formatação
            df['Saldo Inicial'] = df['Saldo Inicial'].apply(formatar_moeda)
            df['Saldo Atual'] = df['Saldo Atual'].apply(formatar_moeda)
            
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Nenhuma conta cadastrada.")
    
    # ------------------------------------------
    # TAB 2: NOVA CONTA
    # ------------------------------------------
    with tab2:
        st.subheader("➕ Cadastrar Nova Conta")
        
        with st.form("form_nova_conta", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("📋 Nome da Conta:", placeholder="Ex: Conta Corrente Inter")
                banco = st.text_input("🏦 Banco:", placeholder="Ex: Inter, Nubank, Itaú")
            
            with col2:
                tipo = st.selectbox("📂 Tipo:", ["Corrente", "Poupança", "Investimento", "Carteira"])
                saldo_inicial = st.number_input("💰 Saldo Inicial:", min_value=0.0, step=100.0, format="%.2f")
                data_saldo = st.date_input("📅 Data do Saldo Inicial:", value=date.today())
            
            if st.form_submit_button("💾 Cadastrar Conta", type="primary"):
                if nome:
                    criar_conta(nome, banco, tipo, saldo_inicial, data_saldo)
                    st.success(f"✅ Conta '{nome}' cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Informe o nome da conta!")
    
  # ------------------------------------------
    # TAB 3: TRANSFERÊNCIAS - VERSÃO CORRIGIDA FINAL
    # ------------------------------------------
    with tab3:
        st.subheader("🔄 Transferências entre Contas")
        
        # Buscar contas diretamente
        contas = listar_contas()
        
        # Debug: Mostrar todas as contas encontradas
        st.markdown("##### 📋 Contas Disponíveis")
        if contas:
            for c in contas:
                st.write(f"• ID: {c['id']} | Nome: {c['nome']}")
        else:
            st.warning("⚠️ Nenhuma conta encontrada!")
            
        if len(contas) < 2:
            st.warning("⚠️ Você precisa ter pelo menos 2 contas cadastradas para fazer transferências.")
        else:
            st.markdown("---")
            st.markdown("##### ➕ Nova Transferência")
            
            # Criar lista de nomes para os selectbox
            nomes_contas = [c['nome'] for c in contas]
            
            # Selectbox para ORIGEM
            nome_origem = st.selectbox(
                "📤 Conta ORIGEM (de onde sai o dinheiro):",
                options=nomes_contas,
                key="transf_conta_origem"
            )
            
            # Encontrar o ID da conta de origem
            conta_origem = next((c for c in contas if c['nome'] == nome_origem), None)
            id_origem = conta_origem['id'] if conta_origem else None
            
            # Criar lista de destinos EXCLUINDO a origem
            nomes_destino = [c['nome'] for c in contas if c['nome'] != nome_origem]
            
            # Debug
            st.caption(f"🔍 Origem selecionada: {nome_origem} (ID: {id_origem})")
            st.caption(f"🔍 Destinos disponíveis: {nomes_destino}")
            
            if not nomes_destino:
                st.error("❌ Não há outras contas disponíveis para transferência!")
            else:
                # Selectbox para DESTINO
                nome_destino = st.selectbox(
                    "📥 Conta DESTINO (para onde vai o dinheiro):",
                    options=nomes_destino,
                    key="transf_conta_destino"
                )
                
                # Encontrar o ID da conta de destino
                conta_destino = next((c for c in contas if c['nome'] == nome_destino), None)
                id_destino = conta_destino['id'] if conta_destino else None
                
                # Mostrar resumo
                st.info(f"📤 **De:** {nome_origem}  →  📥 **Para:** {nome_destino}")
                
                # Formulário
                with st.form("form_transferencia_final", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        data_transf = st.date_input("📅 Data:", value=date.today())
                    
                    with col2:
                        valor = st.number_input("💰 Valor:", min_value=0.01, step=100.0, format="%.2f")
                    
                    descricao = st.text_input("📝 Descrição (opcional):", placeholder="Ex: Transferência para reserva")
                    
                    submitted = st.form_submit_button("💾 Registrar Transferência", type="primary")
                    
                    if submitted:
                        if valor > 0 and id_origem and id_destino and id_origem != id_destino:
                            try:
                                criar_transferencia(
                                    data_transf,
                                    id_origem,
                                    id_destino,
                                    valor,
                                    descricao
                                )
                                st.success(f"✅ Transferência registrada: {formatar_moeda(valor)} de **{nome_origem}** para **{nome_destino}**")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {e}")
                        else:
                            st.error("❌ Verifique os dados! Valor deve ser maior que zero e contas devem ser diferentes.")
            
            # Informativo
            st.markdown("---")
            st.info("""
            💡 **Como funciona:**
            - Transferência **não é receita nem despesa** - é movimentação interna
            - O valor **sai** da conta de origem e **entra** na conta de destino
            - O **saldo total** das suas contas permanece o mesmo
            """)
            
            st.markdown("---")
            
            # Histórico de Transferências
            st.markdown("##### 📋 Histórico de Transferências")
            
            col1, col2 = st.columns(2)
            with col1:
                ano = st.selectbox("📅 Ano:", [2025, 2026, 2027], index=1, key="hist_transf_ano")
            with col2:
                meses = ["Todos", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
                mes_nome = st.selectbox("📆 Mês:", meses, key="hist_transf_mes")
                mes = meses.index(mes_nome) if mes_nome != "Todos" else 0
            
            transferencias = listar_transferencias(ano, mes if mes > 0 else None)
            
            if transferencias:
                # KPIs
                total_movimentado = sum(t['valor'] for t in transferencias)
                st.metric("🔄 Total Movimentado", formatar_moeda(total_movimentado))
                
                # Tabela
                df_transf = pd.DataFrame(transferencias)
                df_transf['data'] = pd.to_datetime(df_transf['data']).dt.strftime('%d/%m/%Y')
                df_transf['valor'] = df_transf['valor'].apply(formatar_moeda)
                
                df_exibir = df_transf[['data', 'conta_origem', 'conta_destino', 'valor', 'descricao']].copy()
                df_exibir.columns = ['📅 Data', '📤 Origem', '📥 Destino', '💰 Valor', '📝 Descrição']
                
                st.dataframe(df_exibir, use_container_width=True, hide_index=True)
                
                # Excluir
                st.markdown("---")
                st.markdown("##### 🗑️ Excluir Transferência")
                
                opcoes_excluir = []
                for t in transferencias:
                    data_fmt = pd.to_datetime(t['data']).strftime('%d/%m/%Y')
                    opcao = f"[{t['id']}] {data_fmt} | {t['conta_origem']} → {t['conta_destino']} | {formatar_moeda(t['valor'])}"
                    opcoes_excluir.append(opcao)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    selecionado = st.selectbox("Selecione:", opcoes_excluir, key="excluir_transf_sel")
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("🗑️ Excluir", type="secondary"):
                        id_excluir = int(selecionado.split(']')[0].replace('[', ''))
                        excluir_transferencia(id_excluir)
                        st.success("✅ Transferência excluída!")
                        st.rerun()
            else:
                st.info("📭 Nenhuma transferência encontrada no período.")
                
    # ------------------------------------------
    # TAB 4: GERENCIAR
    # ------------------------------------------
    with tab4:
        st.subheader("✏️ Gerenciar Contas")
        
        contas = listar_contas()
        
        if contas:
            # Selecionar conta
            contas_dict = {c['nome']: c['id'] for c in contas}
            conta_selecionada = st.selectbox("Selecione a conta:", list(contas_dict.keys()))
            conta_id = contas_dict[conta_selecionada]
            
            # Buscar dados da conta
            conta_dados = next((c for c in contas if c['id'] == conta_id), None)
            
            if conta_dados:
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    novo_nome = st.text_input("📋 Nome:", value=conta_dados['nome'])
                    novo_banco = st.text_input("🏦 Banco:", value=conta_dados['banco'] or "")
                
                with col2:
                    tipos = ["Corrente", "Poupança", "Investimento", "Carteira"]
                    idx_tipo = tipos.index(conta_dados['tipo']) if conta_dados['tipo'] in tipos else 0
                    novo_tipo = st.selectbox("📂 Tipo:", tipos, index=idx_tipo)
                    novo_saldo = st.number_input("💰 Saldo Inicial:", value=float(conta_dados['saldo_inicial'] or 0))
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Salvar Alterações", type="primary"):
                        atualizar_conta(conta_id, nome=novo_nome, banco=novo_banco, tipo=novo_tipo, saldo_inicial=novo_saldo)
                        st.success("✅ Conta atualizada!")
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Desativar Conta", type="secondary"):
                        excluir_conta(conta_id)
                        st.success("✅ Conta desativada!")
                        st.rerun()
        else:
            st.info("📭 Nenhuma conta cadastrada.")
