"""
app.py — Ponto de entrada do servidor Flask

Responsabilidade: apenas definir rotas HTTP e delegar para os services.
NAO contem logica de negocio aqui — tudo vai para services/.

Rotas disponveis:
  GET  /                      -> serve o frontend
  POST /rota                  -> calcula rota otimizada
  POST /salvar_rota           -> persiste rota calculada
  GET  /rotas                 -> lista rotas salvas
  GET  /clientes              -> lista clientes
  POST /clientes              -> adiciona cliente

  --- Feature 1: Multi-Veiculos ---
  GET  /veiculos              -> lista veiculos
  POST /veiculos              -> adiciona veiculo
  PUT  /veiculos/<id>         -> atualiza veiculo
  DELETE /veiculos/<id>       -> remove veiculo
  POST /roteirizar            -> roteiriza frota multi-veiculos

  --- Feature 2: Rastreamento ---
  GET  /motoristas            -> lista motoristas
  POST /motoristas            -> adiciona motorista
  POST /motoristas/<id>/posicao -> atualiza posicao GPS
  GET  /rastreamento          -> posicoes de todos os motoristas ativos

  --- Feature 3: Simulacao ---
  POST /simular               -> simula cenarios de custo

  --- Feature 4: Dashboard ---
  GET  /dashboard             -> KPIs operacionais

  --- Feature 5: Importacao ---
  POST /importar              -> importa pedidos (Excel/CSV)
  GET  /pedidos               -> lista pedidos
  DELETE /pedidos              -> limpa pedidos
  GET  /template-importacao   -> download template CSV
"""

from flask import Flask, render_template, request, jsonify, Response
from config import FLASK_DEBUG, PORT, validar_configuracao
from services.rota_service import processar_rota
from services.storage_service import (
    listar_clientes,
    adicionar_cliente,
    listar_rotas,
    salvar_rota,
    listar_veiculos,
    adicionar_veiculo,
    atualizar_veiculo,
    remover_veiculo,
    listar_pedidos,
    adicionar_pedido,
    adicionar_pedidos_em_lote,
    limpar_pedidos,
    listar_motoristas,
    adicionar_motorista,
    atualizar_posicao_motorista,
    obter_posicoes_motoristas,
)
from services.frota_service import roteirizar_frota, simular_cenario
from services.dashboard_service import calcular_kpis
from services.importacao_service import processar_excel, processar_csv, gerar_template_csv


# -- Inicializacao -------------------------------------------------------------
app = Flask(__name__)


# -- Helpers de resposta padronizada -------------------------------------------

def resposta_erro(mensagem: str, codigo: int = 400) -> tuple:
    """Retorna resposta de erro padronizada."""
    return jsonify({"erro": mensagem}), codigo

def resposta_ok(dados: dict) -> tuple:
    """Retorna resposta de sucesso."""
    return jsonify(dados), 200


# -- Rotas originais -----------------------------------------------------------

@app.route("/")
def index():
    """Serve o frontend principal."""
    return render_template("index.html")


@app.route("/rota", methods=["POST"])
def calcular_rota():
    """
    Recebe pontos do mapa, otimiza ordem e calcula rota real.

    Body: { "pontos": [[lat, lng], [lat, lng], ...] }
    """
    dados = request.get_json(silent=True)
    if not dados:
        return resposta_erro("Body JSON invalido ou ausente.")

    pontos = dados.get("pontos", [])

    try:
        resultado = processar_rota(pontos)
        return resposta_ok(resultado)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    except RuntimeError as e:
        return resposta_erro(str(e), 502)
    except Exception as e:
        app.logger.error(f"Erro inesperado em /rota: {e}")
        return resposta_erro("Erro interno do servidor.", 500)


@app.route("/salvar_rota", methods=["POST"])
def endpoint_salvar_rota():
    """
    Persiste uma rota calculada com dados do cliente.

    Body: { cliente, nome, data, rota, distancia_km, duracao_min, custo, instrucoes }
    """
    dados = request.get_json(silent=True)
    if not dados:
        return resposta_erro("Body JSON invalido ou ausente.")

    nova_rota = {
        "cliente":      dados.get("cliente",      "Sem cliente"),
        "nome":         dados.get("nome",         "Sem nome"),
        "data":         dados.get("data"),
        "rota":         dados.get("rota",         []),
        "distancia_km": dados.get("distancia_km", 0),
        "duracao_min":  dados.get("duracao_min",  0),
        "custo":        dados.get("custo",        0),
        "instrucoes":   dados.get("instrucoes",   []),
    }

    resultado = salvar_rota(nova_rota)
    return resposta_ok(resultado)


@app.route("/rotas", methods=["GET"])
def endpoint_listar_rotas():
    """Lista todas as rotas salvas."""
    return resposta_ok(listar_rotas())


