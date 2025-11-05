// Portfolio Chart
let portfolioChart = null;
let portfolioData = {
    '1D': [],
    '1W': [],
    '1M': [],
    '3M': [],
    'ALL': []
};
let currentRange = '1D';

function initPortfolioChart() {
    const ctx = document.getElementById('portfolioChart');
    if (!ctx) {
        console.error('Chart canvas not found!');
        return;
    }
    
    console.log('Creating chart...');
    portfolioChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Portfolio Value',
                data: [],
                borderColor: '#e0e0e0',
                backgroundColor: 'rgba(224, 224, 224, 0.15)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 5,
                pointHoverBackgroundColor: '#ffffff',
                pointHoverBorderColor: '#e0e0e0',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(10, 10, 10, 0.95)',
                    titleColor: '#e0e0e0',
                    bodyColor: '#ffffff',
                    borderColor: '#e0e0e0',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false,
                    titleFont: { family: 'JetBrains Mono', size: 12, weight: 'bold' },
                    bodyFont: { family: 'JetBrains Mono', size: 12 },
                    callbacks: {
                        title: (ctx) => ctx[0].label,
                        label: (ctx) => formatCurrency(ctx.parsed.y)
                    }
                }
            },
            scales: {
                x: {
                    grid: { 
                        display: true,
                        color: 'rgba(224, 224, 224, 0.1)',
                        drawBorder: false 
                    },
                    ticks: {
                        color: '#999999',
                        font: { family: 'JetBrains Mono', size: 10 },
                        maxRotation: 0,
                        maxTicksLimit: 8
                    }
                },
                y: {
                    grid: { 
                        display: true,
                        color: 'rgba(224, 224, 224, 0.15)',
                        drawBorder: false 
                    },
                    ticks: {
                        color: '#999999',
                        font: { family: 'JetBrains Mono', size: 10 },
                        maxTicksLimit: 6,
                        callback: (val) => '$' + (val/1000).toFixed(1) + 'k'
                    }
                }
            },
            layout: {
                padding: { left: 5, right: 5, top: 10, bottom: 5 }
            }
        }
    });
    console.log('Chart created successfully!');
}

function updatePortfolioChart(data) {
    if (!portfolioChart) {
        console.error('Chart not initialized!');
        return;
    }
    
    const range = currentRange;
    let chartData = portfolioData[range] || [];
    
    console.log(`Updating chart with ${chartData.length} data points for ${range}`);
    
    if (chartData.length === 0) {
        console.warn('No data to display');
        return;
    }
    
    // Update chart
    portfolioChart.data.labels = chartData.map(d => d.time);
    portfolioChart.data.datasets[0].data = chartData.map(d => d.value);
    portfolioChart.update();
    
    console.log('Chart updated successfully');
    
    // Update stats
    if (chartData.length > 0) {
        const currentValue = chartData[chartData.length - 1].value;
        const startValue = chartData[0].value;
        const change = currentValue - startValue;
        const changePercent = (change / startValue) * 100;
        
        console.log(`Stats: Value=${currentValue}, Change=${change}, Return=${changePercent}%`);
        
        document.getElementById('chartPortfolioValue').textContent = formatCurrency(currentValue);
        document.getElementById('chartDailyPnl').textContent = formatCurrency(change);
        document.getElementById('chartDailyPnl').className = 'stat-value ' + (change >= 0 ? 'positive' : 'negative');
        document.getElementById('chartTotalReturn').textContent = formatPercent(changePercent);
        document.getElementById('chartTotalReturn').className = 'stat-value ' + (changePercent >= 0 ? 'positive' : 'negative');
    }
}

async function loadPortfolioData(timeframe) {
    try {
        console.log(`Loading portfolio data for ${timeframe}...`);
        const response = await fetch(`/api/portfolio/history?timeframe=${timeframe}`);
        const result = await response.json();
        
        if (result.error) {
            console.error('Error loading portfolio data:', result.error);
            return;
        }
        
        console.log(`Loaded ${result.data?.length || 0} data points for ${timeframe}`);
        
        // Store data
        portfolioData[timeframe] = result.data || [];
        
        // Update chart if this is the current timeframe
        if (timeframe === currentRange) {
            console.log('Updating chart...');
            updatePortfolioChart();
        }
    } catch (error) {
        console.error('Failed to load portfolio data:', error);
    }
}

