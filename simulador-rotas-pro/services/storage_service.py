"""
storage_service.py — Camada de persistencia de dados

Responsabilidade: ler e escrever dados no armazenamento atual (JSON).

IMPORTANTE: esta camada esta preparada para migracao futura para banco de dados.
Para migrar para SQLite/PostgreSQL, basta implementar as mesmas funcoes
usando SQLAlchemy — o resto do sistema nao muda.
"""

import json
from pathlib import Path
from config import CLIENTES_FILE, ROTAS_FILE, VEICULOS_FILE, PEDIDOS_FILE, MOTORISTAS_FILE


# -- Utilitarios internos ------------------------------------------------------

def _ler_json(caminho: Path) -> list:
    """Le arquivo JSON. Retorna lista vazia se nao existir ou estiver corrompido."""
    if not caminho.exists():
        return []
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _escrever_json(caminho: Path, dados) -> bool:
    """Escreve dados em arquivo JSON. Retorna True se bem-sucedido."""
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        return True
    except IOError:
        return False


# -- Clientes ------------------------------------------------------------------

def listar_clientes() -> list[str]:
    """Retorna lista de nomes de clientes cadastrados."""
    return _ler_json(CLIENTES_FILE)


def adicionar_cliente(nome: str) -> bool:
    """
    Adiciona cliente se nao existir.

    Returns:
        True se adicionado, False se ja existia.
    """
    nome = nome.strip()
    clientes = listar_clientes()

    if nome in clientes:
        return False

    clientes.append(nome)
    return _escrever_json(CLIENTES_FILE, clientes)


def cliente_existe(nome: str) -> bool:
    return nome.strip() in listar_clientes()


# -- Rotas ---------------------------------------------------------------------

def listar_rotas() -> list[dict]:
    """Retorna todas as rotas salvas."""
    return _ler_json(ROTAS_FILE)


def salvar_rota(dados_rota: dict) -> dict:
    """
    Salva uma nova rota.

    Args:
        dados_rota: dict com todos os dados da rota

    Returns:
        dict com status e total de rotas salvas
    """
    rotas = listar_rotas()
    rotas.append(dados_rota)
    _escrever_json(ROTAS_FILE, rotas)

    return {
        "status": "ok",
        "total_salvas": len(rotas)
    }


def buscar_rota_por_indice(indice: int) -> dict | None:
    """Retorna rota pelo indice. Retorna None se nao encontrar."""
    rotas = listar_rotas()
    if 0 <= indice < len(rotas):
        return rotas[indice]
    return None


# -- Veiculos (Feature 1: Roteirizacao Multi-Veiculos) -------------------------

def listar_veiculos() -> list[dict]:
    """Retorna todos os veiculos cadastrados."""
    return _ler_json(VEICULOS_FILE)


def adicionar_veiculo(veiculo: dict) -> dict:
    """Adiciona um novo veiculo."""
    veiculos = listar_veiculos()
    veiculo["id"] = len(veiculos) + 1
    veiculos.append(veiculo)
    _escrever_json(VEICULOS_FILE, veiculos)
    return {"status": "ok", "veiculo": veiculo}


def atualizar_veiculo(veiculo_id: int, dados: dict) -> dict | None:
    """Atualiza dados de um veiculo existente."""
    veiculos = listar_veiculos()
    for v in veiculos:
        if v.get("id") == veiculo_id:
            v.update(dados)
            v["id"] = veiculo_id
            _escrever_json(VEICULOS_FILE, veiculos)
            return v
    return None


def remover_veiculo(veiculo_id: int) -> bool:
    """Remove um veiculo pelo ID."""
    veiculos = listar_veiculos()
    veiculos_filtrados = [v for v in veiculos if v.get("id") != veiculo_id]
    if len(veiculos_filtrados) == len(veiculos):
        return False
    _escrever_json(VEICULOS_FILE, veiculos_filtrados)
    return True


# -- Pedidos (Feature 5: Importacao de Pedidos) --------------------------------

def listar_pedidos() -> list[dict]:
    """Retorna todos os pedidos cadastrados."""
    return _ler_json(PEDIDOS_FILE)


def adicionar_pedido(pedido: dict) -> dict:
    """Adiciona um novo pedido."""
    pedidos = listar_pedidos()
    pedido["id"] = len(pedidos) + 1
    pedidos.append(pedido)
    _escrever_json(PEDIDOS_FILE, pedidos)
    return {"status": "ok", "pedido": pedido}


def adicionar_pedidos_em_lote(lista_pedidos: list[dict]) -> dict:
    """Adiciona multiplos pedidos de uma vez (importacao Excel/API)."""
    pedidos = listar_pedidos()
    proximo_id = len(pedidos) + 1
    novos = []
    for p in lista_pedidos:
        p["id"] = proximo_id
        proximo_id += 1
        pedidos.append(p)
        novos.append(p)
    _escrever_json(PEDIDOS_FILE, pedidos)
    return {"status": "ok", "importados": len(novos), "total": len(pedidos)}


def limpar_pedidos() -> dict:
    """Remove todos os pedidos."""
    _escrever_json(PEDIDOS_FILE, [])
    return {"status": "ok"}


# -- Motoristas (Feature 2: Rastreamento) --------------------------------------

def listar_motoristas() -> list[dict]:
    """Retorna todos os motoristas."""
    return _ler_json(MOTORISTAS_FILE)


def adicionar_motorista(motorista: dict) -> dict:
    """Adiciona um novo motorista."""
    motoristas = listar_motoristas()
    motorista["id"] = len(motoristas) + 1
    motorista["status"] = motorista.get("status", "inativo")
    motorista["posicao"] = motorista.get("posicao", None)
    motoristas.append(motorista)
    _escrever_json(MOTORISTAS_FILE, motoristas)
    return {"status": "ok", "motorista": motorista}


def atualizar_posicao_motorista(motorista_id: int, lat: float, lng: float) -> dict | None:
    """Atualiza a posicao GPS de um motorista."""
    import time
    motoristas = listar_motoristas()
    for m in motoristas:
        if m.get("id") == motorista_id:
            m["posicao"] = {"lat": lat, "lng": lng, "timestamp": time.time()}
            m["status"] = "ativo"
            _escrever_json(MOTORISTAS_FILE, motoristas)
            return m
    return None


def obter_posicoes_motoristas() -> list[dict]:
    """Retorna posicoes de todos os motoristas ativos."""
    motoristas = listar_motoristas()
    ativos = []
    for m in motoristas:
        if m.get("status") == "ativo" and m.get("posicao"):
            ativos.append({
                "id": m["id"],
                "nome": m.get("nome", "Sem nome"),
                "veiculo_id": m.get("veiculo_id"),
                "posicao": m["posicao"]
            })
    return ativos
