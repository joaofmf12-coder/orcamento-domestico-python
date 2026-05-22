"""
╔══════════════════════════════════════════════════════════════╗
║                    SERVIÇO DE RELATÓRIOS                     ║
║                                                              ║
║  Funções para gerar dados para o Dashboard e relatórios      ║
║  INTEGRADO com Contas Bancárias                              ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date, timedelta
from typing import List, Dict
from sqlalchemy import func, extract
from database.connection import get_db, get_engine
from database.models import Receita, Despesa, Parcela, CompraCartao, Investimento
import pandas as pd

from services.receitas import total_receitas, receitas_por_categoria
from services.despesas import total_despesas, despesas_por_categoria
from services.cartoes import total_parcelas_mes
from services.investimentos import total_investimentos


def get_saldo_atual_contas():
    """
    Calcula o saldo ATUAL de TODAS as contas bancárias ativas.
    INTEGRADO com a Conciliação Bancária.
    """
    engine = get_engine()
    
    try:
        # Buscar todas as contas ativas
        query_contas = "SELECT id, saldo_inicial, data_saldo_inicial FROM contas WHERE ativo = 1"
        df_contas = pd.read_sql(query_contas, engine)
        
        if df_contas.empty:
            return 0.0
        
        total_saldo = 0.0
        
        for _, conta in df_contas.iterrows():
            conta_id = conta['id']
            saldo_inicial = float(conta['saldo_inicial']) if conta['saldo_inicial'] else 0.0
            data_ref = conta['data_saldo_inicial']
            
            # Filtro de data (a partir da data de referência do saldo)
            filtro_data = f"AND data >= '{data_ref}'" if data_ref else ""
            
            # Receitas realizadas desta conta
            query_rec = f"""
                SELECT COALESCE(SUM(valor), 0) as total
                FROM receitas
                WHERE conta_id = {conta_id} AND status = 'Realizado' {filtro_data}
            """
            df_rec = pd.read_sql(query_rec, engine)
            total_rec = float(df_rec.iloc[0]['total']) if not df_rec.empty else 0.0
            
            # Despesas realizadas desta conta
            query_desp = f"""
                SELECT COALESCE(SUM(valor), 0) as total
                FROM despesas
                WHERE conta_id = {conta_id} AND status = 'Realizado' {filtro_data}
            """
            df_desp = pd.read_sql(query_desp, engine)
            total_desp = float(df_desp.iloc[0]['total']) if not df_desp.empty else 0.0
            
            # Saldo da conta
            saldo_conta = saldo_inicial + total_rec - total_desp
            total_saldo += saldo_conta
        
        return total_saldo
    
    except Exception as e:
        print(f"Erro ao calcular saldo das contas: {e}")
        return 0.0


def get_saldo_inicial_para_fluxo(ano):
    """
    Busca o saldo inicial configurado para o fluxo de caixa.
    Primeiro tenta buscar da tabela configuracoes, depois retorna 0.
    """
    engine = get_engine()
    
    # Tentar buscar da tabela configuracoes
    try:
        query = f"SELECT valor FROM configuracoes WHERE chave = 'saldo_inicial_{ano}'"
        df = pd.read_sql(query, engine)
        if not df.empty:
            return float(df['valor'].iloc[0])
    except:
        pass
    
    return 0.0


def dashboard_resumo(ano: int, mes: int = None) -> dict:
    """
    Retorna o resumo para o Dashboard.
    INTEGRADO com saldo das contas bancárias.
    
    Args:
        ano: Ano de referência
        mes: Mês de referência (None = ano inteiro)
    
    Returns:
        {
            'receitas': float,
            'despesas': float,
            'saldo': float,
            'investimentos': float,
            'economia_percentual': float,
            'saldo_contas': float  # NOVO: saldo atual das contas
        }
    """
    receitas = total_receitas(ano, mes)
    despesas = total_despesas(ano, mes)
    parcelas = total_parcelas_mes(ano, mes) if mes else sum(
        total_parcelas_mes(ano, m) for m in range(1, 13)
    )
    
    total_desp = despesas + parcelas
    saldo = receitas - total_desp
    investimentos = total_investimentos(ano, mes, movimento="Aporte")
    
    # NOVO: Saldo atual das contas bancárias
    saldo_contas = get_saldo_atual_contas()
    
    economia_pct = (saldo / receitas * 100) if receitas > 0 else 0
    
    return {
        'receitas': receitas,
        'despesas': total_desp,
        'saldo': saldo,
        'investimentos': investimentos,
        'economia_percentual': round(economia_pct, 1),
        'saldo_contas': saldo_contas  # NOVO
    }


def fluxo_caixa_mensal(ano: int, saldo_inicial: float = None) -> List[dict]:
    """
    Gera o fluxo de caixa mensal.
    INTEGRADO com saldo das contas bancárias.
    
    Se saldo_inicial não for fornecido, busca da tabela configuracoes.
    
    Returns:
        Lista com dados de cada mês
    """
    # Se não passou saldo_inicial, busca da configuração
    if saldo_inicial is None:
        saldo_inicial = get_saldo_inicial_para_fluxo(ano)
    
    resultado = []
    saldo_acumulado = saldo_inicial
    
    for mes in range(1, 13):
        entradas = total_receitas(ano, mes)
        despesas = total_despesas(ano, mes)
        parcelas = total_parcelas_mes(ano, mes)
        saidas = despesas + parcelas
        
        saldo_mes = entradas - saidas
        saldo_acumulado += saldo_mes
        
        mes_nome = date(ano, mes, 1).strftime("%b/%Y").lower()
        
        resultado.append({
            'mes': mes,
            'mes_nome': mes_nome,
            'entradas': entradas,
            'saidas': saidas,
            'saldo_mes': saldo_mes,
            'saldo_acumulado': saldo_acumulado
        })
    
    return resultado


def fluxo_caixa_30_dias(data_inicio: date = None, saldo_inicial: float = None) -> List[dict]:
    """
    Gera o fluxo de caixa para os próximos 30 dias.
    INTEGRADO com saldo das contas bancárias.
    
    Se saldo_inicial não for fornecido, usa o saldo atual das contas.
    """
    if data_inicio is None:
        data_inicio = date.today()
    
    # Se não passou saldo_inicial, usa o saldo atual das contas
    if saldo_inicial is None:
        saldo_inicial = get_saldo_atual_contas()
    
    resultado = []
    saldo_acumulado = saldo_inicial
    
    with get_db() as db:
        for i in range(30):
            data = data_inicio + timedelta(days=i)
            
            # Receitas do dia
            entradas = db.query(func.sum(Receita.valor)).filter(
                Receita.data == data,
                Receita.status == "Realizado"
            ).scalar() or 0.0
            
            # Despesas do dia
            despesas = db.query(func.sum(Despesa.valor)).filter(
                Despesa.data == data,
                Despesa.status == "Realizado"
            ).scalar() or 0.0
            
            # Parcelas do dia
            parcelas = db.query(func.sum(Parcela.valor)).filter(
                Parcela.data_vencimento == data
            ).scalar() or 0.0
            
            saidas = despesas + parcelas
            saldo_dia = entradas - saidas
            saldo_acumulado += saldo_dia
            
            resultado.append({
                'data': data,
                'dia_semana': data.strftime("%a"),
                'entradas': entradas,
                'saidas': saidas,
                'saldo_dia': saldo_dia,
                'saldo_acumulado': saldo_acumulado
            })
    
    return resultado


def orcado_vs_realizado(ano: int, mes: int = None, orcamento: dict = None) -> List[dict]:
    """
    Compara valores orçados vs realizados por categoria.
    
    Args:
        ano: Ano de referência
        mes: Mês de referência
        orcamento: Dicionário com valores orçados {categoria: valor}
    
    Returns:
        Lista de comparativos por categoria
    """
    if orcamento is None:
        orcamento = {}
    
    realizado = despesas_por_categoria(ano, mes)
    
    resultado = []
    todas_categorias = set(orcamento.keys()) | set(realizado.keys())
    
    for cat in sorted(todas_categorias):
        orc = orcamento.get(cat, 0)
        real = realizado.get(cat, 0)
        variacao = real - orc
        pct = ((real / orc - 1) * 100) if orc > 0 else 0
        
        resultado.append({
            'categoria': cat,
            'orcado': orc,
            'realizado': real,
            'variacao': variacao,
            'variacao_percentual': round(pct, 1),
            'status': '✅ OK' if real <= orc else '⚠️ Acima'
        })
    
    return resultado
