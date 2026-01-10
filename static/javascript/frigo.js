// ============================================
// Fichier: static/javascript/frigo.js
// Gestion du frigo - Édition rapide des quantités
// VERSION CORRIGÉE - Compatible avec SelectSearch
// ============================================

(function() {
    'use strict';

    // ============================================
    // AFFICHAGE DE L'UNITÉ SELON L'INGRÉDIENT
    // ============================================
    
    /**
     * Initialise l'affichage de l'unité quand un ingrédient est sélectionné
     * Compatible avec SelectSearch (écoute l'événement change sur le select original)
     */
    function initIngredientSelect() {
        const select = document.getElementById('ingredient-select');
        const uniteDisplay = document.getElementById('unite-display');
        
        if (!select || !uniteDisplay) {
            console.log('initIngredientSelect: select ou uniteDisplay non trouvé');
            return;
        }
        
        // Fonction pour mettre à jour l'unité
        function updateUnite() {
            const selectedOption = select.options[select.selectedIndex];
            if (selectedOption && selectedOption.value) {
                const unite = selectedOption.getAttribute('data-unite');
                uniteDisplay.value = unite || '';
            } else {
                uniteDisplay.value = '';
            }
        }
        
        // Écouter l'événement change sur le select original
        // SelectSearch déclenche cet événement quand une option est sélectionnée
        select.addEventListener('change', updateUnite);
        
        // Initialiser au cas où une valeur est déjà sélectionnée
        updateUnite();
        
        console.log('initIngredientSelect: initialisé avec succès');
    }

    // ============================================
    // ÉDITION RAPIDE - MODE GRILLE
    // ============================================
    
    /**
     * Active le mode édition pour un stock (vue grille)
     */
    window.enableEdit = function(stockId) {
        const editForm = document.getElementById(`quantite-edit-${stockId}`);
        const displayDiv = editForm?.previousElementSibling;
        
        if (!editForm || !displayDiv) return;
        
        displayDiv.style.display = 'none';
        editForm.style.display = 'flex';
        
        const input = document.getElementById(`quantite-input-grid-${stockId}`);
        if (input) {
            input.focus();
            input.select();
        }
    };

    /**
     * Annule l'édition et restaure la valeur originale (vue grille)
     */
    window.cancelEdit = function(stockId) {
        const input = document.getElementById(`quantite-input-grid-${stockId}`);
        const editForm = document.getElementById(`quantite-edit-${stockId}`);
        const statusDiv = document.getElementById(`status-grid-${stockId}`);
        
        if (!input || !editForm) return;
        
        // Restaurer la valeur originale
        input.value = input.dataset.original;
        
        // Cacher le formulaire d'édition
        editForm.style.display = 'none';
        
        // Afficher le display
        const displayDiv = editForm.previousElementSibling;
        if (displayDiv) {
            displayDiv.style.display = 'flex';
        }
        
        // Nettoyer le statut
        if (statusDiv) {
            statusDiv.textContent = '';
        }
    };

    /**
     * Sauvegarde la quantité (vue grille)
     */
    window.saveQuantiteGrid = async function(stockId) {
        const input = document.getElementById(`quantite-input-grid-${stockId}`);
        const statusDiv = document.getElementById(`status-grid-${stockId}`);
        const editForm = document.getElementById(`quantite-edit-${stockId}`);
        
        if (!input) return;
        
        const nouvelleQuantite = parseFloat(input.value);
        
        if (isNaN(nouvelleQuantite) || nouvelleQuantite < 0) {
            if (statusDiv) {
                statusDiv.textContent = '❌ Quantité invalide';
                statusDiv.className = 'edit-status error';
            }
            return;
        }
        
        if (statusDiv) {
            statusDiv.textContent = '⏳ Sauvegarde...';
            statusDiv.className = 'edit-status loading';
        }
        
        try {
            const response = await fetch(`/frigo/update-quantite/${stockId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quantite: nouvelleQuantite })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Mettre à jour l'affichage
                const displaySpan = document.querySelector(`#quantite-edit-${stockId}`)
                    ?.previousElementSibling?.querySelector('.quantite-value');
                if (displaySpan) {
                    displaySpan.textContent = data.quantite;
                }
                
                input.dataset.original = data.quantite;
                
                if (statusDiv) {
                    statusDiv.textContent = '✓ Sauvegardé';
                    statusDiv.className = 'edit-status success';
                }
                
                // Fermer le mode édition après 1 seconde
                setTimeout(() => {
                    if (editForm) {
                        editForm.style.display = 'none';
                        const displayDiv = editForm.previousElementSibling;
                        if (displayDiv) {
                            displayDiv.style.display = 'flex';
                        }
                    }
                    if (statusDiv) {
                        statusDiv.textContent = '';
                    }
                }, 1000);
            } else {
                if (statusDiv) {
                    statusDiv.textContent = '❌ ' + (data.message || 'Erreur');
                    statusDiv.className = 'edit-status error';
                }
            }
        } catch (error) {
            console.error('Erreur saveQuantiteGrid:', error);
            if (statusDiv) {
                statusDiv.textContent = '❌ Erreur réseau';
                statusDiv.className = 'edit-status error';
            }
        }
    };

    // Alias pour compatibilité
    window.saveQuantite = window.saveQuantiteGrid;

    // ============================================
    // ÉDITION RAPIDE - MODE TABLEAU
    // ============================================
    
    /**
     * Sauvegarde la quantité depuis le tableau (vue liste)
     */
    window.saveQuantiteTable = async function(stockId) {
        const input = document.getElementById(`quantite-input-${stockId}`);
        const statusDiv = document.getElementById(`status-${stockId}`);
        
        if (!input) return;
        
        const nouvelleQuantite = parseFloat(input.value);
        
        if (isNaN(nouvelleQuantite) || nouvelleQuantite < 0) {
            if (statusDiv) {
                statusDiv.textContent = '❌';
                statusDiv.className = 'edit-status-mini error';
            }
            return;
        }
        
        if (statusDiv) {
            statusDiv.textContent = '⏳';
            statusDiv.className = 'edit-status-mini loading';
        }
        
        try {
            const response = await fetch(`/frigo/update-quantite/${stockId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quantite: nouvelleQuantite })
            });
            
            const data = await response.json();
            
            if (data.success) {
                input.dataset.original = data.quantite;
                input.value = data.quantite;
                
                if (statusDiv) {
                    statusDiv.textContent = '✓';
                    statusDiv.className = 'edit-status-mini success';
                    
                    setTimeout(() => {
                        statusDiv.textContent = '';
                    }, 2000);
                }
            } else {
                if (statusDiv) {
                    statusDiv.textContent = '❌';
                    statusDiv.className = 'edit-status-mini error';
                }
            }
        } catch (error) {
            console.error('Erreur saveQuantiteTable:', error);
            if (statusDiv) {
                statusDiv.textContent = '❌';
                statusDiv.className = 'edit-status-mini error';
            }
        }
    };

    // ============================================
    // INITIALISATION
    // ============================================
    
    function init() {
        // Initialiser l'affichage de l'unité
        initIngredientSelect();
        
        // Gestion des touches pour les inputs du tableau
        document.querySelectorAll('.quantite-input-table').forEach(input => {
            const stockId = input.dataset.stockId;
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    saveQuantiteTable(stockId);
                }
            });
            
            // Auto-save on blur si la valeur a changé
            input.addEventListener('blur', () => {
                const original = parseFloat(input.dataset.original);
                const current = parseFloat(input.value);
                if (!isNaN(current) && original !== current) {
                    saveQuantiteTable(stockId);
                }
            });
        });
        
        // Gestion des touches pour les inputs inline (grille)
        document.querySelectorAll('.quantite-input-inline').forEach(input => {
            input.addEventListener('keydown', (e) => {
                const stockId = input.id.replace('quantite-input-grid-', '');
                if (e.key === 'Enter') {
                    e.preventDefault();
                    saveQuantiteGrid(stockId);
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    cancelEdit(stockId);
                }
            });
        });
        
        console.log('Frigo.js initialisé');
    }

    // Lancer l'initialisation au chargement du DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
