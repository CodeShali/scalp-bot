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
        const response = await fetch('/api/watchlist');
        const data = await response.json();
        updateWatchlistDisplay(data.watchlist);
    } catch (error) {
        console.error('Error loading watchlist:', error);
    }
}

function updateWatchlistDisplay(watchlist) {
    const container = document.getElementById('watchlistContainer');
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
    
    try {
        const response = await fetch('/api/watchlist/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            input.value = '';
            updateWatchlistDisplay(data.watchlist);
            alert(`✓ ${ticker} added to watchlist`);
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert('Failed to add ticker');
        console.error(error);
    }
}

async function removeTicker(ticker) {
    if (!confirm(`Remove ${ticker} from watchlist?`)) return;
    
    try {
        const response = await fetch('/api/watchlist/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            updateWatchlistDisplay(data.watchlist);
            alert(`✓ ${ticker} removed from watchlist`);
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert('Failed to remove ticker');
        console.error(error);
    }
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
                tickerInfo.innerHTML = `
                    <div style="text-align: center;">
                        <div class="ticker-badge">${ticker.symbol}</div>
                        <div style="margin-top: 12px; color: #666666; font-size: 12px;">
                            Score: ${ticker.score.toFixed(2)}
                        </div>
                    </div>
                `;
            } else {
                tickerInfo.innerHTML = '<div class="empty-state">AWAITING PRE-MARKET SCAN...</div>';
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
    fetch('/api/logs?lines=30')
        .then(response => response.json())
        .then(data => {
            const logsContainer = document.getElementById('logsContainer');
            logsContainer.innerHTML = data.map(line => {
                let className = 'log-line';
                if (line.includes('ERROR')) className += ' log-error';
                else if (line.includes('WARNING')) className += ' log-warning';
                else if (line.includes('INFO')) className += ' log-info';
                return `<div class="${className}">${line.trim()}</div>`;
            }).join('');
            logsContainer.scrollTop = logsContainer.scrollHeight;
        });
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
    
    // Start dashboard updates
    loadWatchlist();
    updateDashboard();
    setInterval(updateDashboard, 5000); // Refresh every 5 seconds
    setInterval(loadWatchlist, 30000); // Refresh watchlist every 30 seconds
});
