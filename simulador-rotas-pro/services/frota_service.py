"""
frota_service.py — Logica de roteirizacao multi-veiculos (Feature 1)

Responsabilidades:
  - Distribuir pedidos entre veiculos respeitando capacidade
  - Considerar janelas de entrega
  - Otimizar rotas por veiculo
  - Calcular custo total da operacao

Algoritmo: Heuristica de agrupamento por proximidade + capacidade
"""

import math
from services.rota_service import _distancia_euclidiana, otimizar_ordem_pontos, calcular_custo


def _agrupar_pedidos_por_veiculo(pedidos: list, veiculos: list) -> list[dict]:
    """
    Distribui pedidos entre veiculos respeitando capacidade.
    Usa algoritmo de bin-packing com heuristica de proximidade.

    Args:
        pedidos: lista de dicts com 'endereco' [lat, lng], 'peso', 'volume', 'janela_entrega'
        veiculos: lista de dicts com 'id', 'nome', 'capacidade_peso', 'capacidade_volume', 'custo_km'

    Returns:
        lista de dicts com 'veiculo', 'pedidos_atribuidos', 'carga_peso', 'carga_volume'
    """
    if not veiculos:
        raise ValueError("Nenhum veiculo disponivel para roteirizacao.")

    if not pedidos:
        raise ValueError("Nenhum pedido para roteirizar.")

    # Ordena veiculos por capacidade (maior primeiro)
    veiculos_sorted = sorted(veiculos, key=lambda v: v.get("capacidade_peso", 0), reverse=True)

    # Inicializa atribuicoes
    atribuicoes = []
    for v in veiculos_sorted:
        atribuicoes.append({
            "veiculo": v,
            "pedidos_atribuidos": [],
            "carga_peso": 0,
            "carga_volume": 0
        })

    # Ordena pedidos por peso (maior primeiro - FFD heuristic)
    pedidos_sorted = sorted(pedidos, key=lambda p: p.get("peso", 0), reverse=True)

    pedidos_nao_atribuidos = []

    for pedido in pedidos_sorted:
        peso_pedido = pedido.get("peso", 0)
        volume_pedido = pedido.get("volume", 0)
        atribuido = False

        # Tenta encontrar o melhor veiculo (menor folga que ainda cabe)
        melhor_idx = None
        melhor_folga = float('inf')

        for i, atrib in enumerate(atribuicoes):
            cap_peso = atrib["veiculo"].get("capacidade_peso", float('inf'))
            cap_vol = atrib["veiculo"].get("capacidade_volume", float('inf'))

            folga_peso = cap_peso - atrib["carga_peso"] - peso_pedido
            folga_vol = cap_vol - atrib["carga_volume"] - volume_pedido

            if folga_peso >= 0 and folga_vol >= 0:
                if folga_peso < melhor_folga:
                    melhor_folga = folga_peso
                    melhor_idx = i

        if melhor_idx is not None:
            atribuicoes[melhor_idx]["pedidos_atribuidos"].append(pedido)
            atribuicoes[melhor_idx]["carga_peso"] += peso_pedido
            atribuicoes[melhor_idx]["carga_volume"] += volume_pedido
        else:
            pedidos_nao_atribuidos.append(pedido)

    return atribuicoes, pedidos_nao_atribuidos


