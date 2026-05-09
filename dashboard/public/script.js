// Global chart instances
let dailyChartInstance = null;
let methodChartInstance = null;

// Configure Chart.js defaults for Dark Mode
Chart.defaults.color = '#9ca3af';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 17, 21, 0.9)';
Chart.defaults.plugins.tooltip.titleColor = '#f3f4f6';
Chart.defaults.plugins.tooltip.bodyColor = '#e5e7eb';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.displayColors = true;

document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    
    // Handle resize to fix chart scaling issues
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            // No need to fetch data again, just re-render if instances exist
            if (dailyChartInstance || methodChartInstance) {
                fetchStats(); 
            }
        }, 250);
    });
});

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        updateHeroStats(data);
        renderTable(data.recent_activity);
        renderDailyChart(data.daily_stats);
        renderMethodChart(data.method_distribution);
        
        document.getElementById('bot-status').querySelector('.status-text').textContent = 'Online / Sync OK';
        
    } catch (error) {
        console.error("Error fetching stats:", error);
        document.getElementById('bot-status').classList.add('error');
        document.getElementById('bot-status').querySelector('.pulse-dot').style.backgroundColor = '#ef4444';
        document.getElementById('bot-status').querySelector('.status-text').textContent = 'API Error';
    }
}

function updateHeroStats(data) {
    document.getElementById('stat-total-downloads').textContent = data.total_downloads;
    document.getElementById('stat-total-downloads').classList.remove('loading');
    
    document.getElementById('stat-total-size').textContent = `${data.total_size_gb} GB`;
    document.getElementById('stat-total-size').classList.remove('loading');
    
    if (data.recent_activity && data.recent_activity.length > 0) {
        const lastDate = new Date(data.recent_activity[0].delivered_at);
        // Format relative time (e.g., "Hace 2 horas") - simplified here
        document.getElementById('stat-last-active').textContent = lastDate.toLocaleDateString('es-ES', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } else {
        document.getElementById('stat-last-active').textContent = 'N/A';
    }
    document.getElementById('stat-last-active').classList.remove('loading');
}

function getMethodBadge(method) {
    const map = {
        'telegram': { icon: 'ph-telegram-logo', class: 'telegram', label: 'Telegram' },
        'r2': { icon: 'ph-cloud', class: 'r2', label: 'R2 Cloud' },
        'usb': { icon: 'ph-usb', class: 'usb', label: 'USB' }
    };
    
    const m = method ? method.toLowerCase() : 'unknown';
    const info = map[m] || { icon: 'ph-file', class: '', label: method || 'Unknown' };
    
    return `<span class="badge ${info.class}"><i class="ph-fill ${info.icon}"></i> ${info.label}</span>`;
}

function renderTable(recentData) {
    const tbody = document.getElementById('recent-tbody');
    tbody.innerHTML = '';
    
    if (!recentData || recentData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No hay descargas registradas.</td></tr>';
        return;
    }
    
    recentData.forEach(row => {
        const date = new Date(row.delivered_at);
        const dateStr = date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        
        const tr = document.createElement('tr');
        tr.classList.add('table-row');
        tr.innerHTML = `
            <td class="td-manga"><strong>${row.manga}</strong></td>
            <td class="td-volume">Vol. ${row.volume}</td>
            <td class="td-lang">${row.lang.toUpperCase()}</td>
            <td class="td-size">${row.size_mb ? row.size_mb.toFixed(1) + ' MB' : '-'}</td>
            <td class="td-method">${getMethodBadge(row.method)}</td>
            <td class="td-date">${dateStr}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderDailyChart(dailyData) {
    const ctx = document.getElementById('dailyChart').getContext('2d');
    
    if (dailyChartInstance) {
        dailyChartInstance.destroy();
    }
    
    if (!dailyData || dailyData.length === 0) {
        return;
    }
    
    const labels = dailyData.map(d => {
        const date = new Date(d.day);
        return date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' });
    });
    
    const values = dailyData.map(d => d.count);
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.8)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.1)');

    dailyChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Tomos Entregados',
                data: values,
                backgroundColor: gradient,
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1,
                borderRadius: 4,
                hoverBackgroundColor: 'rgba(59, 130, 246, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderMethodChart(methodData) {
    const ctx = document.getElementById('methodChart').getContext('2d');
    
    if (methodChartInstance) {
        methodChartInstance.destroy();
    }
    
    if (!methodData || methodData.length === 0) {
        return;
    }
    
    const labels = methodData.map(d => (d.method || 'Unknown').toUpperCase());
    const values = methodData.map(d => d.count);
    
    // Colors matching the badges
    const bgColors = methodData.map(d => {
        const m = (d.method || '').toLowerCase();
        if (m === 'telegram') return 'rgba(56, 189, 248, 0.8)';
        if (m === 'r2') return 'rgba(249, 115, 22, 0.8)';
        if (m === 'usb') return 'rgba(168, 85, 247, 0.8)';
        return 'rgba(156, 163, 175, 0.8)';
    });

    const borderColors = bgColors.map(color => color.replace('0.8)', '1)'));

    methodChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: bgColors,
                borderColor: 'rgba(25, 28, 36, 1)',
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { 
                        padding: 20, 
                        usePointStyle: true,
                        font: { size: 11 }
                    }
                }
            },
            layout: {
                padding: 10
            }
        }
    });
}
