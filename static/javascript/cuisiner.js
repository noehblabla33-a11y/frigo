// ============================================
// Fichier: static/cuisiner.js
// Mode cuisson avec minuteurs interactifs
// ============================================

// État global des minuteurs
const timers = {};
const completedSteps = new Set();

// Initialiser les minuteurs (à appeler avec les données du template)
function initTimers(etapesData) {
    etapesData.forEach(etape => {
        if (etape.duree_minutes) {
            timers[etape.id] = {
                duration: etape.duree_minutes * 60,
                remaining: etape.duree_minutes * 60,
                interval: null,
                isPaused: false
            };
        }
    });
}

function startTimer(etapeId, minutes) {
    if (timers[etapeId].interval) return; // Déjà démarré
    
    document.getElementById(`start-${etapeId}`).style.display = 'none';
    document.getElementById(`pause-${etapeId}`).style.display = 'inline-block';
    
    const statusBadge = document.querySelector(`#status-${etapeId} .status-badge`);
    statusBadge.className = 'status-badge status-in-progress';
    statusBadge.textContent = 'En cours';
    
    timers[etapeId].interval = setInterval(() => {
        if (!timers[etapeId].isPaused) {
            timers[etapeId].remaining--;
            
            const mins = Math.floor(timers[etapeId].remaining / 60);
            const secs = timers[etapeId].remaining % 60;
            
            document.getElementById(`timer-time-${etapeId}`).textContent = 
                `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
            
            // Barre de progression
            const progress = ((timers[etapeId].duration - timers[etapeId].remaining) / timers[etapeId].duration) * 100;
            document.getElementById(`progress-${etapeId}`).style.width = progress + '%';
            
            // Changement de couleur selon le temps restant
            const timerDisplay = document.getElementById(`timer-display-${etapeId}`);
            if (timers[etapeId].remaining <= 10) {
                timerDisplay.classList.add('timer-critical');
            } else if (timers[etapeId].remaining <= 60) {
                timerDisplay.classList.add('timer-warning');
            }
            
            // Timer terminé
            if (timers[etapeId].remaining <= 0) {
                clearInterval(timers[etapeId].interval);
                timers[etapeId].interval = null;
                
                timerDisplay.classList.add('timer-finished');
                document.getElementById(`pause-${etapeId}`).style.display = 'none';
                document.getElementById(`start-${etapeId}`).style.display = 'none';
                
                // Jouer le son d'alarme
                playAlarm();
                
                // Notification visuelle
                showNotification(`⏰ Timer terminé pour l'étape ${getEtapeOrdre(etapeId)} !`);
                
                // Animation de la carte
                const card = document.getElementById(`etape-${etapeId}`);
                card.classList.add('etape-timer-finished');
            }
        }
    }, 1000);
}

function pauseTimer(etapeId) {
    timers[etapeId].isPaused = true;
    document.getElementById(`pause-${etapeId}`).style.display = 'none';
    document.getElementById(`resume-${etapeId}`).style.display = 'inline-block';
}

function resumeTimer(etapeId) {
    timers[etapeId].isPaused = false;
    document.getElementById(`resume-${etapeId}`).style.display = 'none';
    document.getElementById(`pause-${etapeId}`).style.display = 'inline-block';
}

function resetTimer(etapeId, minutes) {
    if (timers[etapeId].interval) {
        clearInterval(timers[etapeId].interval);
        timers[etapeId].interval = null;
    }
    
    timers[etapeId].remaining = minutes * 60;
    timers[etapeId].isPaused = false;
    
    document.getElementById(`timer-time-${etapeId}`).textContent = 
        `${String(minutes).padStart(2, '0')}:00`;
    document.getElementById(`progress-${etapeId}`).style.width = '0%';
    
    document.getElementById(`start-${etapeId}`).style.display = 'inline-block';
    document.getElementById(`pause-${etapeId}`).style.display = 'none';
    document.getElementById(`resume-${etapeId}`).style.display = 'none';
    
    const timerDisplay = document.getElementById(`timer-display-${etapeId}`);
    timerDisplay.classList.remove('timer-warning', 'timer-critical', 'timer-finished');
    
    const card = document.getElementById(`etape-${etapeId}`);
    card.classList.remove('etape-timer-finished');
}

