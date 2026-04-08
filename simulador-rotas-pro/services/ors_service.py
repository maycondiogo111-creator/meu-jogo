"""
ors_service.py — Integracao com a API OpenRouteService

Responsabilidade UNICA: comunicar com a API externa de mapas.
Se trocar de provedor (Google Maps, HERE, etc.), so muda este arquivo.

Controle de rate limit simples incluido para evitar surpresas de custo.
"""

import time
import requests
from config import ORS_ENDPOINT_ROTA, ORS_API_KEY, ORS_MAX_REQUESTS_POR_HORA


# -- Rate Limit Simples (em memoria) ------------------------------------------
# Para producao real, use Redis. Para uso atual, esta solucao e suficiente.
_historico_requisicoes: list[float] = []


def _verificar_rate_limit() -> bool:
    """
    Retorna True se ainda esta dentro do limite de requisicoes por hora.
    Remove entradas com mais de 1 hora automaticamente.
    """
    global _historico_requisicoes
    agora = time.time()
    uma_hora_atras = agora - 3600

    # Limpa entradas antigas
    _historico_requisicoes = [t for t in _historico_requisicoes if t > uma_hora_atras]

    if len(_historico_requisicoes) >= ORS_MAX_REQUESTS_POR_HORA:
        return False

    _historico_requisicoes.append(agora)
    return True


def buscar_rota_ors(coordenadas: list[list[float]]) -> dict:
    """
    Envia coordenadas para a OpenRouteService e retorna a rota calculada.

    Args:
        coordenadas: lista de [longitude, latitude] — ex: [[-46.63, -23.55], ...]

    Returns:
        dict com 'geometry', 'summary' e 'steps', ou lanca excecao.

    Raises:
        RuntimeError: se a API retornar erro ou rate limit atingido.
    """
    if not ORS_API_KEY or ORS_API_KEY == "COLE_SUA_CHAVE_AQUI":
        raise RuntimeError(
            "API Key nao configurada. "
            "Insira sua ORS_API_KEY no arquivo .env"
        )

    if not _verificar_rate_limit():
        raise RuntimeError(
            f"Limite de {ORS_MAX_REQUESTS_POR_HORA} requisicoes/hora atingido. "
            "Aguarde antes de calcular novas rotas."
        )

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }
    body = {"coordinates": coordenadas}

    try:
        response = requests.post(ORS_ENDPOINT_ROTA, json=body, headers=headers, timeout=15)
    except requests.Timeout:
        raise RuntimeError("Timeout na API de rotas. Tente novamente.")
    except requests.ConnectionError:
        raise RuntimeError("Sem conexao com a API de rotas. Verifique sua internet.")

    if response.status_code == 401:
        raise RuntimeError("API Key invalida ou expirada. Verifique o arquivo .env")

    if response.status_code == 403:
        raise RuntimeError("Limite da API atingido. Verifique seu plano na OpenRouteService.")

    if response.status_code != 200:
        raise RuntimeError(f"Erro na API ({response.status_code}): {response.text[:200]}")

    dados = response.json()

    if "features" not in dados or not dados["features"]:
        raise RuntimeError("Resposta inesperada da API de rotas.")

    return dados["features"][0]
