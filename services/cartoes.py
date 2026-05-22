"""
Servico de Cartoes de Credito
"""

from database.connection import get_db
from database.models import Cartao, CompraCartao, Parcela
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract


def criar_cartao(nome, banco=None, dia_corte=7, dia_vencimento=15, limite=0.0):
    """Cria um novo cartao de credito."""
    with get_db() as db:
        cartao = Cartao(
            nome=nome,
            banco=banco,
            dia_corte=dia_corte,
            dia_vencimento=dia_vencimento,
            limite=limite
        )
        db.add(cartao)
        db.commit()
        db.refresh(cartao)
        return cartao.id


def listar_cartoes():
    """Lista todos os cartoes ativos."""
    with get_db() as db:
        cartoes = db.query(Cartao).filter(Cartao.ativo == True).all()
        resultado = []
        for c in cartoes:
            resultado.append({
                'id': c.id,
                'nome': c.nome,
                'banco': c.banco,
                'dia_corte': c.dia_corte,
                'dia_vencimento': c.dia_vencimento,
                'limite': c.limite
            })
        return resultado


def buscar_cartao(cartao_id):
    """Busca um cartao pelo ID."""
    with get_db() as db:
        cartao = db.query(Cartao).filter(Cartao.id == cartao_id).first()
        if cartao:
            return {
                'id': cartao.id,
                'nome': cartao.nome,
                'banco': cartao.banco,
                'dia_corte': cartao.dia_corte,
                'dia_vencimento': cartao.dia_vencimento,
                'limite': cartao.limite
            }
        return None


def excluir_cartao(cartao_id):
    """Desativa um cartao (soft delete)."""
    with get_db() as db:
        cartao = db.query(Cartao).filter(Cartao.id == cartao_id).first()
        if cartao:
            cartao.ativo = False
            db.commit()
            return True
        return False


def criar_compra_cartao(data_compra, categoria, descricao, valor_total, num_parcelas, cartao_id, subcategoria=None):
    """Cria uma compra no cartao e gera as parcelas automaticamente."""
    with get_db() as db:
        cartao = db.query(Cartao).filter(Cartao.id == cartao_id).first()
        if not cartao:
            raise ValueError("Cartao nao encontrado")
        
        compra = CompraCartao(
            data_compra=data_compra,
            categoria=categoria,
            subcategoria=subcategoria,
            descricao=descricao,
            valor_total=valor_total,
            num_parcelas=num_parcelas,
            cartao_id=cartao_id
        )
        db.add(compra)
        db.commit()
        db.refresh(compra)
        
        valor_parcela = valor_total / num_parcelas
        
        dia_corte = cartao.dia_corte
        dia_vencimento = cartao.dia_vencimento
        
        if data_compra.day <= dia_corte:
            primeiro_vencimento = date(data_compra.year, data_compra.month, dia_vencimento)
        else:
            proximo_mes = data_compra + relativedelta(months=1)
            primeiro_vencimento = date(proximo_mes.year, proximo_mes.month, dia_vencimento)
        
        for i in range(num_parcelas):
            data_vencimento = primeiro_vencimento + relativedelta(months=i)
            fatura_mes_ano = data_vencimento.strftime("%m/%Y")
            
            parcela = Parcela(
                compra_id=compra.id,
                num_parcela=i + 1,
                valor=valor_parcela,
                data_vencimento=data_vencimento,
                fatura_mes_ano=fatura_mes_ano,
                pago=False
            )
            db.add(parcela)
        
        db.commit()
        return compra.id


