"""
╔══════════════════════════════════════════════════════════════╗
║                    SERVIÇO DE CATEGORIAS                     ║
║                                                              ║
║  Funções para gerenciar categorias e subcategorias           ║
╚══════════════════════════════════════════════════════════════╝
"""

from typing import List, Optional, Dict
from database.connection import get_db, get_engine
from database.models import Categoria
import pandas as pd


def criar_categoria(
    tipo: str,
    categoria: str,
    subcategoria: str = None
) -> Dict:
    """
    Cria uma nova categoria.
    
    Args:
        tipo: "Receita" ou "Despesa"
        categoria: Nome da categoria (ex: "Salário", "Habitação")
        subcategoria: Nome da subcategoria (ex: "Salário Marido", "Aluguel")
    
    Returns:
        Dicionário com dados da categoria criada
    """
    with get_db() as db:
        cat = Categoria(
            tipo=tipo,
            categoria=categoria,
            subcategoria=subcategoria
        )
        db.add(cat)
        db.commit()
        db.refresh(cat)
        
        # Retorna dicionário em vez do objeto ORM
        return {
            'id': cat.id,
            'tipo': cat.tipo,
            'categoria': cat.categoria,
            'subcategoria': cat.subcategoria,
            'ativo': cat.ativo
        }


def listar_categorias(tipo: str = None, apenas_ativas: bool = True) -> List[Dict]:
    """
    Lista categorias, opcionalmente filtradas por tipo.
    
    Args:
        tipo: "Receita", "Despesa" ou None para todas
        apenas_ativas: Se True, retorna apenas ativas
    
    Returns:
        Lista de dicionários com categorias
    """
    engine = get_engine()
    
    # Construir query
    if tipo and apenas_ativas:
        query = f"""
            SELECT id, tipo, categoria, subcategoria, ativo
            FROM categorias
            WHERE tipo = '{tipo}' AND ativo = 1
            ORDER BY tipo, categoria, subcategoria
        """
    elif tipo:
        query = f"""
            SELECT id, tipo, categoria, subcategoria, ativo
            FROM categorias
            WHERE tipo = '{tipo}'
            ORDER BY tipo, categoria, subcategoria
        """
    elif apenas_ativas:
        query = """
            SELECT id, tipo, categoria, subcategoria, ativo
            FROM categorias
            WHERE ativo = 1
            ORDER BY tipo, categoria, subcategoria
        """
    else:
        query = """
            SELECT id, tipo, categoria, subcategoria, ativo
            FROM categorias
            ORDER BY tipo, categoria, subcategoria
        """
    
    df = pd.read_sql(query, engine)
    
    # Converter para lista de dicionários
    return df.to_dict('records')


def listar_categorias_receita() -> List[str]:
    """Retorna lista de categorias de receita (únicas)."""
    engine = get_engine()
    query = """
        SELECT DISTINCT categoria
        FROM categorias
        WHERE tipo = 'Receita' AND ativo = 1
        ORDER BY categoria
    """
    df = pd.read_sql(query, engine)
    return df['categoria'].tolist()


def listar_categorias_despesa() -> List[str]:
    """Retorna lista de categorias de despesa (únicas)."""
    engine = get_engine()
    query = """
        SELECT DISTINCT categoria
        FROM categorias
        WHERE tipo = 'Despesa' AND ativo = 1
        ORDER BY categoria
    """
    df = pd.read_sql(query, engine)
    return df['categoria'].tolist()


def listar_subcategorias(tipo: str, categoria: str) -> List[str]:
    """
    Retorna lista de subcategorias para uma categoria.
    
    Args:
        tipo: "Receita" ou "Despesa"
        categoria: Nome da categoria
    
    Returns:
        Lista de subcategorias
    """
    engine = get_engine()
    query = f"""
        SELECT DISTINCT subcategoria
        FROM categorias
        WHERE tipo = '{tipo}' 
          AND categoria = '{categoria}'
          AND ativo = 1
          AND subcategoria IS NOT NULL
        ORDER BY subcategoria
    """
    df = pd.read_sql(query, engine)
    return df['subcategoria'].tolist()


def excluir_categoria(categoria_id: int) -> bool:
    """Desativa uma categoria (soft delete)."""
    with get_db() as db:
        cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
        if not cat:
            return False
        cat.ativo = False
        db.commit()
        return True


def buscar_categoria_por_id(categoria_id: int) -> Optional[Dict]:
    """Busca uma categoria pelo ID."""
    engine = get_engine()
    query = f"""
        SELECT id, tipo, categoria, subcategoria, ativo
        FROM categorias
        WHERE id = {categoria_id}
    """
    df = pd.read_sql(query, engine)
    
    if df.empty:
        return None
    
    return df.iloc[0].to_dict()
