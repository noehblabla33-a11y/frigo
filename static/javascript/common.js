/**
 * ============================================
 * Fichier: static/javascript/common.js
 * Fonctions JavaScript communes et réutilisables
 * ============================================
 * 
 * Ce fichier centralise :
 * - Confirmations de suppression (data-confirm)
 * - Auto-initialisation des composants
 * - Utilitaires communs
 * 
 * UTILISATION :
 * 1. Inclure ce fichier dans base.html
 * 2. Utiliser les data-attributes pour activer les fonctionnalités
 */

(function() {
    'use strict';

    // ============================================
    // CONFIGURATION
    // ============================================
    
    const CONFIG = {
        // Messages par défaut
        messages: {
            confirmDelete: 'Êtes-vous sûr de vouloir supprimer cet élément ?',
            confirmAction: 'Êtes-vous sûr de vouloir effectuer cette action ?'
        },
        // Sélecteurs
        selectors: {
            confirmable: '[data-confirm]',
            collapsable: '[data-collapsable]',
            searchableSelect: '.searchable-select',
            dynamicForm: '[data-dynamic-form]'
        }
    };

    // ============================================
    // CONFIRMATIONS
    // ============================================
    
    /**
     * Initialise les confirmations automatiques basées sur data-confirm
     * 
     * Usage HTML :
     * <a href="/delete/1" data-confirm="Supprimer cet ingrédient ?">Supprimer</a>
     * <button data-confirm="Êtes-vous sûr ?">Action</button>
     * <form data-confirm="Valider ce formulaire ?">...</form>
     */
    function initConfirmations() {
        document.querySelectorAll(CONFIG.selectors.confirmable).forEach(element => {
            // Éviter la double initialisation
            if (element.dataset.confirmInitialized) return;
            element.dataset.confirmInitialized = 'true';
            
            const message = element.dataset.confirm || CONFIG.messages.confirmAction;
            
            element.addEventListener('click', function(e) {
                if (!confirm(message)) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            });
            
            // Pour les formulaires, intercepter aussi le submit
            if (element.tagName === 'FORM') {
                element.addEventListener('submit', function(e) {
                    if (!confirm(message)) {
                        e.preventDefault();
                        return false;
                    }
                });
            }
        });
    }

    /**
     * Fonction de confirmation manuelle (pour usage dans le code)
     * @param {string} message - Message de confirmation
     * @param {Function} onConfirm - Callback si confirmé
     * @param {Function} onCancel - Callback si annulé (optionnel)
     */
    window.confirmAction = function(message, onConfirm, onCancel) {
        if (confirm(message)) {
            if (typeof onConfirm === 'function') onConfirm();
        } else {
            if (typeof onCancel === 'function') onCancel();
        }
    };

    // ============================================
    // FORMULAIRES DYNAMIQUES (Ingrédients/Étapes)
    // ============================================
    
    /**
     * Gestionnaire générique pour les listes dynamiques
     * (ingrédients dans recettes, étapes, etc.)
     */
    class DynamicList {
        constructor(container, options = {}) {
            this.container = typeof container === 'string' 
                ? document.getElementById(container) 
                : container;
            
            if (!this.container) return;
            
            this.options = {
                itemSelector: options.itemSelector || '.dynamic-item',
                removeButtonSelector: options.removeButtonSelector || '.btn-remove',
                counterName: options.counterName || 'itemCount',
                minItems: options.minItems || 0,
                onAdd: options.onAdd || null,
                onRemove: options.onRemove || null,
                template: options.template || null
            };
            
            this.counter = this.container.querySelectorAll(this.options.itemSelector).length;
            
            // Initialiser le compteur global si spécifié
            if (this.options.counterName) {
                window[this.options.counterName] = this.counter;
            }
            
            this.init();
        }
        
        init() {
            this.updateRemoveButtons();
        }
        
        /**
         * Ajoute un nouvel élément
         * @param {string|Function} template - HTML template ou fonction qui génère le HTML
         */
        add(template) {
            const html = typeof template === 'function' 
                ? template(this.counter) 
                : (template || this.options.template);
            
            if (!html) {
                console.warn('DynamicList: Aucun template fourni');
                return null;
            }
            
            const div = document.createElement('div');
            div.innerHTML = typeof html === 'function' ? html(this.counter) : html;
            const newItem = div.firstElementChild;
            
            if (newItem) {
                // Ajouter l'attribut de données pour l'index
                newItem.dataset.index = this.counter;
                
                this.container.appendChild(newItem);
                this.counter++;
                
                // Mettre à jour le compteur global
                if (this.options.counterName) {
                    window[this.options.counterName] = this.counter;
                }
                
                this.updateRemoveButtons();
                
                // Callback
                if (typeof this.options.onAdd === 'function') {
                    this.options.onAdd(newItem, this.counter - 1);
                }
                
                // Réinitialiser les selects searchable si nécessaire
                if (typeof window.initSelectSearch === 'function') {
                    window.initSelectSearch();
                }
                
                return newItem;
            }
            
            return null;
        }
        
        /**
         * Supprime un élément par son index
         * @param {number} index - Index de l'élément à supprimer
         */
        remove(index) {
            const item = this.container.querySelector(`${this.options.itemSelector}[data-index="${index}"]`);
            
            if (item) {
                const items = this.container.querySelectorAll(this.options.itemSelector);
                
                // Vérifier le minimum
                if (items.length <= this.options.minItems) {
                    console.warn(`DynamicList: Minimum ${this.options.minItems} élément(s) requis`);
                    return false;
                }
                
                // Callback avant suppression
                if (typeof this.options.onRemove === 'function') {
                    this.options.onRemove(item, index);
                }
                
                item.remove();
                this.updateRemoveButtons();
                
                return true;
            }
            
            return false;
        }
        
        /**
         * Met à jour la visibilité des boutons de suppression
         */
        updateRemoveButtons() {
            const items = this.container.querySelectorAll(this.options.itemSelector);
            const canRemove = items.length > this.options.minItems;
            
            items.forEach(item => {
                const btn = item.querySelector(this.options.removeButtonSelector);
                if (btn) {
                    btn.style.display = canRemove ? '' : 'none';
                }
            });
        }
        
        /**
         * Renumérote les éléments (utile pour les étapes)
         * @param {string} numberSelector - Sélecteur de l'élément numéro
         * @param {Function} formatter - Fonction de formatage (index => string)
         */
        renumber(numberSelector, formatter) {
            const items = this.container.querySelectorAll(this.options.itemSelector);
            items.forEach((item, index) => {
                const numberEl = item.querySelector(numberSelector);
                if (numberEl) {
                    numberEl.textContent = formatter ? formatter(index) : (index + 1);
                }
            });
        }
        
        /**
         * Retourne le nombre d'éléments
         */
        get count() {
            return this.container.querySelectorAll(this.options.itemSelector).length;
        }
    }
    
    // Exposer globalement
    window.DynamicList = DynamicList;

    // ============================================
    // UTILITAIRES
    // ============================================
    
    /**
     * Debounce - Limite le nombre d'appels d'une fonction
     */
    window.debounce = function(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    /**
     * Formate un nombre en prix
     */
    window.formatPrice = function(amount, currency = '€') {
        if (isNaN(amount) || amount === null) return '-';
        return parseFloat(amount).toFixed(2) + ' ' + currency;
    };

    /**
     * Parse un nombre de façon sécurisée
     */
    window.parseNumber = function(value, defaultValue = 0) {
        const parsed = parseFloat(value);
        return isNaN(parsed) ? defaultValue : parsed;
    };

    /**
     * Affiche une notification temporaire (toast)
     */
    window.showToast = function(message, type = 'info', duration = 3000) {
        // Créer le conteneur si nécessaire
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }
        
        // Créer le toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideInRight 0.3s ease-out;
            cursor: pointer;
            max-width: 300px;
        `;
        
        // Couleurs selon le type
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        toast.style.background = colors[type] || colors.info;
        if (type === 'warning') toast.style.color = '#333';
        
        toast.textContent = message;
        
        // Fermer au clic
        toast.addEventListener('click', () => toast.remove());
        
        container.appendChild(toast);
        
        // Auto-fermer après la durée
        if (duration > 0) {
            setTimeout(() => {
                toast.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        
        return toast;
    };

    // ============================================
    // AUTO-INITIALISATION
    // ============================================
    
    /**
     * Initialise tous les composants au chargement du DOM
     */
    function initAll() {
        // Confirmations
        initConfirmations();
        
        // Observer pour les éléments ajoutés dynamiquement
        observeDynamicContent();
    }
    
    /**
     * Observe les changements du DOM pour initialiser les nouveaux éléments
     */
    function observeDynamicContent() {
        const observer = new MutationObserver((mutations) => {
            let hasNewNodes = false;
            
            mutations.forEach(mutation => {
                if (mutation.addedNodes.length > 0) {
                    hasNewNodes = true;
                }
            });
            
            if (hasNewNodes) {
                // Réinitialiser les confirmations pour les nouveaux éléments
                initConfirmations();
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // ============================================
    // STYLES POUR LES TOASTS
    // ============================================
    
    function injectToastStyles() {
        if (document.getElementById('common-js-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'common-js-styles';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    opacity: 0;
                    transform: translateX(100%);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            @keyframes slideOutRight {
                from {
                    opacity: 1;
                    transform: translateX(0);
                }
                to {
                    opacity: 0;
                    transform: translateX(100%);
                }
            }
        `;
        document.head.appendChild(style);
    }

    // ============================================
    // INITIALISATION AU CHARGEMENT
    // ============================================
    
    document.addEventListener('DOMContentLoaded', () => {
        injectToastStyles();
        initAll();
    });

    // Exposer les fonctions pour utilisation externe
    window.CommonJS = {
        initConfirmations,
        DynamicList,
        CONFIG
    };

})();
