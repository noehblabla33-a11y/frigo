/**
 * Gestion de l'affichage des quantités d'ingrédients avec conversion en pièces
 * Fichier: static/javascript/ingredient-pieces.js
 */

/**
 * Met à jour l'affichage de l'unité et du helper pour les pièces
 * @param {HTMLSelectElement} selectElement - Le select de l'ingrédient
 */
function updateUniteEtHelper(selectElement) {
    const row = selectElement.closest('.ingredient-row');
    if (!row) return;
    
    const uniteDisplay = row.querySelector('.unite-display');
    const helper = row.querySelector('.piece-helper');
    const quantiteInput = row.querySelector('input[name^="quantite_"]');
    
    if (!uniteDisplay || !helper || !quantiteInput) return;
    
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const unite = selectedOption.dataset.unite || 'g';
    const poidsPiece = selectedOption.dataset.poidsPiece;
    const nomIngredient = selectedOption.text;
    
    // Afficher l'unité réelle
    uniteDisplay.value = unite;
    
    // Si l'ingrédient a un poids_piece défini
    if (poidsPiece && parseFloat(poidsPiece) > 0) {
        const quantite = parseFloat(quantiteInput.value) || 0;
        const poids = parseFloat(poidsPiece);
        
        if (quantite > 0) {
            const nbPieces = quantite / poids;
            const nbPiecesArrondi = Math.round(nbPieces);
            
            // Si c'est proche d'un nombre entier (±10%)
            if (Math.abs(nbPieces - nbPiecesArrondi) / nbPieces < 0.1) {
                const pluriel = nbPiecesArrondi > 1 ? 's' : '';
                helper.textContent = `💡 ${nbPiecesArrondi} ${nomIngredient}${pluriel}`;
            } else {
                helper.textContent = `💡 ≈${nbPieces.toFixed(1)} ${nomIngredient}`;
            }
        } else {
            helper.textContent = `💡 1 ${nomIngredient} = ${poids}g`;
        }
        helper.style.display = 'block';
    } else {
        helper.style.display = 'none';
    }
}

/**
 * Initialise les écouteurs d'événements pour les ingrédients
 */
function initIngredientPiecesHelpers() {
    // Pour tous les selects d'ingrédients
    document.querySelectorAll('.ingredient-select').forEach(select => {
        // Événement au changement d'ingrédient
        select.addEventListener('change', function() {
            updateUniteEtHelper(this);
        });
        
        // Initialiser au chargement si un ingrédient est déjà sélectionné
        if (select.value) {
            updateUniteEtHelper(select);
        }
    });
    
    // Pour tous les champs de quantité
    document.querySelectorAll('input[name^="quantite_"]').forEach(input => {
        input.addEventListener('input', function() {
            const row = this.closest('.ingredient-row');
            if (row) {
                const select = row.querySelector('.ingredient-select');
                if (select) {
                    updateUniteEtHelper(select);
                }
            }
        });
    });
}

// Initialiser au chargement du DOM
document.addEventListener('DOMContentLoaded', function() {
    initIngredientPiecesHelpers();
});

// Exposer les fonctions pour utilisation externe si nécessaire
window.IngredientPiecesHelper = {
    init: initIngredientPiecesHelpers,
    update: updateUniteEtHelper
};
