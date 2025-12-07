// ============================================
// Fichier: static/javascript/historique.js
// Graphiques et statistiques de l'historique
// ============================================

/**
 * Initialise tous les graphiques de la page historique
 */
function initHistoriqueCharts(graphiqueMois, graphiqueTop, statsCategories, coutsPeriodiques, ingredientsPopulaires) {
    // Graphique des recettes par mois
    initChartMois(graphiqueMois);
    
    // Graphique top recettes
    initChartTop(graphiqueTop);
    
    // Graphique consommation par catégorie
    if (statsCategories && statsCategories.labels.length > 0) {
        initChartCategories(statsCategories);
    }
    
    // Graphiques des coûts périodiques
    if (coutsPeriodiques) {
        if (coutsPeriodiques.semaines.labels.length > 0) {
            initChartCoutsSemaines(coutsPeriodiques.semaines);
        }
        if (coutsPeriodiques.mois.labels.length > 0) {
            initChartCoutsMois(coutsPeriodiques.mois);
        }
    }
    
    // Graphique des ingrédients populaires
    if (ingredientsPopulaires && ingredientsPopulaires.labels.length > 0) {
        initChartIngredients(ingredientsPopulaires);
    }
}

/**
 * Graphique des recettes par mois (ligne)
 */
function initChartMois(data) {
    const ctx = document.getElementById('chartMois');
    if (!ctx) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Recettes préparées',
                data: data.data,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 3,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Graphique top recettes (barres horizontales)
 */
function initChartTop(data) {
    const ctx = document.getElementById('chartTop');
    if (!ctx || data.labels.length === 0) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Nombre de préparations',
                data: data.data,
                backgroundColor: [
                    '#FFD700', '#C0C0C0', '#CD7F32',
                    '#667eea', '#667eea', '#667eea', 
                    '#667eea', '#667eea', '#667eea', '#667eea'
                ],
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: { 
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Graphique consommation par catégorie (doughnut)
 */
function initChartCategories(data) {
    const ctx = document.getElementById('chartCategories');
    if (!ctx) return;
    
    // Palette de couleurs variée
    const colors = [
        '#667eea', '#f39c12', '#e74c3c', '#3498db', 
        '#2ecc71', '#9b59b6', '#1abc9c', '#e67e22',
        '#34495e', '#16a085', '#c0392b', '#8e44ad'
    ];
    
    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Utilisations',
                data: data.counts,
                backgroundColor: colors.slice(0, data.labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        font: { size: 12 },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const count = data.datasets[0].data[i];
                                    const cout = statsCategories.couts[i];
                                    let text = `${label} (${count})`;
                                    if (cout > 0) {
                                        text += ` - ${cout.toFixed(2)}€`;
                                    }
                                    return {
                                        text: text,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const cout = data.couts[context.dataIndex] || 0;
                            let result = `${label}: ${value} utilisations`;
                            if (cout > 0) {
                                result += ` (${cout.toFixed(2)}€)`;
                            }
                            return result;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Graphique coûts moyens par semaine
 */
function initChartCoutsSemaines(data) {
    const ctx = document.getElementById('chartCoutsSemaines');
    if (!ctx) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Coût moyen/recette (€)',
                data: data.couts_moyens,
                borderColor: '#20c997',
                backgroundColor: 'rgba(32, 201, 151, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 3,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: '#20c997',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const moy = context.parsed.y.toFixed(2);
                            const total = data.couts_totaux[context.dataIndex].toFixed(2);
                            return [
                                `Coût moyen: ${moy}€`,
                                `Coût total: ${total}€`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2) + '€';
                        }
                    },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Graphique coûts moyens par mois
 */
function initChartCoutsMois(data) {
    const ctx = document.getElementById('chartCoutsMois');
    if (!ctx) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Coût moyen/recette (€)',
                data: data.couts_moyens,
                backgroundColor: 'rgba(243, 156, 18, 0.7)',
                borderColor: '#f39c12',
                borderWidth: 2,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const moy = context.parsed.y.toFixed(2);
                            const total = data.couts_totaux[context.dataIndex].toFixed(2);
                            return [
                                `Coût moyen: ${moy}€`,
                                `Coût total: ${total}€`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2) + '€';
                        }
                    },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Graphique ingrédients les plus utilisés (barres horizontales)
 */
function initChartIngredients(data) {
    const ctx = document.getElementById('chartIngredients');
    if (!ctx) return;
    
    // Générer des couleurs en dégradé
    const baseColor = [102, 126, 234]; // #667eea
    const colors = data.labels.map((_, i) => {
        const factor = 1 - (i * 0.05); // Diminuer progressivement l'intensité
        return `rgba(${baseColor[0]}, ${baseColor[1]}, ${baseColor[2]}, ${factor})`;
    });
    
    new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Nombre d\'utilisations',
                data: data.counts,
                backgroundColor: colors,
                borderColor: '#667eea',
                borderWidth: 1,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const count = context.parsed.x;
                            const quantite = data.quantites[context.dataIndex];
                            const unite = data.unites[context.dataIndex];
                            return [
                                `${count} utilisations`,
                                `Quantité totale: ${quantite} ${unite}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

// Exposition de la fonction pour utilisation dans le template
window.initHistoriqueCharts = initHistoriqueCharts;
