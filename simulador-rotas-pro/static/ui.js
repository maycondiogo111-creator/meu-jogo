/**
 * ui.js — Atualizacao da interface
 *
 * Responsabilidade UNICA: manipular elementos HTML.
 * - Mostrar resultados de rota
 * - Renderizar lista de rotas salvas
 * - Controlar cards (minimizar/expandir)
 * - Exibir estados de loading e erro
 * - Renderizar veiculos, motoristas, pedidos, dashboard, simulacao
 *
 * NAO faz fetch, NAO mexe no mapa — so atualiza o DOM.
 */


// -- Painel de informacoes da rota --------------------------------------------

function uiMostrarLoading() {
    document.getElementById('tempo').innerText      = 'Calculando...';
    document.getElementById('distancia').innerText  = '...';
    document.getElementById('custo').innerText      = '...';
    document.getElementById('instrucoes').innerHTML = '';
}

function uiMostrarResultadoRota(dados) {
    document.getElementById('distancia').innerText = dados.distancia_km + ' km';
    document.getElementById('tempo').innerText     = dados.duracao_min  + ' min';

    if (dados.custo_detalhado) {
        document.getElementById('custo').innerText =
            'R$ ' + dados.custo +
            ' (Dist: R$ ' + dados.custo_detalhado.distancia +
            ' | Tempo: R$ ' + dados.custo_detalhado.tempo + ')';
    } else {
        document.getElementById('custo').innerText = 'R$ ' + dados.custo;
    }

    uiRenderizarInstrucoes(dados.instrucoes || []);
}

function uiResetarPainel() {
    document.getElementById('distancia').innerText  = '-';
    document.getElementById('tempo').innerText      = '-';
    document.getElementById('custo').innerText      = '-';
    document.getElementById('instrucoes').innerHTML = '';
}

function uiRenderizarInstrucoes(instrucoes) {
    var lista = document.getElementById('instrucoes');
    lista.innerHTML = '';

    instrucoes.forEach(function(instrucao, i) {
        var item = document.createElement('p');
        item.innerText = (i + 1) + '. ' + instrucao;
        lista.appendChild(item);
    });
}


// -- Lista de rotas salvas ----------------------------------------------------

function uiRenderizarListaRotas(rotas) {
    var container = document.getElementById('lista-rotas');
    container.innerHTML = '';

    if (rotas.length === 0) {
        container.innerHTML = '<p style="color:#999;font-size:12px">Nenhuma rota salva ainda.</p>';
        return;
    }

    rotas.forEach(function(rota) {
        var item = document.createElement('div');
        item.className = 'rota-item';
        item.innerHTML =
            '<strong>' + (rota.nome || 'Sem nome') + '</strong><br>' +
            'Cliente: ' + (rota.cliente || 'N/A') + '<br>' +
            (rota.distancia_km || '?') + ' km — ' + (rota.duracao_min || '?') + ' min';

        item.onclick = function() { mapCarregarRota(rota); };

        container.appendChild(item);
    });
}


// -- Cards (minimizar / expandir) ---------------------------------------------

function toggleCard(cardId) {
    var card = document.getElementById(cardId);
    var btn  = card.querySelector('.toggle-btn');

    card.classList.toggle('minimized');
    btn.innerText = card.classList.contains('minimized') ? '+' : '\u2212';
}


// =============================================================================
// Feature 1: Veiculos
// =============================================================================

function uiRenderizarVeiculos(veiculos) {
    var container = document.getElementById('lista-veiculos');
    if (!container) return;
    container.innerHTML = '';

    if (veiculos.length === 0) {
        container.innerHTML = '<p style="color:#999;font-size:12px">Nenhum veiculo cadastrado.</p>';
        return;
    }

    veiculos.forEach(function(v) {
        var item = document.createElement('div');
        item.className = 'rota-item';
        item.innerHTML =
            '<div style="display:flex;justify-content:space-between;align-items:center;">' +
            '<div><strong>' + v.nome + '</strong>' +
            (v.placa ? ' <span style="color:#888;">(' + v.placa + ')</span>' : '') +
            '<br>Cap: ' + (v.capacidade_peso || 0) + 'kg / ' + (v.capacidade_volume || 0) + 'm&sup3;' +
            '<br>Custo: R$ ' + (v.custo_km || 0) + '/km</div>' +
            '<button onclick="removerVeiculo(' + v.id + ')" style="background:#e74c3c;padding:4px 8px;font-size:11px;">' +
            '<i class="fas fa-trash"></i></button></div>';
        container.appendChild(item);
    });
}

