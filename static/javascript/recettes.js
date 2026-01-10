/**
 * static/javascript/recettes.js
 * Gestion des formulaires de recettes (ingrédients et étapes)
 * 
 * SYSTÈME D'UNITÉS SIMPLIFIÉ :
 * Les quantités sont saisies dans l'unité native de l'ingrédient.
 * 
 * NOMS DES CHAMPS (correspondant à parse_etapes_list et parse_ingredients_list) :
 * - Ingrédients : ingredient_X, quantite_X
 * - Étapes : etape_desc_X, etape_duree_X
 */

(function() {
    'use strict';

    // Compteurs globaux (seront initialisés par le template si nécessaire)
    window.ingredientCount = window.ingredientCount || 1;
    window.etapeCount = window.etapeCount || 1;

    // =============================================
    // GESTION DES INGRÉDIENTS
    // =============================================

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
        
        // Récupérer l'unité depuis l'attribut data
        const unite = selectedOption.dataset.unite || 'g';
        uniteDisplay.value = unite;
        
        // Ajuster le step selon l'unité
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
     * Ajoute une nouvelle ligne d'ingrédient
     */
    function ajouterIngredient() {
        const container = document.getElementById('ingredients-container');
        if (!container) return;
        
        // Récupérer les options depuis le premier select
        const firstSelect = container.querySelector('.ingredient-select');
        if (!firstSelect) return;
        
        const optionsHTML = firstSelect.innerHTML;
        
        const div = document.createElement('div');
        div.className = 'ingredient-row';
        div.dataset.ingredientRow = window.ingredientCount;
        
        div.innerHTML = `
            <div class="form-group" style="flex: 2;">
                <select name="ingredient_${window.ingredientCount}" class="ingredient-select searchable-select" required>
                    ${optionsHTML}
                </select>
            </div>
            
            <div class="form-group" style="flex: 1;">
                <input type="number" 
                       step="1" 
                       name="quantite_${window.ingredientCount}" 
                       placeholder="Quantité"
                       required>
            </div>
            
            <div class="form-group" style="flex: 0.5;">
                <input type="text" 
                       class="unite-display" 
                       value="g" 
                       readonly 
                       style="background: #f0f0f0; cursor: not-allowed; text-align: center; font-weight: 600;">
            </div>
            
            <div class="form-group" style="flex: 0;">
                <button type="button" 
                        class="btn-remove-ingredient" 
                        onclick="removeIngredient(${window.ingredientCount})">
                    ✖
                </button>
            </div>
        `;
        
        container.appendChild(div);
        window.ingredientCount++;
        
        // Configurer le nouveau select
        const newSelect = div.querySelector('.ingredient-select');
        if (newSelect) {
            newSelect.addEventListener('change', function() {
                updateUniteDisplay(this);
            });
            // Réinitialiser la sélection
            newSelect.value = '';
        }
        
        // Initialiser SelectSearch si disponible
        if (typeof initSelectSearch === 'function') {
            initSelectSearch();
        }
        
        updateRemoveIngredientsButtons();
    }

    /**
     * Supprime une ligne d'ingrédient
     */
    function removeIngredient(index) {
        const row = document.querySelector(`.ingredient-row[data-ingredient-row="${index}"]`);
        if (row) {
            row.remove();
            updateRemoveIngredientsButtons();
        }
    }

    /**
     * Met à jour l'affichage des boutons de suppression d'ingrédients
     */
    function updateRemoveIngredientsButtons() {
        const rows = document.querySelectorAll('.ingredient-row');
        rows.forEach((row) => {
            const btn = row.querySelector('.btn-remove-ingredient');
            if (btn) {
                btn.style.display = rows.length > 1 ? 'inline-block' : 'none';
            }
        });
    }

    /**
     * Initialise les selects d'ingrédients existants
     */
    function initIngredientSelects() {
        document.querySelectorAll('.ingredient-select').forEach(select => {
            select.addEventListener('change', function() {
                updateUniteDisplay(this);
            });
            
            // Initialiser l'affichage si un ingrédient est déjà sélectionné
            if (select.value) {
                updateUniteDisplay(select);
            }
        });
    }

    // =============================================
    // GESTION DES ÉTAPES
    // =============================================

    /**
     * Ajoute une nouvelle étape
     * IMPORTANT: Les noms de champs doivent correspondre à parse_etapes_list :
     * - etape_desc_X pour la description
     * - etape_duree_X pour la durée
     */
    function ajouterEtape() {
        const container = document.getElementById('etapes-container');
        if (!container) return;
        
        const currentCount = window.etapeCount;
        
        const div = document.createElement('div');
        div.className = 'etape-row';
        div.dataset.etape = currentCount;
        
        // Structure cohérente avec le template recette_modifier.html
        div.innerHTML = `
            <div class="etape-number">${currentCount + 1}</div>
            <div class="etape-inputs">
                <div class="form-group" style="flex: 3; margin-bottom: 0;">
                    <textarea name="etape_desc_${currentCount}" 
                              placeholder="Décrivez cette étape..."
                              rows="2"></textarea>
                </div>
                <div class="form-group" style="flex: 1; margin-bottom: 0;">
                    <input type="number" 
                           name="etape_duree_${currentCount}" 
                           placeholder="⏱️ Minutes (opt.)"
                           min="0"
                           title="Durée en minutes pour le minuteur (optionnel)">
                </div>
            </div>
            <button type="button" 
                    class="btn-remove-etape" 
                    onclick="removeEtape(${currentCount})">
                ✖
            </button>
        `;
        
        container.appendChild(div);
        window.etapeCount++;
        updateRemoveEtapesButtons();
    }

    /**
     * Supprime une étape
     */
    function removeEtape(index) {
        const row = document.querySelector(`.etape-row[data-etape="${index}"]`);
        if (row) {
            row.remove();
            updateRemoveEtapesButtons();
            renumberEtapes();
        }
    }

    /**
     * Met à jour l'affichage des boutons de suppression des étapes
     */
    function updateRemoveEtapesButtons() {
        const rows = document.querySelectorAll('.etape-row');
        rows.forEach((row) => {
            const btn = row.querySelector('.btn-remove-etape');
            if (btn) {
                btn.style.display = rows.length > 1 ? 'inline-block' : 'none';
            }
        });
    }

    /**
     * Renumérote les étapes après suppression (affichage uniquement)
     * Note: Les noms des champs ne sont PAS renommés car parse_etapes_list
     * parcourt séquentiellement et s'arrête au premier index manquant.
     * Mais cela fonctionne car les champs existants gardent leurs indices.
     */
    function renumberEtapes() {
        const rows = document.querySelectorAll('.etape-row');
        rows.forEach((row, visualIndex) => {
            const numberSpan = row.querySelector('.etape-number');
            if (numberSpan) {
                numberSpan.textContent = visualIndex + 1;
            }
        });
    }

    // =============================================
    // INITIALISATION
    // =============================================

    function initRecettesForm() {
        // Initialiser les selects d'ingrédients
        initIngredientSelects();
        
        // Mettre à jour les boutons de suppression
        updateRemoveIngredientsButtons();
        updateRemoveEtapesButtons();
    }

    // Exposer les fonctions globalement
    window.ajouterIngredient = ajouterIngredient;
    window.removeIngredient = removeIngredient;
    window.ajouterEtape = ajouterEtape;
    window.removeEtape = removeEtape;
    window.updateUniteDisplay = updateUniteDisplay;
    window.initIngredientSelects = initIngredientSelects;
    window.updateRemoveEtapesButtons = updateRemoveEtapesButtons;
    window.renumberEtapes = renumberEtapes;

    // Initialisation au chargement du DOM
    document.addEventListener('DOMContentLoaded', initRecettesForm);

})();
