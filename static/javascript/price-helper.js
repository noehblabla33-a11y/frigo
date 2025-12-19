/**
 * Gestion intelligente du prix des ingrédients avec CONVERSION AUTOMATIQUE
 * Version simplifiée - utilise poids_piece de la base de données
 * Fichier: static/javascript/price-helper.js
 */

(function() {
    'use strict';
    
    // Variable pour stocker le mode de saisie (piece ou gramme)
    let modeSaisie = 'gramme'; // 'piece' ou 'gramme'
    
    // ============================================
    // CONTRÔLES DE MODE DE SAISIE
    // ============================================
    
    /**
     * Crée les contrôles de mode de saisie (pièce vs gramme)
     */
    function createModeSaisieControls() {
        const prixFormGroup = document.querySelector('input[name="prix_unitaire"]')?.closest('.form-group');
        const poidsPieceInput = document.getElementById('poids-piece-input') || 
                                document.querySelector('input[name="poids_piece"]');
        
        if (!prixFormGroup || !poidsPieceInput) return;
        
        const poidsPiece = parseFloat(poidsPieceInput.value) || 0;
        
        // Ne créer les contrôles que si poids_piece est défini
        if (poidsPiece <= 0) return;
        
        // Ne pas dupliquer
        if (document.getElementById('mode-saisie-controls')) return;
        
        // Créer les contrôles
        const controls = document.createElement('div');
        controls.id = 'mode-saisie-controls';
        controls.style.cssText = `
            margin: 15px 0;
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 8px;
            border-left: 4px solid #667eea;
        `;
        
        controls.innerHTML = `
            <div style="margin-bottom: 10px;">
                <strong>💡 Mode de saisie du prix :</strong>
            </div>
            <div style="display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="radio" name="mode_saisie" value="gramme" checked 
                           style="margin-right: 5px;">
                    <span>Prix au gramme (€/g)</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="radio" name="mode_saisie" value="piece" 
                           style="margin-right: 5px;">
                    <span>Prix par pièce (€)</span>
                </label>
            </div>
        `;
        
        // Insérer avant le form-group du prix
        prixFormGroup.parentNode.insertBefore(controls, prixFormGroup);
        
        // Créer le champ prix par pièce (caché par défaut)
        const prixPieceContainer = document.createElement('div');
        prixPieceContainer.id = 'prix-piece-input-container';
        prixPieceContainer.className = 'form-group';
        prixPieceContainer.style.display = 'none';
        prixPieceContainer.innerHTML = `
            <label>Prix par pièce (€)</label>
            <input type="number" 
                   step="0.01" 
                   id="prix-piece-temp" 
                   placeholder="Ex: 1.50 pour un avocat à 1.50€">
            <small style="color: #6c757d; display: block; margin-top: 5px;">
                Le prix sera automatiquement converti en €/g (${poidsPiece}g par pièce)
            </small>
        `;
        
        // Insérer après les contrôles de mode
        controls.parentNode.insertBefore(prixPieceContainer, controls.nextSibling);
        
        // Attacher les événements
        document.querySelectorAll('input[name="mode_saisie"]').forEach(radio => {
            radio.addEventListener('change', function() {
                modeSaisie = this.value;
                toggleModeSaisie(this.value);
            });
        });
    }
    
    /**
     * Bascule entre les modes de saisie
     */
    function toggleModeSaisie(mode) {
        const prixFormGroup = document.querySelector('input[name="prix_unitaire"]')?.closest('.form-group');
        const prixInput = document.getElementById('prix-unitaire-input') || 
                          document.getElementById('prix_input') ||
                          document.querySelector('input[name="prix_unitaire"]');
        
        const prixPieceContainer = document.getElementById('prix-piece-input-container');
        const prixPieceInput = document.getElementById('prix-piece-temp');
        
        if (!prixFormGroup || !prixInput) return;
        
        if (mode === 'piece') {
            // Masquer le champ prix €/g
            prixFormGroup.style.display = 'none';
            
            // Afficher le champ prix par pièce
            if (prixPieceContainer) {
                prixPieceContainer.style.display = 'block';
            }
            
            // Convertir le prix existant si présent
            const prixGramme = parseFloat(prixInput.value) || 0;
            const poidsPieceInput = document.getElementById('poids-piece-input') || 
                                     document.querySelector('input[name="poids_piece"]');
            const poidsPiece = parseFloat(poidsPieceInput?.value) || 0;
            
            if (prixGramme > 0 && poidsPiece > 0 && prixPieceInput) {
                const prixPiece = prixGramme * poidsPiece;
                prixPieceInput.value = prixPiece.toFixed(2);
            }
            
        } else {
            // Afficher le champ prix €/g
            prixFormGroup.style.display = 'block';
            
            // Masquer le champ prix par pièce
            if (prixPieceContainer) {
                prixPieceContainer.style.display = 'none';
            }
        }
        
        updatePrixHelper();
    }
    
    /**
     * Met à jour le prix en €/g depuis le prix par pièce
     */
    window.updatePrixFromPiece = function() {
        const prixPieceInput = document.getElementById('prix-piece-temp');
        const prixInput = document.getElementById('prix-unitaire-input') || 
                          document.getElementById('prix_input') ||
                          document.querySelector('input[name="prix_unitaire"]');
        const poidsPieceInput = document.getElementById('poids-piece-input') || 
                                document.querySelector('input[name="poids_piece"]');
        
        if (!prixPieceInput || !prixInput || !poidsPieceInput) return;
        
        const prixPiece = parseFloat(prixPieceInput.value) || 0;
        const poidsPiece = parseFloat(poidsPieceInput.value) || 0;
        
        if (prixPiece > 0 && poidsPiece > 0) {
            const prixGramme = prixPiece / poidsPiece;
            prixInput.value = prixGramme.toFixed(6);
            
            updatePrixHelper();
        } else {
            prixInput.value = '';
        }
    };
    
    // ============================================
    // AFFICHAGE DU HELPER DE PRIX
    // ============================================
    
    /**
     * Met à jour le helper de prix selon le contexte
     */
    window.updatePrixHelper = function() {
        const poidsPieceInput = document.getElementById('poids-piece-input') || 
                                document.querySelector('input[name="poids_piece"]');
        const prixLabel = document.getElementById('prix-label-detail');
        const prixHelper = document.getElementById('prix-helper');
        const prixInput = document.getElementById('prix-unitaire-input') || 
                          document.getElementById('prix_input') ||
                          document.querySelector('input[name="prix_unitaire"]');
        const uniteSelect = document.getElementById('unite-select') || 
                            document.querySelector('select[name="unite"]');
        
        if (!prixInput || !uniteSelect || !prixHelper) return;
        
        // Réinitialiser
        prixHelper.innerHTML = '';
        prixHelper.style.display = 'none';
        
        const poidsPiece = poidsPieceInput ? (parseFloat(poidsPieceInput.value) || 0) : 0;
        const unite = uniteSelect.value;
        const prixActuel = parseFloat(prixInput.value) || 0;
        
        // Mettre à jour le label
        if (prixLabel) {
            if (poidsPiece > 0 && unite === 'g') {
                prixLabel.textContent = modeSaisie === 'piece' ? '(€/pièce)' : '(€/g)';
            } else if (unite === 'g') {
                prixLabel.textContent = '(€/g)';
            } else if (unite === 'ml') {
                prixLabel.textContent = '(€/ml)';
            } else {
                prixLabel.textContent = `(€/${unite})`;
            }
        }
        
        // Générer le helper
        if (poidsPiece > 0 && unite === 'g' && modeSaisie === 'gramme') {
            // MODE GRAMME avec poids_piece
            if (prixActuel > 0) {
                const prixParPiece = prixActuel * poidsPiece;
                const prixParKg = prixActuel * 1000;
                
                prixHelper.innerHTML = `
                    <div style="background: linear-gradient(135deg, #e8f9ed, #d4f4dd); 
                                padding: 15px; 
                                border-radius: 8px; 
                                border-left: 3px solid #28a745;
                                margin-top: 10px;">
                        <strong>💡 Conversion automatique :</strong><br>
                        <div style="margin-top: 10px; line-height: 1.8; font-size: 1.05em;">
                            • ${prixActuel.toFixed(6)}€/g = <strong style="color: #28a745; font-size: 1.2em;">${prixParPiece.toFixed(2)}€/pièce</strong><br>
                            • Soit environ <strong>${prixParKg.toFixed(2)}€/kg</strong>
                        </div>
                    </div>
                `;
                prixHelper.style.display = 'block';
            }
            
        } else if (poidsPiece > 0 && unite === 'g' && modeSaisie === 'piece') {
            // MODE PIÈCE
            if (prixActuel > 0) {
                const prixParPiece = prixActuel * poidsPiece;
                const prixParKg = prixActuel * 1000;
                
                prixHelper.innerHTML = `
                    <div style="background: linear-gradient(135deg, #d4edda, #c3e6cb); 
                                padding: 15px; 
                                border-radius: 8px; 
                                border-left: 3px solid #28a745;
                                margin-top: 10px;">
                        <strong>✅ Prix qui sera enregistré :</strong><br>
                        <div style="margin-top: 10px; line-height: 1.8;">
                            • Prix par pièce : <strong style="color: #28a745; font-size: 1.2em;">${prixParPiece.toFixed(2)}€</strong><br>
                            • Prix au gramme : ${prixActuel.toFixed(6)}€/g<br>
                            • Soit environ ${prixParKg.toFixed(2)}€/kg
                        </div>
                    </div>
                `;
                prixHelper.style.display = 'block';
            }
            
        } else if (unite === 'g') {
            // MODE GRAMME classique (sans poids_piece)
            if (prixActuel > 0) {
                const prixParKg = prixActuel * 1000;
                prixHelper.innerHTML = `
                    <small style="color: #28a745; font-weight: bold; display: block; margin-top: 10px;">
                        💡 Équivaut à ${prixParKg.toFixed(2)}€/kg
                    </small>
                `;
                prixHelper.style.display = 'block';
            } else {
                prixHelper.innerHTML = `
                    <small style="color: #6c757d; display: block; margin-top: 10px;">
                        Entrez le prix en €/g (ex: 0.015 pour 15€/kg)
                    </small>
                `;
                prixHelper.style.display = 'block';
            }
            
        } else if (unite === 'ml') {
            // MODE MILLILITRE
            if (prixActuel > 0) {
                const prixParL = prixActuel * 1000;
                prixHelper.innerHTML = `
                    <small style="color: #28a745; font-weight: bold; display: block; margin-top: 10px;">
                        💡 Équivaut à ${prixParL.toFixed(2)}€/L
                    </small>
                `;
                prixHelper.style.display = 'block';
            }
        }
    };
    
    // ============================================
    // ÉVÉNEMENTS
    // ============================================
    
    /**
     * Attache tous les événements nécessaires
     */
    function attachEventListeners() {
        // Unité select
        const uniteSelect = document.getElementById('unite-select') || 
                            document.querySelector('select[name="unite"]');
        
        if (uniteSelect) {
            uniteSelect.addEventListener('change', function() {
                const existingControls = document.getElementById('mode-saisie-controls');
                if (existingControls) {
                    existingControls.remove();
                }
                createModeSaisieControls();
                updatePrixHelper();
            });
        }
        
        // Prix input
        const prixInput = document.getElementById('prix-unitaire-input') || 
                          document.getElementById('prix_input') ||
                          document.querySelector('input[name="prix_unitaire"]');
        
        if (prixInput) {
            prixInput.addEventListener('input', updatePrixHelper);
        }
        
        // Poids pièce input
        const poidsPieceInput = document.getElementById('poids-piece-input') || 
                                document.querySelector('input[name="poids_piece"]');
        
        if (poidsPieceInput) {
            poidsPieceInput.addEventListener('input', function() {
                const existingControls = document.getElementById('mode-saisie-controls');
                if (existingControls) {
                    existingControls.remove();
                }
                createModeSaisieControls();
                updatePrixHelper();
            });
        }
        
        // Prix par pièce (créé dynamiquement)
        document.addEventListener('input', function(e) {
            if (e.target.id === 'prix-piece-temp') {
                window.updatePrixFromPiece();
            }
        });
    }
    
    // ============================================
    // INITIALISATION
    // ============================================
    
    document.addEventListener('DOMContentLoaded', function() {
        // Créer les contrôles de mode
        createModeSaisieControls();
        
        // Attacher les événements
        attachEventListeners();
        
        // Initialiser l'affichage
        updatePrixHelper();
    });
})();
