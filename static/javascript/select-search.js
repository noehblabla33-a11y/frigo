// ============================================
// Fichier: static/javascript/select-search.js
// Transforme les selects en champs de recherche
// VERSION CORRIGÉE - Protection double chargement
// ============================================

// ✅ PROTECTION GLOBALE : Éviter de redéclarer si déjà chargé
if (typeof window.SelectSearch === 'undefined') {

class SelectSearch {
    constructor(selectElement) {
        // ✅ PROTECTION : Vérifier si déjà initialisé
        if (!selectElement) {
            console.warn('SelectSearch: Element null ou undefined');
            return;
        }
        
        // Vérifier si déjà initialisé via data attribute
        if (selectElement.dataset.selectSearchInit === 'true') {
            console.warn('SelectSearch: Element déjà initialisé, ignoré');
            return;
        }
        
        // Vérifier si déjà dans un wrapper
        if (selectElement.parentElement && 
            selectElement.parentElement.classList.contains('select-search-wrapper')) {
            console.warn('SelectSearch: Element déjà dans un wrapper, ignoré');
            return;
        }
        
        this.select = selectElement;
        this.options = Array.from(selectElement.options);
        this.selectedValue = selectElement.value;
        this.isInitialized = false;
        
        // Log pour debug
        console.log(`SelectSearch: Initialisation de ${selectElement.id || selectElement.name} avec ${this.options.length} options`);
        
        this.init();
    }

    init() {
        // ✅ Double vérification
        if (this.isInitialized) return;
        
        // Marquer comme initialisé AVANT de modifier le DOM
        this.select.dataset.selectSearchInit = 'true';
        this.isInitialized = true;
        
        // Créer le wrapper
        this.wrapper = document.createElement('div');
        this.wrapper.className = 'select-search-wrapper';
        
        // Créer l'input de recherche
        this.input = document.createElement('input');
        this.input.type = 'text';
        this.input.className = 'select-search-input';
        this.input.placeholder = this.select.getAttribute('placeholder') || 'Rechercher...';
        this.input.autocomplete = 'off';
        
        // Afficher la valeur sélectionnée si elle existe
        const selectedOption = this.options.find(opt => opt.value === this.selectedValue);
        if (selectedOption && selectedOption.value) {
            this.input.value = selectedOption.text;
        }
        
        // Créer le dropdown
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'select-search-dropdown';
        
        // ✅ Cacher le select original (mais le garder fonctionnel)
        this.select.style.display = 'none';
        this.select.setAttribute('aria-hidden', 'true');
        this.select.tabIndex = -1;
        
        // Insérer le wrapper
        this.select.parentNode.insertBefore(this.wrapper, this.select);
        this.wrapper.appendChild(this.input);
        this.wrapper.appendChild(this.dropdown);
        this.wrapper.appendChild(this.select);
        
        // Attacher les événements
        this.attachEvents();
        
        console.log(`SelectSearch: ${this.select.id || this.select.name} initialisé avec succès`);
    }

    attachEvents() {
        // Focus sur l'input : afficher toutes les options
        this.input.addEventListener('focus', () => {
            this.input.select();
            this.showDropdown();
        });

        // Saisie dans l'input : filtrer les options
        this.input.addEventListener('input', () => {
            this.filterOptions(this.input.value);
        });

        // Clic en dehors : fermer le dropdown
        this._documentClickHandler = (e) => {
            if (!this.wrapper.contains(e.target)) {
                this.hideDropdown();
            }
        };
        document.addEventListener('click', this._documentClickHandler);

        // Navigation au clavier
        this.input.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
        });
        
        // ✅ Sync si le select change programmatiquement
        this.select.addEventListener('change', () => {
            this.syncFromSelect();
        });
    }

    showDropdown() {
        this.filterOptions(this.input.value);
        this.dropdown.classList.add('active');
    }

    hideDropdown() {
        this.dropdown.classList.remove('active');
    }

    filterOptions(searchTerm) {
        this.dropdown.innerHTML = '';
        const term = searchTerm.toLowerCase().trim();
        
        // Recharger les options au cas où elles auraient changé
        this.options = Array.from(this.select.options);
        
        const filteredOptions = this.options.filter(option => {
            if (!option.value) return false; // Ignorer l'option vide
            return option.text.toLowerCase().includes(term);
        });

        if (filteredOptions.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'select-search-no-results';
            noResults.textContent = 'Aucun résultat trouvé';
            this.dropdown.appendChild(noResults);
            return;
        }

        filteredOptions.forEach((option, index) => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'select-search-option';
            optionDiv.textContent = option.text;
            optionDiv.dataset.value = option.value;
            optionDiv.dataset.index = index;
            
            // Copier les data attributes
            Array.from(option.attributes).forEach(attr => {
                if (attr.name.startsWith('data-')) {
                    optionDiv.setAttribute(attr.name, attr.value);
                }
            });

            if (option.value === this.selectedValue) {
                optionDiv.classList.add('selected');
            }

            optionDiv.addEventListener('click', () => {
                this.selectOption(option, optionDiv);
            });

            this.dropdown.appendChild(optionDiv);
        });
    }

    selectOption(option, optionDiv) {
        this.selectedValue = option.value;
        this.select.value = option.value;
        this.input.value = option.text;
        
        // Déclencher l'événement change sur le select original
        const event = new Event('change', { bubbles: true });
        this.select.dispatchEvent(event);
        
        // Mettre à jour les classes
        this.dropdown.querySelectorAll('.select-search-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        if (optionDiv) {
            optionDiv.classList.add('selected');
        }
        
        this.hideDropdown();
    }
    
    // ✅ Synchroniser l'input depuis le select (si changé programmatiquement)
    syncFromSelect() {
        const newValue = this.select.value;
        if (newValue !== this.selectedValue) {
            this.selectedValue = newValue;
            const selectedOption = this.options.find(opt => opt.value === newValue);
            this.input.value = selectedOption ? selectedOption.text : '';
        }
    }

    handleKeyboard(e) {
        const options = this.dropdown.querySelectorAll('.select-search-option');
        if (options.length === 0) return;

        const highlighted = this.dropdown.querySelector('.select-search-option.highlighted');
        let currentIndex = highlighted ? parseInt(highlighted.dataset.index) : -1;

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                currentIndex = Math.min(currentIndex + 1, options.length - 1);
                this.highlightOption(currentIndex);
                break;

            case 'ArrowUp':
                e.preventDefault();
                currentIndex = Math.max(currentIndex - 1, 0);
                this.highlightOption(currentIndex);
                break;

            case 'Enter':
                e.preventDefault();
                if (highlighted) {
                    highlighted.click();
                } else if (options.length === 1) {
                    options[0].click();
                }
                break;

            case 'Escape':
                this.hideDropdown();
                this.input.blur();
                break;
                
            case 'Tab':
                this.hideDropdown();
                break;
        }
    }

    highlightOption(index) {
        const options = this.dropdown.querySelectorAll('.select-search-option');
        options.forEach(opt => opt.classList.remove('highlighted'));
        
        if (options[index]) {
            options[index].classList.add('highlighted');
            options[index].scrollIntoView({ block: 'nearest' });
        }
    }

    // Méthode pour mettre à jour les options (utile pour les selects dynamiques)
    updateOptions() {
        this.options = Array.from(this.select.options);
        if (this.dropdown.classList.contains('active')) {
            this.filterOptions(this.input.value);
        }
    }
    
    // ✅ Méthode pour réinitialiser (vider la sélection)
    reset() {
        this.selectedValue = '';
        this.select.value = '';
        this.input.value = '';
    }
    
    // ✅ Méthode pour détruire l'instance (cleanup)
    destroy() {
        if (this._documentClickHandler) {
            document.removeEventListener('click', this._documentClickHandler);
        }
        
        // Remettre le select visible
        this.select.style.display = '';
        this.select.removeAttribute('aria-hidden');
        this.select.tabIndex = 0;
        this.select.dataset.selectSearchInit = 'false';
        
        // Retirer le wrapper
        if (this.wrapper && this.wrapper.parentNode) {
            this.wrapper.parentNode.insertBefore(this.select, this.wrapper);
            this.wrapper.remove();
        }
        
        this.isInitialized = false;
    }
}

