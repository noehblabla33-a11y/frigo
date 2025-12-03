// ============================================
// Fichier: static/recettes.js
// Gestion du formulaire de création/modification de recettes
// ============================================

let etapeCount = 1;
let ingredientCount = 1;

// Gestion des étapes
function ajouterEtape() {
    const container = document.getElementById('etapes-container');
    if (!container) return;
    
    const div = document.createElement('div');
    div.className = 'etape-row';
    div.dataset.etape = etapeCount;
    div.innerHTML = `
        <div class="etape-number">${etapeCount + 1}</div>
        <div class="etape-inputs">
            <div class="form-group" style="flex: 3; margin-bottom: 0;">
                <textarea name="etape_desc_${etapeCount}" 
                          placeholder="Décrivez cette étape..."
                          rows="2"></textarea>
            </div>
            <div class="form-group" style="flex: 1; margin-bottom: 0;">
                <input type="number" 
                       name="etape_duree_${etapeCount}" 
                       placeholder="⏱️ Minutes (opt.)"
                       min="0"
                       title="Durée en minutes pour le minuteur (optionnel)">
            </div>
        </div>
        <button type="button" 
                class="btn-remove-etape" 
                onclick="removeEtape(${etapeCount})">
            ✖
        </button>
    `;
    container.appendChild(div);
    
    // Afficher le bouton de suppression de la première étape si elle existe
    if (etapeCount === 1) {
        const firstRemove = document.querySelector('.etape-row[data-etape="0"] .btn-remove-etape');
        if (firstRemove) firstRemove.style.display = 'block';
    }
    
    etapeCount++;
    updateEtapeNumbers();
}

function removeEtape(index) {
    const etape = document.querySelector(`.etape-row[data-etape="${index}"]`);
    if (etape) {
        etape.remove();
        updateEtapeNumbers();
        
        // Cacher le bouton de suppression si une seule étape reste
        const allEtapes = document.querySelectorAll('.etape-row');
        if (allEtapes.length === 1) {
            const removeBtn = allEtapes[0].querySelector('.btn-remove-etape');
            if (removeBtn) removeBtn.style.display = 'none';
        }
    }
}

function updateEtapeNumbers() {
    const etapes = document.querySelectorAll('.etape-row');
    etapes.forEach((etape, index) => {
        const numberDiv = etape.querySelector('.etape-number');
        if (numberDiv) numberDiv.textContent = index + 1;
    });
}

// Gestion des ingrédients
function updateUnite(selectElement) {
    const index = selectElement.dataset.index;
    const uniteSpan = document.getElementById('unite-' + index);
    if (!uniteSpan) return;
    
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const unite = selectedOption.getAttribute('data-unite');
    
    if (unite && selectedOption.value) {
        uniteSpan.textContent = unite;
    } else {
        uniteSpan.textContent = '';
    }
}

function ajouterIngredient() {
    const container = document.getElementById('ingredients-container');
    if (!container) return;
    
    // Récupérer le HTML des options depuis le premier select
    const firstSelect = document.querySelector('.ingredient-select');
    if (!firstSelect) return;
    
    const optionsHTML = firstSelect.innerHTML;
    
    const div = document.createElement('div');
    div.className = 'ingredient-row';
    div.dataset.ingredientRow = ingredientCount;
    div.innerHTML = `
        <div style="flex: 2;">
            <select name="ingredient_${ingredientCount}" class="ingredient-select searchable-select" data-index="${ingredientCount}">
                ${optionsHTML}
            </select>
        </div>
        <div style="flex: 1;">
            <input type="number" step="0.01" name="quantite_${ingredientCount}" placeholder="Quantité">
        </div>
        <div style="flex: 0; min-width: 50px;">
            <span class="unite-display" id="unite-${ingredientCount}" style="font-weight: bold; color: #667eea;"></span>
        </div>
        <div style="flex: 0;">
            <button type="button" 
                    class="btn-remove-ingredient" 
                    onclick="removeIngredient(${ingredientCount})"
                    style="padding: 8px 12px; background: #dc3545; color: white; border: none; border-radius: 5px; cursor: pointer;">
                ✖
            </button>
        </div>
    `;
    container.appendChild(div);
    
    const newSelect = div.querySelector('.ingredient-select');
    newSelect.addEventListener('change', function() {
        updateUnite(this);
    });
    
    // Réinitialiser le select avec recherche si disponible
    if (window.SelectSearch) {
        new window.SelectSearch(newSelect);
    }
    
    ingredientCount++;
    updateRemoveIngredientsButtons();
}

function removeIngredient(index) {
    const row = document.querySelector(`.ingredient-row[data-ingredient-row="${index}"]`);
    if (row) {
        row.remove();
        updateRemoveIngredientsButtons();
    }
}

function updateRemoveIngredientsButtons() {
    const rows = document.querySelectorAll('.ingredient-row');
    rows.forEach((row) => {
        const btn = row.querySelector('.btn-remove-ingredient');
        if (btn) {
            btn.style.display = rows.length > 1 ? 'inline-block' : 'none';
        }
    });
}

// Initialisation
function initRecettesForm() {
    // Ajouter les événements aux selects d'ingrédients existants
    document.querySelectorAll('.ingredient-select').forEach(select => {
        select.addEventListener('change', function() {
            updateUnite(this);
        });
        // Afficher l'unité initiale si un ingrédient est déjà sélectionné
        if (select.value) {
            updateUnite(select);
        }
    });
    
    // Mettre à jour les boutons de suppression au chargement
    updateRemoveIngredientsButtons();
}

// Exposition des fonctions globales
window.ajouterEtape = ajouterEtape;
window.removeEtape = removeEtape;
window.ajouterIngredient = ajouterIngredient;
window.removeIngredient = removeIngredient;

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    initRecettesForm();
});