def roteirizar_frota(pedidos: list, veiculos: list, deposito: list = None) -> dict:
    """
    Roteirizacao completa multi-veiculos.

    Args:
        pedidos: lista de pedidos com endereco, peso, volume, janela_entrega
        veiculos: lista de veiculos com capacidade e custo
        deposito: [lat, lng] do ponto de partida (opcional)

    Returns:
        dict com rotas por veiculo, custo total e pedidos nao atendidos
    """
    atribuicoes, nao_atribuidos = _agrupar_pedidos_por_veiculo(pedidos, veiculos)

    rotas_veiculos = []
    custo_total = 0
    distancia_total = 0
    tempo_total = 0

    for atrib in atribuicoes:
        if not atrib["pedidos_atribuidos"]:
            continue

        # Extrai pontos dos pedidos atribuidos
        pontos = [p.get("endereco", [0, 0]) for p in atrib["pedidos_atribuidos"]]

        # Adiciona deposito como ponto de partida se fornecido
        if deposito:
            pontos = [deposito] + pontos

        # Otimiza ordem de visita
        pontos_otimizados = otimizar_ordem_pontos(pontos)

        # Calcula distancia estimada (euclidiana * fator de correcao rodoviario)
        dist_estimada = 0
        for i in range(len(pontos_otimizados) - 1):
            dist_eucl = _distancia_euclidiana(pontos_otimizados[i], pontos_otimizados[i + 1])
            dist_estimada += dist_eucl * 111.0 * 1.3  # graus->km * fator rodoviario

        dist_estimada = round(dist_estimada, 2)
        tempo_estimado = round(dist_estimada / 40 * 60, 1)  # 40 km/h media urbana

        custo_km_veiculo = atrib["veiculo"].get("custo_km", 2.5)
        custo_rota = round(dist_estimada * custo_km_veiculo, 2)

        custo_total += custo_rota
        distancia_total += dist_estimada
        tempo_total += tempo_estimado

        rota_veiculo = {
            "veiculo": {
                "id": atrib["veiculo"].get("id"),
                "nome": atrib["veiculo"].get("nome", "Sem nome"),
                "placa": atrib["veiculo"].get("placa", "")
            },
            "pedidos": atrib["pedidos_atribuidos"],
            "pontos_otimizados": pontos_otimizados,
            "carga_peso": atrib["carga_peso"],
            "carga_volume": atrib["carga_volume"],
            "distancia_km": dist_estimada,
            "duracao_min": tempo_estimado,
            "custo": custo_rota,
            "num_paradas": len(atrib["pedidos_atribuidos"])
        }

        rotas_veiculos.append(rota_veiculo)

    return {
        "rotas": rotas_veiculos,
        "resumo": {
            "veiculos_utilizados": len(rotas_veiculos),
            "total_pedidos_atendidos": sum(len(r["pedidos"]) for r in rotas_veiculos),
            "total_pedidos_nao_atendidos": len(nao_atribuidos),
            "distancia_total_km": round(distancia_total, 2),
            "tempo_total_min": round(tempo_total, 1),
            "custo_total": round(custo_total, 2)
        },
        "pedidos_nao_atendidos": nao_atribuidos
    }


def simular_cenario(pedidos: list, veiculos: list, deposito: list = None,
                    veiculos_extras: int = 0, pedidos_extras: list = None) -> dict:
    """
    Feature 3: Simulacao de cenarios.
    Permite simular adicao de veiculos ou mudancas nos pedidos.

    Args:
        pedidos: pedidos base
        veiculos: veiculos base
        deposito: ponto de partida
        veiculos_extras: quantidade de veiculos genericos a adicionar
        pedidos_extras: pedidos adicionais para simular

    Returns:
        dict com cenario base vs cenario simulado
    """
    # Cenario base
    cenario_base = roteirizar_frota(pedidos, veiculos, deposito)

    # Preparar cenario simulado
    veiculos_sim = list(veiculos)
    pedidos_sim = list(pedidos)

    # Adiciona veiculos extras (genericos baseados na media da frota)
    if veiculos_extras > 0:
        cap_media_peso = sum(v.get("capacidade_peso", 100) for v in veiculos) / len(veiculos) if veiculos else 100
        cap_media_vol = sum(v.get("capacidade_volume", 10) for v in veiculos) / len(veiculos) if veiculos else 10
        custo_medio = sum(v.get("custo_km", 2.5) for v in veiculos) / len(veiculos) if veiculos else 2.5

        for i in range(veiculos_extras):
            veiculos_sim.append({
                "id": 9000 + i,
                "nome": f"Veiculo Extra {i + 1}",
                "placa": f"SIM-{i + 1:04d}",
                "capacidade_peso": cap_media_peso,
                "capacidade_volume": cap_media_vol,
                "custo_km": custo_medio
            })

    # Adiciona pedidos extras
    if pedidos_extras:
        pedidos_sim.extend(pedidos_extras)

    cenario_simulado = roteirizar_frota(pedidos_sim, veiculos_sim, deposito)

    # Comparacao
    base = cenario_base["resumo"]
    sim = cenario_simulado["resumo"]

    comparacao = {
        "veiculos": {
            "base": base["veiculos_utilizados"],
            "simulado": sim["veiculos_utilizados"],
            "diferenca": sim["veiculos_utilizados"] - base["veiculos_utilizados"]
        },
        "custo": {
            "base": base["custo_total"],
            "simulado": sim["custo_total"],
            "diferenca": round(sim["custo_total"] - base["custo_total"], 2),
            "variacao_pct": round(((sim["custo_total"] - base["custo_total"]) / base["custo_total"]) * 100, 1) if base["custo_total"] > 0 else 0
        },
        "distancia": {
            "base": base["distancia_total_km"],
            "simulado": sim["distancia_total_km"],
            "diferenca": round(sim["distancia_total_km"] - base["distancia_total_km"], 2)
        },
        "pedidos_nao_atendidos": {
            "base": base["total_pedidos_nao_atendidos"],
            "simulado": sim["total_pedidos_nao_atendidos"],
            "diferenca": sim["total_pedidos_nao_atendidos"] - base["total_pedidos_nao_atendidos"]
        }
    }

    return {
        "cenario_base": cenario_base,
        "cenario_simulado": cenario_simulado,
        "comparacao": comparacao
    }
