"""
Servico de Receitas
"""

from database.connection import get_db
from database.models import Receita
from datetime import date
from sqlalchemy import extract


def criar_receita(data, categoria, valor, subcategoria=None, descricao=None, status="Realizado", conta_id=None):
    """Cria uma nova receita."""
    with get_db() as db:
        receita = Receita(
            data=data,
            categoria=categoria,
            subcategoria=subcategoria,
            valor=valor,
            descricao=descricao,
            status=status,
            conta_id=conta_id
        )
        db.add(receita)
        db.commit()
        db.refresh(receita)
        return receita.id


def listar_receitas(ano=None, mes=None, categoria=None, status=None, conta_id=None):
    """Lista receitas com filtros opcionais."""
    with get_db() as db:
        query = db.query(Receita)
        
        if ano:
            query = query.filter(extract('year', Receita.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Receita.data) == mes)
        
        if categoria:
            query = query.filter(Receita.categoria == categoria)
        
        if status:
            query = query.filter(Receita.status == status)
        
        if conta_id:
            query = query.filter(Receita.conta_id == conta_id)
        
        receitas = query.order_by(Receita.data.desc()).all()
        
        resultado = []
        for r in receitas:
            resultado.append({
                'id': r.id,
                'data': r.data,
                'categoria': r.categoria,
                'subcategoria': r.subcategoria,
                'valor': r.valor,
                'descricao': r.descricao,
                'status': r.status,
                'conta_id': r.conta_id
            })
        return resultado


def buscar_receita(receita_id):
    """Busca uma receita pelo ID."""
    with get_db() as db:
        receita = db.query(Receita).filter(Receita.id == receita_id).first()
        if receita:
            return {
                'id': receita.id,
                'data': receita.data,
                'categoria': receita.categoria,
                'subcategoria': receita.subcategoria,
                'valor': receita.valor,
                'descricao': receita.descricao,
                'status': receita.status,
                'conta_id': receita.conta_id
            }
        return None


def atualizar_receita(receita_id, **kwargs):
    """Atualiza uma receita existente."""
    with get_db() as db:
        receita = db.query(Receita).filter(Receita.id == receita_id).first()
        if receita:
            for key, value in kwargs.items():
                if hasattr(receita, key):
                    setattr(receita, key, value)
            db.commit()
            return True
        return False


def excluir_receita(receita_id):
    """Exclui uma receita."""
    with get_db() as db:
        receita = db.query(Receita).filter(Receita.id == receita_id).first()
        if receita:
            db.delete(receita)
            db.commit()
            return True
        return False


def total_receitas(ano=None, mes=None):
    """Retorna o total de receitas para um periodo."""
    with get_db() as db:
        query = db.query(Receita)
        
        if ano:
            query = query.filter(extract('year', Receita.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Receita.data) == mes)
        
        receitas = query.all()
        return sum(r.valor for r in receitas)


def receitas_por_categoria(ano=None, mes=None):
    """Retorna receitas agrupadas por categoria."""
    with get_db() as db:
        query = db.query(Receita)
        
        if ano:
            query = query.filter(extract('year', Receita.data) == ano)
        
        if mes:
            query = query.filter(extract('month', Receita.data) == mes)
        
        receitas = query.all()
        
        resultado = {}
        for r in receitas:
            if r.categoria not in resultado:
                resultado[r.categoria] = 0
            resultado[r.categoria] += r.valor
        
        return resultado