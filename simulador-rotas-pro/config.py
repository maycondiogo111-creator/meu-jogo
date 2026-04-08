"""
config.py — Configuracao centralizada do sistema

Todas as configuracoes vem de variaveis de ambiente (.env).
NUNCA escreva valores sensiveis diretamente neste arquivo.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variaveis do arquivo .env automaticamente
load_dotenv()


# -- Diretorios ----------------------------------------------------------------
BASE_DIR = Path(__file__).parent
BASE_DATA_DIR = BASE_DIR / "base"


# -- API Externa ---------------------------------------------------------------
ORS_API_KEY = os.getenv("ORS_API_KEY", "")
ORS_BASE_URL = "https://api.openrouteservice.org/v2"
ORS_ENDPOINT_ROTA = f"{ORS_BASE_URL}/directions/driving-car/geojson"

# Limite de requisicoes por sessao (protecao basica de custo)
ORS_MAX_REQUESTS_POR_HORA = int(os.getenv("ORS_MAX_REQUESTS_POR_HORA", "40"))


# -- Custos Operacionais -------------------------------------------------------
# Para mudar os custos: edite o arquivo .env, nao este arquivo
CUSTO_KM  = float(os.getenv("CUSTO_KM",  "2.5"))
CUSTO_MIN = float(os.getenv("CUSTO_MIN", "0.8"))


# -- Arquivos de Dados ---------------------------------------------------------
CLIENTES_FILE = BASE_DATA_DIR / "clientes.json"
ROTAS_FILE    = BASE_DATA_DIR / "rotas.json"
VEICULOS_FILE = BASE_DATA_DIR / "veiculos.json"
PEDIDOS_FILE  = BASE_DATA_DIR / "pedidos.json"
MOTORISTAS_FILE = BASE_DATA_DIR / "motoristas.json"


# -- Flask ---------------------------------------------------------------------
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
PORT        = int(os.getenv("PORT", "5000"))


# -- Banco de dados (preparado para uso futuro) --------------------------------
# Para ativar SQLite: descomente e ajuste conforme necessario
# DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'database' / 'app.db'}")


# -- Validacao de inicializacao ------------------------------------------------
def validar_configuracao():
    """Verifica se todas as configuracoes obrigatorias estao presentes."""
    problemas = []

    if not ORS_API_KEY or ORS_API_KEY == "COLE_SUA_CHAVE_AQUI":
        problemas.append(
            "ORS_API_KEY nao configurada. "
            "Edite o arquivo .env e insira sua chave da OpenRouteService."
        )

    if not BASE_DATA_DIR.exists():
        BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    return problemas
