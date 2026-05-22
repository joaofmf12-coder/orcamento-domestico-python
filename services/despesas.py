"""
Servico de Despesas
"""

from database.connection import get_db
from database.models import Despesa
from datetime import date
from sqlalchemy import extract


def criar_despesa(data, categoria, valor, subcategoria=None, descricao=None, status="Realizado", conta_id=None):
    """Cria uma nova despesa."""
    with get_db() as db:
        despesa = Despesa(
            data=data,
            categoria=categoria,
            subcategoria=subcategoria,
            valor=valor,
            descricao=descricao,
            status=status,
            conta_id=conta_id
        )
        db.add(despesa)
        db.commit()
        db.refresh(despesa)
        return despesa.id


def listar_despesas(ano=None, mes=None, categoria=None, status=None, conta_id=None):
    """Lista despesas com filtros opcionais."""
    with get_db() as db:
        query = db.query(Despesa)
        
        if ano:
            query = query.filter(extract('year', Despesa.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Despesa.data) == mes)
        
        if categoria:
            query = query.filter(Despesa.categoria == categoria)
        
        if status:
            query = query.filter(Despesa.status == status)
        
        if conta_id:
            query = query.filter(Despesa.conta_id == conta_id)
        
        despesas = query.order_by(Despesa.data.desc()).all()
        
        resultado = []
        for d in despesas:
            resultado.append({
                'id': d.id,
                'data': d.data,
                'categoria': d.categoria,
                'subcategoria': d.subcategoria,
                'valor': d.valor,
                'descricao': d.descricao,
                'status': d.status,
                'conta_id': d.conta_id
            })
        return resultado


def buscar_despesa(despesa_id):
    """Busca uma despesa pelo ID."""
    with get_db() as db:
        despesa = db.query(Despesa).filter(Despesa.id == despesa_id).first()
        if despesa:
            return {
                'id': despesa.id,
                'data': despesa.data,
                'categoria': despesa.categoria,
                'subcategoria': despesa.subcategoria,
                'valor': despesa.valor,
                'descricao': despesa.descricao,
                'status': despesa.status,
                'conta_id': despesa.conta_id
            }
        return None


def atualizar_despesa(despesa_id, **kwargs):
    """Atualiza uma despesa existente."""
    with get_db() as db:
        despesa = db.query(Despesa).filter(Despesa.id == despesa_id).first()
        if despesa:
            for key, value in kwargs.items():
                if hasattr(despesa, key):
                    setattr(despesa, key, value)
            db.commit()
            return True
        return False


def excluir_despesa(despesa_id):
    """Exclui uma despesa."""
    with get_db() as db:
        despesa = db.query(Despesa).filter(Despesa.id == despesa_id).first()
        if despesa:
            db.delete(despesa)
            db.commit()
            return True
        return False


def total_despesas(ano=None, mes=None):
    """Retorna o total de despesas para um periodo."""
    with get_db() as db:
        query = db.query(Despesa)
        
        if ano:
            query = query.filter(extract('year', Despesa.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Despesa.data) == mes)
        
        despesas = query.all()
        return sum(d.valor for d in despesas)


def despesas_por_categoria(ano=None, mes=None):
    """Retorna despesas agrupadas por categoria."""
    with get_db() as db:
        query = db.query(Despesa)
        
        if ano:
            query = query.filter(extract('year', Despesa.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Despesa.data) == mes)
        
        despesas = query.all()
        
        resultado = {}
        for d in despesas:
            if d.categoria not in resultado:
                resultado[d.categoria] = 0
            resultado[d.categoria] += d.valor
        
        return resultado