def listar_compras_cartao(cartao_id=None, ano=None, mes=None):
    """Lista compras no cartao com filtros opcionais."""
    with get_db() as db:
        query = db.query(CompraCartao)
        
        if cartao_id:
            query = query.filter(CompraCartao.cartao_id == cartao_id)
        
        if ano:
            query = query.filter(extract('year', CompraCartao.data_compra) == ano)
        
        if mes:
            query = query.filter(extract('month', CompraCartao.data_compra) == mes)
        
        compras = query.order_by(CompraCartao.data_compra.desc()).all()
        
        resultado = []
        for c in compras:
            resultado.append({
                'id': c.id,
                'data_compra': c.data_compra,
                'categoria': c.categoria,
                'subcategoria': c.subcategoria,
                'descricao': c.descricao,
                'valor_total': c.valor_total,
                'num_parcelas': c.num_parcelas,
                'cartao_id': c.cartao_id
            })
        return resultado


def excluir_compra_cartao(compra_id):
    """Exclui uma compra e suas parcelas."""
    with get_db() as db:
        db.query(Parcela).filter(Parcela.compra_id == compra_id).delete()
        
        compra = db.query(CompraCartao).filter(CompraCartao.id == compra_id).first()
        if compra:
            db.delete(compra)
            db.commit()
            return True
        return False


def listar_parcelas(cartao_id=None, ano=None, mes=None, pago=None):
    """Lista parcelas com filtros opcionais."""
    with get_db() as db:
        query = db.query(Parcela).join(CompraCartao)
        
        if cartao_id:
            query = query.filter(CompraCartao.cartao_id == cartao_id)
        
        if ano:
            query = query.filter(extract('year', Parcela.data_vencimento) == ano)
        
        if mes:
            query = query.filter(extract('month', Parcela.data_vencimento) == mes)
        
        if pago is not None:
            query = query.filter(Parcela.pago == pago)
        
        parcelas = query.order_by(Parcela.data_vencimento).all()
        
        resultado = []
        for p in parcelas:
            resultado.append({
                'id': p.id,
                'compra_id': p.compra_id,
                'num_parcela': p.num_parcela,
                'valor': p.valor,
                'data_vencimento': p.data_vencimento,
                'fatura_mes_ano': p.fatura_mes_ano,
                'pago': p.pago,
                'descricao': p.compra.descricao if p.compra else '',
                'total_parcelas': p.compra.num_parcelas if p.compra else 1
            })
        return resultado


def calcular_fatura(cartao_id, ano, mes):
    """Calcula o valor total da fatura de um cartao para um mes/ano."""
    with get_db() as db:
        # Tentar diferentes formatos de fatura_mes_ano
        formatos = [
            f"{mes:02d}/{ano}",      # 05/2026
            f"{mes}/{ano}",           # 5/2026
            f"{ano}-{mes:02d}",       # 2026-05
            f"{ano}-{mes}"            # 2026-5
        ]
        
        parcelas = []
        for formato in formatos:
            parcelas = db.query(Parcela).join(CompraCartao).filter(
                CompraCartao.cartao_id == cartao_id,
                Parcela.fatura_mes_ano == formato
            ).all()
            if parcelas:
                break
        
        # Se ainda não encontrou, buscar por data de vencimento
        if not parcelas:
            parcelas = db.query(Parcela).join(CompraCartao).filter(
                CompraCartao.cartao_id == cartao_id,
                extract('year', Parcela.data_vencimento) == ano,
                extract('month', Parcela.data_vencimento) == mes
            ).all()
        
        total = sum(p.valor for p in parcelas)
        
        parcelas_lista = []
        for p in parcelas:
            parcelas_lista.append({
                'id': p.id,
                'descricao': p.compra.descricao if p.compra else '',
                'num_parcela': p.num_parcela,
                'total_parcelas': p.compra.num_parcelas if p.compra else 1,
                'valor': p.valor
            })
        
        return {
            'total': total,
            'qtd_lancamentos': len(parcelas),
            'parcelas': parcelas_lista
        }


def total_parcelas_mes(ano, mes):
    """Retorna o total de parcelas de todos os cartoes para um mes/ano."""
    with get_db() as db:
        fatura_mes_ano = f"{mes:02d}/{ano}"
        
        parcelas = db.query(Parcela).filter(
            Parcela.fatura_mes_ano == fatura_mes_ano
        ).all()
        
        return sum(p.valor for p in parcelas)