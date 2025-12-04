// ============================================
// Fichier: static/javascript/collapsable.js
// Gestion des sections collapsables (formulaires)
// ============================================

/**
 * Initialise une section collapsable
 */
function initCollapsable(sectionId) {
    const header = document.querySelector(`[data-collapsable="${sectionId}"]`);
    const content = document.getElementById(sectionId);
    
    if (!header || !content) return;
    
    // Ajouter l'icône si elle n'existe pas
    let icon = header.querySelector('.collapsable-icon');
    if (!icon) {
        icon = document.createElement('span');
        icon.className = 'collapsable-icon';
        icon.textContent = '▼';
        header.appendChild(icon);
    }
    
    // Récupérer l'état sauvegardé (localStorage)
    const savedState = localStorage.getItem(`collapsable_${sectionId}`);
    const isCollapsed = savedState === 'collapsed';
    
    // Appliquer l'état initial
    if (isCollapsed) {
        content.style.display = 'none';
        icon.textContent = '▶';
        header.classList.add('collapsed');
    } else {
        content.style.display = 'block';
        icon.textContent = '▼';
        header.classList.remove('collapsed');
    }
    
    // Événement de clic
    header.addEventListener('click', () => {
        toggleCollapsable(sectionId);
    });
    
    // Rendre le header visuellement cliquable
    header.style.cursor = 'pointer';
    header.style.userSelect = 'none';
}

/**
 * Bascule l'état d'une section
 */
function toggleCollapsable(sectionId) {
    const header = document.querySelector(`[data-collapsable="${sectionId}"]`);
    const content = document.getElementById(sectionId);
    const icon = header.querySelector('.collapsable-icon');
    
    if (!header || !content || !icon) return;
    
    const isCurrentlyVisible = content.style.display !== 'none';
    
    if (isCurrentlyVisible) {
        // Collapse avec animation
        content.style.maxHeight = content.scrollHeight + 'px';
        content.style.overflow = 'hidden';
        content.style.transition = 'max-height 0.3s ease-out, opacity 0.3s ease-out';
        
        // Force reflow
        content.offsetHeight;
        
        content.style.maxHeight = '0';
        content.style.opacity = '0';
        
        setTimeout(() => {
            content.style.display = 'none';
            content.style.maxHeight = '';
            content.style.opacity = '';
            content.style.overflow = '';
            content.style.transition = '';
        }, 300);
        
        icon.textContent = '▶';
        header.classList.add('collapsed');
        localStorage.setItem(`collapsable_${sectionId}`, 'collapsed');
    } else {
        // Expand avec animation
        content.style.display = 'block';
        content.style.maxHeight = '0';
        content.style.opacity = '0';
        content.style.overflow = 'hidden';
        content.style.transition = 'max-height 0.3s ease-in, opacity 0.3s ease-in';
        
        // Force reflow
        content.offsetHeight;
        
        const height = content.scrollHeight;
        content.style.maxHeight = height + 'px';
        content.style.opacity = '1';
        
        setTimeout(() => {
            content.style.maxHeight = '';
            content.style.opacity = '';
            content.style.overflow = '';
            content.style.transition = '';
        }, 300);
        
        icon.textContent = '▼';
        header.classList.remove('collapsed');
        localStorage.setItem(`collapsable_${sectionId}`, 'expanded');
    }
}

/**
 * Initialise toutes les sections collapsables au chargement
 */
document.addEventListener('DOMContentLoaded', () => {
    // Trouver tous les headers avec data-collapsable
    document.querySelectorAll('[data-collapsable]').forEach(header => {
        const sectionId = header.getAttribute('data-collapsable');
        initCollapsable(sectionId);
    });
});

// Exposer les fonctions globalement
window.toggleCollapsable = toggleCollapsable;
window.initCollapsable = initCollapsable;
