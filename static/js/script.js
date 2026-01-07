let priceChart = null;
let volumeChart = null;
let cachedMarketHistory = null;
let currentMA = 0;
let fullHistory = []; // Store ALL loaded history

// Mock Ticker List for Suggestion (Ideally fetched from backend/app context)
const availableTickers = [
    "XOM", "CVX", "COP", "EOG", "OXY", "SLB", "PXD", "MPC", "PSX", "VLO",
    "WMB", "HES", "KMI", "BKR", "HAL", "DVN", "TRGP", "FANG", "CTRA", "MRO"
];

document.addEventListener('DOMContentLoaded', () => {
    setupSearch('tickerInput', 'tickerSuggestions');
    setupSearch('landingInput', 'landingSuggestions');
});

function setupSearch(inputId, dropdownId) {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);

    if (!input || !dropdown) return;

    const renderSuggestions = () => {
        const val = input.value.toUpperCase();
        // Show all if empty, otherwise filter
        const matches = val ? availableTickers.filter(t => t.startsWith(val)) : availableTickers;

        if (matches.length === 0) {
            dropdown.style.display = 'none';
            return;
        }

        dropdown.innerHTML = '';
        matches.forEach(t => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.innerHTML = `<span>${t}</span>`;
            div.onclick = (e) => {
                e.stopPropagation(); // Prevent document click from closing immediately
                input.value = t;
                dropdown.style.display = 'none';
                runAnalysis(t);
            };
            dropdown.appendChild(div);
        });
        dropdown.style.display = 'block';
    };

    input.addEventListener('input', renderSuggestions);
    input.addEventListener('focus', renderSuggestions);
    input.addEventListener('click', renderSuggestions);

    // Close on click outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    // Also close on Enter
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') dropdown.style.display = 'none';
    });
}

function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

async function runAnalysis(tickerOverride) {
    let ticker = tickerOverride;
    if (!ticker) {
        // Fallback if called without arg (e.g. from header input enter)
        ticker = document.getElementById('tickerInput').value.toUpperCase();
    }
    ticker = ticker.toUpperCase();

    if (!ticker) return;

    // Switch to Dashboard View if not already
    document.getElementById('landingView').style.display = 'none';
    document.getElementById('dashboardView').style.display = 'flex';

    // Sync Header Input
    document.getElementById('tickerInput').value = ticker;

    showLoading(true);

    try {
        // Fetch MAX history for client-side filtering
        const [analysisRes, marketRes] = await Promise.all([
            fetch(`/api/analyze?ticker=${ticker}`),
            fetch(`/api/market-data?ticker=${ticker}&period=max`)
        ]);

        const analysis = await analysisRes.json();
        const market = await marketRes.json();

        showLoading(false);

        if (analysis.error) {
            alert(analysis.error);
            return;
        }

        fullHistory = market.history; // Store Max
        cachedMarketHistory = fullHistory; // Default view

        // Update UI info
        document.getElementById('tickerTitle').innerText = ticker;
        updateHeader(market);

        // Initial View (2Y default)
        setPeriod('2y', null, true); // true = skip fetch, just filter

        updateVolumeProfile(market.volume_profile); // Note: VP derived from server 'period' param. 
        // If we want VP to update with client time, we'd need to calc VP in JS or fetch VP separately. 
        // For now, let's keep VP static or re-fetch VP if critical. 
        // User asked for fast chart. Let's keep VP static based on 1Y or MAX server side for now to avoid complexity.

        updateScorecard(analysis);

    } catch (e) {
        showLoading(false);
        console.error(e);
        alert("Failed to fetch data.");
    }
}

function updateHeader(market) {
    document.getElementById('currentPrice').innerText = `$${market.current_price?.toFixed(2)}`;
    // Change logic...
    const change = 0; // Need live change or calc from history
    // ... same as before ... 

    // Metrics
    const html = `
        <div class="metric-box">
            <span class="metric-label">MARKET CAP</span>
            <span class="metric-val">$${(market.market_cap / 1e9).toFixed(1)}B</span>
        </div>
        <div class="metric-box">
            <span class="metric-label">DIV YIELD</span>
            <span class="metric-val">${(market.dividend_yield * 100).toFixed(2)}%</span>
        </div>
        <div class="metric-box">
            <span class="metric-label">P/E</span>
            <span class="metric-val">${market.trailing_pe?.toFixed(1)}x</span>
        </div>
    `;
    document.getElementById('marketMetrics').innerHTML = html;
}


