/**
 * Gestion des ingrédients dans les formulaires de recettes
 *
 * Supporte deux structures HTML :
 * - recette_modifier.html : .ingredient-row > .unite-display (input readonly)
 * - formulaire création  : .ingredient-item-premium > .unite-badge (span)
 *
 * Catégories spéciales :
 * - "Huiles"     → saisie en cuillères à soupe (cs), 1 cs = 15 ml
 * - "Épices" / "Condiments" → saisie en pincées, 1 pincée = 0.5 g
 */

(function() {
    'use strict';

    const CATEGORIE_HUILES   = 'Huiles';
    const CATEGORIES_PINCEES = ['Épices', 'Condiments'];

    function updateUniteDisplay(selectElement) {
        const row = selectElement.closest('.ingredient-row')
                 || selectElement.closest('.ingredient-item-premium');
        if (!row) return;

        const uniteInput    = row.querySelector('.unite-display');
        const uniteBadge    = row.querySelector('.unite-badge');
        const quantiteInput = row.querySelector('input[name^="quantite_"]');

        const selectedOption = selectElement.options[selectElement.selectedIndex];

        if (!selectedOption || !selectedOption.value) {
            if (uniteInput)  uniteInput.value       = 'g';
            if (uniteBadge)  uniteBadge.textContent = 'g';
            if (quantiteInput) {
                quantiteInput.step = '1';
                quantiteInput.placeholder = 'Quantité';
            }
            return;
        }

        const unite     = selectedOption.dataset.unite     || 'g';
        const categorie = selectedOption.dataset.categorie || '';
        const isHuile   = categorie === CATEGORIE_HUILES;
        const isPincee  = CATEGORIES_PINCEES.includes(categorie);

        let display;
        if (isHuile)       display = 'cs';
        else if (isPincee) display = 'pincée';
        else               display = unite;

        if (uniteInput)  uniteInput.value       = display;
        if (uniteBadge)  uniteBadge.textContent = display;

        if (quantiteInput) {
            if (isHuile) {
                quantiteInput.step = '0.5';
                quantiteInput.placeholder = 'Ex: 2';
            } else if (isPincee) {
                quantiteInput.step = '1';
                quantiteInput.placeholder = 'Ex: 2';
            } else if (unite === 'pièce') {
                quantiteInput.step = '0.5';
                quantiteInput.placeholder = 'Ex: 2';
            } else {
                quantiteInput.step = '1';
                quantiteInput.placeholder = unite === 'ml' ? 'Ex: 250' : 'Ex: 200';
            }
        }
    }

    function initIngredientSelects() {
        document.querySelectorAll('.ingredient-select').forEach(select => {
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