// ============================================
// FONCTIONS GLOBALES
// ============================================

/**
 * Initialise tous les selects avec recherche
 * @param {string} selector - Sélecteur CSS (défaut: '.searchable-select')
 * @returns {SelectSearch[]} - Tableau des instances créées
 */
function initSelectSearch(selector = '.searchable-select') {
    const selects = document.querySelectorAll(selector);
    const instances = [];
    
    console.log(`initSelectSearch: Trouvé ${selects.length} select(s) avec le sélecteur "${selector}"`);
    
    selects.forEach((select, i) => {
        // ✅ Triple vérification pour éviter les doublons
        if (select.dataset.selectSearchInit === 'true') {
            console.log(`initSelectSearch: Select #${i} déjà initialisé, ignoré`);
            return;
        }
        if (select.parentElement && 
            select.parentElement.classList.contains('select-search-wrapper')) {
            console.log(`initSelectSearch: Select #${i} déjà dans un wrapper, ignoré`);
            return;
        }
        
        const instance = new SelectSearch(select);
        if (instance.isInitialized) {
            instances.push(instance);
        }
    });
    
    console.log(`initSelectSearch: ${instances.length} instance(s) créée(s)`);
    return instances;
}

/**
 * Initialise un select spécifique (pour les éléments ajoutés dynamiquement)
 * @param {HTMLSelectElement} select - L'élément select à transformer
 * @returns {SelectSearch|null} - L'instance créée ou null si déjà initialisé
 */
function initSingleSelectSearch(select) {
    if (!select) return null;
    
    // Vérifier si déjà initialisé
    if (select.dataset.selectSearchInit === 'true') {
        return null;
    }
    
    const instance = new SelectSearch(select);
    return instance.isInitialized ? instance : null;
}

// ============================================
// INITIALISATION AUTOMATIQUE
// ============================================

// Initialiser automatiquement au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    console.log('SelectSearch: DOMContentLoaded, initialisation...');
    initSelectSearch();
});

// ✅ Observer les nouveaux éléments ajoutés au DOM
const selectSearchObserver = new MutationObserver((mutations) => {
    let hasNewSelects = false;
    
    mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
                // Vérifier si c'est un select searchable
                if (node.matches && node.matches('.searchable-select')) {
                    hasNewSelects = true;
                }
                // Vérifier les enfants
                if (node.querySelectorAll) {
                    const selects = node.querySelectorAll('.searchable-select');
                    if (selects.length > 0) {
                        hasNewSelects = true;
                    }
                }
            }
        });
    });
    
    // Initialiser les nouveaux selects (avec un petit délai pour laisser le DOM se stabiliser)
    if (hasNewSelects) {
        setTimeout(() => {
            initSelectSearch();
        }, 10);
    }
});

// Démarrer l'observation après le chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    selectSearchObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Exporter pour utilisation dans d'autres scripts
window.SelectSearch = SelectSearch;
window.initSelectSearch = initSelectSearch;
window.initSingleSelectSearch = initSingleSelectSearch;

console.log('SelectSearch: Script chargé');

} else {
    console.log('SelectSearch: Script déjà chargé, ignoré');
}