function setPeriod(period, btnElement, initial = false) {
    // 1. Update Buttons
    if (btnElement) {
        document.querySelectorAll('#timeRangeGroup .btn-toggle').forEach(b => b.classList.remove('active'));
        btnElement.classList.add('active');
    } else if (initial) {
        // Set 2Y active by default logic (already set in HTML)
    }

    // 2. Filter Data (Client Side - Instant)
    if (!fullHistory || fullHistory.length === 0) return;

    const now = new Date();
    let cutoff = new Date();

    if (period === '1y') cutoff.setFullYear(now.getFullYear() - 1);
    if (period === '2y') cutoff.setFullYear(now.getFullYear() - 2);
    if (period === '5y') cutoff.setFullYear(now.getFullYear() - 5);
    if (period === 'max') cutoff = new Date(1900, 0, 1);

    cachedMarketHistory = fullHistory.filter(d => new Date(d.Date) >= cutoff);

    // 3. Update Chart
    updateChartFromCache();
}

function toggleMA(windowSize, btnElement) {
    currentMA = windowSize;
    document.querySelectorAll('#maGroup .btn-toggle').forEach(b => b.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');
    updateChartFromCache();
}

function updateChartFromCache() {
    if (!cachedMarketHistory) return;

    const labels = cachedMarketHistory.map(d => new Date(d.Date).toLocaleDateString());
    const prices = cachedMarketHistory.map(d => d.Close);

    const ctx = document.getElementById('priceChart').getContext('2d');
    if (priceChart) priceChart.destroy();

    // Gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(0, 255, 157, 0.15)');
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

    if (currentMA > 0) {
        const maData = calculateMovingAverage(cachedMarketHistory, currentMA);
        datasets.push({
            label: `MA ${currentMA}`,
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
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: {
                    display: true, // SHOW X AXIS
                    grid: { display: false },
                    ticks: { maxTicksLimit: 8, color: '#444' }
                },
                y: {
                    position: 'right',
                    grid: { color: '#222' },
                    ticks: { color: '#666' }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

// ... Keep updateVolumeProfile and updateScorecard as is (or ensure they exist) ...
function calculateMovingAverage(data, windowSize) {
    // ... same as before
    let ma = [];
    for (let i = 0; i < data.length; i++) {
        if (i < windowSize - 1) { ma.push(null); continue; }
        let sum = 0;
        for (let j = 0; j < windowSize; j++) sum += data[i - j].Close;
        ma.push(sum / windowSize);
    }
    return ma;
}

function updateVolumeProfile(profile) {
    if (!profile) return;
    const ctx = document.getElementById('volumeChart').getContext('2d');
    if (volumeChart) volumeChart.destroy();

    // Horizontal Bar: Y = Price, X = Volume
    const prices = profile.map(p => p.priceLevel.toFixed(2));
    const volumes = profile.map(p => p.volume);

    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: prices,
            datasets: [{
                data: volumes,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                hoverBackgroundColor: 'rgba(0, 255, 157, 0.4)',
                borderWidth: 0,
                barPercentage: 1.0,
                categoryPercentage: 1.0
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { display: false },
                y: {
                    display: true,
                    grid: { display: false },
                    ticks: { color: '#555', font: { size: 9 } }
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
        let color = '#666';
        if (item.status === 'OK') color = '#00ff9d';
        if (item.status === 'RED') color = '#ff3333';
        if (item.status === 'WATCH') color = '#ff9900';

        // Extract Reference
        let reference = '-';
        if (item.evidence && item.evidence.length > 0) {
            // Assuming first evidence has source or we just say "Found"
            // Usually evidence list contains text or Location. 
            // Let's try to show a snippet or just "10-K" if available
            // For now, let's just count them or show "See 10-K"
            reference = "10-K"; // Placeholder or parse item.evidence[0].source if exists
        }

        // Format Check Name
        let displayName = item.check_name.replace(/_/g, ' ');
        displayName = displayName.replace(/\b\w/g, l => l.toUpperCase());

        table.innerHTML += `
            <tr>
                <td>${displayName}</td>
                <td style="color: #fff;">${item.value !== null && typeof item.value === 'number' ? item.value.toFixed(2) : (item.value || '-')}</td>
                <td style="color: #888; font-size: 0.8rem;">${reference}</td>
                <td style="color: ${color}; font-weight: bold;">${item.status}</td>
            </tr>
        `;
    });

    document.getElementById('scoreText').innerText = `${score}/18`;
    document.getElementById('scoreFill').style.width = `${(score / 18) * 100}%`;
}