function uiRenderizarResultadoFrota(resultado) {
    var container = document.getElementById('resultado-frota');
    if (!container) return;

    var resumo = resultado.resumo;
    var html = '<div class="resultado-roteirizacao">' +
        '<h3 style="margin:0 0 8px 0;font-size:14px;">Resultado da Roteirizacao</h3>' +
        '<p><strong>Veiculos utilizados:</strong> ' + resumo.veiculos_utilizados + '</p>' +
        '<p><strong>Pedidos atendidos:</strong> ' + resumo.total_pedidos_atendidos + '</p>' +
        '<p><strong>Distancia total:</strong> ' + resumo.distancia_total_km + ' km</p>' +
        '<p><strong>Tempo total:</strong> ' + resumo.tempo_total_min + ' min</p>' +
        '<p><strong>Custo total:</strong> R$ ' + resumo.custo_total + '</p>';

    if (resumo.total_pedidos_nao_atendidos > 0) {
        html += '<p style="color:#e74c3c;"><strong>Nao atendidos:</strong> ' +
                resumo.total_pedidos_nao_atendidos + ' pedidos</p>';
    }

    html += '<hr style="margin:8px 0;">';

    resultado.rotas.forEach(function(rota, i) {
        html += '<div style="border-left:3px solid ' + (coresFrota[i % coresFrota.length]) + ';padding-left:8px;margin-bottom:8px;">' +
            '<strong>' + rota.veiculo.nome + '</strong>' +
            (rota.veiculo.placa ? ' (' + rota.veiculo.placa + ')' : '') +
            '<br>Paradas: ' + rota.num_paradas +
            ' | ' + rota.distancia_km + ' km' +
            ' | R$ ' + rota.custo +
            '<br>Carga: ' + rota.carga_peso + 'kg / ' + rota.carga_volume + 'm&sup3;' +
            '</div>';
    });

    html += '</div>';
    container.innerHTML = html;
}


// =============================================================================
// Feature 2: Motoristas / Rastreamento
// =============================================================================

function uiRenderizarMotoristas(motoristas) {
    var container = document.getElementById('lista-motoristas');
    if (!container) return;
    container.innerHTML = '';

    if (motoristas.length === 0) {
        container.innerHTML = '<p style="color:#999;font-size:12px">Nenhum motorista cadastrado.</p>';
        return;
    }

    motoristas.forEach(function(m) {
        var statusColor = m.status === 'ativo' ? '#2ecc71' : '#999';
        var statusIcon = m.status === 'ativo' ? 'fa-circle' : 'fa-circle';

        var item = document.createElement('div');
        item.className = 'rota-item';
        item.innerHTML =
            '<div style="display:flex;align-items:center;gap:8px;">' +
            '<i class="fas ' + statusIcon + '" style="color:' + statusColor + ';font-size:8px;"></i>' +
            '<div><strong>' + m.nome + '</strong>' +
            '<br><span style="color:#888;font-size:11px;">Status: ' + (m.status || 'inativo') + '</span>' +
            (m.posicao ? '<br><span style="font-size:10px;color:#555;">Lat: ' + m.posicao.lat.toFixed(4) + ' Lng: ' + m.posicao.lng.toFixed(4) + '</span>' : '') +
            '</div></div>';
        container.appendChild(item);
    });
}


// =============================================================================
// Feature 3: Simulacao
// =============================================================================

