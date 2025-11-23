// ============================================
// Fichier: static/select-search.js
// Transforme les selects en champs de recherche
// ============================================

class SelectSearch {
    constructor(selectElement) {
        this.select = selectElement;
        this.options = Array.from(selectElement.options);
        this.selectedValue = selectElement.value;
        this.init();
    }

    init() {
        // Créer le wrapper
        this.wrapper = document.createElement('div');
        this.wrapper.className = 'select-search-wrapper';
        
        // Créer l'input de recherche
        this.input = document.createElement('input');
        this.input.type = 'text';
        this.input.className = 'select-search-input';
        this.input.placeholder = this.select.getAttribute('placeholder') || 'Rechercher...';
        
        // Afficher la valeur sélectionnée si elle existe
        const selectedOption = this.options.find(opt => opt.value === this.selectedValue);
        if (selectedOption && selectedOption.value) {
            this.input.value = selectedOption.text;
        }
        
        // Créer le dropdown
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'select-search-dropdown';
        
        // Remplacer le select par le wrapper
        this.select.parentNode.insertBefore(this.wrapper, this.select);
        this.wrapper.appendChild(this.input);
        this.wrapper.appendChild(this.dropdown);
        this.wrapper.appendChild(this.select);
        
        // Attacher les événements
        this.attachEvents();
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
        document.addEventListener('click', (e) => {
            if (!this.wrapper.contains(e.target)) {
                this.hideDropdown();
            }
        });

        // Navigation au clavier
        this.input.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
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
        optionDiv.classList.add('selected');
        
        this.hideDropdown();
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
}

// Fonction pour initialiser tous les selects avec recherche
function initSelectSearch(selector = '.searchable-select') {
    const selects = document.querySelectorAll(selector);
    const instances = [];
    
    selects.forEach(select => {
        // Ne pas réinitialiser si déjà fait
        if (select.parentElement.classList.contains('select-search-wrapper')) {
            return;
        }
        instances.push(new SelectSearch(select));
    });
    
    return instances;
}

// Initialiser automatiquement au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    initSelectSearch();
});

// Exporter pour utilisation dans d'autres scripts
window.SelectSearch = SelectSearch;
window.initSelectSearch = initSelectSearch;
