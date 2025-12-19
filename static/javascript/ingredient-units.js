/**
 * Gestion des ingrédients dans les formulaires de recettes
 * SYSTÈME D'UNITÉS SIMPLIFIÉ
 * 
 * Les quantités sont saisies et stockées dans l'unité NATIVE de l'ingrédient.
 */

(function() {
    'use strict';

    /**
     * Met à jour l'affichage de l'unité quand on change d'ingrédient
     */
    function updateUniteDisplay(selectElement) {
        const row = selectElement.closest('.ingredient-row');
        if (!row) return;
        
        const uniteDisplay = row.querySelector('.unite-display');
        const quantiteInput = row.querySelector('input[name^="quantite_"]');
        
        if (!uniteDisplay) return;
        
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        
        if (!selectedOption || !selectedOption.value) {
            uniteDisplay.value = 'g';
            if (quantiteInput) {
                quantiteInput.step = '1';
                quantiteInput.placeholder = 'Quantité';
            }
            return;
        }
        
        const unite = selectedOption.dataset.unite || 'g';
        uniteDisplay.value = unite;
        
        if (quantiteInput) {
            if (unite === 'pièce') {
                quantiteInput.step = '0.5';
                quantiteInput.placeholder = 'Ex: 2';
            } else {
                quantiteInput.step = '1';
                quantiteInput.placeholder = unite === 'ml' ? 'Ex: 250' : 'Ex: 200';
            }
        }
    }

    /**
     * Initialise tous les selects d'ingrédients
     */
    function initIngredientSelects() {
        const selects = document.querySelectorAll('.ingredient-select');
        
        selects.forEach(select => {
            select.addEventListener('change', function() {
                updateUniteDisplay(this);
            });
            
            if (select.value) {
                updateUniteDisplay(select);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        initIngredientSelects();
    });

    window.IngredientUnits = {
        updateUniteDisplay: updateUniteDisplay,
        initIngredientSelects: initIngredientSelects
    };

})();
