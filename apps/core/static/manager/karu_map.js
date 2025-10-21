// apps/core/static/core/js/karu_map.js
(function (w) {
    const KaruMap = {};
    let Lready = null;

    function injectLeafletAssetsOnce() {
        if (typeof L !== 'undefined') return Promise.resolve();
        if (Lready) return Lready;

        if (!document.getElementById('leaflet-css')) {
            const lcss = document.createElement('link');
            lcss.id = 'leaflet-css';
            lcss.rel = 'stylesheet';
            lcss.href = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css';
            document.head.appendChild(lcss);
        }
        if (!document.getElementById('leaflet-js')) {
            const ljs = document.createElement('script');
            ljs.id = 'leaflet-js';
            ljs.src = 'https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js';
            document.head.appendChild(ljs);
        }
        Lready = new Promise((res) => {
            const tick = () => (typeof L !== 'undefined' ? res() : setTimeout(tick, 50));
            tick();
        });
        return Lready;
    }

    const normalize = (s) =>
        (s || '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();

    function computeBreaks(values) {
        const arr = values.filter(v => v > 0).sort((a, b) => a - b);
        if (!arr.length) return [0, 1, 2, 3, 4];
        const q = (p) => arr[Math.floor((arr.length - 1) * p)];
        return [q(0.1) || 0, q(0.3) || 0, q(0.5) || 0, q(0.7) || 0, q(0.9) || 0];
    }

    function colorScale(v, br) {
        if (v <= br[0]) return '#e6f5ec';
        if (v <= br[1]) return '#bfe6d5';
        if (v <= br[2]) return '#8fd6bd';
        if (v <= br[3]) return '#5ac4a5';
        if (v <= br[4]) return '#2fb18f';
        return '#14967a';
    }

    KaruMap.create = async function create(containerId, opts) {
        const {
            geojsonUrl,
            countsUrl,
            category = 'acompanhamento',
            center = [-9.6567872, -36.69474085],
            zoom = 8,
        } = opts;

        await injectLeafletAssetsOnce();

        const map = L.map(containerId, { center, zoom });
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        // Carrega GeoJSON e contagens
        const [geojson, counts] = await Promise.all([
            fetch(geojsonUrl).then(r => r.json()),
            fetch(countsUrl).then(r => r.json()).catch(() => ({ acompanhamento: {}, alerta: {}, critico: {} })),
        ]);

        let layer = null;
        const getVal = (munName, cat) => {
            const dict = (counts && counts[cat]) || {};
            const direct = dict[munName];
            if (direct != null) return Number(direct || 0);
            const foundKey = Object.keys(dict).find(k => normalize(k) === normalize(munName));
            return Number((foundKey ? dict[foundKey] : 0) || 0);
        };

        function colorScaleFixed(v) {
            if (v === 0) return '#e5e7eb';     // 0 -> cinza
            if (v <= 5) return '#80d6eaff';     // 1–5
            if (v <= 10) return '#7ad287ff';     // 6–10
            if (v <= 20) return '#5ac4a5';     // 11–20
            if (v <= 50) return '#e3dd6fff';     // 21–50
            return '#14967a';                  // 51+
        }

        function draw(cat) {
            if (layer) { map.removeLayer(layer); layer = null; }
            const values = (geojson.features || []).map(f => getVal(f.properties.NM_MUN || f.properties.name, cat));
            const br = computeBreaks(values);

            layer = L.geoJSON(geojson, {
                style: (f) => {
                    const name = f.properties.NM_MUN || f.properties.name;
                    const v = getVal(name, cat);
                    const fill = colorScaleFixed(v);
                    return { color: '#000', weight: 0.5, opacity: 1, fillOpacity: 0.7, fillColor: fill };
                },
                onEachFeature: (f, lyr) => {
                    const name = f.properties.NM_MUN || f.properties.name;
                    const v = getVal(name, cat);
                    lyr.bindTooltip(
                        `<div class="foliumtooltip"><table>
                    <tr><th>Município:</th><td>${name}</td></tr>
                    <tr><th>RN acompanhados</th><td>${v}</td></tr>
                </table></div>`,
                        { sticky: true, className: 'foliumtooltip' }
                    );
                    lyr.bindPopup(
                        `<div class="foliumpopup"><table>
                    <tr><th>Município:</th><td>${name}</td></tr>
                    <tr><th>RN acompanhados</th><td>${v}</td></tr>
                </table></div>`,
                        { className: 'foliumpopup' }
                    );
                }
            }).addTo(map);
        }

        draw(category);

        return {
            setCategory: (cat) => draw(cat),
            getMap: () => map,
            reloadCounts: async () => {
                const fresh = await fetch(countsUrl).then(r => r.json());
                Object.assign(counts, fresh);
                draw(category);
            }
        };
    };

    w.KaruMap = KaruMap;
}(window));