function uiRenderizarSimulacao(resultado) {
    var container = document.getElementById('resultado-simulacao');
    if (!container) return;

    var comp = resultado.comparacao;
    var html = '<div class="resultado-simulacao">' +
        '<h3 style="margin:0 0 10px 0;font-size:14px;">Comparacao de Cenarios</h3>' +
        '<table style="width:100%;font-size:12px;border-collapse:collapse;">' +
        '<tr style="background:#f0f0f0;"><th style="padding:4px;text-align:left;">Metrica</th>' +
        '<th style="padding:4px;">Base</th><th style="padding:4px;">Simulado</th><th style="padding:4px;">Diferenca</th></tr>';

    // Custo
    var custoCor = comp.custo.diferenca < 0 ? '#2ecc71' : (comp.custo.diferenca > 0 ? '#e74c3c' : '#333');
    html += '<tr><td style="padding:4px;">Custo Total</td>' +
        '<td style="padding:4px;text-align:center;">R$ ' + comp.custo.base + '</td>' +
        '<td style="padding:4px;text-align:center;">R$ ' + comp.custo.simulado + '</td>' +
        '<td style="padding:4px;text-align:center;color:' + custoCor + ';">' +
        (comp.custo.diferenca >= 0 ? '+' : '') + 'R$ ' + comp.custo.diferenca +
        ' (' + (comp.custo.variacao_pct >= 0 ? '+' : '') + comp.custo.variacao_pct + '%)</td></tr>';

    // Distancia
    html += '<tr><td style="padding:4px;">Distancia</td>' +
        '<td style="padding:4px;text-align:center;">' + comp.distancia.base + ' km</td>' +
        '<td style="padding:4px;text-align:center;">' + comp.distancia.simulado + ' km</td>' +
        '<td style="padding:4px;text-align:center;">' +
        (comp.distancia.diferenca >= 0 ? '+' : '') + comp.distancia.diferenca + ' km</td></tr>';

    // Veiculos
    html += '<tr><td style="padding:4px;">Veiculos</td>' +
        '<td style="padding:4px;text-align:center;">' + comp.veiculos.base + '</td>' +
        '<td style="padding:4px;text-align:center;">' + comp.veiculos.simulado + '</td>' +
        '<td style="padding:4px;text-align:center;">' +
        (comp.veiculos.diferenca >= 0 ? '+' : '') + comp.veiculos.diferenca + '</td></tr>';

    // Nao atendidos
    var naCor = comp.pedidos_nao_atendidos.diferenca < 0 ? '#2ecc71' : (comp.pedidos_nao_atendidos.diferenca > 0 ? '#e74c3c' : '#333');
    html += '<tr><td style="padding:4px;">Nao Atendidos</td>' +
        '<td style="padding:4px;text-align:center;">' + comp.pedidos_nao_atendidos.base + '</td>' +
        '<td style="padding:4px;text-align:center;">' + comp.pedidos_nao_atendidos.simulado + '</td>' +
        '<td style="padding:4px;text-align:center;color:' + naCor + ';">' +
        (comp.pedidos_nao_atendidos.diferenca >= 0 ? '+' : '') + comp.pedidos_nao_atendidos.diferenca + '</td></tr>';

    html += '</table></div>';
    container.innerHTML = html;
}


// =============================================================================
// Feature 4: Dashboard
// =============================================================================

