/**
 * app.js — Orquestrador da aplicacao
 *
 * Liga os modulos: state + map + api + ui.
 * Contem as funcoes chamadas diretamente pelo HTML (onclick=).
 */


// -- Calcular rota ------------------------------------------------------------

async function calcularRota() {
    if (pontos.length < 2) {
        alert('Clique no mapa para adicionar pelo menos 2 pontos.');
        return;
    }

    uiMostrarLoading();

    try {
        var dados = await apiCalcularRota(pontos);

        if (dados.erro) {
            alert('Erro: ' + dados.erro);
            uiResetarPainel();
            return;
        }

        desenharRota(dados.rota);
        uiMostrarResultadoRota(dados);

        ultimaRota = dados;

    } catch (err) {
        console.error('Erro ao calcular rota:', err);
        alert('Erro de conexao ao calcular rota. Verifique se o servidor esta rodando.');
        uiResetarPainel();
    }
}


// -- Limpar mapa --------------------------------------------------------------

function limparMapaCompleto() {
    mapLimparMapa();
    uiResetarPainel();
    ultimaRota = null;
}

var limparMapa_original = mapLimparMapa;


// -- Salvar rota --------------------------------------------------------------

async function salvarRota() {
    if (!ultimaRota) {
        alert('Calcule uma rota antes de salvar.');
        return;
    }

    try {
        var clientes = await apiListarClientes();

        var listaTexto = clientes.length > 0
            ? 'Clientes existentes:\n' + clientes.join('\n') + '\n\n'
            : '';

        var cliente = prompt(listaTexto + 'Digite o nome do cliente (ou deixe em branco):');
        if (cliente === null) return;
        if (!cliente.trim()) cliente = 'Sem cliente';

        if (cliente !== 'Sem cliente' && !clientes.includes(cliente)) {
            await apiAdicionarCliente(cliente);
        }

        var payload = Object.assign({}, ultimaRota, {
            cliente: cliente,
            nome:    'Rota ' + new Date().toLocaleTimeString('pt-BR'),
            data:    new Date().toISOString()
        });

        await apiSalvarRota(payload);
        alert('Rota salva com sucesso!');

        await recarregarListaRotas();

    } catch (err) {
        console.error('Erro ao salvar rota:', err);
        alert('Erro ao salvar rota. Verifique o console para detalhes.');
    }
}


// -- Listar rotas -------------------------------------------------------------

async function recarregarListaRotas() {
    try {
        var rotas = await apiListarRotas();
        uiRenderizarListaRotas(rotas);
    } catch (err) {
        console.error('Erro ao carregar rotas:', err);
    }
}


// -- Carregar rota salva no mapa ----------------------------------------------

function carregarRotaNoMapa(rota) {
    limparMapa_original();
    desenharRota(rota.rota);
    uiMostrarResultadoRota(rota);
    ultimaRota = rota;
}


// =============================================================================
// Feature 1: Multi-Veiculos
// =============================================================================

async function carregarVeiculos() {
    try {
        var veiculos = await apiListarVeiculos();
        uiRenderizarVeiculos(veiculos);
    } catch (err) {
        console.error('Erro ao carregar veiculos:', err);
    }
}

async function adicionarVeiculo() {
    var nome = document.getElementById('veiculo-nome').value.trim();
    if (!nome) { alert('Informe o nome do veiculo.'); return; }

    var veiculo = {
        nome: nome,
        placa: document.getElementById('veiculo-placa').value.trim(),
        capacidade_peso: parseFloat(document.getElementById('veiculo-peso').value) || 0,
        capacidade_volume: parseFloat(document.getElementById('veiculo-volume').value) || 0,
        custo_km: parseFloat(document.getElementById('veiculo-custo').value) || 2.5
    };

    try {
        var res = await apiAdicionarVeiculo(veiculo);
        if (res.erro) { alert(res.erro); return; }

        document.getElementById('veiculo-nome').value = '';
        document.getElementById('veiculo-placa').value = '';
        document.getElementById('veiculo-peso').value = '';
        document.getElementById('veiculo-volume').value = '';
        document.getElementById('veiculo-custo').value = '';

        await carregarVeiculos();
    } catch (err) {
        console.error('Erro ao adicionar veiculo:', err);
        alert('Erro ao adicionar veiculo.');
    }
}

async function removerVeiculo(id) {
    if (!confirm('Remover este veiculo?')) return;
    try {
        await apiRemoverVeiculo(id);
        await carregarVeiculos();
    } catch (err) {
        console.error('Erro ao remover veiculo:', err);
    }
}

