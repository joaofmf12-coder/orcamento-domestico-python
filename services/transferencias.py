"""
╔══════════════════════════════════════════════════════════════╗
║                    SERVIÇO DE TRANSFERÊNCIAS                 ║
║                                                              ║
║  Funções para gerenciar transferências entre contas          ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date
from typing import List, Optional
from sqlalchemy import extract
from database.connection import get_db
from database.models import Transferencia, Conta


def criar_transferencia(
    data: date,
    conta_origem_id: int,
    conta_destino_id: int,
    valor: float,
    descricao: str = None
) -> Transferencia:
    """
    Cria uma nova transferência entre contas.
    
    Args:
        data: Data da transferência
        conta_origem_id: ID da conta de origem
        conta_destino_id: ID da conta de destino
        valor: Valor transferido
        descricao: Descrição opcional
    
    Returns:
        Transferência criada
    """
    if conta_origem_id == conta_destino_id:
        raise ValueError("Conta de origem e destino devem ser diferentes")
    
    with get_db() as db:
        # Verificar se as contas existem
        conta_origem = db.query(Conta).filter(Conta.id == conta_origem_id).first()
        conta_destino = db.query(Conta).filter(Conta.id == conta_destino_id).first()
        
        if not conta_origem:
            raise ValueError(f"Conta de origem {conta_origem_id} não encontrada")
        if not conta_destino:
            raise ValueError(f"Conta de destino {conta_destino_id} não encontrada")
        
        transf = Transferencia(
            data=data,
            conta_origem_id=conta_origem_id,
            conta_destino_id=conta_destino_id,
            valor=valor,
            descricao=descricao
        )
        db.add(transf)
        db.commit()
        db.refresh(transf)
        return transf


def listar_transferencias(
    ano: int = None,
    mes: int = None,
    conta_id: int = None
) -> List[Transferencia]:
    """Lista transferências com filtros."""
    with get_db() as db:
        query = db.query(Transferencia)
        
        if ano:
            query = query.filter(extract('year', Transferencia.data) == ano)
        if mes:
            query = query.filter(extract('month', Transferencia.data) == mes)
        if conta_id:
            query = query.filter(
                (Transferencia.conta_origem_id == conta_id) |
                (Transferencia.conta_destino_id == conta_id)
            )
        
        return query.order_by(Transferencia.data.desc()).all()


def buscar_transferencia(transferencia_id: int) -> Optional[Transferencia]:
    """Busca uma transferência pelo ID."""
    with get_db() as db:
        return db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()


def excluir_transferencia(transferencia_id: int) -> bool:
    """Exclui uma transferência permanentemente."""
    with get_db() as db:
        transf = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
        if not transf:
            return False
        db.delete(transf)
        db.commit()
        return True