// ============================================
// Fichier: static/frigo.js
// Gestion du frigo - Édition rapide des quantités
// ============================================

// Affichage de l'unité selon l'ingrédient sélectionné
function initIngredientSelect() {
    const select = document.getElementById('ingredient-select');
    const uniteDisplay = document.getElementById('unite-display');
    
    if (!select || !uniteDisplay) return;
    
    select.addEventListener('change', function() {
        const option = this.options[this.selectedIndex];
        const unite = option.getAttribute('data-unite');
        if (unite) {
            uniteDisplay.textContent = unite;
        } else {
            uniteDisplay.textContent = '';
        }
    });
}

// Édition rapide pour la grille
function enableEdit(stockId) {
    document.querySelector(`#quantite-edit-${stockId}`).previousElementSibling.style.display = 'none';
    document.getElementById(`quantite-edit-${stockId}`).style.display = 'flex';
    const input = document.getElementById(`quantite-input-grid-${stockId}`);
    input.focus();
    input.select();
}

function cancelEdit(stockId) {
    const input = document.getElementById(`quantite-input-grid-${stockId}`);
    input.value = input.dataset.original;
    document.getElementById(`quantite-edit-${stockId}`).style.display = 'none';
    document.querySelector(`#quantite-edit-${stockId}`).previousElementSibling.style.display = 'flex';
    document.getElementById(`status-grid-${stockId}`).textContent = '';
}

async function saveQuantiteGrid(stockId) {
    const input = document.getElementById(`quantite-input-grid-${stockId}`);
    const statusDiv = document.getElementById(`status-grid-${stockId}`);
    const nouvelleQuantite = parseFloat(input.value);
    
    if (isNaN(nouvelleQuantite) || nouvelleQuantite < 0) {
        statusDiv.textContent = '❌ Quantité invalide';
        statusDiv.className = 'edit-status error';
        return;
    }
    
    statusDiv.textContent = '⏳ Sauvegarde...';
    statusDiv.className = 'edit-status loading';
    
    try {
        const response = await fetch(`/frigo/update-quantite/${stockId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ quantite: nouvelleQuantite })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById(`quantite-display-${stockId}`).textContent = data.quantite;
            input.dataset.original = data.quantite;
            statusDiv.textContent = '✓ Sauvegardé';
            statusDiv.className = 'edit-status success';
            
            setTimeout(() => {
                document.getElementById(`quantite-edit-${stockId}`).style.display = 'none';
                document.querySelector(`#quantite-edit-${stockId}`).previousElementSibling.style.display = 'flex';
                statusDiv.textContent = '';
            }, 1000);
        } else {
            statusDiv.textContent = '❌ ' + data.message;
            statusDiv.className = 'edit-status error';
        }
    } catch (error) {
        statusDiv.textContent = '❌ Erreur réseau';
        statusDiv.className = 'edit-status error';
    }
}

// Édition rapide pour la liste (tableau)
async function saveQuantite(stockId) {
    const input = document.getElementById(`quantite-input-${stockId}`);
    const statusDiv = document.getElementById(`status-${stockId}`);
    const nouvelleQuantite = parseFloat(input.value);
    
    if (isNaN(nouvelleQuantite) || nouvelleQuantite < 0) {
        statusDiv.textContent = '❌';
        statusDiv.className = 'edit-status-mini error';
        return;
    }
    
    statusDiv.textContent = '⏳';
    statusDiv.className = 'edit-status-mini loading';
    
    try {
        const response = await fetch(`/frigo/update-quantite/${stockId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ quantite: nouvelleQuantite })
        });
        
        const data = await response.json();
        
        if (data.success) {
            input.dataset.original = data.quantite;
            input.value = data.quantite;
            statusDiv.textContent = '✓';
            statusDiv.className = 'edit-status-mini success';
            
            setTimeout(() => {
                statusDiv.textContent = '';
            }, 2000);
        } else {
            statusDiv.textContent = '❌';
            statusDiv.className = 'edit-status-mini error';
        }
    } catch (error) {
        statusDiv.textContent = '❌';
        statusDiv.className = 'edit-status-mini error';
    }
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    initIngredientSelect();
    
    // Sauvegarder avec Entrée pour les inputs du tableau
    document.querySelectorAll('.quantite-input-table').forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const stockId = input.dataset.stockId;
                saveQuantite(stockId);
            }
        });
        
        // Auto-save on blur (perte de focus)
        input.addEventListener('blur', (e) => {
            const stockId = input.dataset.stockId;
            const original = parseFloat(input.dataset.original);
            const current = parseFloat(input.value);
            if (original !== current && !isNaN(current)) {
                saveQuantite(stockId);
            }
        });
    });
    
    // Gestion des touches pour les inputs inline (grille)
    document.querySelectorAll('.quantite-input-inline').forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const stockId = input.dataset.stockId;
                saveQuantiteGrid(stockId);
            } else if (e.key === 'Escape') {
                const stockId = input.dataset.stockId;
                cancelEdit(stockId);
            }
        });
    });
});
