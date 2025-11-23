// ============================================
// Fichier: static/courses.js
// Gestion de la liste de courses et calcul du budget
// ============================================

function updateTotal() {
    const inputs = document.querySelectorAll('.quantite-input');
    let total = 0;
    
    inputs.forEach(input => {
        const prix = parseFloat(input.dataset.prix) || 0;
        const quantite = parseFloat(input.value) || 0;
        total += prix * quantite;
    });
    
    const totalFooter = document.getElementById('total-footer');
    if (totalFooter && total > 0) {
        totalFooter.textContent = total.toFixed(2) + ' €';
    }
}

function initQuantiteInputs() {
    const inputs = document.querySelectorAll('.quantite-input');
    
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            const prix = parseFloat(this.dataset.prix) || 0;
            const quantite = parseFloat(this.value) || 0;
            const itemId = this.dataset.itemId;
            const prixLigne = document.getElementById('prix-' + itemId);
            
            if (prix > 0 && prixLigne) {
                const total = prix * quantite;
                prixLigne.innerHTML = `<span class="prix-estime">${total.toFixed(2)} €</span>`;
            }
            
            // Recalculer le total
            updateTotal();
        });
    });
}

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    initQuantiteInputs();
});
