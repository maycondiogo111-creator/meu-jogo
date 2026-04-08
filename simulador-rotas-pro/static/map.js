/**
 * map.js — Gerenciamento do mapa Leaflet
 *
 * Responsabilidade UNICA: tudo relacionado ao mapa.
 * - Inicializar o mapa
 * - Adicionar/remover marcadores
 * - Desenhar/limpar rotas
 * - Capturar cliques no mapa
 * - Mostrar motoristas em tempo real
 *
 * Para mudar o provedor de mapas (ex: Google Maps), mexa APENAS aqui.
 */

// -- Inicializacao do mapa ----------------------------------------------------

var map = L.map('map').setView([-23.45, -46.53], 11);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);


// -- Captura cliques no mapa --------------------------------------------------

map.on('click', function(e) {
    var lat = e.latlng.lat;
    var lng = e.latlng.lng;

    pontos.push([lat, lng]);

    var marker = L.marker([lat, lng]).addTo(map);
    markers.push(marker);
});


// -- Funcoes de manipulacao do mapa -------------------------------------------

/**
 * Desenha a polilinha da rota no mapa.
 * @param {Array} coords - Array de [lat, lng]
 */
function desenharRota(coords) {
    if (!coords || coords.length < 2) {
        alert("Rota invalida ou sem coordenadas suficientes.");
        return;
    }

    // Remove rota anterior se existir
    if (linhaRota) {
        map.removeLayer(linhaRota);
    }

    linhaRota = L.polyline(coords, {
        color:  'blue',
        weight: 4
    }).addTo(map);

    // Ajusta zoom para mostrar rota completa
    map.fitBounds(linhaRota.getBounds());
}

/**
 * Remove todos os marcadores e a rota do mapa.
 * Reseta o estado global dos pontos.
 */
function mapLimparMapa() {
    pontos = [];

    markers.forEach(function(m) { map.removeLayer(m); });
    markers = [];

    if (linhaRota) {
        map.removeLayer(linhaRota);
        linhaRota = null;
    }

    // Limpa rotas de frota
    limparRotasFrota();
}


/**
 * Desenha rotas multi-veiculos no mapa com cores diferentes.
 * @param {Array} rotas - Array de objetos de rota por veiculo
 */
var coresFrota = ['#e74c3c', '#2ecc71', '#3498db', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#e91e63'];

function desenharRotasFrota(rotas) {
    limparRotasFrota();

    rotas.forEach(function(rota, index) {
        var cor = coresFrota[index % coresFrota.length];
        var pontosRota = rota.pontos_otimizados;

        if (pontosRota && pontosRota.length >= 2) {
            var linha = L.polyline(pontosRota, {
                color: cor,
                weight: 4,
                opacity: 0.8,
                dashArray: index > 0 ? '10, 5' : null
            }).addTo(map);

            linha.bindPopup(
                '<strong>' + rota.veiculo.nome + '</strong><br>' +
                'Paradas: ' + rota.num_paradas + '<br>' +
                'Distancia: ' + rota.distancia_km + ' km<br>' +
                'Custo: R$ ' + rota.custo
            );

            linhasRotaFrota.push(linha);

            // Marcadores para cada parada
            pontosRota.forEach(function(p, pi) {
                if (pi === 0) return; // skip deposito
                var m = L.circleMarker([p[0], p[1]], {
                    radius: 6,
                    color: cor,
                    fillColor: cor,
                    fillOpacity: 0.8
                }).addTo(map);
                m.bindPopup('Parada ' + pi + ' - ' + rota.veiculo.nome);
                linhasRotaFrota.push(m);
            });
        }
    });

    // Ajusta zoom para mostrar todas as rotas
    if (linhasRotaFrota.length > 0) {
        var group = L.featureGroup(linhasRotaFrota);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function limparRotasFrota() {
    linhasRotaFrota.forEach(function(l) { map.removeLayer(l); });
    linhasRotaFrota = [];
}


/**
 * Feature 2: Atualiza marcadores de motoristas no mapa.
 * @param {Array} motoristas - Array de { id, nome, posicao: { lat, lng } }
 */
function atualizarMotoristasMapa(motoristas) {
    // Remove marcadores antigos de motoristas que nao estao mais na lista
    var idsAtivos = motoristas.map(function(m) { return m.id; });
    Object.keys(marcadoresMotoristas).forEach(function(id) {
        if (idsAtivos.indexOf(parseInt(id)) === -1) {
            map.removeLayer(marcadoresMotoristas[id]);
            delete marcadoresMotoristas[id];
        }
    });

    motoristas.forEach(function(m) {
        var pos = [m.posicao.lat, m.posicao.lng];

        if (marcadoresMotoristas[m.id]) {
            // Atualiza posicao existente
            marcadoresMotoristas[m.id].setLatLng(pos);
        } else {
            // Cria novo marcador de motorista
            var icone = L.divIcon({
                className: 'motorista-marker',
                html: '<div style="background:#e74c3c;color:#fff;border-radius:50%;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:bold;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.3);">' +
                      '<i class="fas fa-truck" style="font-size:14px;"></i></div>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });

            marcadoresMotoristas[m.id] = L.marker(pos, { icon: icone }).addTo(map);
        }

        marcadoresMotoristas[m.id].bindPopup(
            '<strong>' + m.nome + '</strong><br>' +
            'Lat: ' + m.posicao.lat.toFixed(5) + '<br>' +
            'Lng: ' + m.posicao.lng.toFixed(5)
        );
    });
}


function mapCarregarRota(rota) {
    mapLimparMapa();
    desenharRota(rota.rota);

    document.getElementById("distancia").innerText = rota.distancia_km + " km";
    document.getElementById("tempo").innerText = rota.duracao_min + " min";
    document.getElementById("custo").innerText = "R$ " + rota.custo;

    var lista = document.getElementById("instrucoes");
    lista.innerHTML = "";

    if (rota.instrucoes) {
        rota.instrucoes.forEach(function(inst, i) {
            var item = document.createElement("p");
            item.innerText = (i + 1) + ". " + inst;
            lista.appendChild(item);
        });
    }

    window.ultimaRota = rota;
}

window.mapCarregarRota = mapCarregarRota;
