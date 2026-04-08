/**
 * state.js — Estado global da aplicacao
 *
 * Centraliza todas as variaveis compartilhadas entre os modulos.
 * Para adicionar estado: declare aqui e use em qualquer outro modulo.
 *
 * NAO coloque logica aqui — apenas declaracoes de estado.
 */

// Pontos clicados pelo usuario no mapa [lat, lng]
var pontos = [];

// Marcadores Leaflet ativos no mapa
var markers = [];

// Linha da rota desenhada no mapa
var linhaRota = null;

// Ultima rota calculada (usada para salvar)
var ultimaRota = null;

// Linhas de rotas multi-veiculos
var linhasRotaFrota = [];

// Marcadores de motoristas no mapa (rastreamento)
var marcadoresMotoristas = {};

// Intervalo de atualizacao do rastreamento
var intervaloRastreamento = null;

// Aba ativa do painel
var abaAtiva = 'simulador';
