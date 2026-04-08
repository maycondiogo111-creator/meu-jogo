/**
 * api.js — Comunicacao com o backend
 *
 * Responsabilidade UNICA: fazer fetch para o servidor.
 * - Nenhuma logica de UI aqui
 * - Nenhuma manipulacao de DOM aqui
 * - Apenas chamadas HTTP e retorno de dados
 *
 * Para trocar a URL base ou adicionar autenticacao, mexa APENAS aqui.
 */

var API_BASE = '';  // relativo — funciona em qualquer host


/**
 * Calcula rota a partir de array de pontos.
 * @param {Array} pontosArray - [[lat, lng], ...]
 * @returns {Promise<Object>} dados da rota
 */
async function apiCalcularRota(pontosArray) {
    var response = await fetch(API_BASE + '/rota', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ pontos: pontosArray })
    });
    return response.json();
}


/**
 * Salva rota no servidor.
 * @param {Object} dadosRota - dados completos da rota + cliente
 * @returns {Promise<Object>}
 */
async function apiSalvarRota(dadosRota) {
    var response = await fetch(API_BASE + '/salvar_rota', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(dadosRota)
    });
    return response.json();
}


/**
 * Lista todas as rotas salvas.
 * @returns {Promise<Array>}
 */
async function apiListarRotas() {
    var response = await fetch(API_BASE + '/rotas');
    return response.json();
}


/**
 * Lista todos os clientes.
 * @returns {Promise<Array>}
 */
async function apiListarClientes() {
    var response = await fetch(API_BASE + '/clientes');
    return response.json();
}


/**
 * Adiciona novo cliente.
 * @param {string} nome
 * @returns {Promise<Object>}
 */
async function apiAdicionarCliente(nome) {
    var response = await fetch(API_BASE + '/clientes', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ nome: nome })
    });
    return response.json();
}


// === Feature 1: Multi-Veiculos ===

async function apiListarVeiculos() {
    var response = await fetch(API_BASE + '/veiculos');
    return response.json();
}

async function apiAdicionarVeiculo(veiculo) {
    var response = await fetch(API_BASE + '/veiculos', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(veiculo)
    });
    return response.json();
}

async function apiRemoverVeiculo(id) {
    var response = await fetch(API_BASE + '/veiculos/' + id, {
        method: 'DELETE'
    });
    return response.json();
}

async function apiRoteirizar(dados) {
    var response = await fetch(API_BASE + '/roteirizar', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(dados || {})
    });
    return response.json();
}


// === Feature 2: Rastreamento ===

async function apiListarMotoristas() {
    var response = await fetch(API_BASE + '/motoristas');
    return response.json();
}

async function apiAdicionarMotorista(motorista) {
    var response = await fetch(API_BASE + '/motoristas', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(motorista)
    });
    return response.json();
}

async function apiAtualizarPosicao(motoristaId, lat, lng) {
    var response = await fetch(API_BASE + '/motoristas/' + motoristaId + '/posicao', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ lat: lat, lng: lng })
    });
    return response.json();
}

async function apiRastreamento() {
    var response = await fetch(API_BASE + '/rastreamento');
    return response.json();
}


// === Feature 3: Simulacao ===

async function apiSimular(dados) {
    var response = await fetch(API_BASE + '/simular', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(dados)
    });
    return response.json();
}


// === Feature 4: Dashboard ===

async function apiDashboard() {
    var response = await fetch(API_BASE + '/dashboard');
    return response.json();
}


// === Feature 5: Importacao ===

async function apiListarPedidos() {
    var response = await fetch(API_BASE + '/pedidos');
    return response.json();
}

async function apiLimparPedidos() {
    var response = await fetch(API_BASE + '/pedidos', { method: 'DELETE' });
    return response.json();
}

async function apiImportarArquivo(formData) {
    var response = await fetch(API_BASE + '/importar', {
        method: 'POST',
        body:   formData
    });
    return response.json();
}
