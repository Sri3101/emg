let rmsHistory = [];
let pollInterval = null;

function startTest() {
    const patient = document.getElementById('patientName').value.trim();
    if (!patient) { alert('Please enter patient name'); return; }

    fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient })
    })
    .then(() => {
        document.getElementById('inputSection').classList.add('hidden');
        document.getElementById('progressSection').classList.remove('hidden');
        rmsHistory = [];
        pollInterval = setInterval(pollStatus, 500);
    });
}

function pollStatus() {
    fetch('/api/status')
    .then(r => r.json())
    .then(data => {
        const pct = (data.progress / data.total) * 100;
        document.getElementById('progressBar').style.width = pct + '%';
        document.getElementById('progressText').textContent = `${data.progress} / ${data.total} readings`;
        document.getElementById('liveRms').textContent = data.latest_rms;

        rmsHistory.push(data.latest_rms);
        drawChart();

        if (data.result) {
            clearInterval(pollInterval);
            showResult(data.result);
        }
    });
}

function showResult(result) {
    document.getElementById('progressSection').classList.add('hidden');
    document.getElementById('resultSection').classList.remove('hidden');

    const card = document.getElementById('resultCard');
    document.getElementById('resultLabel').textContent = result.label;
    document.getElementById('resultRms').textContent   = result.avg_rms;
    document.getElementById('resultConfidence').textContent = result.confidence + '%';

    const rec = {
        'Normal':          '✅ Your muscle is healthy. Keep it up!',
        'Moderate Fatigue':'⚠️ Take a short break and hydrate.',
        'High Fatigue':    '🔴 Stop activity immediately. Rest is required.'
    };
    document.getElementById('recommendation').textContent = rec[result.label] || '';

    // Assign appropriate layout classes based on the result label
    const styleClass = result.label.toLowerCase().replace(' ', '-');
    card.className = `result-card glass-panel ${styleClass}`;
}

function resetTest() {
    rmsHistory = [];
    document.getElementById('inputSection').classList.remove('hidden');
    document.getElementById('progressSection').classList.add('hidden');
    document.getElementById('resultSection').classList.add('hidden');
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').textContent = '0 / 20 readings';
    document.getElementById('liveRms').textContent = '--';
    document.getElementById('patientName').value = '';
    
    // Clear the chart
    const canvas = document.getElementById('rmsChart');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
}

function drawChart() {
    const canvas = document.getElementById('rmsChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Ensure actual width properly maps to CSS set width
    const rect = canvas.getBoundingClientRect();
    if (canvas.width !== rect.width) canvas.width = rect.width;
    
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    if (rmsHistory.length < 2) return;

    const max = Math.max(...rmsHistory) + 200;
    let min = Math.min(...rmsHistory) - 200;
    if (min < 0) min = 0;

    // Create Gradient for the line
    const gradient = ctx.createLinearGradient(0, 0, w, 0);
    gradient.addColorStop(0, '#00e5ff');
    gradient.addColorStop(1, '#b000ff');

    ctx.strokeStyle = gradient;
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // Line Glow effect
    ctx.shadowBlur = 15;
    ctx.shadowColor = 'rgba(0, 229, 255, 0.6)';

    ctx.beginPath();
    rmsHistory.forEach((val, i) => {
        const x = (i / (rmsHistory.length - 1)) * w;
        // Map height
        const y = h - ((val - min) / (max - min)) * (h - 40) - 20; 
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // reset shadow
    ctx.shadowBlur = 0;
}