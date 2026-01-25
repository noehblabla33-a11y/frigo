/**
 * modal.js
 * Système de gestion des modals/popups
 */

(function() {
    'use strict';
    
    /**
     * Ouvre une modal
     * @param {string} modalId - ID de la modal à ouvrir
     */
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal #${modalId} not found`);
            return;
        }
        
        modal.classList.add('active');
        document.body.classList.add('modal-open');
        
        // Focus sur le premier champ du formulaire
        setTimeout(() => {
            const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);
    };
    
    /**
     * Ferme une modal
     * @param {string} modalId - ID de la modal à fermer
     */
    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        // Animation de fermeture
        modal.classList.add('closing');
        
        setTimeout(() => {
            modal.classList.remove('active', 'closing');
            document.body.classList.remove('modal-open');
        }, 200);
    };
    
    /**
     * Initialisation au chargement du DOM
     */
    document.addEventListener('DOMContentLoaded', function() {
        // Fermer en cliquant sur l'overlay
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', function(e) {
                if (e.target === overlay) {
                    closeModal(overlay.id);
                }
            });
        });
        
        // Fermer avec la touche Échap
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal-overlay.active');
                if (activeModal) {
                    closeModal(activeModal.id);
                }
            }
        });
        
        // Boutons de fermeture
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', function() {
                const modal = this.closest('.modal-overlay');
                if (modal) {
                    closeModal(modal.id);
                }
            });
        });
        
        // Boutons d'annulation
        document.querySelectorAll('[data-modal-cancel]').forEach(btn => {
            btn.addEventListener('click', function() {
                const modalId = this.getAttribute('data-modal-cancel');
                closeModal(modalId);
            });
        });
    });
    
})();
