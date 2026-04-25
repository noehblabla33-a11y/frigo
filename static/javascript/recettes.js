/**
 * Gestion des formulaires de recettes (ingrédients et étapes).
 * Noms de champs : ingredient_X, quantite_X, etape_desc_X, etape_duree_X
 */

(function() {
    'use strict';

    window.ingredientCount = window.ingredientCount || 1;
    window.etapeCount = window.etapeCount || 1;

    // -----------------------------------------------
    // INGRÉDIENTS
    // -----------------------------------------------

    /**
     * Met à jour le badge d'unité quand on change d'ingrédient.
     */
    function updateUniteDisplay(selectElement) {
        const row = selectElement.closest('.ingredient-item-premium');
        if (!row) return;

        const uniteBadge = row.querySelector('.unite-badge');
        const quantiteInput = row.querySelector('input[name^="quantite_"]');
        const selectedOption = selectElement.options[selectElement.selectedIndex];

        const unite = (selectedOption && selectedOption.value)
            ? (selectedOption.dataset.unite || 'g')
            : 'g';

        if (uniteBadge) uniteBadge.textContent = unite;

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
     * Ajoute un nouvel ingrédient avec le style premium.
     */
    function ajouterIngredient() {
        const container = document.getElementById('ingredients-container');
        if (!container) return;

        const firstSelect = container.querySelector('.ingredient-select');
        if (!firstSelect) return;

        const optionsHTML = firstSelect.innerHTML;
        const index = window.ingredientCount;

        const div = document.createElement('div');
        div.className = 'ingredient-item-premium dynamic-item';
        div.dataset.index = index;

        div.innerHTML = `
            <div class="ingredient-drag-handle">⋮⋮</div>
            <div class="form-group" style="flex: 2; margin: 0;">
                <select name="ingredient_${index}" class="input-premium ingredient-select searchable-select" required>
                    ${optionsHTML}
                </select>
            </div>
            <div class="form-group" style="flex: 1; margin: 0;">
                <input type="number" step="1" name="quantite_${index}"
                       class="input-premium" placeholder="Quantité" required>
            </div>
            <div class="unite-badge">g</div>
            <button type="button" class="btn-delete-modern btn-remove-ingredient"
                    onclick="removeIngredient(${index})">🗑️</button>
        `;

        container.appendChild(div);
        window.ingredientCount++;

        const newSelect = div.querySelector('.ingredient-select');
        if (newSelect) {
            newSelect.value = '';
            newSelect.addEventListener('change', function() {
                updateUniteDisplay(this);
            });
        }

        if (typeof initSelectSearch === 'function') {
            initSelectSearch();
        }

        updateRemoveIngredientsButtons();
    }

    /**
     * Supprime un ingrédient par son index.
     */
    function removeIngredient(index) {
        const row = document.querySelector(`.ingredient-item-premium[data-index="${index}"]`);
        if (row) {
            row.remove();
            updateRemoveIngredientsButtons();
        }
    }

    /**
     * Masque le bouton supprimer quand il ne reste qu'un ingrédient.
     */
    function updateRemoveIngredientsButtons() {
        const rows = document.querySelectorAll('.ingredient-item-premium');
        rows.forEach((row) => {
            const btn = row.querySelector('.btn-remove-ingredient');
            if (btn) btn.style.display = rows.length > 1 ? 'inline-block' : 'none';
        });
    }

    /**
     * Attache les listeners de changement d'unité sur les selects existants.
     */
    function initIngredientSelects() {
        document.querySelectorAll('.ingredient-select').forEach(select => {
            select.addEventListener('change', function() {
                updateUniteDisplay(this);
            });
            if (select.value) updateUniteDisplay(select);
        });
    }

    // -----------------------------------------------
    // ÉTAPES
    // -----------------------------------------------

    /**
     * Ajoute une nouvelle étape avec le style premium.
     */
    function ajouterEtape() {
        const container = document.getElementById('etapes-container');
        if (!container) return;

        const index = window.etapeCount;
        const numeroAffichage = container.querySelectorAll('.etape-item-premium').length + 1;

        const div = document.createElement('div');
        div.className = 'etape-item-premium dynamic-item';
        div.dataset.index = index;

        div.innerHTML = `
            <div class="etape-numero-premium">${numeroAffichage}</div>
            <div class="etape-content-premium">
                <textarea name="etape_desc_${index}" class="input-premium"
                          placeholder="Décrivez cette étape en détail..." rows="3"></textarea>
                <div class="timer-input-group">
                    <span class="timer-icon">⏱️</span>
                    <input type="number" name="etape_duree_${index}" placeholder="0" min="0">
                    <span class="timer-label">minutes</span>
                </div>
            </div>
            <button type="button" class="btn-delete-modern btn-remove-etape"
                    onclick="removeEtape(${index})">🗑️</button>
        `;

        container.appendChild(div);
        window.etapeCount++;
        updateRemoveEtapesButtons();
    }

    /**
     * Supprime une étape par son index.
     */
    function removeEtape(index) {
        const row = document.querySelector(`.etape-item-premium[data-index="${index}"]`);
        if (row) {
            row.remove();
            updateRemoveEtapesButtons();
            renumberEtapes();
        }
    }

    /**
     * Masque le bouton supprimer quand il ne reste qu'une étape.
     */
    function updateRemoveEtapesButtons() {
        const rows = document.querySelectorAll('.etape-item-premium');
        rows.forEach((row) => {
            const btn = row.querySelector('.btn-remove-etape');
            if (btn) btn.style.display = rows.length > 1 ? 'inline-block' : 'none';
        });
    }

    /**
     * Renumérote visuellement les étapes (les noms de champs ne changent pas).
     */
    function renumberEtapes() {
        document.querySelectorAll('.etape-item-premium').forEach((row, i) => {
            const numero = row.querySelector('.etape-numero-premium');
            if (numero) numero.textContent = i + 1;
        });
    }

    // -----------------------------------------------
    // INITIALISATION
    // -----------------------------------------------

    function initRecettesForm() {
        initIngredientSelects();
        updateRemoveIngredientsButtons();
        updateRemoveEtapesButtons();
    }

    window.ajouterIngredient = ajouterIngredient;
    window.removeIngredient = removeIngredient;
    window.ajouterEtape = ajouterEtape;
    window.removeEtape = removeEtape;
    window.updateUniteDisplay = updateUniteDisplay;
    window.initIngredientSelects = initIngredientSelects;
    window.updateRemoveEtapesButtons = updateRemoveEtapesButtons;
    window.renumberEtapes = renumberEtapes;

    document.addEventListener('DOMContentLoaded', initRecettesForm);

})();
