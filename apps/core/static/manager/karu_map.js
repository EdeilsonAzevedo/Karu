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
                const geoJsonKey = props["Região de Saúde"];
                dataKey = GEOJSON_KEY_TO_API_KEY[geoJsonKey];
                value = mapData.microrregiao[dataKey]?.[metric];
            } else if (level === 'macrorregiao') {
                // --- CORREÇÃO: Busca o nome da Macro diretamente da feature ---
                // Ajuste 'NM_MACRO' se o nome da propriedade no seu novo GeoJSON for diferente (ex: 'Nome', 'Macroregiao')
                dataKey = props.NM_MACRO;
                value = mapData.macrorregiao[dataKey]?.[metric];
                // --- FIM DA CORREÇÃO ---
            }
        } catch (e) { value = undefined; }

        return {
            fillColor: getColor(value, w.KaruMap.currentBreaks),
            weight: 0.5, opacity: 1, color: '#666', fillOpacity: 0.8
        };
    }

    function onEachFeature(feature, layer, level, metric) {
        const props = feature.properties;
        let content = "Dados não disponíveis";
        let value = 0;
        let data = null; // Para armazenar os dados encontrados

        try {
            if (level === 'municipio') {
                const dataKey = props.NM_MUN.normalize('NFD').replace(/[\u0300-\u036f]/g, '').title();
                data = mapData.municipio[dataKey];
                value = data?.[metric] || 0;
                content = `<strong>Município:</strong> ${props.NM_MUN}<br>
                           <strong>${metric.title()}:</strong> ${value}<br>
                           (Total: ${data?.total || 0}, Crítico: ${data?.critico || 0}, Alerta: ${data?.alerta || 0}, Estável: ${data?.estavel || 0})`;
            } else if (level === 'microrregiao') {
                const geoJsonKey = props["Região de Saúde"] || "N/A";
                const dataKey = GEOJSON_KEY_TO_API_KEY[geoJsonKey] || `Região ${geoJsonKey}`;
                data = mapData.microrregiao[dataKey];
                value = data?.[metric] || 0;
                content = `<strong>Microrregião:</strong> ${dataKey}<br>
                           <strong>${metric.title()}:</strong> ${value}<br>
                           (Total: ${data?.total || 0}, Crítico: ${data?.critico || 0}, Alerta: ${data?.alerta || 0}, Estável: ${data?.estavel || 0})`;
            } else if (level === 'macrorregiao') {
                // --- CORREÇÃO: Simplifica tooltip para Macrorregião ---
                // Ajuste 'NM_MACRO' se o nome da propriedade for diferente
                const macroKey = props.NM_MACRO || 'N/A';
                data = mapData.macrorregiao[macroKey];
                value = data?.[metric] || 0;
                content = `<strong>Macrorregião:</strong> ${macroKey}<br>
                           <strong>${metric.title()}:</strong> ${value}<br>
                           (Total: ${data?.total || 0}, Crítico: ${data?.critico || 0}, Alerta: ${data?.alerta || 0}, Estável: ${data?.estavel || 0})`;
                // --- FIM DA CORREÇÃO ---
            }
        } catch (e) { /* console.warn */ }

        layer.bindTooltip(content);

        layer.on({
            mouseover: (e) => e.target.setStyle({ weight: 2, color: '#000', fillOpacity: 1 }),
            mouseout: (e) => currentLayer.resetStyle(e.target)
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

    const publicApi = {
        init: function (mapId, geoJsonUrls, countsUrl) {
            if (map) {
                console.warn("KaruMap WARN: Tentando inicializar um mapa já existente. Removendo o antigo.");
                map.remove();
            }
            map = L.map(mapId).setView([-9.57, -36.75], 8.5); // Centro de Alagoas

            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(map);


            const cacheBustedCountsUrl = new URL(countsUrl, window.location.origin);
            cacheBustedCountsUrl.searchParams.append('_', new Date().getTime());

            const p_municipio = fetch(geoJsonUrls.municipio).then(r => r.json());
            const p_micro = fetch(geoJsonUrls.microrregiao).then(r => r.json());
            const p_macro = fetch(geoJsonUrls.macrorregiao).then(r => r.json()); 
            const p_counts = fetch(cacheBustedCountsUrl).then(r => r.json());

            Promise.all([p_municipio, p_micro, p_macro, p_counts])
                .then(([gMunicipios, gMicrorregioes, gMacrorregioes, counts]) => {

                    geoJsonData.municipio = gMunicipios;
                    geoJsonData.microrregiao = gMicrorregioes;
                    geoJsonData.macrorregiao = gMacrorregioes;
                    mapData = counts;

                    console.log("KaruMap: Dados carregados.", mapData);

                    if (onLoadCallback) {
                        onLoadCallback();
                    }
                })
                .catch(err => { /* ... (tratamento de erro) ... */ });

            return publicApi;
        },

        onLoad: function (callback) {
            if (mapData && Object.keys(mapData).length > 0) {
                callback();
            } else {
                onLoadCallback = callback; 
            }
        },

        updateView: function (level, metric) {
            if (!map || !mapData || !geoJsonData || !geoJsonData[level]) {
                console.warn(`KaruMap WARN: Tentando atualizar view para '${level}' antes do mapa/dados carregarem. Nível existe em geoJsonData?`, !!geoJsonData[level]);
                return;
            }

            if (currentLayer) {
                map.removeLayer(currentLayer);
                currentLayer = null;
            }
            if (currentLegend) {
                map.removeControl(currentLegend);
                currentLegend = null;
            }

            currentPalette = METRIC_PALETTES[metric] || METRIC_PALETTES.total;
            const values = Object.values(mapData[level] || {}).map(d => d[metric]);
            const breaks = getBreaks(values);
            w.KaruMap.currentBreaks = breaks;

            try {
                currentLayer = L.geoJSON(geoJsonData[level], {
                    style: (feature) => styleFeature(feature, level, metric),
                    onEachFeature: (feature, layer) => onEachFeature(feature, layer, level, metric)
                });

                currentLayer.addTo(map);
            } catch (e) {
                console.error(`KaruMap ERRO: Falha ao criar ou adicionar camada GeoJSON para '${level}'`, e);
            }


            // --- Atualizar a Legenda ---
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