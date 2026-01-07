let priceChart = null;
let volumeChart = null;
let cachedMarketHistory = null;
let currentPeriod = '2y';

async function runAnalysis() {
    const ticker = document.getElementById('tickerInput').value.toUpperCase();
    if (!ticker) return;

    // Reset UI
    document.getElementById('tickerBreadcrumb').innerText = ticker;
    document.getElementById('tickerTitle').innerText = ticker;

    // Fetch Data
    try {
        const [analysisRes, marketRes] = await Promise.all([
            fetch(`/api/analyze?ticker=${ticker}`),
            fetch(`/api/market-data?ticker=${ticker}&period=${currentPeriod}`)
        ]);

        const analysis = await analysisRes.json();
        const market = await marketRes.json();

        if (analysis.error) {
            alert(analysis.error);
            return;
        }

        cachedMarketHistory = market.history;

        // Update Header Stats
        updateHeader(ticker, market);

        // Update Charts
        updateChartFromCache();
        updateVolumeProfile(market.volume_profile);

        // Update Scorecard
        updateScorecard(analysis);

    } catch (e) {
        console.error(e);
        alert("Failed to fetch data.");
    }
}

function setPeriod(p) {
    currentPeriod = p;
    // Highlight button
    document.querySelectorAll('.time-filter').forEach(el => el.classList.remove('active'));
    event.target.classList.add('active');

    // Simple way: re-run analysis to fetch new period data
    // Or just re-fetch market data if we want to be efficient
    const ticker = document.getElementById('tickerInput').value;
    if (ticker) runAnalysis();
}

function updateHeader(ticker, market) {
    document.getElementById('currentPrice').innerText = `$${market.current_price?.toFixed(2)}`;
    // Calculate change if history exists
    if (market.history && market.history.length > 1) {
        const last = market.history[market.history.length - 1].Close;
        const prev = market.history[market.history.length - 2].Close;
        const change = last - prev;
        const pct = (change / prev) * 100;
        const sign = change >= 0 ? '+' : '';
        const color = change >= 0 ? '#00ff9d' : '#ff3333';

        const el = document.getElementById('priceChange');
        el.innerText = `${sign}${change.toFixed(2)} (${sign}${pct.toFixed(2)}%)`;
        el.style.color = color;
    }
}

function calculateMovingAverage(data, windowSize) {
    let ma = [];
    for (let i = 0; i < data.length; i++) {
        if (i < windowSize - 1) {
            ma.push(null);
            continue;
        }
        let sum = 0;
        for (let j = 0; j < windowSize; j++) {
            sum += data[i - j].Close;
        }
        ma.push(sum / windowSize);
    }
    return ma;
}

function updateChartFromCache() {
    if (!cachedMarketHistory) return;

    const maWindow = parseInt(document.getElementById('maSelect').value);
    const labels = cachedMarketHistory.map(d => new Date(d.Date).toLocaleDateString());
    const prices = cachedMarketHistory.map(d => d.Close);

    const ctx = document.getElementById('priceChart').getContext('2d');

    if (priceChart) priceChart.destroy();

    // Gradient Fill
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(0, 255, 157, 0.2)');
    gradient.addColorStop(1, 'rgba(0, 255, 157, 0.0)');

    const datasets = [{
        label: 'Price',
        data: prices,
        borderColor: '#00ff9d',
        backgroundColor: gradient,
        borderWidth: 2,
        fill: true,
        pointRadius: 0,
        tension: 0.1
    }];

    if (maWindow > 0) {
        const maData = calculateMovingAverage(cachedMarketHistory, maWindow);
        datasets.push({
            label: `MA ${maWindow}`,
            data: maData,
            borderColor: '#ff9900',
            borderWidth: 1.5,
            pointRadius: 0,
            borderDash: [5, 5],
            tension: 0.4
        });
    }

    priceChart = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    display: false,
                    grid: { display: false }
                },
                y: {
                    position: 'right',
                    grid: { color: '#222' },
                    ticks: { color: '#666' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1a1a1a',
                    titleColor: '#fff',
                    bodyColor: '#ccc',
                    borderColor: '#333',
                    borderWidth: 1
                }
            }
        }
    });
}

function updateVolumeProfile(profile) {
    if (!profile) return;
    const ctx = document.getElementById('volumeChart').getContext('2d');

    if (volumeChart) volumeChart.destroy();

    // Sort by price (descending usually for vertical, but this will be horizontal bar)
    // Actually standard bar char: X axis = Price Level, Y axis = Volume?
    // Or X axis = Volume, Y axis = Price? (Horizontal Bar).
    // Let's do Horizontal Bar: Y axis is price buckets.

    const prices = profile.map(p => p.priceLevel.toFixed(2));
    const volumes = profile.map(p => p.volume);

    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: prices,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderColor: 'rgba(255, 255, 255, 0.3)',
                borderWidth: 1,
                barPercentage: 1.0,
                categoryPercentage: 1.0
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { display: false },
                y: {
                    display: true,
                    grid: { display: false },
                    ticks: { color: '#555', font: { size: 10 } }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function updateScorecard(analysis) {
    const table = document.getElementById('scoreTable').querySelector('tbody');
    table.innerHTML = '';

    let score = 0;

    analysis.scorecard.forEach(item => {
        if (item.status === 'OK') score++;

        let statusClass = 'status-check-na';
        if (item.status === 'OK') statusClass = 'status-check-ok';
        if (item.status === 'RED') statusClass = 'status-check-red';
        if (item.status === 'WATCH') statusClass = 'status-check-watch';

        const row = `
            <tr>
                <td>${item.check_name}</td>
                <td style="color: #fff;">${item.value !== null && typeof item.value === 'number' ? item.value.toFixed(2) : (item.value || '-')}</td>
                <td class="${statusClass}">${item.status}</td>
            </tr>
        `;
        table.innerHTML += row;
    });

    document.getElementById('scoreText').innerText = `${score}/18`;
    document.getElementById('scoreFill').style.width = `${(score / 18) * 100}%`;
}