function completeStep(etapeId) {
    // Arrêter le timer s'il est actif
    if (timers[etapeId] && timers[etapeId].interval) {
        clearInterval(timers[etapeId].interval);
        timers[etapeId].interval = null;
    }
    
    completedSteps.add(etapeId);
    
    const statusBadge = document.querySelector(`#status-${etapeId} .status-badge`);
    statusBadge.className = 'status-badge status-completed';
    statusBadge.textContent = '✓ Terminée';
    
    const card = document.getElementById(`etape-${etapeId}`);
    card.classList.add('etape-completed');
    
    updateGlobalProgress();
    
    // Faire défiler jusqu'à la prochaine étape
    scrollToNextStep(etapeId);
}

function updateGlobalProgress() {
    const totalEtapes = document.querySelectorAll('.etape-card').length;
    const completed = completedSteps.size;
    const percentage = (completed / totalEtapes) * 100;
    
    document.getElementById('progress-text').textContent = `${completed} / ${totalEtapes}`;
    document.getElementById('global-progress').style.width = percentage + '%';
    
    if (completed === totalEtapes) {
        showNotification('🎉 Félicitations ! Toutes les étapes sont terminées !');
    }
}

function scrollToNextStep(currentEtapeId) {
    const allEtapes = document.querySelectorAll('.etape-card');
    let foundCurrent = false;
    
    for (let etape of allEtapes) {
        if (foundCurrent && !completedSteps.has(parseInt(etape.dataset.etapeId))) {
            etape.scrollIntoView({ behavior: 'smooth', block: 'center' });
            break;
        }
        if (parseInt(etape.dataset.etapeId) === currentEtapeId) {
            foundCurrent = true;
        }
    }
}

function getEtapeOrdre(etapeId) {
    const card = document.getElementById(`etape-${etapeId}`);
    return card.querySelector('.etape-numero').textContent;
}

function playAlarm() {
    const alarm = document.getElementById('timer-alarm');
    if (alarm) {
        alarm.currentTime = 0;
        alarm.play().catch(err => {
            console.log('Impossible de jouer le son:', err);
            // Fallback : utiliser l'API Web Notification si disponible
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('Timer terminé !', {
                    body: 'Une étape de votre recette est terminée.',
                    icon: '/static/icon.png'
                });
            }
        });
    }
}

function showNotification(message) {
    // Créer une notification en haut de l'écran
    const notification = document.createElement('div');
    notification.className = 'cooking-notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function reinitialiser() {
    if (!confirm('Voulez-vous vraiment réinitialiser toutes les étapes ?')) {
        return;
    }
    
    // Arrêter tous les timers
    for (let etapeId in timers) {
        if (timers[etapeId].interval) {
            clearInterval(timers[etapeId].interval);
        }
        resetTimer(parseInt(etapeId), timers[etapeId].duration / 60);
    }
    
    // Réinitialiser les étapes complétées
    completedSteps.clear();
    
    document.querySelectorAll('.etape-card').forEach(card => {
        card.classList.remove('etape-completed', 'etape-timer-finished');
        const statusBadge = card.querySelector('.status-badge');
        statusBadge.className = 'status-badge status-pending';
        statusBadge.textContent = 'En attente';
    });
    
    // Réinitialiser les checkboxes
    document.querySelectorAll('.ingredient-checkbox').forEach(cb => cb.checked = false);
    
    updateGlobalProgress();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function toggleSection(sectionId) {
    const content = document.getElementById(`content-${sectionId}`);
    const icon = document.getElementById(`toggle-${sectionId}`);
    
    if (!content || !icon) return;
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.textContent = '▼';
    } else {
        content.style.display = 'none';
        icon.textContent = '▶';
    }
}

// Demander la permission pour les notifications
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Empêcher la fermeture accidentelle de la page pendant la cuisson
function preventAccidentalClose() {
    window.addEventListener('beforeunload', (e) => {
        const totalEtapes = document.querySelectorAll('.etape-card').length;
        if (completedSteps.size > 0 && completedSteps.size < totalEtapes) {
            e.preventDefault();
            e.returnValue = 'Vous avez des étapes en cours. Voulez-vous vraiment quitter ?';
        }
    });
}

// Exposition des fonctions globales
window.initTimers = initTimers;
window.startTimer = startTimer;
window.pauseTimer = pauseTimer;
window.resumeTimer = resumeTimer;
window.resetTimer = resetTimer;
window.completeStep = completeStep;
window.reinitialiser = reinitialiser;
window.toggleSection = toggleSection;

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    requestNotificationPermission();
    preventAccidentalClose();
});
