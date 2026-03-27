// =========================
// FUNÇÃO DE CORES
// =========================
function gerarCores(qtd) {
    if (!qtd || qtd <= 0) return ['#3b82f6'];

    const cores = [];
    for (let i = 0; i < qtd; i++) {
        const hue = (360 / qtd) * i;
        cores.push(`hsl(${hue}, 65%, 55%)`);
    }
    return cores;
}

// =========================
// CATEGORIAS
// =========================
const labels = (window.categorias && categorias.length)
    ? categorias.map(c => c.nome)
    : ['Sem dados'];

const valores = (window.categorias && categorias.length)
    ? categorias.map(c => c.total)
    : [0];

const coresCategorias = gerarCores(labels.length);

// =========================
// GRÁFICO CATEGORIAS
// =========================
const ctxCategoria = document.getElementById('graficoCategoria');

if (ctxCategoria) {
    new Chart(ctxCategoria, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: valores,
                backgroundColor: coresCategorias,
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

// =========================
// EVOLUÇÃO MENSAL
// =========================
const meses = (window.dadosMensais || []).map(d => d.mes);
const valoresMensais = (window.dadosMensais || []).map(d => d.total);

const ctxLinha = document.getElementById('graficoLinha');

if (ctxLinha) {
    new Chart(ctxLinha, {
        type: 'line',
        data: {
            labels: meses,
            datasets: [{
                label: 'Gastos',
                data: valoresMensais,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59,130,246,0.2)',
                fill: true,
                tension: 0.4,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#e2e8f0'
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

// =========================
// GANHOS POR CATEGORIA
// =========================
const ganhosLabels = (window.ganhosCategoria && ganhosCategoria.length)
    ? ganhosCategoria.map(g => g.nome)
    : ['Sem dados'];

const ganhosValores = (window.ganhosCategoria && ganhosCategoria.length)
    ? ganhosCategoria.map(g => g.total)
    : [0];

const coresGanhos = gerarCores(ganhosLabels.length);

const ctxGanhos = document.getElementById('graficoGanhos');

if (ctxGanhos) {
    new Chart(ctxGanhos, {
        type: 'doughnut',
        data: {
            labels: ganhosLabels,
            datasets: [{
                data: ganhosValores,
                backgroundColor: coresGanhos,
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

// =========================
// GANHOS VS GASTOS
// =========================
const ctxComparativo = document.getElementById('graficoComparativo');

if (ctxComparativo) {
    new Chart(ctxComparativo, {
        type: 'bar',
        data: {
            labels: ['Ganhos', 'Gastos'],
            datasets: [{
                label: 'R$',
                data: [
                    window.totalGanhos || 0,
                    window.totalGastos || 0
                ],
                backgroundColor: ['#22c55e', '#ef4444']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
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