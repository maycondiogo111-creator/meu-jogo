"""
importacao_service.py — Servico de importacao de pedidos (Feature 5)

Responsabilidades:
  - Processar arquivos Excel (.xlsx, .xls)
  - Processar arquivos CSV
  - Validar dados importados
  - Converter para formato interno de pedidos
"""

import csv
import io
import json


def processar_excel(arquivo_bytes: bytes, nome_arquivo: str) -> list[dict]:
    """
    Processa arquivo Excel e retorna lista de pedidos.

    Colunas esperadas:
    - endereco_lat (ou latitude)
    - endereco_lng (ou longitude)
    - cliente (nome do cliente)
    - peso (peso do pedido em kg)
    - volume (volume em m3)
    - janela_inicio (horario inicio entrega, ex: "08:00")
    - janela_fim (horario fim entrega, ex: "18:00")
    - descricao (descricao do pedido)

    Args:
        arquivo_bytes: conteudo do arquivo em bytes
        nome_arquivo: nome do arquivo original

    Returns:
        lista de dicts de pedidos validados
    """
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(arquivo_bytes))
        ws = wb.active

        # Extrai cabecalho
        headers = []
        for cell in ws[1]:
            headers.append(str(cell.value or "").strip().lower())

        pedidos = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue

            dados = dict(zip(headers, row))
            pedido = _mapear_pedido(dados)
            if pedido:
                pedidos.append(pedido)

        return pedidos

    except ImportError:
        raise RuntimeError(
            "Biblioteca openpyxl nao instalada. "
            "Para importar Excel, instale com: pip install openpyxl"
        )
    except Exception as e:
        raise RuntimeError(f"Erro ao processar arquivo Excel: {str(e)}")


def processar_csv(arquivo_bytes: bytes, nome_arquivo: str) -> list[dict]:
    """
    Processa arquivo CSV e retorna lista de pedidos.

    Args:
        arquivo_bytes: conteudo do arquivo em bytes
        nome_arquivo: nome do arquivo original

    Returns:
        lista de dicts de pedidos validados
    """
    try:
        # Tenta detectar encoding
        texto = arquivo_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            texto = arquivo_bytes.decode("latin-1")
        except UnicodeDecodeError:
            raise RuntimeError("Nao foi possivel decodificar o arquivo CSV.")

    # Detecta delimitador
    delimitador = ","
    if texto.count(";") > texto.count(","):
        delimitador = ";"

    reader = csv.DictReader(io.StringIO(texto), delimiter=delimitador)

    pedidos = []
    for row in reader:
        # Normaliza chaves
        dados = {k.strip().lower(): v for k, v in row.items() if k}
        pedido = _mapear_pedido(dados)
        if pedido:
            pedidos.append(pedido)

    return pedidos


def _mapear_pedido(dados: dict) -> dict | None:
    """
    Mapeia dados brutos para formato de pedido interno.
    Aceita varios nomes de coluna para flexibilidade.

    Args:
        dados: dict com dados brutos

    Returns:
        dict de pedido formatado ou None se invalido
    """
    # Mapeamento flexivel de nomes de colunas
    lat = _extrair_numero(dados, ["endereco_lat", "latitude", "lat", "endereco_latitude"])
    lng = _extrair_numero(dados, ["endereco_lng", "longitude", "lng", "endereco_longitude", "lon"])

    if lat is None or lng is None:
        return None

    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return None

    peso = _extrair_numero(dados, ["peso", "weight", "peso_kg"]) or 0
    volume = _extrair_numero(dados, ["volume", "vol", "volume_m3"]) or 0

    cliente = _extrair_texto(dados, ["cliente", "client", "customer", "nome_cliente"])
    descricao = _extrair_texto(dados, ["descricao", "description", "desc", "observacao"])
    endereco_texto = _extrair_texto(dados, ["endereco", "address", "endereco_completo"])

    janela_inicio = _extrair_texto(dados, ["janela_inicio", "inicio_entrega", "hora_inicio", "window_start"])
    janela_fim = _extrair_texto(dados, ["janela_fim", "fim_entrega", "hora_fim", "window_end"])

    return {
        "endereco": [lat, lng],
        "endereco_texto": endereco_texto or "",
        "cliente": cliente or "Sem cliente",
        "peso": peso,
        "volume": volume,
        "janela_entrega": {
            "inicio": janela_inicio or "08:00",
            "fim": janela_fim or "18:00"
        },
        "descricao": descricao or ""
    }


def _extrair_numero(dados: dict, chaves: list[str]) -> float | None:
    """Tenta extrair valor numerico de varias chaves possiveis."""
    for chave in chaves:
        valor = dados.get(chave)
        if valor is not None:
            try:
                # Trata virgula como separador decimal
                if isinstance(valor, str):
                    valor = valor.replace(",", ".").strip()
                return float(valor)
            except (ValueError, TypeError):
                continue
    return None


def _extrair_texto(dados: dict, chaves: list[str]) -> str | None:
    """Tenta extrair valor texto de varias chaves possiveis."""
    for chave in chaves:
        valor = dados.get(chave)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return None


def gerar_template_csv() -> str:
    """
    Gera um template CSV para download.

    Returns:
        string CSV com cabecalho e exemplo
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # Cabecalho
    writer.writerow([
        "latitude", "longitude", "cliente", "endereco",
        "peso", "volume", "janela_inicio", "janela_fim", "descricao"
    ])

    # Exemplos
    writer.writerow([
        "-23.5505", "-46.6333", "Cliente Exemplo 1", "Av. Paulista, 1000",
        "10", "0.5", "08:00", "12:00", "Entrega urgente"
    ])
    writer.writerow([
        "-23.5629", "-46.6544", "Cliente Exemplo 2", "Rua Augusta, 500",
        "5", "0.2", "13:00", "18:00", "Entrega padrao"
    ])

    return output.getvalue()