async function roteirizarFrota() {
    try {
        var deposito = null;
        var depLat = document.getElementById('deposito-lat').value;
        var depLng = document.getElementById('deposito-lng').value;
        if (depLat && depLng) {
            deposito = [parseFloat(depLat), parseFloat(depLng)];
        }

        var res = await apiRoteirizar({ deposito: deposito });
        if (res.erro) { alert(res.erro); return; }

        uiRenderizarResultadoFrota(res);
        desenharRotasFrota(res.rotas);
    } catch (err) {
        console.error('Erro na roteirizacao:', err);
        alert('Erro ao roteirizar frota.');
    }
}


// =============================================================================
// Feature 2: Rastreamento em Tempo Real
// =============================================================================

async function carregarMotoristas() {
    try {
        var motoristas = await apiListarMotoristas();
        uiRenderizarMotoristas(motoristas);
    } catch (err) {
        console.error('Erro ao carregar motoristas:', err);
    }
}

async function adicionarMotorista() {
    var nome = document.getElementById('motorista-nome').value.trim();
    if (!nome) { alert('Informe o nome do motorista.'); return; }

    try {
        var res = await apiAdicionarMotorista({ nome: nome });
        if (res.erro) { alert(res.erro); return; }

        document.getElementById('motorista-nome').value = '';
        await carregarMotoristas();
    } catch (err) {
        console.error('Erro ao adicionar motorista:', err);
        alert('Erro ao adicionar motorista.');
    }
}

function iniciarRastreamento() {
    if (intervaloRastreamento) clearInterval(intervaloRastreamento);

    atualizarRastreamento();
    intervaloRastreamento = setInterval(atualizarRastreamento, 5000);
}

function pararRastreamento() {
    if (intervaloRastreamento) {
        clearInterval(intervaloRastreamento);
        intervaloRastreamento = null;
    }
}

async function atualizarRastreamento() {
    try {
        var posicoes = await apiRastreamento();
        atualizarMotoristasMapa(posicoes);
    } catch (err) {
        console.error('Erro no rastreamento:', err);
    }
}


// =============================================================================
// Feature 3: Simulacao de Cenarios
// =============================================================================

async function executarSimulacao() {
    var veiculosExtras = parseInt(document.getElementById('sim-veiculos-extras').value) || 0;

    var deposito = null;
    var depLat = document.getElementById('deposito-lat');
    var depLng = document.getElementById('deposito-lng');
    if (depLat && depLng && depLat.value && depLng.value) {
        deposito = [parseFloat(depLat.value), parseFloat(depLng.value)];
    }

    try {
        var res = await apiSimular({
            veiculos_extras: veiculosExtras,
            deposito: deposito
        });
        if (res.erro) { alert(res.erro); return; }

        uiRenderizarSimulacao(res);
    } catch (err) {
        console.error('Erro na simulacao:', err);
        alert('Erro ao simular cenario.');
    }
}


// =============================================================================
// Feature 4: Dashboard
// =============================================================================

async function carregarDashboard() {
    try {
        var dados = await apiDashboard();
        uiRenderizarDashboard(dados);
    } catch (err) {
        console.error('Erro ao carregar dashboard:', err);
    }
}


// =============================================================================
// Feature 5: Importacao de Pedidos
// =============================================================================

async function carregarPedidos() {
    try {
        var pedidos = await apiListarPedidos();
        uiRenderizarPedidos(pedidos);
    } catch (err) {
        console.error('Erro ao carregar pedidos:', err);
    }
}

async function importarArquivo() {
    var input = document.getElementById('arquivo-importacao');
    if (!input.files.length) {
        alert('Selecione um arquivo Excel (.xlsx) ou CSV (.csv).');
        return;
    }

    var formData = new FormData();
    formData.append('arquivo', input.files[0]);

    try {
        var res = await apiImportarArquivo(formData);
        if (res.erro) { alert(res.erro); return; }

        alert('Importados ' + res.importados + ' pedidos com sucesso!');
        input.value = '';
        await carregarPedidos();
    } catch (err) {
        console.error('Erro na importacao:', err);
        alert('Erro ao importar arquivo.');
    }
}

async function limparTodosPedidos() {
    if (!confirm('Remover todos os pedidos?')) return;
    try {
        await apiLimparPedidos();
        await carregarPedidos();
    } catch (err) {
        console.error('Erro ao limpar pedidos:', err);
    }
}

function baixarTemplate() {
    window.location.href = API_BASE + '/template-importacao';
}


// -- Inicializacao ------------------------------------------------------------

window.addEventListener('load', function() {
    recarregarListaRotas();
    mostrarAba('simulador');
});
