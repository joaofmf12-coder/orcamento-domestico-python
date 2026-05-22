"""
╔══════════════════════════════════════════════════════════════╗
║                    MODELOS DO BANCO DE DADOS                 ║
║                                                              ║
║  Define a estrutura das tabelas usando SQLAlchemy ORM.       ║
║  Cada classe representa uma tabela no banco de dados.        ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, 
    Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database.connection import Base


# ============================================
# TABELAS DE CADASTRO (Configurações)
# ============================================

class Conta(Base):
    """Contas bancárias do usuário."""
    __tablename__ = "contas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    banco: Mapped[str] = mapped_column(String(50), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), default="Corrente")
    saldo_inicial: Mapped[float] = mapped_column(Float, default=0.0)
    data_saldo_inicial: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relacionamentos
    receitas: Mapped[List["Receita"]] = relationship(back_populates="conta")
    despesas: Mapped[List["Despesa"]] = relationship(back_populates="conta")


class Categoria(Base):
    """Categorias e subcategorias de receitas/despesas."""
    __tablename__ = "categorias"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategoria: Mapped[str] = mapped_column(String(50), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Cartao(Base):
    """Cartões de crédito."""
    __tablename__ = "cartoes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    banco: Mapped[str] = mapped_column(String(50), nullable=True)
    dia_corte: Mapped[int] = mapped_column(Integer, nullable=False)
    dia_vencimento: Mapped[int] = mapped_column(Integer, nullable=False)
    limite: Mapped[float] = mapped_column(Float, default=0.0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relacionamentos
    compras: Mapped[List["CompraCartao"]] = relationship(back_populates="cartao")


# ============================================
# TABELAS DE LANÇAMENTOS
# ============================================

class Receita(Base):
    """Lançamentos de receitas."""
    __tablename__ = "receitas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategoria: Mapped[str] = mapped_column(String(50), nullable=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Realizado")
    
    # Campos para conciliação bancária
    conta_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contas.id"), nullable=True)
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False)
    
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relacionamentos
    conta: Mapped[Optional["Conta"]] = relationship(back_populates="receitas")


class Despesa(Base):
    """Lançamentos de despesas."""
    __tablename__ = "despesas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategoria: Mapped[str] = mapped_column(String(50), nullable=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Realizado")
    
    # Campos para conciliação bancária
    conta_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contas.id"), nullable=True)
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False)
    
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relacionamentos
    conta: Mapped[Optional["Conta"]] = relationship(back_populates="despesas")


class CompraCartao(Base):
    """Compras no cartão de crédito."""
    __tablename__ = "compras_cartao"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data_compra: Mapped[date] = mapped_column(Date, nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategoria: Mapped[str] = mapped_column(String(50), nullable=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    valor_total: Mapped[float] = mapped_column(Float, nullable=False)
    num_parcelas: Mapped[int] = mapped_column(Integer, default=1)
    cartao_id: Mapped[int] = mapped_column(ForeignKey("cartoes.id"), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relacionamentos
    cartao: Mapped["Cartao"] = relationship(back_populates="compras")
    parcelas: Mapped[List["Parcela"]] = relationship(back_populates="compra", cascade="all, delete-orphan")


class Parcela(Base):
    """Parcelas de compras no cartão."""
    __tablename__ = "parcelas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras_cartao.id"), nullable=False)
    num_parcela: Mapped[int] = mapped_column(Integer, nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    fatura_mes_ano: Mapped[str] = mapped_column(String(10), nullable=False)
    pago: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relacionamentos
    compra: Mapped["CompraCartao"] = relationship(back_populates="parcelas")


class Investimento(Base):
    """Lançamentos de investimentos."""
    __tablename__ = "investimentos"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    ativo: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_ativo: Mapped[str] = mapped_column(String(50), nullable=False)
    movimento: Mapped[str] = mapped_column(String(20), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    observacao: Mapped[str] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Transferencia(Base):
    """Transferências entre contas."""
    __tablename__ = "transferencias"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    conta_origem_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), nullable=False)
    conta_destino_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# ============================================
# TABELAS PARA CONCILIAÇÃO BANCÁRIA
# ============================================

class Extrato(Base):
    """Extratos importados dos bancos."""
    __tablename__ = "extratos"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conta_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), nullable=False)
    data_importacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    arquivo_nome: Mapped[str] = mapped_column(String(255), nullable=True)
    periodo_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    periodo_fim: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Relacionamentos
    linhas: Mapped[List["LinhaExtrato"]] = relationship(back_populates="extrato", cascade="all, delete-orphan")


class LinhaExtrato(Base):
    """Linhas individuais do extrato bancário."""
    __tablename__ = "linhas_extrato"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    extrato_id: Mapped[int] = mapped_column(ForeignKey("extratos.id"), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Campos de conciliação
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False)
    receita_id: Mapped[Optional[int]] = mapped_column(ForeignKey("receitas.id"), nullable=True)
    despesa_id: Mapped[Optional[int]] = mapped_column(ForeignKey("despesas.id"), nullable=True)
    transferencia_id: Mapped[Optional[int]] = mapped_column(ForeignKey("transferencias.id"), nullable=True)
    
    # Relacionamentos
    extrato: Mapped["Extrato"] = relationship(back_populates="linhas")


# ============================================
# FUNÇÃO AUXILIAR PARA CRIAR TABELAS
# ============================================

def criar_tabelas():
    """Cria todas as tabelas no banco de dados."""
    from database.connection import engine
    Base.metadata.create_all(bind=engine)