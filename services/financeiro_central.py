"""
╔══════════════════════════════════════════════════════════════╗
║              MÓDULO FINANCEIRO CENTRAL                       ║
║                                                              ║
║  ÚNICA FONTE DE VERDADE para todos os cálculos financeiros   ║
║  Todos os módulos DEVEM usar este arquivo para garantir      ║
║  consistência dos dados em todo o sistema.                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import pandas as pd
from datetime import date, datetime, timedelta
from database.connection import get_engine
from typing import Dict, List, Optional


# ============================================================
# CONFIGURAÇÕES CENTRAIS
# ============================================================

def get_saldo_inicial_ano(ano: int) -> float:
    """
    FONTE ÚNICA: Busca o saldo inicial do ano.
    Primeiro tenta tabela 'configuracoes', depois soma saldos das contas.
    """
    engine = get_engine()
    
    # Tentar buscar da tabela configuracoes
    try:
        query = f"SELECT valor FROM configuracoes WHERE chave = 'saldo_inicial_{ano}'"
        df = pd.read_sql(query, engine)
        if not df.empty and df['valor'].iloc[0]:
            return float(df['valor'].iloc[0])
    except:
        pass
    
    # Fallback: calcular a partir das contas bancárias
    return get_saldo_atual_contas()


def get_saldo_atual_contas() -> float:
    """
    FONTE ÚNICA: Calcula o saldo ATUAL de TODAS as contas bancárias ativas.
    """
    engine = get_engine()
    
    try:
        query_contas = "SELECT id, saldo_inicial, data_saldo_inicial FROM contas WHERE ativo = 1"
        df_contas = pd.read_sql(query_contas, engine)
        
        if df_contas.empty:
            return 0.0
        
        total_saldo = 0.0
        
        for _, conta in df_contas.iterrows():
            conta_id = conta['id']
            saldo_inicial = float(conta['saldo_inicial']) if conta['saldo_inicial'] else 0.0
            data_ref = conta['data_saldo_inicial']
            
            filtro_data = f"AND data >= '{data_ref}'" if data_ref else ""
            
            # Receitas realizadas
            query_rec = f"""
                SELECT COALESCE(SUM(valor), 0) as total
                FROM receitas
                WHERE conta_id = {conta_id} AND status = 'Realizado' {filtro_data}
            """
            df_rec = pd.read_sql(query_rec, engine)
            total_rec = float(df_rec.iloc[0]['total']) if not df_rec.empty else 0.0
            
            # Despesas realizadas
            query_desp = f"""
                SELECT COALESCE(SUM(valor), 0) as total
                FROM despesas
                WHERE conta_id = {conta_id} AND status = 'Realizado' {filtro_data}
            """
            df_desp = pd.read_sql(query_desp, engine)
            total_desp = float(df_desp.iloc[0]['total']) if not df_desp.empty else 0.0
            
            saldo_conta = saldo_inicial + total_rec - total_desp
            total_saldo += saldo_conta
        
        return total_saldo
    
    except Exception as e:
        print(f"Erro ao calcular saldo das contas: {e}")
        return 0.0


# ============================================================
# RECEITAS
# ============================================================

def get_total_receitas(ano: int, mes: int = None) -> float:
    """FONTE ÚNICA: Total de receitas realizadas."""
    engine = get_engine()
    
    filtro_mes = f"AND MONTH(data) = {mes}" if mes else ""
    
    query = f"""
        SELECT COALESCE(SUM(valor), 0) as total
        FROM receitas
        WHERE YEAR(data) = {ano} AND status = 'Realizado' {filtro_mes}
    """
    df = pd.read_sql(query, engine)
    return float(df['total'].iloc[0]) if not df.empty else 0.0


def get_receitas_previstas(ano: int, mes: int = None) -> float:
    """FONTE ÚNICA: Total de receitas previstas (ativas)."""
    engine = get_engine()
    
    filtro_mes = f"AND MONTH(data) = {mes}" if mes else ""
    
    query = f"""
        SELECT COALESCE(SUM(valor), 0) as total
        FROM previsoes
        WHERE YEAR(data) = {ano} AND tipo = 'Receita' AND status = 'Ativa' {filtro_mes}
    """
    df = pd.read_sql(query, engine)
    return float(df['total'].iloc[0]) if not df.empty else 0.0


# ============================================================
# DESPESAS
# ============================================================

def get_total_despesas(ano: int, mes: int = None) -> float:
    """FONTE ÚNICA: Total de despesas realizadas."""
    engine = get_engine()
    
    filtro_mes = f"AND MONTH(data) = {mes}" if mes else ""
    
    query = f"""
        SELECT COALESCE(SUM(valor), 0) as total
        FROM despesas
        WHERE YEAR(data) = {ano} AND status = 'Realizado' {filtro_mes}
    """
    df = pd.read_sql(query, engine)
    return float(df['total'].iloc[0]) if not df.empty else 0.0


def get_despesas_previstas(ano: int, mes: int = None) -> float:
    """FONTE ÚNICA: Total de despesas previstas (ativas)."""
    engine = get_engine()
    
    filtro_mes = f"AND MONTH(data) = {mes}" if mes else ""
    
    query = f"""
        SELECT COALESCE(SUM(valor), 0) as total
        FROM previsoes
        WHERE YEAR(data) = {ano} AND tipo = 'Despesa' AND status = 'Ativa' {filtro_mes}
    """
    df = pd.read_sql(query, engine)
    return float(df['total'].iloc[0]) if not df.empty else 0.0


def get_despesas_por_categoria(ano: int, mes: int = None) -> Dict[str, float]:
    """FONTE ÚNICA: Despesas agrupadas por categoria."""
    engine = get_engine()
    
    filtro_mes = f"AND MONTH(data) = {mes}" if mes else ""
    
    query = f"""
        SELECT categoria, COALESCE(SUM(valor), 0) as total
        FROM despesas
        WHERE YEAR(data) = {ano} AND status = 'Realizado' {filtro_mes}
        GROUP BY categoria
        ORDER BY total DESC
    """
    df = pd.read_sql(query, engine)
    
    if df.empty:
        return {}
    
    return dict(zip(df['categoria'], df['total']))


def get_receitas_por_categoria(ano: int, mes: int = None) -> Dict[str, float]:
    """FONTE ÚNICA: Receitas agrupadas por categoria."""
    engine = get_engine()
    
    filtro_mes = f"AND MONTH(data) = {mes}" if mes else ""
    
    query = f"""
        SELECT categoria, COALESCE(SUM(valor), 0) as total
        FROM receitas
        WHERE YEAR(data) = {ano} AND status = 'Realizado' {filtro_mes}
        GROUP BY categoria
        ORDER BY total DESC
    """
    df = pd.read_sql(query, engine)
    
    if df.empty:
        return {}
    
    return dict(zip(df['categoria'], df['total']))


# ============================================================
# PARCELAS DE CARTÃO
# ============================================================

def get_total_parcelas(ano: int, mes: int = None) -> float:
    """FONTE ÚNICA: Total de parcelas de cartão."""
    engine = get_engine()
    
    filtro_mes = f"AND MONTH(data_vencimento) = {mes}" if mes else ""
    
    query = f"""
        SELECT COALESCE(SUM(valor), 0) as total
        FROM parcelas
        WHERE YEAR(data_vencimento) = {ano} {filtro_mes}
    """
    df = pd.read_sql(query, engine)
    return float(df['total'].iloc[0]) if not df.empty else 0.0


# ============================================================
# INVESTIMENTOS
# ============================================================

def get_total_investimentos(ano: int, mes: int = None, movimento: str = None) -> float:
    """FONTE ÚNICA: Total de investimentos (aportes ou resgates)."""
    engine = get_engine()
    
    filtro_mes = f"AND MONTH(data) = {mes}" if mes else ""
    filtro_mov = f"AND movimento = '{movimento}'" if movimento else ""
    
    try:
        query = f"""
            SELECT COALESCE(SUM(valor), 0) as total
            FROM investimentos
            WHERE YEAR(data) = {ano} {filtro_mes} {filtro_mov}
        """
        df = pd.read_sql(query, engine)
        return float(df['total'].iloc[0]) if not df.empty else 0.0
    except:
        return 0.0


# ============================================================
# FLUXO DE CAIXA MENSAL - FONTE ÚNICA
# ============================================================

def get_fluxo_caixa_mensal(ano: int) -> List[Dict]:
    """
    FONTE ÚNICA: Gera o fluxo de caixa mensal completo.
    Este é O ÚNICO método que deve ser usado em TODO o sistema.
    """
    saldo_inicial = get_saldo_inicial_ano(ano)
    resultado = []
    saldo_acumulado = saldo_inicial
    
    meses_nomes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 
                   'jul', 'ago', 'set', 'out', 'nov', 'dez']
    
    for mes in range(1, 13):
        # Entradas
        entradas_reais = get_total_receitas(ano, mes)
        entradas_previstas = get_receitas_previstas(ano, mes)
        entradas_total = entradas_reais + entradas_previstas
        
        # Saídas
        despesas_reais = get_total_despesas(ano, mes)
        parcelas = get_total_parcelas(ano, mes)
        saidas_reais = despesas_reais + parcelas
        saidas_previstas = get_despesas_previstas(ano, mes)
        saidas_total = saidas_reais + saidas_previstas
        
        # Saldos
        saldo_mes = entradas_total - saidas_total
        saldo_acumulado += saldo_mes
        
        status = "🟢 OK" if saldo_acumulado >= 0 else "🔴 Negativo"
        
        resultado.append({
            'mes': mes,
            'mes_nome': f"{meses_nomes[mes-1]}/{ano}",
            'entradas_reais': entradas_reais,
            'entradas_previstas': entradas_previstas,
            'entradas_total': entradas_total,
            'saidas_reais': saidas_reais,
            'saidas_previstas': saidas_previstas,
            'saidas_total': saidas_total,
            'saldo_mes': saldo_mes,
            'saldo_acumulado': saldo_acumulado,
            'status': status
        })
    
    return resultado


# ============================================================
# FLUXO DE CAIXA DIÁRIO - FONTE ÚNICA
# ============================================================

def get_fluxo_caixa_diario(dias: int = 30) -> List[Dict]:
    """
    FONTE ÚNICA: Gera o fluxo de caixa diário.
    Usa o saldo atual das contas como ponto de partida.
    """
    engine = get_engine()
    saldo_inicial = get_saldo_atual_contas()
    
    hoje = date.today()
    resultado = []
    saldo_acumulado = saldo_inicial
    
    dias_semana = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']
    
    for i in range(dias):
        data = hoje + timedelta(days=i)
        data_str = data.strftime('%Y-%m-%d')
        
        # Entradas do dia
        query_rec = f"""
            SELECT COALESCE(SUM(valor), 0) as total FROM receitas 
            WHERE data = '{data_str}' AND status = 'Realizado'
        """
        df = pd.read_sql(query_rec, engine)
        entradas = float(df['total'].iloc[0])
        
        query_prev_rec = f"""
            SELECT COALESCE(SUM(valor), 0) as total FROM previsoes 
            WHERE data = '{data_str}' AND tipo = 'Receita' AND status = 'Ativa'
        """
        df = pd.read_sql(query_prev_rec, engine)
        entradas += float(df['total'].iloc[0])
        
        # Saídas do dia
        query_desp = f"""
            SELECT COALESCE(SUM(valor), 0) as total FROM despesas 
            WHERE data = '{data_str}' AND status = 'Realizado'
        """
        df = pd.read_sql(query_desp, engine)
        saidas = float(df['total'].iloc[0])
        
        query_parc = f"""
            SELECT COALESCE(SUM(valor), 0) as total FROM parcelas 
            WHERE data_vencimento = '{data_str}'
        """
        df = pd.read_sql(query_parc, engine)
        saidas += float(df['total'].iloc[0])
        
        query_prev_desp = f"""
            SELECT COALESCE(SUM(valor), 0) as total FROM previsoes 
            WHERE data = '{data_str}' AND tipo = 'Despesa' AND status = 'Ativa'
        """
        df = pd.read_sql(query_prev_desp, engine)
        saidas += float(df['total'].iloc[0])
        
        saldo_dia = entradas - saidas
        saldo_acumulado += saldo_dia
        
        marcador = ""
        if data == hoje:
            marcador = "📅"
        elif data.day == 1:
            marcador = "🔶"
        
        resultado.append({
            'num': i + 1,
            'data': data,
            'data_fmt': data.strftime('%d/%m'),
            'dia_semana': dias_semana[data.weekday()],
            'entradas': entradas,
            'saidas': saidas,
            'saldo_dia': saldo_dia,
            'saldo_acumulado': saldo_acumulado,
            'marcador': marcador
        })
    
    return resultado


# ============================================================
# DASHBOARD RESUMO - FONTE ÚNICA
# ============================================================

def get_dashboard_resumo(ano: int, mes: int = None) -> Dict:
    """
    FONTE ÚNICA: Resumo para o Dashboard.
    """
    receitas = get_total_receitas(ano, mes)
    despesas = get_total_despesas(ano, mes)
    
    if mes:
        parcelas = get_total_parcelas(ano, mes)
    else:
        parcelas = sum(get_total_parcelas(ano, m) for m in range(1, 13))
    
    total_desp = despesas + parcelas
    saldo = receitas - total_desp
    
    investimentos = get_total_investimentos(ano, mes, movimento="Aporte")
    saldo_contas = get_saldo_atual_contas()
    
    economia_pct = (saldo / receitas * 100) if receitas > 0 else 0
    
    return {
        'receitas': receitas,
        'despesas': total_desp,
        'saldo': saldo,
        'investimentos': investimentos,
        'economia_percentual': round(economia_pct, 1),
        'saldo_contas': saldo_contas
    }


# ============================================================
# ORÇADO VS REALIZADO - FONTE ÚNICA
# ============================================================

def get_orcado_vs_realizado(ano: int, mes: int = None, orcamento: Dict = None) -> List[Dict]:
    """
    FONTE ÚNICA: Comparativo orçado vs realizado.
    """
    if orcamento is None:
        orcamento = {}
    
    realizado = get_despesas_por_categoria(ano, mes)
    
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