/**
 * Gestion de l'affichage des quantités d'ingrédients avec conversion en pièces
 * Fichier: static/javascript/ingredient-pieces.js
 * 
 * LOGIQUE INTELLIGENTE :
 * - Si l'ingrédient a un poids_piece → afficher "g" (car on saisit en grammes)
 * - Sinon → afficher l'unité réelle (g, ml, cl, L, etc.)
 */

(function() {
    'use strict';

    /**
     * Formate le pluriel d'un mot français
     */
    function pluraliser(nom, nombre) {
        if (nombre <= 1) return nom;
        
        const nomLower = nom.toLowerCase();
        
        // Exceptions
        const exceptions = {
            'oeuf': 'oeufs',
            'œuf': 'œufs',
            'chou': 'choux',
            'bijou': 'bijoux'
        };
        
        if (exceptions[nomLower]) {
            const resultat = exceptions[nomLower];
            return nom[0] === nom[0].toUpperCase() ? 
                   resultat.charAt(0).toUpperCase() + resultat.slice(1) : 
                   resultat;
        }
        
        // Déjà au pluriel
        if (nomLower.endsWith('s') || nomLower.endsWith('x') || nomLower.endsWith('z')) {
            return nom;
        }
        
        // -au, -eau, -eu → ajouter x
        if (nomLower.endsWith('au') || nomLower.endsWith('eau') || nomLower.endsWith('eu')) {
            return nom + 'x';
        }
        
        // -al → -aux
        if (nomLower.endsWith('al')) {
            return nom.slice(0, -2) + 'aux';
        }
        
        // Règle générale : ajouter s
        return nom + 's';
    }

    /**
     * Met à jour l'affichage de l'unité et le helper pour les pièces
     * LOGIQUE :
     * - Si poids_piece défini → unité = "g" (saisie en grammes pour conversion pièces)
     * - Sinon → unité = unité réelle de l'ingrédient
     */
    function updateUniteEtHelper(selectElement) {
        const row = selectElement.closest('.ingredient-row');
        if (!row) return;
        
        const uniteDisplay = row.querySelector('.unite-display');
        const helper = row.querySelector('.piece-helper');
        const quantiteInput = row.querySelector('input[name^="quantite_"]');
        
        if (!uniteDisplay || !helper || !quantiteInput) return;
        
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        if (!selectedOption || !selectedOption.value) {
            helper.style.display = 'none';
            uniteDisplay.value = 'g'; // Défaut
            return;
        }
        
        const unite = selectedOption.dataset.unite || 'g';
        const poidsPiece = selectedOption.dataset.poidsPiece;
        const nomIngredient = selectedOption.textContent.trim();
        
        // LOGIQUE INTELLIGENTE :
        // Si l'ingrédient a un poids_piece, on saisit en grammes
        // Sinon, on garde l'unité réelle
        if (poidsPiece && parseFloat(poidsPiece) > 0) {
            uniteDisplay.value = 'g'; // Toujours grammes pour les ingrédients en pièces
            
            // Stocker les données pour le helper
            quantiteInput.dataset.poidsPiece = poidsPiece;
            quantiteInput.dataset.nomIngredient = nomIngredient;
            quantiteInput.dataset.unite = unite;
            
            // Mettre à jour le helper
            updateQuantiteHelper(quantiteInput);
            
            // Listener sur l'input
            quantiteInput.removeEventListener('input', handleQuantiteChange);
            quantiteInput.addEventListener('input', handleQuantiteChange);
        } else {
            // Pas de poids_piece : afficher l'unité réelle
            uniteDisplay.value = unite;
            
            // Cacher le helper
            helper.style.display = 'none';
            delete quantiteInput.dataset.poidsPiece;
            delete quantiteInput.dataset.nomIngredient;
            quantiteInput.removeEventListener('input', handleQuantiteChange);
        }
    }

    /**
     * Gère le changement de quantité
     */
    function handleQuantiteChange(event) {
        updateQuantiteHelper(event.target);
    }

    /**
     * Met à jour le helper de quantité (affiche le nombre de pièces)
     */
    function updateQuantiteHelper(quantiteInput) {
        const row = quantiteInput.closest('.ingredient-row');
        if (!row) return;
        
        const helper = row.querySelector('.piece-helper');
        if (!helper) return;
        
        const poidsPiece = parseFloat(quantiteInput.dataset.poidsPiece);
        const nomIngredient = quantiteInput.dataset.nomIngredient;
        
        if (!poidsPiece || !nomIngredient) {
            helper.style.display = 'none';
            return;
        }
        
        const quantite = parseFloat(quantiteInput.value) || 0;
        
        if (quantite <= 0) {
            helper.style.display = 'none';
            return;
        }
        
        const nbPieces = quantite / poidsPiece;
        const nbPiecesArrondi = Math.round(nbPieces);
        
        // Si c'est proche d'un nombre entier (±10%)
        if (nbPieces > 0 && Math.abs(nbPieces - nbPiecesArrondi) / nbPieces < 0.1) {
            const nomPluriel = pluraliser(nomIngredient, nbPiecesArrondi);
            helper.innerHTML = `💡 = ${nbPiecesArrondi} ${nomPluriel}`;
            helper.style.display = 'inline-block';
            helper.style.color = '#28a745';
            helper.style.fontWeight = '600';
        } else if (nbPieces > 0) {
            // Quantité non standard, afficher l'approximation
            helper.innerHTML = `💡 ≈ ${nbPieces.toFixed(1)} ${nomIngredient}${nbPieces > 1 ? 's' : ''}`;
            helper.style.display = 'inline-block';
            helper.style.color = '#667eea';
            helper.style.fontWeight = '600';
        } else {
            helper.style.display = 'none';
        }
    }

    /**
     * Initialise tous les selects d'ingrédients présents dans la page
     */
    function initIngredientSelects() {
        const selects = document.querySelectorAll('.ingredient-select');
        
        selects.forEach(select => {
            // Ajouter le listener de changement
            select.addEventListener('change', function() {
                updateUniteEtHelper(this);
            });
            
            // Initialiser l'affichage si un ingrédient est déjà sélectionné
            if (select.value) {
                updateUniteEtHelper(select);
            }
        });
    }

    /**
     * Initialise les inputs de quantité existants (mode édition)
     */
    function initExistingQuantites() {
        const rows = document.querySelectorAll('.ingredient-row');
        
        rows.forEach(row => {
            const select = row.querySelector('.ingredient-select');
            const quantiteInput = row.querySelector('input[name^="quantite_"]');
            
            if (select && select.value && quantiteInput && quantiteInput.value) {
                updateUniteEtHelper(select);
            }
        });
    }

    /**
     * Ajoute un bandeau explicatif clair
     */
    function addExplicativeLabel() {
        const ingredientsContainer = document.getElementById('ingredients-container');
        if (!ingredientsContainer) return;
        
        // Chercher s'il y a déjà un label
        if (document.querySelector('.ingredient-quantite-explainer')) return;
        
        // Ajouter un bandeau explicatif au-dessus du container
        const explainer = document.createElement('div');
        explainer.className = 'ingredient-quantite-explainer';
        explainer.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 0.95em;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        `;
        explainer.innerHTML = `
            <span style="font-size: 1.5em;">ℹ️</span>
            <div>
                <strong>Saisie des quantités :</strong><br>
                Pour les ingrédients en <strong>pièces</strong> (avocat, œuf...), entrez la quantité <strong>en grammes</strong>. 
                L'équivalent en pièces s'affichera automatiquement.<br>
                Pour les autres ingrédients, utilisez l'unité indiquée (g, ml, cl, L...).
            </div>
        `;
        
        ingredientsContainer.parentNode.insertBefore(explainer, ingredientsContainer);
    }

    /**
     * Améliore visuellement les helpers de pièces
     */
    function styleHelpers() {
        const helpers = document.querySelectorAll('.piece-helper');
        
        helpers.forEach(helper => {
            helper.style.cssText = `
                display: none;
                padding: 5px 10px;
                background: linear-gradient(135deg, #e8f9ed, #d4f4dd);
                border-radius: 5px;
                font-size: 0.9em;
                border-left: 3px solid #28a745;
                line-height: 1.8;
                margin-top: 5px;
            `;
        });
    }

    /**
     * Initialisation au chargement du DOM
     */
    document.addEventListener('DOMContentLoaded', function() {
        // Initialiser les selects
        initIngredientSelects();
        
        // Initialiser les quantités existantes (mode édition)
        initExistingQuantites();
        
        // Ajouter le bandeau explicatif
        addExplicativeLabel();
        
        // Améliorer le style des helpers
        styleHelpers();
    });

    // Exposer les fonctions globalement pour être utilisées par d'autres scripts
    window.IngredientPieces = {
        updateUniteEtHelper: updateUniteEtHelper,
        updateQuantiteHelper: updateQuantiteHelper,
        initIngredientSelects: initIngredientSelects,
        pluraliser: pluraliser
    };

})();