@app.route("/clientes", methods=["GET"])
def endpoint_listar_clientes():
    """Lista todos os clientes cadastrados."""
    return resposta_ok(listar_clientes())


@app.route("/clientes", methods=["POST"])
def endpoint_adicionar_cliente():
    """
    Adiciona novo cliente se nao existir.

    Body: { "nome": "Nome do Cliente" }
    """
    dados = request.get_json(silent=True)
    if not dados:
        return resposta_erro("Body JSON invalido ou ausente.")

    nome = dados.get("nome", "").strip()

    if not nome:
        return resposta_erro("Nome do cliente e obrigatorio.")

    if len(nome) < 2:
        return resposta_erro("Nome do cliente deve ter pelo menos 2 caracteres.")

    if len(nome) > 200:
        return resposta_erro("Nome do cliente muito longo (maximo 200 caracteres).")

    adicionar_cliente(nome)
    return resposta_ok({"ok": True})


# =============================================================================
# Feature 1: Roteirizacao Multi-Veiculos
# =============================================================================

@app.route("/veiculos", methods=["GET"])
def endpoint_listar_veiculos():
    """Lista todos os veiculos cadastrados."""
    return resposta_ok(listar_veiculos())


@app.route("/veiculos", methods=["POST"])
def endpoint_adicionar_veiculo():
    """
    Adiciona novo veiculo.

    Body: { "nome", "placa", "capacidade_peso", "capacidade_volume", "custo_km" }
    """
    dados = request.get_json(silent=True)
    if not dados:
        return resposta_erro("Body JSON invalido ou ausente.")

    nome = dados.get("nome", "").strip()
    if not nome:
        return resposta_erro("Nome do veiculo e obrigatorio.")

    veiculo = {
        "nome": nome,
        "placa": dados.get("placa", ""),
        "capacidade_peso": float(dados.get("capacidade_peso", 0)),
        "capacidade_volume": float(dados.get("capacidade_volume", 0)),
        "custo_km": float(dados.get("custo_km", 2.5)),
    }

    resultado = adicionar_veiculo(veiculo)
    return resposta_ok(resultado)


@app.route("/veiculos/<int:veiculo_id>", methods=["PUT"])
def endpoint_atualizar_veiculo(veiculo_id):
    """Atualiza dados de um veiculo."""
    dados = request.get_json(silent=True)
    if not dados:
        return resposta_erro("Body JSON invalido ou ausente.")

    resultado = atualizar_veiculo(veiculo_id, dados)
    if resultado is None:
        return resposta_erro("Veiculo nao encontrado.", 404)
    return resposta_ok({"status": "ok", "veiculo": resultado})


@app.route("/veiculos/<int:veiculo_id>", methods=["DELETE"])
def endpoint_remover_veiculo(veiculo_id):
    """Remove um veiculo."""
    if remover_veiculo(veiculo_id):
        return resposta_ok({"status": "ok"})
    return resposta_erro("Veiculo nao encontrado.", 404)


@app.route("/roteirizar", methods=["POST"])
def endpoint_roteirizar():
    """
    Roteiriza pedidos entre veiculos da frota.

    Body: {
        "pedidos": [...] (opcional, usa pedidos salvos se nao informado),
        "veiculos": [...] (opcional, usa veiculos salvos se nao informado),
        "deposito": [lat, lng] (opcional)
    }
    """
    dados = request.get_json(silent=True)
    if not dados:
        dados = {}

    pedidos = dados.get("pedidos") or listar_pedidos()
    veiculos = dados.get("veiculos") or listar_veiculos()
    deposito = dados.get("deposito")

    try:
        resultado = roteirizar_frota(pedidos, veiculos, deposito)
        return resposta_ok(resultado)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    except Exception as e:
        app.logger.error(f"Erro na roteirizacao: {e}")
        return resposta_erro("Erro ao roteirizar frota.", 500)


# =============================================================================
# Feature 2: Rastreamento em Tempo Real
# =============================================================================

@app.route("/motoristas", methods=["GET"])
def endpoint_listar_motoristas():
    """Lista todos os motoristas."""
    return resposta_ok(listar_motoristas())


@app.route("/motoristas", methods=["POST"])
def endpoint_adicionar_motorista():
    """
    Adiciona novo motorista.

    Body: { "nome", "veiculo_id" (opcional) }
    """
    dados = request.get_json(silent=True)
    if not dados:
        return resposta_erro("Body JSON invalido ou ausente.")

    nome = dados.get("nome", "").strip()
    if not nome:
        return resposta_erro("Nome do motorista e obrigatorio.")

    motorista = {
        "nome": nome,
        "veiculo_id": dados.get("veiculo_id"),
    }

    resultado = adicionar_motorista(motorista)
    return resposta_ok(resultado)


