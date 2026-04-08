"""
rota_service.py — Logica de negocio para calculo e otimizacao de rotas

Responsabilidades:
  - Validar pontos de entrada
  - Otimizar ordem de paradas (TSP Greedy)
  - Calcular custos (km + tempo)
  - Orquestrar chamada ao ors_service
  - Formatar resposta para o frontend

Nao conhece Flask, nao conhece HTTP — pura logica de negocio.
"""

import math
from config import CUSTO_KM, CUSTO_MIN
from services.ors_service import buscar_rota_ors


# -- Validacao -----------------------------------------------------------------

def validar_pontos(pontos: list) -> list[str]:
    """
    Valida lista de pontos geograficos.

    Args:
        pontos: lista de [lat, lng]

    Returns:
        lista de erros encontrados (vazia = tudo ok)
    """
    erros = []

    if not isinstance(pontos, list):
        erros.append("Pontos deve ser uma lista.")
        return erros

    if len(pontos) < 2:
        erros.append("Adicione pelo menos 2 pontos no mapa.")
        return erros

    if len(pontos) > 25:
        erros.append("Maximo de 25 pontos por rota.")
        return erros

    for i, ponto in enumerate(pontos):
        if not isinstance(ponto, (list, tuple)) or len(ponto) != 2:
            erros.append(f"Ponto {i+1} invalido: deve ser [latitude, longitude].")
            continue

        lat, lng = ponto
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            erros.append(f"Ponto {i+1}: coordenadas devem ser numeros.")
            continue

        if not (-90 <= lat <= 90):
            erros.append(f"Ponto {i+1}: latitude {lat} fora do intervalo [-90, 90].")

        if not (-180 <= lng <= 180):
            erros.append(f"Ponto {i+1}: longitude {lng} fora do intervalo [-180, 180].")

    return erros


# -- Otimizacao TSP Greedy -----------------------------------------------------

def _distancia_euclidiana(a: list, b: list) -> float:
    """Distancia euclidiana entre dois pontos [lat, lng]."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def otimizar_ordem_pontos(pontos: list) -> list:
    """
    Otimiza a ordem de visita dos pontos usando o algoritmo Nearest Neighbor (TSP Greedy).

    O primeiro ponto e sempre mantido como ponto de partida.
    Complexidade: O(n^2) — suficiente para ate ~50 pontos.

    Args:
        pontos: lista de [lat, lng]

    Returns:
        lista de pontos na ordem otimizada
    """
    if len(pontos) <= 2:
        return pontos

    visitados = [pontos[0]]
    nao_visitados = list(pontos[1:])

    while nao_visitados:
        ultimo = visitados[-1]
        proximo = min(nao_visitados, key=lambda p: _distancia_euclidiana(ultimo, p))
        visitados.append(proximo)
        nao_visitados.remove(proximo)

    return visitados


# -- Calculo de Custo ----------------------------------------------------------

def calcular_custo(distancia_km: float, duracao_min: float) -> dict:
    """
    Calcula custo detalhado da rota.

    Returns:
        dict com 'total', 'por_distancia', 'por_tempo'
    """
    custo_distancia = round(distancia_km * CUSTO_KM, 2)
    custo_tempo     = round(duracao_min  * CUSTO_MIN, 2)
    custo_total     = round(custo_distancia + custo_tempo, 2)

    return {
        "total":         custo_total,
        "por_distancia": custo_distancia,
        "por_tempo":     custo_tempo
    }


# -- Orquestrador Principal ---------------------------------------------------

def processar_rota(pontos_entrada: list) -> dict:
    """
    Ponto de entrada principal do servico.
    Orquestra validacao -> otimizacao -> calculo -> retorno.

    Args:
        pontos_entrada: lista de [lat, lng] do frontend

    Returns:
        dict completo com rota, metricas e instrucoes

    Raises:
        ValueError: para erros de validacao (400)
        RuntimeError: para erros de API externa (500)
    """
    # 1. Validar
    erros = validar_pontos(pontos_entrada)
    if erros:
        raise ValueError(erros[0])

    # 2. Otimizar ordem
    pontos_otimizados = otimizar_ordem_pontos(pontos_entrada)

    # 3. Converter para formato ORS: [lng, lat] (ORS usa longitude primeiro)
    coords_ors = [[p[1], p[0]] for p in pontos_otimizados]

    # 4. Chamar API externa
    feature = buscar_rota_ors(coords_ors)

    # 5. Extrair geometria (ORS retorna [lng, lat], Leaflet precisa [lat, lng])
    geometry = feature["geometry"]["coordinates"]
    rota_leaflet = [[p[1], p[0]] for p in geometry]

    # 6. Extrair metricas
    summary      = feature["properties"]["summary"]
    distancia_km = round(summary["distance"] / 1000, 2)
    duracao_min  = round(summary["duration"] / 60, 1)

    # 7. Calcular custo
    custo = calcular_custo(distancia_km, duracao_min)

    # 8. Extrair instrucoes de navegacao
    steps     = feature["properties"]["segments"][0]["steps"]
    instrucoes = [step["instruction"] for step in steps]

    # 9. Retornar resposta completa (compativel com frontend original)
    return {
        "rota":           rota_leaflet,
        "distancia_km":   distancia_km,
        "duracao_min":    duracao_min,
        "custo":          custo["total"],
        "custo_detalhado": {
            "distancia": custo["por_distancia"],
            "tempo":     custo["por_tempo"]
        },
        "instrucoes":       instrucoes,
        "ordem_otimizada":  pontos_otimizados
    }
