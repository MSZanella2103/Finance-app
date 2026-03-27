const ctx = document.getElementById('graficoInvestimentos');

if (ctx && window.investimentosData) {

    const labels = investimentosData.length
        ? investimentosData.map(i => i.nome)
        : ['Sem dados'];

    const valores = investimentosData.length
        ? investimentosData.map(i => i.valor_atual)
        : [0];

    const cores = gerarCores(labels.length);

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: valores,
                backgroundColor: cores,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    labels: {
                        color: '#e2e8f0'
                    }
                }
            }
        }
    });
}

// REUTILIZA SUA FUNÇÃO
function gerarCores(qtd) {
    if (!qtd || qtd <= 0) return ['#3b82f6'];

    const cores = [];
    for (let i = 0; i < qtd; i++) {
        const hue = (360 / qtd) * i;
        cores.push(`hsl(${hue}, 65%, 55%)`);
    }
    return cores;
}