@app.route("/motoristas/<int:motorista_id>/posicao", methods=["POST"])
def endpoint_atualizar_posicao(motorista_id):
    """
    Atualiza posicao GPS de um motorista.

    Body: { "lat": -23.55, "lng": -46.63 }
    """
    dados = request.get_json(silent=True)
    if not dados:
        return resposta_erro("Body JSON invalido ou ausente.")

    lat = dados.get("lat")
    lng = dados.get("lng")

    if lat is None or lng is None:
        return resposta_erro("Latitude e longitude sao obrigatorias.")

    resultado = atualizar_posicao_motorista(motorista_id, float(lat), float(lng))
    if resultado is None:
        return resposta_erro("Motorista nao encontrado.", 404)

    return resposta_ok({"status": "ok", "motorista": resultado})


@app.route("/rastreamento", methods=["GET"])
def endpoint_rastreamento():
    """Retorna posicoes de todos os motoristas ativos."""
    return resposta_ok(obter_posicoes_motoristas())


# =============================================================================
# Feature 3: Simulacao de Custos e Cenarios
# =============================================================================

@app.route("/simular", methods=["POST"])
def endpoint_simular():
    """
    Simula cenarios de custo.

    Body: {
        "pedidos": [...] (opcional),
        "veiculos": [...] (opcional),
        "deposito": [lat, lng] (opcional),
        "veiculos_extras": 1 (int, opcional),
        "pedidos_extras": [...] (opcional)
    }
    """
    dados = request.get_json(silent=True)
    if not dados:
        dados = {}

    pedidos = dados.get("pedidos") or listar_pedidos()
    veiculos = dados.get("veiculos") or listar_veiculos()
    deposito = dados.get("deposito")
    veiculos_extras = int(dados.get("veiculos_extras", 0))
    pedidos_extras = dados.get("pedidos_extras")

    try:
        resultado = simular_cenario(
            pedidos, veiculos, deposito,
            veiculos_extras=veiculos_extras,
            pedidos_extras=pedidos_extras
        )
        return resposta_ok(resultado)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    except Exception as e:
        app.logger.error(f"Erro na simulacao: {e}")
        return resposta_erro("Erro ao simular cenario.", 500)


# =============================================================================
# Feature 4: Dashboard Operacional
# =============================================================================

@app.route("/dashboard", methods=["GET"])
def endpoint_dashboard():
    """Retorna KPIs operacionais."""
    try:
        kpis = calcular_kpis()
        return resposta_ok(kpis)
    except Exception as e:
        app.logger.error(f"Erro no dashboard: {e}")
        return resposta_erro("Erro ao calcular KPIs.", 500)


# =============================================================================
# Feature 5: Importacao de Pedidos
# =============================================================================

@app.route("/pedidos", methods=["GET"])
def endpoint_listar_pedidos():
    """Lista todos os pedidos."""
    return resposta_ok(listar_pedidos())


@app.route("/pedidos", methods=["DELETE"])
def endpoint_limpar_pedidos():
    """Remove todos os pedidos."""
    return resposta_ok(limpar_pedidos())


@app.route("/importar", methods=["POST"])
def endpoint_importar():
    """
    Importa pedidos de arquivo Excel ou CSV.

    Form: arquivo (file upload)
    """
    if "arquivo" not in request.files:
        return resposta_erro("Nenhum arquivo enviado. Use o campo 'arquivo'.")

    arquivo = request.files["arquivo"]
    if not arquivo.filename:
        return resposta_erro("Nome do arquivo invalido.")

    nome = arquivo.filename.lower()
    conteudo = arquivo.read()

    try:
        if nome.endswith((".xlsx", ".xls")):
            pedidos = processar_excel(conteudo, arquivo.filename)
        elif nome.endswith(".csv"):
            pedidos = processar_csv(conteudo, arquivo.filename)
        else:
            return resposta_erro("Formato nao suportado. Use .xlsx, .xls ou .csv")

        if not pedidos:
            return resposta_erro("Nenhum pedido valido encontrado no arquivo.")

        resultado = adicionar_pedidos_em_lote(pedidos)
        return resposta_ok(resultado)

    except RuntimeError as e:
        return resposta_erro(str(e), 400)
    except Exception as e:
        app.logger.error(f"Erro na importacao: {e}")
        return resposta_erro("Erro ao processar arquivo.", 500)


@app.route("/template-importacao", methods=["GET"])
def endpoint_template():
    """Download template CSV para importacao."""
    csv_content = gerar_template_csv()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=template_pedidos.csv"}
    )


# -- Inicializacao -------------------------------------------------------------

if __name__ == "__main__":
    # Valida configuracao antes de iniciar
    problemas = validar_configuracao()
    if problemas:
        print("\n  ATENCAO - Problemas de configuracao encontrados:")
        for p in problemas:
            print(f"   - {p}")
        print()

    print(f"\n  Servidor rodando em http://localhost:{PORT}")
    print(f"  Modo debug: {FLASK_DEBUG}")
    print()

    app.run(debug=FLASK_DEBUG, port=PORT)
