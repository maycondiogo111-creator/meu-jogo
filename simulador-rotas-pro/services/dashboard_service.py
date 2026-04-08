"""
dashboard_service.py — Logica do Dashboard Operacional (Feature 4)

Responsabilidades:
  - Calcular KPIs operacionais
  - Custo por km
  - Tempo medio de entrega
  - Produtividade por motorista
  - Estatisticas gerais da operacao
"""

from services.storage_service import listar_rotas, listar_veiculos, listar_motoristas, listar_pedidos


def calcular_kpis() -> dict:
    """
    Calcula todos os KPIs operacionais.

    Returns:
        dict com metricas de desempenho
    """
    rotas = listar_rotas()
    veiculos = listar_veiculos()
    motoristas = listar_motoristas()
    pedidos = listar_pedidos()

    # Metricas de rotas
    total_rotas = len(rotas)
    total_distancia = 0
    total_duracao = 0
    total_custo = 0

    custos_por_rota = []
    distancias = []
    duracoes = []

    for rota in rotas:
        dist = rota.get("distancia_km", 0)
        dur = rota.get("duracao_min", 0)
        custo = rota.get("custo", 0)

        total_distancia += dist
        total_duracao += dur
        total_custo += custo

        distancias.append(dist)
        duracoes.append(dur)
        custos_por_rota.append(custo)

    # KPIs calculados
    custo_por_km = round(total_custo / total_distancia, 2) if total_distancia > 0 else 0
    tempo_medio = round(total_duracao / total_rotas, 1) if total_rotas > 0 else 0
    distancia_media = round(total_distancia / total_rotas, 2) if total_rotas > 0 else 0
    custo_medio = round(total_custo / total_rotas, 2) if total_rotas > 0 else 0

    # Produtividade por motorista
    motoristas_ativos = [m for m in motoristas if m.get("status") == "ativo"]
    rotas_por_motorista = round(total_rotas / len(motoristas_ativos), 1) if motoristas_ativos else 0

    # Contagem de clientes unicos
    clientes_unicos = set()
    for rota in rotas:
        cliente = rota.get("cliente", "")
        if cliente and cliente != "Sem cliente":
            clientes_unicos.add(cliente)

    return {
        "resumo": {
            "total_rotas": total_rotas,
            "total_distancia_km": round(total_distancia, 2),
            "total_duracao_min": round(total_duracao, 1),
            "total_custo": round(total_custo, 2),
            "total_veiculos": len(veiculos),
            "total_motoristas": len(motoristas),
            "motoristas_ativos": len(motoristas_ativos),
            "total_pedidos": len(pedidos),
            "clientes_unicos": len(clientes_unicos)
        },
        "kpis": {
            "custo_por_km": custo_por_km,
            "tempo_medio_min": tempo_medio,
            "distancia_media_km": distancia_media,
            "custo_medio_rota": custo_medio,
            "rotas_por_motorista": rotas_por_motorista
        },
        "distribuicao": {
            "custos": custos_por_rota[-10:] if custos_por_rota else [],
            "distancias": distancias[-10:] if distancias else [],
            "duracoes": duracoes[-10:] if duracoes else []
        }
    }
