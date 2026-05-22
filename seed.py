"""
🌱 SCRIPT DE POPULAÇÃO INICIAL (SEED)
Este script insere dados fictícios no banco de dados para testes e demonstração.
"""

from datetime import date
from database.connection import get_db, engine
from database.models import Base, Receita, Despesa, Investimento, Conta
from services.receitas import criar_receita
from services.despesas import criar_despesa
from services.investimentos import criar_investimento

def popular_banco():
    print("🔄 Certificando que as tabelas existem no banco...")
    # Cria as tabelas caso elas ainda não existam no MySQL do usuário
    Base.metadata.create_all(bind=engine)
    
    with get_db() as db:
        # 1. Criar Contas Bancárias de Teste (se não existirem)
        print("🏦 Criando contas bancárias de teste...")
        conta_principal = db.query(Conta).filter(Conta.id == 1).first()
        if not conta_principal:
            conta_principal = Conta(id=1, saldo_inicial=5000.0, data_saldo_inicial=date(2026, 1, 1), ativo=1)
            db.add(conta_principal)
            db.commit()

        print("💰 Inserindo receitas e despesas fictícias para o Dashboard...")
        
        # --- DADOS DE JANEIRO/2026 ---
        # Receitas
        criar_receita(data=date(2026, 1, 5), categoria="Salário", valor=8500.00, descricao="Salário Mensal", status="Realizado", conta_id=1)
        criar_receita(data=date(2026, 1, 15), categoria="Rendimentos", valor=350.00, descricao="Dividendos", status="Realizado", conta_id=1)
        
        # Despesas
        criar_despesa(data=date(2026, 1, 10), categoria="Moradia", valor=2200.00, descricao="Aluguel/Condomínio", status="Realizado", conta_id=1)
        criar_despesa(data=date(2026, 1, 12), categoria="Alimentação", valor=850.00, descricao="Supermercado", status="Realizado", conta_id=1)
        criar_despesa(data=date(2026, 1, 20), categoria="Transporte", valor=400.00, descricao="Combustível", status="Realizado", conta_id=1)
        criar_despesa(data=date(2026, 1, 25), categoria="Lazer", valor=350.00, descricao="Restaurantes", status="Realizado", conta_id=1)
        
        # Investimentos
        criar_investimento(data=date(2026, 1, 28), ativo="CDB Fictício", tipo_ativo="Renda Fixa", movimento="Aporte", valor=1500.00, observacao="Aporte mensal automático")

        # --- DADOS DE FEVEREIRO/2026 ---
        # Receitas
        criar_receita(data=date(2026, 2, 5), categoria="Salário", valor=8500.00, descricao="Salário Mensal", status="Realizado", conta_id=1)
        
        # Despesas
        criar_despesa(data=date(2026, 2, 10), categoria="Moradia", valor=2200.00, descricao="Aluguel/Condomínio", status="Realizado", conta_id=1)
        criar_despesa(data=date(2026, 2, 11), categoria="Alimentação", valor=920.00, descricao="Supermercado", status="Realizado", conta_id=1)
        criar_despesa(data=date(2026, 2, 18), categoria="Saúde", valor=310.00, descricao="Farmácia", status="Realizado", conta_id=1)
        
        # Investimentos
        criar_investimento(data=date(2026, 2, 26), ativo="Ações Fictícias", tipo_ativo="Renda Variável", movimento="Aporte", valor=1000.00)

        # --- DADOS DE MARÇO/2026 ---
        # Receitas
        criar_receita(data=date(2026, 3, 5), categoria="Salário", valor=8500.00, descricao="Salário Mensal", status="Realizado", conta_id=1)
        criar_receita(data=date(2026, 3, 20), categoria="Outros", valor=1200.00, descricao="Venda de item usado", status="Realizado", conta_id=1)
        
        # Despesas
        criar_despesa(data=date(2026, 3, 10), categoria="Moradia", valor=2200.00, descricao="Aluguel/Condomínio", status="Realizado", conta_id=1)
        criar_despesa(data=date(2026, 3, 14), categoria="Alimentação", valor=780.00, descricao="Supermercado", status="Realizado", conta_id=1)
        criar_despesa(data=date(2026, 3, 22), categoria="Educação", valor=650.00, descricao="Curso Online", status="Realizado", conta_id=1)

    print("✅ Banco de dados populado com sucesso com dados de teste!")

if __name__ == "__main__":
    popular_banco()