function uiRenderizarDashboard(dados) {
    var container = document.getElementById('dashboard-content');
    if (!container) return;

    var resumo = dados.resumo;
    var kpis = dados.kpis;

    var html = '<div class="dashboard-grid">';

    // KPI Cards
    html += '<div class="kpi-card"><div class="kpi-valor">' + resumo.total_rotas + '</div><div class="kpi-label">Rotas</div></div>';
    html += '<div class="kpi-card"><div class="kpi-valor">' + resumo.total_veiculos + '</div><div class="kpi-label">Veiculos</div></div>';
    html += '<div class="kpi-card"><div class="kpi-valor">' + resumo.motoristas_ativos + '/' + resumo.total_motoristas + '</div><div class="kpi-label">Motoristas Ativos</div></div>';
    html += '<div class="kpi-card"><div class="kpi-valor">' + resumo.total_pedidos + '</div><div class="kpi-label">Pedidos</div></div>';

    html += '</div>';

    // KPIs detalhados
    html += '<div style="margin-top:12px;">' +
        '<h3 style="font-size:13px;margin:0 0 8px 0;">Indicadores</h3>' +
        '<p style="margin:4px 0;font-size:12px;"><strong>Custo/km:</strong> R$ ' + kpis.custo_por_km + '</p>' +
        '<p style="margin:4px 0;font-size:12px;"><strong>Tempo medio:</strong> ' + kpis.tempo_medio_min + ' min</p>' +
        '<p style="margin:4px 0;font-size:12px;"><strong>Distancia media:</strong> ' + kpis.distancia_media_km + ' km</p>' +
        '<p style="margin:4px 0;font-size:12px;"><strong>Custo medio/rota:</strong> R$ ' + kpis.custo_medio_rota + '</p>' +
        '<p style="margin:4px 0;font-size:12px;"><strong>Rotas/motorista:</strong> ' + kpis.rotas_por_motorista + '</p>' +
        '<p style="margin:4px 0;font-size:12px;"><strong>Distancia total:</strong> ' + resumo.total_distancia_km + ' km</p>' +
        '<p style="margin:4px 0;font-size:12px;"><strong>Custo total:</strong> R$ ' + resumo.total_custo + '</p>' +
        '</div>';

    // Grafico simples de barras (ultimas 10 rotas)
    if (dados.distribuicao && dados.distribuicao.custos && dados.distribuicao.custos.length > 0) {
        var maxCusto = Math.max.apply(null, dados.distribuicao.custos);
        html += '<div style="margin-top:12px;">' +
            '<h3 style="font-size:13px;margin:0 0 8px 0;">Ultimas Rotas (Custo)</h3>' +
            '<div style="display:flex;align-items:flex-end;gap:3px;height:60px;">';

        dados.distribuicao.custos.forEach(function(c, i) {
            var altura = maxCusto > 0 ? Math.max(4, (c / maxCusto) * 55) : 4;
            html += '<div style="flex:1;background:#3498db;height:' + altura + 'px;border-radius:2px 2px 0 0;" ' +
                    'title="R$ ' + c + '"></div>';
        });

        html += '</div></div>';
    }

    container.innerHTML = html;
}


// =============================================================================
// Feature 5: Pedidos / Importacao
// =============================================================================

function uiRenderizarPedidos(pedidos) {
    var container = document.getElementById('lista-pedidos');
    if (!container) return;
    container.innerHTML = '';

    var countEl = document.getElementById('pedidos-count');
    if (countEl) countEl.innerText = pedidos.length + ' pedido(s)';

    if (pedidos.length === 0) {
        container.innerHTML = '<p style="color:#999;font-size:12px">Nenhum pedido importado.</p>';
        return;
    }

    pedidos.forEach(function(p, i) {
        var item = document.createElement('div');
        item.className = 'rota-item';
        item.style.fontSize = '11px';
        item.innerHTML =
            '<strong>#' + (p.id || (i + 1)) + '</strong> ' + (p.cliente || 'Sem cliente') +
            '<br>Peso: ' + (p.peso || 0) + 'kg | Vol: ' + (p.volume || 0) + 'm&sup3;' +
            '<br><span style="color:#888;">' + (p.endereco_texto || (p.endereco ? p.endereco[0].toFixed(4) + ', ' + p.endereco[1].toFixed(4) : 'N/A')) + '</span>';
        container.appendChild(item);
    });
}


// -- Navegacao por abas -------------------------------------------------------

function mostrarAba(nomeAba) {
    abaAtiva = nomeAba;

    // Esconde todos os paineis
    var paineis = document.querySelectorAll('.painel-aba');
    paineis.forEach(function(p) { p.style.display = 'none'; });

    // Mostra o painel selecionado
    var painel = document.getElementById('painel-' + nomeAba);
    if (painel) painel.style.display = 'block';

    // Atualiza botoes da sidebar
    var botoes = document.querySelectorAll('.sidebar .icon');
    botoes.forEach(function(b) { b.classList.remove('active'); });

    var botaoAtivo = document.querySelector('.sidebar .icon[data-aba="' + nomeAba + '"]');
    if (botaoAtivo) botaoAtivo.classList.add('active');

    // Carrega dados se necessario
    if (nomeAba === 'dashboard') carregarDashboard();
    if (nomeAba === 'frota') { carregarVeiculos(); carregarPedidos(); }
    if (nomeAba === 'rastreamento') { carregarMotoristas(); iniciarRastreamento(); }
    if (nomeAba === 'importacao') carregarPedidos();
}
