"""
╔══════════════════════════════════════════════════════════════╗
║                    CONEXÃO COM BANCO DE DADOS                ║
║                                                              ║
║  Este módulo gerencia a conexão com o banco de dados MySQL.  ║
║  Pode ser facilmente migrado para nuvem alterando a URL.     ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
from dotenv import load_dotenv # ◄── ADICIONE ESTA LINHA
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# Carrega o arquivo .env antes de qualquer configuração)
load_dotenv() 

# Base para os modelos ORM
Base = declarative_base()

# ============================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================

# Configurações MySQL (altere conforme necessário)
# Se o .env existir, ele vai puxar os dados reais daqui de dentro:
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "SUA SENHA")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "orcamento_domestico")

# URL de conexão MySQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

# Engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Mude para True para ver os comandos SQL no console (debug)
    pool_pre_ping=True,  # Verifica conexão antes de usar
    pool_recycle=3600,   # Recicla conexões a cada 1 hora
)

# Fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """
    Retorna uma nova sessão do banco de dados.
    
    Uso:
        session = get_session()
        try:
            # usar session aqui
            session.commit()
        finally:
            session.close()
    """
    return SessionLocal()


def get_engine():
    """
    Retorna o engine do SQLAlchemy.
    Útil para operações com pandas (pd.read_sql).
    """
    return engine


def testar_conexao() -> bool:
    """
    Testa se a conexão com o banco de dados está funcionando.
    Retorna True se conectou, False caso contrário.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexão com MySQL estabelecida com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar com MySQL: {e}")
        return False


def inicializar_banco():
    """
    Inicializa o banco de dados criando todas as tabelas.
    Chamado uma vez quando a aplicação inicia.
    """
    from database.models import Base
    
    # Testa conexão primeiro
    if not testar_conexao():
        raise Exception("Não foi possível conectar ao banco de dados!")
    
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado - Tabelas criadas com sucesso!")


# ============================================
# CONTEXT MANAGER PARA SESSÕES
# ============================================

from contextlib import contextmanager

@contextmanager
def get_db():
    """
    Context manager para gerenciar sessões do banco.
    
    Uso:
        with get_db() as db:
            db.query(Receita).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()