"""
Servico de Investimentos
"""

from database.connection import get_db
from database.models import Investimento
from datetime import date
from sqlalchemy import extract


def criar_investimento(data, ativo, tipo_ativo, movimento, valor, observacao=None):
    """Cria um novo lancamento de investimento."""
    with get_db() as db:
        inv = Investimento(
            data=data,
            ativo=ativo,
            tipo_ativo=tipo_ativo,
            movimento=movimento,
            valor=valor,
            observacao=observacao
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return inv.id


def listar_investimentos(ano=None, mes=None, tipo_ativo=None, movimento=None):
    """Lista investimentos com filtros opcionais."""
    with get_db() as db:
        query = db.query(Investimento)
        
        if ano:
            query = query.filter(extract('year', Investimento.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Investimento.data) == mes)
        
        if tipo_ativo:
            query = query.filter(Investimento.tipo_ativo == tipo_ativo)
        
        if movimento:
            query = query.filter(Investimento.movimento == movimento)
        
        investimentos = query.order_by(Investimento.data.desc()).all()
        
        resultado = []
        for i in investimentos:
            resultado.append({
                'id': i.id,
                'data': i.data,
                'ativo': i.ativo,
                'tipo_ativo': i.tipo_ativo,
                'movimento': i.movimento,
                'valor': i.valor,
                'observacao': i.observacao
            })
        return resultado


def buscar_investimento(investimento_id):
    """Busca um investimento pelo ID."""
    with get_db() as db:
        inv = db.query(Investimento).filter(Investimento.id == investimento_id).first()
        if inv:
            return {
                'id': inv.id,
                'data': inv.data,
                'ativo': inv.ativo,
                'tipo_ativo': inv.tipo_ativo,
                'movimento': inv.movimento,
                'valor': inv.valor,
                'observacao': inv.observacao
            }
        return None


def excluir_investimento(investimento_id):
    """Exclui um investimento."""
    with get_db() as db:
        inv = db.query(Investimento).filter(Investimento.id == investimento_id).first()
        if inv:
            db.delete(inv)
            db.commit()
            return True
        return False


def total_investimentos(ano=None, mes=None, movimento=None):
    """Retorna o total de investimentos para um periodo."""
    with get_db() as db:
        query = db.query(Investimento)
        
        if ano:
            query = query.filter(extract('year', Investimento.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Investimento.data) == mes)
        
        if movimento:
            query = query.filter(Investimento.movimento == movimento)
        
        investimentos = query.all()
        return sum(i.valor for i in investimentos)


def investimentos_por_tipo(ano=None, mes=None):
    """Retorna investimentos agrupados por tipo de ativo."""
    with get_db() as db:
        query = db.query(Investimento)
        
        if ano:
            query = query.filter(extract('year', Investimento.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Investimento.data) == mes)
        
        investimentos = query.all()
        
        resultado = {}
        for i in investimentos:
            if i.tipo_ativo not in resultado:
                resultado[i.tipo_ativo] = {'aportes': 0, 'resgates': 0}
            
            if i.movimento == 'Aporte':
                resultado[i.tipo_ativo]['aportes'] += i.valor
            else:
                resultado[i.tipo_ativo]['resgates'] += i.valor
        
        return resultado


def saldo_investimentos(ano=None, mes=None):
    """Calcula o saldo liquido de investimentos (aportes - resgates)."""
    with get_db() as db:
        query = db.query(Investimento)
        
        if ano:
            query = query.filter(extract('year', Investimento.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Investimento.data) == mes)
        
        investimentos = query.all()
        
        aportes = sum(i.valor for i in investimentos if i.movimento == 'Aporte')
        resgates = sum(i.valor for i in investimentos if i.movimento == 'Resgate')
        
        return aportes - resgates