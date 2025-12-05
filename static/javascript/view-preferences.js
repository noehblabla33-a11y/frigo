/* ============================================ */
/* Fichier: static/javascript/view-preferences.js */
/* GESTION DES PRÉFÉRENCES DE VUE AVEC COOKIES */
/* Pour les pages: ingrédients, frigo, recettes */
/* ============================================ */

/**
 * Gestionnaire de cookies
 * Permet de sauvegarder et récupérer les préférences utilisateur
 */
const CookieManager = {
    /**
     * Définir un cookie
     * @param {string} name - Nom du cookie
     * @param {string} value - Valeur du cookie
     * @param {number} days - Nombre de jours avant expiration (365 par défaut)
     */
    set: function(name, value, days = 365) {
        let expires = "";
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax";
        console.log(`✅ Cookie sauvegardé: ${name} = ${value}`);
    },
    
    /**
     * Récupérer un cookie
     * @param {string} name - Nom du cookie
     * @returns {string|null} - Valeur du cookie ou null si non trouvé
     */
    get: function(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) {
                const value = c.substring(nameEQ.length, c.length);
                console.log(`📖 Cookie lu: ${name} = ${value}`);
                return value;
            }
        }
        console.log(`❌ Cookie non trouvé: ${name}`);
        return null;
    },
    
    /**
     * Supprimer un cookie
     * @param {string} name - Nom du cookie à supprimer
     */
    delete: function(name) {
        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        console.log(`🗑️ Cookie supprimé: ${name}`);
    }
};

/**
 * Gestionnaire des préférences de vue
 * Gère l'affichage grille/liste et sauvegarde les préférences
 */
const ViewPreferencesManager = {
    // Nom de la page courante (ingredients, frigo, recettes)
    currentPage: null,
    
    // Vue par défaut si aucune préférence n'est sauvegardée
    defaultView: 'grid',
    
    /**
     * Initialiser le gestionnaire de vue
     * @param {string} pageName - Nom de la page (ingredients, frigo, recettes)
     */
    init: function(pageName) {
        if (!pageName) {
            console.error('❌ ViewPreferencesManager: Nom de page requis');
            return;
        }
        
        this.currentPage = pageName;
        console.log(`🎨 Initialisation des préférences de vue pour: ${pageName}`);
        
        // Charger la vue sauvegardée
        const savedView = this.loadViewPreference();
        
        // Si une vue est sauvegardée et différente de l'URL actuelle, rediriger
        const urlParams = new URLSearchParams(window.location.search);
        const currentView = urlParams.get('view') || this.defaultView;
        
        if (savedView && savedView !== currentView) {
            console.log(`🔄 Redirection vers la vue sauvegardée: ${savedView}`);
            this.redirectToView(savedView);
        } else {
            // Appliquer les styles appropriés
            this.applyViewStyles(currentView);
        }
        
        // Attacher les événements aux boutons de toggle
        this.attachEventListeners();
    },
    
    /**
     * Charger la préférence de vue depuis les cookies
     * @returns {string|null} - Vue sauvegardée ou null
     */
    loadViewPreference: function() {
        const cookieName = `view_${this.currentPage}`;
        return CookieManager.get(cookieName);
    },
    
    /**
     * Sauvegarder la préférence de vue dans les cookies
     * @param {string} view - Vue à sauvegarder (grid ou list)
     */
    saveViewPreference: function(view) {
        const cookieName = `view_${this.currentPage}`;
        CookieManager.set(cookieName, view);
        console.log(`💾 Préférence sauvegardée pour ${this.currentPage}: ${view}`);
    },
    
    /**
     * Rediriger vers une vue spécifique en conservant les autres paramètres
     * @param {string} view - Vue cible (grid ou list)
     */
    redirectToView: function(view) {
        const url = new URL(window.location);
        url.searchParams.set('view', view);
        window.location.href = url.toString();
    },
    
    /**
     * Appliquer les styles CSS appropriés selon la vue
     * @param {string} view - Vue actuelle (grid ou list)
     */
    applyViewStyles: function(view) {
        // Marquer le bouton actif
        const buttons = document.querySelectorAll('.view-toggle-btn');
        buttons.forEach(btn => {
            const btnView = btn.href ? new URL(btn.href).searchParams.get('view') : null;
            if (btnView === view) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        console.log(`✨ Styles appliqués pour la vue: ${view}`);
    },
    
    /**
     * Attacher les événements de clic aux boutons de toggle
     */
    attachEventListeners: function() {
        const buttons = document.querySelectorAll('.view-toggle-btn');
        
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Ne pas empêcher le comportement par défaut du lien
                // mais sauvegarder la préférence avant la navigation
                const btnView = new URL(btn.href).searchParams.get('view');
                if (btnView) {
                    this.saveViewPreference(btnView);
                }
            });
        });
        
        console.log(`🔗 ${buttons.length} bouton(s) de toggle configuré(s)`);
    },
    
    /**
     * Réinitialiser les préférences de vue (pour debug)
     */
    reset: function() {
        const cookieName = `view_${this.currentPage}`;
        CookieManager.delete(cookieName);
        console.log(`🔄 Préférences réinitialisées pour ${this.currentPage}`);
    }
};

/**
 * Auto-initialisation au chargement du DOM
 * Détecte automatiquement la page courante depuis le body
 */
document.addEventListener('DOMContentLoaded', function() {
    // Détecter la page courante depuis l'attribut data-page du body
    const body = document.body;
    const pageName = body.dataset.page;
    
    if (pageName) {
        ViewPreferencesManager.init(pageName);
    } else {
        console.warn('⚠️ Attribut data-page non trouvé sur <body>. ViewPreferencesManager non initialisé.');
    }
});

// Exposer globalement pour usage en console (debug)
window.ViewPreferencesManager = ViewPreferencesManager;
window.CookieManager = CookieManager;
