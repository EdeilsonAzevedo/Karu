(function (w) {
    "use strict";

    // --- Variáveis Globais do Módulo ---
    let map;
    let geoJsonLayers = {}; // Armazena as camadas L.geoJSON (municipio, micro, macro)
    let mapData = {};       // Armazena os dados de contagem da API
    let geoJsonData = {};   // Armazena os dados GeoJSON carregados
    let currentLegend;      // Referência para a legenda atual
    let currentLayer;       // Referência para a camada ativa
    let onLoadCallback;     // Callback para ser chamado após o carregamento
    let currentPalette = []; // Paleta de cores ativa (será definida no updateView)

    const GEOJSON_KEY_TO_API_KEY = {
        "1ª": "1ª Região de Saúde",
        "2ª": "2ª Região de Saúde",
        "3ª": "3ª Região de Saúde",
        "4ª": "4ª Região de Saúde",
        "5ª": "5ª Região de Saúde",
        "6ª": "6ª Região de Saúde",
        "7ª": "7ª Região de Saúde",
        "8ª": "8ª Região de Saúde",
        "9ª": "9ª Região de Saúde",
        "10ª": "10ª Região de Saúde",
    };

    // --- Configurações de Cor ---
    // Paletas estilo Matplotlib para cada métrica
    const METRIC_PALETTES = {
        // 'Blues' (para Total)
        'total': ['#F7FBFF', '#DEEBF7', '#C6DBEF', '#9ECAE1', '#6BAED6', '#4292C6', '#2171B5', '#08519C', '#08306B'],
        // 'Reds' (para Crítico)
        'critico': ['#FFF5F0', '#FEE0D2', '#FCBBA1', '#FC9272', '#FB6A4A', '#EF3B2C', '#CB181D', '#A50F15', '#67000D'],
        // 'Oranges' (para Alerta)
        'alerta': ['#FFF5EB', '#FEE6CE', '#FDD0A2', '#FDAE6B', '#FD8D3C', '#F16913', '#D94801', '#A63603', '#7F2704'],
         // 'Greens' (para Estável)
        'estavel': ['#F7FCF5', '#E5F5E0', '#C7E9C0', '#A1D99B', '#74C476', '#41AB5D', '#238B45', '#006D2C', '#00441B']
    };
    
    // Função para obter a cor com base no valor
    // Usa a 'currentPalette' definida no updateView
    function getColor(value, breaks) {
        if (value === undefined || value === null) return '#CCCCCC'; // Cor para dados ausentes
        if (value === 0) return '#FFFFFF'; // Cor para zero (ex: borda leve)

        for (let i = breaks.length - 1; i >= 0; i--) {
            if (value >= breaks[i]) {
                // Usa a paleta de cores ATUAL
                return currentPalette[i];
            }
        }
        // Usa a paleta de cores ATUAL
        return currentPalette[0]; // Cor para valores muito baixos
    }

    // Função para calcular "quebras" (breaks) para a legenda
    // Usa 'currentPalette.length' para definir o número de quebras
    function getBreaks(values) {
        if (values.length === 0) return [1, 2, 3, 4, 5, 6, 7, 8, 9];

        const sorted = values.filter(v => v > 0).sort((a, b) => a - b);
        if (sorted.length === 0) return [1];

        const breaks = [];
        // Usa o tamanho da paleta ATUAL
        const numQuantiles = Math.min(sorted.length, currentPalette.length);

        for (let i = 1; i <= numQuantiles; i++) {
            const index = Math.floor(i * (sorted.length - 1) / numQuantiles);
            const value = sorted[index];
            if (breaks.length === 0 || breaks[breaks.length - 1] < value) {
                breaks.push(value);
            }
        }

        // Garante que o primeiro break seja 1 se houver valores
        if (breaks.length > 0 && breaks[0] > 1) {
            breaks.unshift(1);
        } else if (breaks.length === 0) {
            breaks.push(1);
        }

        // Garante que o número de breaks corresponda à paleta ATUAL
        while (breaks.length < currentPalette.length) {
            breaks.push(breaks[breaks.length - 1] * 2 || 1);
        }
        while (breaks.length > currentPalette.length) {
            breaks.pop();
        }

        return breaks;
    }

    // --- Funções do Mapa ---

    // Função de estilo para as camadas GeoJSON
    function styleFeature(feature, level, metric) {
        const props = feature.properties;
        let value;
        let dataKey;

        try {
            if (level === 'municipio') {
                dataKey = props.NM_MUN.normalize('NFD').replace(/[\u0300-\u036f]/g, '').title();
                value = mapData.municipio[dataKey]?.[metric];
            } else if (level === 'microrregiao') {
                // 1. Pega a chave do GeoJSON (ex: "1ª")
                const geoJsonKey = props["Região de Saúde"];
                // 2. Converte para a chave da API (ex: "1ª Região de Saúde")
                dataKey = GEOJSON_KEY_TO_API_KEY[geoJsonKey];
                value = mapData.microrregiao[dataKey]?.[metric];
            } else if (level === 'macrorregiao') {
                // 1. Pega a chave do GeoJSON (ex: "1ª")
                const geoJsonKey = props["Região de Saúde"];
                // 2. Converte para a chave da API (ex: "1ª Região de Saúde")
                const microKey = GEOJSON_KEY_TO_API_KEY[geoJsonKey];
                // 3. Busca a macro correspondente
                const macroKey = w.KaruMap.mappings.MACRORREGIAO_POR_MICRORREGIAO[microKey];
                value = mapData.macrorregiao[macroKey]?.[metric];
            }
        } catch (e) {
            // console.warn("Erro ao buscar dados para feature:", props, e);
            value = undefined;
        }

        return {
            // 'w.KaruMap.currentBreaks' é calculado em updateView
            // 'getColor' agora usa 'currentPalette' (global do módulo)
            fillColor: getColor(value, w.KaruMap.currentBreaks), 
            weight: 0.5,
            opacity: 1,
            color: '#666',
            fillOpacity: 0.8
        };
    }

    function onEachFeature(feature, layer, level, metric) {
        const props = feature.properties;
        let content = "Dados não disponíveis";
        let value = 0;

        try {
            if (level === 'municipio') {
                const dataKey = props.NM_MUN.normalize('NFD').replace(/[\u0300-\u036f]/g, '').title();
                const data = mapData.municipio[dataKey];
                value = data?.[metric] || 0;
                content = `<strong>Município:</strong> ${props.NM_MUN}<br>
                           <strong>${metric.title()}:</strong> ${value}<br>
                           (Total: ${data?.total || 0}, Crítico: ${data?.critico || 0}, Alerta: ${data?.alerta || 0}, Estável: ${data?.estavel || 0})`; // <-- CORRIGIDO
            } else if (level === 'microrregiao') {
                const geoJsonKey = props["Região de Saúde"] || "N/A";
                const dataKey = GEOJSON_KEY_TO_API_KEY[geoJsonKey] || `Região ${geoJsonKey}`;
                const data = mapData.microrregiao[dataKey];
                value = data?.[metric] || 0;
                content = `<strong>Microrregião:</strong> ${dataKey}<br>
                           <strong>${metric.title()}:</strong> ${value}<br>
                           (Total: ${data?.total || 0}, Crítico: ${data?.critico || 0}, Alerta: ${data?.alerta || 0}, Estável: ${data?.estavel || 0})`; // <-- CORRIGIDO
            } else if (level === 'macrorregiao') {
                const geoJsonKey = props["Região de Saúde"] || "N/A";
                const microKey = GEOJSON_KEY_TO_API_KEY[geoJsonKey] || `Região ${geoJsonKey}`;
                const macroKey = w.KaruMap.mappings.MACRORREGIAO_POR_MICRORREGIAO[microKey];
                const data = mapData.macrorregiao[macroKey];
                value = data?.[metric] || 0;
                content = `<strong>Macrorregião:</strong> ${macroKey || 'N/A'}<br>
                           <strong>Microrregião:</strong> ${microKey} (parte da ${macroKey || 'N/A'})<br>
                           <strong>${metric.title()}:</strong> ${value} (total da Macrorregião)<br>
                           (Total: ${data?.total || 0}, Crítico: ${data?.critico || 0}, Alerta: ${data?.alerta || 0}, Estável: ${data?.estavel || 0})`; // <-- CORRIGIDO
            }
        } catch (e) {
            // console.warn("Erro ao criar tooltip:", props, e);
        }

        layer.bindTooltip(content);

        // Highlight ao passar o mouse
        layer.on({
            mouseover: (e) => {
                e.target.setStyle({ weight: 2, color: '#000', fillOpacity: 1 });
            },
            mouseout: (e) => {
                // Redefine o estilo para o original da camada
                currentLayer.resetStyle(e.target);
            }
        });
    }

    // Atualiza a legenda
    function updateLegend(breaks, metric) {
        if (currentLegend) {
            map.removeControl(currentLegend);
        }

        currentLegend = L.control({ position: 'bottomright' });

        currentLegend.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'info map-legend');
            const metricTitle = metric.charAt(0).toUpperCase() + metric.slice(1);

            div.innerHTML = `<strong>Pacientes (${metricTitle})</strong><br>`;

            // Adiciona a cor para 0
            div.innerHTML += '<i style="background: #FFFFFF; border: 1px solid #EEE;"></i> 0<br>';

            // Loop pelas quebras
            for (let i = 0; i < breaks.length; i++) {
                const from = breaks[i];
                const to = breaks[i + 1];
                // Usa a paleta de cores ATUAL
                const color = currentPalette[i];

                div.innerHTML +=
                    `<i style="background:${color}"></i> ` +
                    from + (to ? `&ndash;${to - 1}` : '+');
                div.innerHTML += '<br>';
            }

            div.innerHTML += '<i style="background: #CCCCCC"></i> N/A';
            return div;
        };

        currentLegend.addTo(map);
    }

    // --- API Pública (o que será exposto em window.KaruMap) ---
    const publicApi = {

        // Compartilha os mapeamentos para uso no onEachFeature
        mappings: {
            // Precisamos de uma versão JS dos mapeamentos do Python
            // Isso é usado para o nível "Macrorregião"
            MACRORREGIAO_POR_MICRORREGIAO: {
                '1ª Região de Saúde': 'Macrorregião I',
                '2ª Região de Saúde': 'Macrorregião I',
                '3ª Região de Saúde': 'Macrorregião I',
                '4ª Região de Saúde': 'Macrorregião I',
                '5ª Região de Saúde': 'Macrorregião I',
                '10ª Região de Saúde': 'Macrorregião II',
                '6ª Região de Saúde': 'Macrorregião I',
                '7ª Região de Saúde': 'Macrorregião II',
                '8ª Região de Saúde': 'Macrorregião II',
                '9ª Região de Saúde': 'Macrorregião II',
            }
        },

        // Função de inicialização
        init: function (mapId, geoJsonUrls, countsUrl) {
            // 1. Inicializa o mapa Leaflet
            map = L.map(mapId).setView([-9.57, -36.75], 8.5); // Centro de Alagoas

            // 2. Adiciona o "tile layer" (mapa base)
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(map);

            // 3. Carrega todos os dados (GeoJSON e Contagens)
            const p1 = fetch(geoJsonUrls.municipio).then(r => r.json());
            const p2 = fetch(geoJsonUrls.microrregiao).then(r => r.json());
            const p3 = fetch(countsUrl).then(r => r.json());

            Promise.all([p1, p2, p3]).then(([gMunicipios, gMicrorregioes, counts]) => {

                // Armazena os dados carregados
                geoJsonData.municipio = gMunicipios;
                geoJsonData.microrregiao = gMicrorregioes;
                geoJsonData.macrorregiao = gMicrorregioes; // Reutiliza o mesmo GeoJSON
                mapData = counts;

                console.log("KaruMap: Dados carregados.", mapData);

                // Chama o callback de 'onLoad' se ele foi definido
                if (onLoadCallback) {
                    onLoadCallback();
                }
            }).catch(err => {
                console.error("KaruMap: Falha ao carregar dados do mapa.", err);
                alert("Erro ao carregar os dados do mapa. Verifique o console.");
            });

            // Retorna o handle para o script da página
            return publicApi;
        },

        // Função para ser chamada quando os dados estiverem prontos
        onLoad: function (callback) {
            if (mapData && Object.keys(mapData).length > 0) {
                callback(); // Se os dados já carregaram
            } else {
                onLoadCallback = callback; // Se ainda não carregaram
            }
        },

        // Função principal: Atualiza a visualização do mapa
        updateView: function (level, metric) {
            if (!mapData || !geoJsonData[level]) {
                console.warn(`KaruMap: Tentando atualizar view para '${level}' antes dos dados carregarem.`);
                return;
            }

            // Limpa a camada anterior
            if (currentLayer) {
                map.removeLayer(currentLayer);
            }
            // Limpa a legenda anterior
            if (currentLegend) {
                map.removeControl(currentLegend);
            }

            // --- 1. Define a Paleta de Cores ---
            // Define a paleta ATUAL baseada na métrica selecionada
            currentPalette = METRIC_PALETTES[metric] || METRIC_PALETTES.total;

            // --- 2. Calcular Quebras e Cores ---
            // Pega todos os valores para a métrica e nível atuais
            const values = Object.values(mapData[level] || {}).map(d => d[metric]);
            // getBreaks() agora usa 'currentPalette'
            const breaks = getBreaks(values); 
            w.KaruMap.currentBreaks = breaks; // Armazena globalmente para a função 'styleFeature'

            // --- 3. Criar e Adicionar a Camada GeoJSON ---
            currentLayer = L.geoJSON(geoJsonData[level], {
                // Define o estilo para CADA feature
                // styleFeature -> getColor -> usa 'currentPalette'
                style: (feature) => styleFeature(feature, level, metric),
                // Adiciona interações (tooltips, etc.) para CADA feature
                onEachFeature: (feature, layer) => onEachFeature(feature, layer, level, metric)
            });

            currentLayer.addTo(map);

            // --- 4. Atualizar a Legenda ---
            // updateLegend() agora usa 'currentPalette'
            updateLegend(breaks, metric);
        }
    };

    // --- Helper para normalizar strings (como title()) ---
    String.prototype.title = function () {
        return this.toLowerCase().split(' ').map(function (word) {
            return word.charAt(0).toUpperCase() + word.slice(1);
        }).join(' ');
    };

    // Expõe a API pública no objeto window
    w.KaruMap = publicApi;

})(window);