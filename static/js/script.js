let priceChart = null;
let cachedMarketHistory = null;

async function runAnalysis() {
    const ticker = document.getElementById('tickerInput').value.toUpperCase();
    if (!ticker) return;

    document.getElementById('tickerDisplay').innerText = `ANALYZING ${ticker}...`;

    // Check if time range changed, we might need new fetch?
    // For now, let's fetch 'max' or '5y' once and filter client side, or just re-fetch.
    // Let's grab the Time Select value.
    const period = document.getElementById('timeSelect').value;

    try {
        const [analysisRes, marketRes] = await Promise.all([
            fetch(`/api/analyze?ticker=${ticker}`),
            fetch(`/api/market-data?ticker=${ticker}&period=${period}`)
        ]);

        const analysis = await analysisRes.json();
        const market = await marketRes.json();

        if (analysis.error) {
            alert(analysis.error);
            return;
        }

        cachedMarketHistory = market.history;

        // Update Header
        updateHeader(ticker, market);

        // Update Chart
        updateChartFromCache();

        // Update Scorecard
        updateScorecard(analysis);

    } catch (e) {
        console.error(e);
        alert("Failed to fetch data.");
    }
}

function updateHeader(ticker, market) {
    document.getElementById('tickerDisplay').innerText = `${ticker}`;
    const html = `
        <div class="metric-box">PRICE: <span class="status-ok">$${market.current_price?.toFixed(2)}</span></div>
        <div class="metric-box">CAP: <span class="status-ok">$${(market.market_cap / 1e9).toFixed(1)}B</span></div>
        <div class="metric-box">P/E: <span class="status-ok">${market.trailing_pe?.toFixed(1)}x</span></div>
        <div class="metric-box">DIV: <span class="status-ok">${(market.dividend_yield * 100).toFixed(2)}%</span></div>
        <!-- EBITDA Display -->
        <div class="metric-box">EBITDA (TTM): <span class="status-ok">${market.ebitda ? '$' + (market.ebitda / 1e9).toFixed(1) + 'B' : 'N/A'}</span></div>
    `;
    document.getElementById('marketMetrics').innerHTML = html;
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

    // Data is already filtered by period from server, but we can re-fetch if needed.
    // Ideally the server handles 'period'.

    const labels = cachedMarketHistory.map(d => new Date(d.Date).toLocaleDateString());
    const prices = cachedMarketHistory.map(d => d.Close);

    const datasets = [{
        label: 'Close Price',
        data: prices,
        borderColor: '#00ff00',
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.1
    }];

    if (maWindow > 0) {
        const maData = calculateMovingAverage(cachedMarketHistory, maWindow);
        datasets.push({
            label: `MA ${maWindow}`,
            data: maData,
            borderColor: '#ff9900', // Orange for MA
            borderWidth: 1,
            pointRadius: 0,
            borderDash: [5, 5],
            tension: 0.1
        });
    }

    const ctx = document.getElementById('priceChart').getContext('2d');

    if (priceChart) priceChart.destroy();

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { display: true, ticks: { display: false }, grid: { display: false } }, // Hide x axis labels for cleaner look?
                y: {
                    grid: { color: '#222' },
                    ticks: { color: '#666' }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#888', font: { family: 'Courier New' } }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
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
        if (item.status === 'NA') statusClass = 'status-check-na';


        const row = `
            <tr>
                <td>${item.check_name}</td>
                <td style="color: #fff;">${item.value !== null && typeof item.value === 'number' ? item.value.toFixed(2) : item.value}</td>
                <td class="${statusClass}">${item.status}</td>
                <td style="color: #888;">${item.interpretation}</td>
            </tr>
        `;
        table.innerHTML += row;
    });

    document.getElementById('scoreText').innerText = `${score}/18`;
    document.getElementById('scoreFill').style.width = `${(score / 18) * 100}%`;
}
