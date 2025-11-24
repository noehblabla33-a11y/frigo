// ============================================
// Fichier: static/historique.js
// Graphiques et statistiques de l'historique
// ============================================

function initHistoriqueCharts(graphiqueMois, graphiqueTop) {
    // Graphique des recettes par mois
    const ctxMois = document.getElementById('chartMois');
    if (ctxMois) {
        new Chart(ctxMois.getContext('2d'), {
            type: 'line',
            data: {
                labels: graphiqueMois.labels,
                datasets: [{
                    label: 'Recettes préparées',
                    data: graphiqueMois.data,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    // Graphique top recettes
    const ctxTop = document.getElementById('chartTop');
    if (ctxTop && graphiqueTop.labels.length > 0) {
        new Chart(ctxTop.getContext('2d'), {
            type: 'bar',
            data: {
                labels: graphiqueTop.labels,
                datasets: [{
                    label: 'Nombre de préparations',
                    data: graphiqueTop.data,
                    backgroundColor: [
                        '#FFD700', '#C0C0C0', '#CD7F32',
                        '#667eea', '#667eea', '#667eea', 
                        '#667eea', '#667eea', '#667eea', '#667eea'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
}

// Exposition de la fonction pour utilisation dans le template
window.initHistoriqueCharts = initHistoriqueCharts;
