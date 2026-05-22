"""
Servico de Contas Bancarias
"""

from database.connection import get_db
from database.models import Conta, Receita, Despesa
from datetime import date
from sqlalchemy import extract


def criar_conta(nome, banco=None, tipo="Corrente", saldo_inicial=0.0, data_saldo_inicial=None):
    """Cria uma nova conta bancaria."""
    with get_db() as db:
        conta = Conta(
            nome=nome,
            banco=banco,
            tipo=tipo,
            saldo_inicial=saldo_inicial,
            data_saldo_inicial=data_saldo_inicial or date.today()
        )
        db.add(conta)
        db.commit()
        db.refresh(conta)
        return conta.id


def listar_contas():
    """Lista todas as contas ativas."""
    with get_db() as db:
        contas = db.query(Conta).filter(Conta.ativo == True).all()
        resultado = []
        for c in contas:
            resultado.append({
                'id': c.id,
                'nome': c.nome,
                'banco': c.banco,
                'tipo': c.tipo,
                'saldo_inicial': c.saldo_inicial,
                'data_saldo_inicial': c.data_saldo_inicial
            })
        return resultado


def buscar_conta(conta_id):
    """Busca uma conta pelo ID."""
    with get_db() as db:
        conta = db.query(Conta).filter(Conta.id == conta_id).first()
        if conta:
            return {
                'id': conta.id,
                'nome': conta.nome,
                'banco': conta.banco,
                'tipo': conta.tipo,
                'saldo_inicial': conta.saldo_inicial,
                'data_saldo_inicial': conta.data_saldo_inicial
            }
        return None


def atualizar_conta(conta_id, **kwargs):
    """Atualiza uma conta existente."""
    with get_db() as db:
        conta = db.query(Conta).filter(Conta.id == conta_id).first()
        if conta:
            for key, value in kwargs.items():
                if hasattr(conta, key):
                    setattr(conta, key, value)
            db.commit()
            return True
        return False


def excluir_conta(conta_id):
    """Desativa uma conta (soft delete)."""
    with get_db() as db:
        conta = db.query(Conta).filter(Conta.id == conta_id).first()
        if conta:
            conta.ativo = False
            db.commit()
            return True
        return False


def calcular_saldo_conta(conta_id):
    """Calcula o saldo atual de uma conta."""
    with get_db() as db:
        # Forçar refresh dos dados
        db.expire_all()
        
        conta = db.query(Conta).filter(Conta.id == conta_id).first()
        if not conta:
            return 0.0
        
        saldo_inicial = float(conta.saldo_inicial) if conta.saldo_inicial else 0.0
        data_referencia = conta.data_saldo_inicial
        
        # Soma das receitas desta conta (a partir da data de referência)
        if data_referencia:
            receitas = db.query(Receita).filter(
                Receita.conta_id == conta_id,
                Receita.data >= data_referencia,
                Receita.status == 'Realizado'
            ).all()
        else:
            receitas = db.query(Receita).filter(
                Receita.conta_id == conta_id,
                Receita.status == 'Realizado'
            ).all()
        total_receitas = sum(float(r.valor) for r in receitas)
        
        # Soma das despesas desta conta (a partir da data de referência)
        if data_referencia:
            despesas = db.query(Despesa).filter(
                Despesa.conta_id == conta_id,
                Despesa.data >= data_referencia,
                Despesa.status == 'Realizado'
            ).all()
        else:
            despesas = db.query(Despesa).filter(
                Despesa.conta_id == conta_id,
                Despesa.status == 'Realizado'
            ).all()
        total_despesas = sum(float(d.valor) for d in despesas)
        
        return saldo_inicial + total_receitas - total_despesas


def calcular_saldo_todas_contas():
    """Calcula o saldo total de todas as contas ativas."""
    with get_db() as db:
        contas = db.query(Conta).filter(Conta.ativo == True).all()
        total = 0.0
        for conta in contas:
            total += calcular_saldo_conta(conta.id)
        return total