// Helper functions
function formatCurrency(value) {
    if (value === undefined || value === null) return '$0.00';
    return '$' + parseFloat(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatPercent(value) {
    if (value === undefined || value === null) return '0.00%';
    const formatted = parseFloat(value).toFixed(2);
    const sign = value >= 0 ? '+' : '';
    return sign + formatted + '%';
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// Watchlist management
async function loadWatchlist() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        // Get watchlist from bot config
        const watchlist = data.config?.watchlist?.symbols || [];
        updateWatchlistDisplay(watchlist);
    } catch (error) {
        console.error('Error loading watchlist:', error);
        updateWatchlistDisplay([]);
    }
}

function updateWatchlistDisplay(watchlist) {
    const container = document.getElementById('watchlistContainer');
    if (!container) {
        console.warn('Watchlist container not found');
        return;
    }
    
    if (!watchlist || watchlist.length === 0) {
        container.innerHTML = '<div class="empty-state">No tickers in watchlist</div>';
        return;
    }
    
    container.innerHTML = watchlist.map(ticker => `
        <div class="ticker-tag">
            <span>${ticker}</span>
            <button class="remove-btn" onclick="removeTicker('${ticker}')">✕</button>
        </div>
    `).join('');
}

async function addTicker() {
    const input = document.getElementById('newTicker');
    const ticker = input.value.trim().toUpperCase();
    
    if (!ticker) {
        alert('Please enter a ticker symbol');
        return;
    }
    
    if (!/^[A-Z]{1,5}$/.test(ticker)) {
        alert('Invalid ticker symbol. Use 1-5 letters only.');
        return;
    }
    
    try {
        const response = await fetch('/api/watchlist/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ticker: ticker })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            input.value = '';
            loadWatchlist(); // Reload watchlist
            showNotification(`✅ Added ${ticker} to watchlist`, 'success');
        } else {
            showNotification(`❌ ${data.error || 'Failed to add ticker'}`, 'error');
        }
    } catch (error) {
        console.error('Error adding ticker:', error);
        showNotification('❌ Failed to add ticker', 'error');
    }
}

async function removeTicker(ticker) {
    if (!confirm(`Remove ${ticker} from watchlist?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/watchlist/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ticker: ticker })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            loadWatchlist(); // Reload watchlist
            showNotification(`✅ Removed ${ticker} from watchlist`, 'success');
        } else {
            showNotification(`❌ ${data.error || 'Failed to remove ticker'}`, 'error');
        }
    } catch (error) {
        console.error('Error removing ticker:', error);
        showNotification('❌ Failed to remove ticker', 'error');
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#00ff41' : type === 'error' ? '#ff0000' : '#00aaff'};
        color: #000;
        border-radius: 5px;
        font-weight: bold;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Update dashboard data
function updateDashboard() {
    // Fetch main status
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            // Bot status
            const statusEl = document.getElementById('botStatus');
            if (data.bot.paused) {
                statusEl.textContent = '⏸ Paused';
                statusEl.className = 'status-badge status-stopped';
                document.getElementById('pauseBtn').style.display = 'none';
                document.getElementById('resumeBtn').style.display = 'block';
            } else if (data.bot.running) {
                statusEl.textContent = data.bot.circuit_open ? '⚠ Circuit Open' : '● Online';
                statusEl.className = 'status-badge status-running';
                document.getElementById('pauseBtn').style.display = 'block';
                document.getElementById('resumeBtn').style.display = 'none';
            } else {
                statusEl.textContent = '○ Offline';
                statusEl.className = 'status-badge status-stopped';
            }
            
            // Account info
            if (data.account && !data.account.error) {
                document.getElementById('cash').textContent = formatCurrency(data.account.cash);
                document.getElementById('buyingPower').textContent = formatCurrency(data.account.buying_power);
                document.getElementById('portfolioValue').textContent = formatCurrency(data.account.portfolio_value);
            }
            
            // Ticker of day
            const tickerInfo = document.getElementById('tickerInfo');
            if (data.ticker_of_day) {
                const ticker = data.ticker_of_day;
                const metrics = ticker.metrics || {};
                const selectionTime = ticker.selection_time ? new Date(ticker.selection_time).toLocaleString() : 'N/A';
                
                // Generate reasoning based on metrics
                const reasoning = generateSelectionReasoning(ticker.symbol, metrics, ticker.score);
                
                let metricsHtml = '';
                if (Object.keys(metrics).length > 0) {
                    metricsHtml = '<div class="ticker-metrics">';
                    for (const [key, value] of Object.entries(metrics)) {
                        const label = key.replace(/_/g, ' ').toUpperCase();
                        const formattedValue = typeof value === 'number' ? value.toFixed(2) : value;
                        
                        // Color code based on value
                        let valueClass = 'ticker-metric-value';
                        if (value >= 75) valueClass += ' metric-excellent';
                        else if (value >= 60) valueClass += ' metric-good';
                        else if (value >= 40) valueClass += ' metric-neutral';
                        else valueClass += ' metric-weak';
                        
                        metricsHtml += `
                            <div class="ticker-metric">
                                <div class="ticker-metric-label">${label}</div>
                                <div class="${valueClass}">${formattedValue}</div>
                            </div>
                        `;
                    }
                    metricsHtml += '</div>';
                }
                
                tickerInfo.innerHTML = `
                    <div class="ticker-selection">
                        <div class="ticker-selection-header">
                            <div class="ticker-symbol">${ticker.symbol}</div>
                            <div class="ticker-score">Score: ${ticker.score.toFixed(3)}</div>
                        </div>
                        <div class="selection-reasoning">
                            <div class="reasoning-title">📊 Why ${ticker.symbol} was selected:</div>
                            <div class="reasoning-content">${reasoning}</div>
                        </div>
                        ${metricsHtml}
                        <div class="selection-time">Selected: ${selectionTime}</div>
                    </div>
                `;
            } else {
                tickerInfo.innerHTML = '<div class="empty-state">AWAITING PRE-MARKET SCAN...</div>';
            }
            
            // Display all active tickers
            const activeTickersList = document.getElementById('activeTickersList');
            if (data.active_tickers && data.active_tickers.length > 1) {
                activeTickersList.innerHTML = `
                    <div style="background: rgba(0, 217, 255, 0.05); padding: 15px; border-radius: 4px; border: 1px solid #00d9ff;">
                        <div style="font-size: 12px; color: #00d9ff; margin-bottom: 10px; font-weight: 700;">
                            MONITORING ${data.active_tickers.length} TICKERS:
                        </div>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                            ${data.active_tickers.map(t => {
                                const emoji = t.rank === 1 ? '🥇' : t.rank === 2 ? '🥈' : '🥉';
                                const color = t.rank === 1 ? '#00ff41' : t.rank === 2 ? '#00d9ff' : '#ffa500';
                                return `
                                    <div style="background: rgba(0, 0, 0, 0.3); padding: 10px 15px; border-left: 3px solid ${color}; border-radius: 4px;">
                                        <div style="font-size: 10px; color: #666;">RANK #${t.rank}</div>
                                        <div style="font-size: 16px; font-weight: 700; color: ${color};">${emoji} ${t.symbol}</div>
                                        <div style="font-size: 11px; color: #999;">Score: ${t.score.toFixed(3)}</div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
            } else {
                activeTickersList.innerHTML = '';
            }
            
            // Current position
            const positionInfo = document.getElementById('positionInfo');
            if (data.position) {
                const pos = data.position;
                const pnlClass = pos.pnl_pct >= 0 ? 'positive' : 'negative';
                positionInfo.innerHTML = `
                    <div class="stat">
                        <span class="stat-label">Symbol</span>
                        <span class="stat-value">${pos.ticker} ${pos.direction.toUpperCase()}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Quantity</span>
                        <span class="stat-value">${pos.contracts}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Entry Price</span>
                        <span class="stat-value">${formatCurrency(pos.entry_price)}</span>
                    </div>
                    ${pos.current_price ? `
                    <div class="stat">
                        <span class="stat-label">Current Price</span>
                        <span class="stat-value">${formatCurrency(pos.current_price)}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Profit/Loss</span>
                        <span class="stat-value ${pnlClass}">${formatPercent(pos.pnl_pct)}</span>
                    </div>
                    ` : ''}
                `;
            } else {
                positionInfo.innerHTML = '<div class="empty-state">NO POSITION DETECTED</div>';
            }
            
            // Today's trades
            if (data.today_trades && data.today_trades.length > 0) {
                const tbody = document.getElementById('tradesBody');
                tbody.innerHTML = data.today_trades.map(trade => {
                    const pnlClass = trade.pnl_pct >= 0 ? 'positive' : 'negative';
                    return `
                        <tr>
                            <td>${formatTime(trade.timestamp)}</td>
                            <td>${trade.ticker}</td>
                            <td>${trade.direction.toUpperCase()}</td>
                            <td>${trade.contracts}</td>
                            <td>${formatCurrency(trade.entry_price)}</td>
                            <td>${formatCurrency(trade.exit_price)}</td>
                            <td class="${pnlClass}">${formatPercent(trade.pnl_pct)}</td>
                            <td>${trade.exit_reason}</td>
                        </tr>
                    `;
                }).join('');
            }
            
            // Update timestamp
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        });
    
    // Fetch performance stats
    fetch('/api/performance')
        .then(response => response.json())
        .then(data => {
            if (data.total_trades !== undefined) {
                document.getElementById('totalTrades').textContent = data.total_trades;
                document.getElementById('winRate').textContent = data.win_rate ? data.win_rate.toFixed(1) + '%' : '0%';
                
                const avgPnlEl = document.getElementById('avgPnl');
                avgPnlEl.textContent = formatPercent(data.avg_pnl);
                avgPnlEl.className = 'stat-value ' + (data.avg_pnl >= 0 ? 'positive' : 'negative');
                
                const totalPnlEl = document.getElementById('totalPnl');
                totalPnlEl.textContent = formatPercent(data.total_pnl);
                totalPnlEl.className = 'stat-value ' + (data.total_pnl >= 0 ? 'positive' : 'negative');
            }
        });
    
    // Fetch market status
    fetch('/api/market_status')
        .then(response => response.json())
        .then(data => {
            const status = document.getElementById('marketStatus').querySelector('.status-value');
            status.textContent = data.market_open ? '🟢 OPEN' : '🔴 CLOSED';
            status.style.color = data.market_open ? '#00ff41' : '#ff0055';
        });
    
    // Fetch daily limits
    fetch('/api/daily_limits')
        .then(response => response.json())
        .then(data => {
            document.getElementById('tradesCount').textContent = `${data.trades_today}/${data.max_trades}`;
            const pnlEl = document.getElementById('dailyPnl');
            pnlEl.textContent = formatPercent(data.daily_pnl_pct);
            pnlEl.className = data.daily_pnl_pct >= 0 ? 'positive' : 'negative';
        });
    
    // Fetch logs
    if (window.logsPaused) return;
    
    fetch('/api/logs?lines=100')
        .then(response => response.json())
        .then(data => {
            window.allLogs = data;
            renderLogs();
            updateLogStats();
        });
}

function renderLogs() {
    const logsContainer = document.getElementById('logsContainer');
    const searchTerm = document.getElementById('logSearch')?.value.toLowerCase() || '';
    const filterLevel = document.getElementById('logFilter')?.value || 'all';
    
    let logs = window.allLogs || [];
    
    // Apply filters
    logs = logs.filter(line => {
        if (filterLevel !== 'all' && !line.includes(`[${filterLevel}]`)) return false;
        if (searchTerm && !line.toLowerCase().includes(searchTerm)) return false;
        return true;
    });
    
    if (logs.length === 0) {
        logsContainer.innerHTML = '<div class="log-line"><span class="log-message">No logs match filters</span></div>';
        return;
    }
    
    logsContainer.innerHTML = logs.map(line => {
        const match = line.match(/^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(.+)$/);
        if (!match) return `<div class="log-line"><span class="log-message">${line}</span></div>`;
        
        const [, timestamp, level, message] = match;
        const time = timestamp.split(' ')[1];
        const icon = {INFO: 'ℹ️', WARNING: '⚠️', ERROR: '❌', DEBUG: '🔧'}[level] || '📝';
        const highlighted = searchTerm ? message.replace(new RegExp(`(${searchTerm})`, 'gi'), '<mark>$1</mark>') : message;
        
        return `
            <div class="log-line">
                <span class="log-timestamp">${time}</span>
                <span class="log-level log-level-${level}">${icon} ${level}</span>
                <span class="log-message">${highlighted}</span>
            </div>
        `;
    }).join('');
    
    if (!searchTerm && filterLevel === 'all') {
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }
}

function updateLogStats() {
    const logs = window.allLogs || [];
    const stats = {total: logs.length, INFO: 0, WARNING: 0, ERROR: 0};
    
    logs.forEach(line => {
        if (line.includes('[INFO]')) stats.INFO++;
        else if (line.includes('[WARNING]')) stats.WARNING++;
        else if (line.includes('[ERROR]')) stats.ERROR++;
    });
    
    document.getElementById('totalLogs').textContent = stats.total;
    document.getElementById('infoCount').textContent = stats.INFO;
    document.getElementById('warningCount').textContent = stats.WARNING;
    document.getElementById('errorCount').textContent = stats.ERROR;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Set up watchlist controls
    const addTickerBtn = document.getElementById('addTickerBtn');
    const newTickerInput = document.getElementById('newTicker');
    
    if (addTickerBtn && newTickerInput) {
        addTickerBtn.addEventListener('click', addTicker);
        newTickerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') addTicker();
        });
    }
    
    // Set up bot controls
    document.getElementById('pauseBtn').addEventListener('click', async () => {
        try {
            const response = await fetch('/api/controls/pause', { method: 'POST' });
            const data = await response.json();
            if (response.ok) {
                document.getElementById('pauseBtn').style.display = 'none';
                document.getElementById('resumeBtn').style.display = 'block';
                alert('Trading paused');
            }
        } catch (error) {
            alert('Error pausing bot');
        }
    });
    
    document.getElementById('resumeBtn').addEventListener('click', async () => {
        try {
            const response = await fetch('/api/controls/resume', { method: 'POST' });
            const data = await response.json();
            if (response.ok) {
                document.getElementById('pauseBtn').style.display = 'block';
                document.getElementById('resumeBtn').style.display = 'none';
                alert('Trading resumed');
            }
        } catch (error) {
            alert('Error resuming bot');
        }
    });
    
    document.getElementById('forceCloseBtn').addEventListener('click', async () => {
        if (!confirm('Are you sure you want to force close the current position?')) return;
        
        try {
            const response = await fetch('/api/controls/force_close', { method: 'POST' });
            const data = await response.json();
            alert(data.message);
        } catch (error) {
            alert('Error closing position');
        }
    });
    
    // Log controls
    window.logsPaused = false;
    window.allLogs = [];
    
    document.getElementById('logSearch')?.addEventListener('input', renderLogs);
    document.getElementById('logFilter')?.addEventListener('change', renderLogs);
    
    document.getElementById('pauseLogs')?.addEventListener('click', () => {
        window.logsPaused = !window.logsPaused;
        const btn = document.getElementById('pauseLogs');
        btn.textContent = window.logsPaused ? '▶️ Resume' : '⏸️ Pause';
    });
    
    document.getElementById('clearLogs')?.addEventListener('click', () => {
        window.allLogs = [];
        renderLogs();
        updateLogStats();
    });
    
    document.getElementById('downloadLogs')?.addEventListener('click', () => {
        const blob = new Blob([window.allLogs.join('\n')], {type: 'text/plain'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tara-logs-${new Date().toISOString().slice(0,10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    });
    
    // Settings modal handlers
    const modal = document.getElementById('settingsModal');
    const settingsBtn = document.getElementById('settingsBtn');
    const cancelBtn = document.getElementById('cancelSettings');
    const saveBtn = document.getElementById('saveSettings');
    const closeBtn = document.querySelector('.close');
    
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            modal.style.display = 'block';
            loadSettings();
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    if (saveBtn) {
        saveBtn.addEventListener('click', saveSettings);
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    loadWatchlist();
    updateDashboard();
    setInterval(updateDashboard, 5000); // Refresh every 5 seconds
    setInterval(loadWatchlist, 30000); // Refresh watchlist every 30 seconds
});

// Settings functions
async function loadSettings() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.config) {
            throw new Error('Config not found in response');
        }
        
        const trading = data.config.trading || {};
        const signals = data.config.signals || {};
        
        // Trading parameters (convert decimals to percentages)
        // Use ?? instead of || to handle 0 values correctly
        document.getElementById('profitTarget').value = ((trading.profit_target_pct ?? 0.15) * 100).toFixed(0);
        document.getElementById('stopLoss').value = ((trading.stop_loss_pct ?? 0.07) * 100).toFixed(0);
        document.getElementById('riskPerTrade').value = ((trading.max_risk_pct ?? 0.01) * 100).toFixed(0);
        document.getElementById('positionTimeout').value = trading.timeout_seconds ?? 300;
        
        // Safety limits (convert decimals to percentages)
        document.getElementById('maxDailyLoss').value = ((trading.max_daily_loss_pct ?? 0.03) * 100).toFixed(0);
        document.getElementById('maxTrades').value = trading.max_trades_per_day ?? 5;
        
        // Signal detection
        document.getElementById('rsiCallMin').value = signals.rsi_call_min ?? 60;
        document.getElementById('rsiPutMax').value = signals.rsi_put_max ?? 40;
        
        console.log('Settings loaded successfully');
    } catch (error) {
        console.error('Error loading settings:', error);
        alert('Failed to load settings: ' + error.message);
    }
}

async function saveSettings() {
    const settings = {
        trading: {
            profit_target_pct: parseFloat(document.getElementById('profitTarget').value) / 100,
            stop_loss_pct: parseFloat(document.getElementById('stopLoss').value) / 100,
            max_risk_pct: parseFloat(document.getElementById('riskPerTrade').value) / 100,
            timeout_seconds: parseInt(document.getElementById('positionTimeout').value),
            max_daily_loss_pct: parseFloat(document.getElementById('maxDailyLoss').value) / 100,
            max_trades_per_day: parseInt(document.getElementById('maxTrades').value)
        },
        signals: {
            rsi_call_min: parseFloat(document.getElementById('rsiCallMin').value),
            rsi_put_max: parseFloat(document.getElementById('rsiPutMax').value)
        }
    };
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ Settings saved successfully!');
            document.getElementById('settingsModal').style.display = 'none';
        } else {
            alert('❌ Failed to save settings: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('❌ Failed to save settings');
    }
}

// Generate intelligent reasoning for ticker selection
function generateSelectionReasoning(symbol, metrics, score) {
    const reasons = [];
    const weights = {
        premarket_volume: 0.25,
        gap_percent: 0.20,
        news_sentiment: 0.15,
        iv_rank: 0.15,
        atr: 0.10,
        option_open_interest: 0.10,
        news_volume: 0.05
    };
    
    // Analyze each metric and generate insights
    const pmVol = metrics.premarket_volume || 0;
    const gap = metrics.gap_percent || 0;
    const newsSent = metrics.news_sentiment || 50;
    const newsVol = metrics.news_volume || 0;
    const ivRank = metrics.iv_rank || 0;
    const atr = metrics.atr || 0;
    const optOI = metrics.option_open_interest || 0;
    
    // Pre-market volume analysis
    if (pmVol >= 75) {
        reasons.push(`<strong>🔥 Exceptional pre-market activity</strong> - Volume is significantly above average, indicating strong institutional interest and potential for momentum.`);
    } else if (pmVol >= 60) {
        reasons.push(`<strong>📈 Strong pre-market volume</strong> - Above-average trading activity suggests increased attention from traders.`);
    } else if (pmVol < 40) {
        reasons.push(`<strong>⚠️ Lower pre-market volume</strong> - Other factors compensated for lighter early trading.`);
    }
    
    // Gap analysis
    if (gap >= 75) {
        reasons.push(`<strong>🚀 Significant price gap</strong> - Large gap from previous close indicates a major catalyst or news event driving price action.`);
    } else if (gap >= 60) {
        reasons.push(`<strong>📊 Notable price gap</strong> - Moderate gap suggests positive momentum or market reaction.`);
    }
    
    // News sentiment analysis (most important for context)
    if (newsSent >= 75) {
        reasons.push(`<strong>📰 Very positive news sentiment</strong> - Recent news articles are overwhelmingly bullish. AI analysis detected strong positive catalysts such as earnings beats, upgrades, or major announcements.`);
    } else if (newsSent >= 60) {
        reasons.push(`<strong>📰 Positive news sentiment</strong> - News coverage is favorable with bullish undertones detected by AI analysis.`);
    } else if (newsSent <= 40 && newsSent > 0) {
        reasons.push(`<strong>📰 Negative news sentiment</strong> - Despite bearish news, other technical factors made this the best available option.`);
    } else if (newsVol > 60) {
        reasons.push(`<strong>📢 High news volume</strong> - Significant media attention (${Math.round(newsVol / 5)} articles) indicates this stock is trending.`);
    }
    
    // IV Rank analysis
    if (ivRank >= 70) {
        reasons.push(`<strong>💹 High implied volatility</strong> - Options are pricing in significant movement, creating favorable conditions for option scalping.`);
    } else if (ivRank >= 55) {
        reasons.push(`<strong>💹 Elevated volatility</strong> - Options show increased premium, good for potential quick gains.`);
    }
    
    // Option OI analysis
    if (optOI >= 70) {
        reasons.push(`<strong>🎯 Strong options activity</strong> - High open interest in 0DTE/1DTE options indicates active options market with good liquidity.`);
    } else if (optOI >= 55) {
        reasons.push(`<strong>🎯 Decent options liquidity</strong> - Sufficient open interest for smooth entry and exit.`);
    }
    
    // ATR analysis
    if (atr >= 70) {
        reasons.push(`<strong>⚡ High volatility range</strong> - Recent price swings suggest potential for quick scalping opportunities.`);
    }
    
    // Overall score interpretation
    if (score >= 0.75) {
        reasons.unshift(`<strong>🏆 Top-tier opportunity</strong> - This ticker scored exceptionally high (${(score * 100).toFixed(1)}/100) across multiple weighted factors.`);
    } else if (score >= 0.60) {
        reasons.unshift(`<strong>✅ Strong candidate</strong> - Solid score (${(score * 100).toFixed(1)}/100) with multiple favorable indicators.`);
    } else {
        reasons.unshift(`<strong>📊 Best available option</strong> - While not perfect (${(score * 100).toFixed(1)}/100), this was the highest-scoring ticker in today's watchlist.`);
    }
    
    // Add weighted contribution insight
    const topMetrics = Object.entries(metrics)
        .map(([key, value]) => ({ key, value, weight: weights[key] || 0, contribution: value * (weights[key] || 0) }))
        .sort((a, b) => b.contribution - a.contribution)
        .slice(0, 3);
    
    const topContributors = topMetrics.map(m => m.key.replace(/_/g, ' ')).join(', ');
    reasons.push(`<strong>🎯 Key drivers:</strong> ${topContributors} contributed most to the selection score.`);
    
    return reasons.join('<br><br>');
}

// Chart range button handlers
document.querySelectorAll('.chart-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // Remove active class from all buttons
        document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
        // Add active class to clicked button
        this.classList.add('active');
        // Update current range
        const newRange = this.dataset.range;
        currentRange = newRange;
        // Load data for this timeframe if not already loaded
        if (!portfolioData[newRange] || portfolioData[newRange].length === 0) {
            loadPortfolioData(newRange);
        } else {
            updatePortfolioChart();
        }
    });
});

// About popup
document.getElementById('aboutBtn')?.addEventListener('click', () => {
    document.getElementById('aboutPopup').style.display = 'flex';
});

document.getElementById('closeAbout')?.addEventListener('click', () => {
    document.getElementById('aboutPopup').style.display = 'none';
});

document.getElementById('aboutPopup')?.addEventListener('click', (e) => {
    if (e.target.id === 'aboutPopup') {
        document.getElementById('aboutPopup').style.display = 'none';
    }
});

// Theme toggle (Dark/Light)
let isDarkMode = true;

document.getElementById('bgToggleSwitch')?.addEventListener('change', (e) => {
    isDarkMode = e.target.checked;
    const matrixCanvas = document.getElementById('matrix-bg');
    const body = document.body;
    const container = document.querySelector('.container');
    
    if (isDarkMode) {
        // Dark theme with matrix
        matrixCanvas.style.display = 'block';
        body.style.background = '#000000';
        body.style.color = '#c0c0c0';
        container.style.color = '#c0c0c0';
        
        // Update all cards
        document.querySelectorAll('.card').forEach(card => {
            card.style.background = '#0a0a0a';
            card.style.borderColor = '#e0e0e0';
            card.style.color = '#c0c0c0';
        });
        
        // Update header
        document.querySelector('.header').style.background = '#0a0a0a';
        document.querySelector('.header').style.borderColor = '#e0e0e0';
        
    } else {
        // Light theme - white background, black text
        matrixCanvas.style.display = 'none';
        body.style.background = '#ffffff';
        body.style.color = '#000000';
        container.style.color = '#000000';
        
        // Update all cards to light theme
        document.querySelectorAll('.card').forEach(card => {
            card.style.background = '#f8f9fa';
            card.style.borderColor = '#dee2e6';
            card.style.color = '#000000';
        });
        
        // Update card titles
        document.querySelectorAll('.card-title').forEach(title => {
            title.style.color = '#212529';
            title.style.borderColor = '#dee2e6';
        });
        
        // Update stat labels
        document.querySelectorAll('.stat-label').forEach(label => {
            label.style.color = '#6c757d';
        });
        
        // Update stat values
        document.querySelectorAll('.stat-value').forEach(value => {
            if (!value.classList.contains('positive') && !value.classList.contains('negative')) {
                value.style.color = '#212529';
            }
        });
        
        // Update header
        document.querySelector('.header').style.background = '#f8f9fa';
        document.querySelector('.header').style.borderColor = '#dee2e6';
        document.querySelector('.header h1').style.color = '#212529';
        document.querySelector('.subtitle').style.color = '#6c757d';
    }
    
    // Save preference
    localStorage.setItem('isDarkMode', isDarkMode);
});

// Load saved preference
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('isDarkMode');
    if (saved !== null) {
        isDarkMode = saved === 'true';
        const toggle = document.getElementById('bgToggleSwitch');
        if (toggle) {
            toggle.checked = isDarkMode;
            if (!isDarkMode) {
                toggle.dispatchEvent(new Event('change'));
            }
        }
    }
});

// Initialize chart on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing portfolio chart...');
    initPortfolioChart();
    console.log('Chart initialized, loading data...');
    // Load initial data
    loadPortfolioData('1D');
    // Refresh every 30 seconds
    setInterval(() => loadPortfolioData(currentRange), 30000);
});
