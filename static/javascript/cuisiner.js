/**
 * cuisiner.js - Gestion du mode cuisine interactif
 * VERSION CORRIGÉE - Compatible avec préfixe rd-
 */

// État des timers
const timers = {};
const completedSteps = new Set();

/**
 * Démarre un timer pour une étape
 */
function startTimer(etapeId, minutes) {
    // Arrêter le timer existant s'il y en a un
    if (timers[etapeId] && timers[etapeId].interval) {
        clearInterval(timers[etapeId].interval);
    }
    
    const totalSeconds = minutes * 60;
    timers[etapeId] = {
        remaining: totalSeconds,
        total: totalSeconds,
        interval: null,
        isPaused: false
    };
    
    // Masquer le bouton start, afficher pause
    document.getElementById(`start-${etapeId}`).style.display = 'none';
    document.getElementById(`pause-${etapeId}`).style.display = 'inline-block';
    document.getElementById(`resume-${etapeId}`).style.display = 'none';
    
    // Mettre à jour le statut
    updateStepStatus(etapeId, 'progress');
    
    // Démarrer l'interval
    timers[etapeId].interval = setInterval(() => {
        if (timers[etapeId].remaining > 0) {
            timers[etapeId].remaining--;
            updateTimerDisplay(etapeId);
        } else {
            // Timer terminé
            clearInterval(timers[etapeId].interval);
            timers[etapeId].interval = null;
            timerFinished(etapeId);
        }
    }, 1000);
}

/**
 * Met en pause un timer
 */
function pauseTimer(etapeId) {
    if (timers[etapeId] && timers[etapeId].interval) {
        clearInterval(timers[etapeId].interval);
        timers[etapeId].interval = null;
        timers[etapeId].isPaused = true;
        
        document.getElementById(`pause-${etapeId}`).style.display = 'none';
        document.getElementById(`resume-${etapeId}`).style.display = 'inline-block';
    }
}

/**
 * Reprend un timer en pause
 */
function resumeTimer(etapeId) {
    if (timers[etapeId] && timers[etapeId].isPaused) {
        timers[etapeId].isPaused = false;
        
        document.getElementById(`pause-${etapeId}`).style.display = 'inline-block';
        document.getElementById(`resume-${etapeId}`).style.display = 'none';
        
        timers[etapeId].interval = setInterval(() => {
            if (timers[etapeId].remaining > 0) {
                timers[etapeId].remaining--;
                updateTimerDisplay(etapeId);
            } else {
                clearInterval(timers[etapeId].interval);
                timers[etapeId].interval = null;
                timerFinished(etapeId);
            }
        }, 1000);
    }
}

/**
 * Réinitialise un timer
 */
function resetTimer(etapeId, minutes) {
    if (timers[etapeId]) {
        if (timers[etapeId].interval) {
            clearInterval(timers[etapeId].interval);
        }
        timers[etapeId].interval = null;
        timers[etapeId].remaining = minutes * 60;
        timers[etapeId].isPaused = false;
    }
    
    // Mettre à jour l'affichage
    const timeDisplay = document.getElementById(`timer-time-${etapeId}`);
    if (timeDisplay) {
        timeDisplay.textContent = `${String(minutes).padStart(2, '0')}:00`;
    }
    
    // Réinitialiser la barre de progression
    const progressFill = document.getElementById(`progress-${etapeId}`);
    if (progressFill) {
        progressFill.style.width = '0%';
    }
    
    // Réinitialiser les boutons
    document.getElementById(`start-${etapeId}`).style.display = 'inline-block';
    document.getElementById(`pause-${etapeId}`).style.display = 'none';
    document.getElementById(`resume-${etapeId}`).style.display = 'none';
    
    // Réinitialiser les classes visuelles
    const timerDisplay = document.getElementById(`timer-display-${etapeId}`);
    if (timerDisplay) {
        timerDisplay.classList.remove('rd-timer-warning', 'rd-timer-critical', 'rd-timer-finished');
    }
    
    const card = document.getElementById(`etape-${etapeId}`);
    if (card) {
        card.classList.remove('rd-step-timer-finished');
    }
}

/**
 * Met à jour l'affichage du timer
 */
function updateTimerDisplay(etapeId) {
    const timer = timers[etapeId];
    if (!timer) return;
    
    const minutes = Math.floor(timer.remaining / 60);
    const seconds = timer.remaining % 60;
    
    const timeDisplay = document.getElementById(`timer-time-${etapeId}`);
    if (timeDisplay) {
        timeDisplay.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    
    // Mettre à jour la barre de progression
    const progressFill = document.getElementById(`progress-${etapeId}`);
    if (progressFill) {
        const percentage = ((timer.total - timer.remaining) / timer.total) * 100;
        progressFill.style.width = `${percentage}%`;
    }
    
    // Changer la couleur selon le temps restant
    const timerDisplay = document.getElementById(`timer-display-${etapeId}`);
    if (timerDisplay) {
        timerDisplay.classList.remove('rd-timer-warning', 'rd-timer-critical');
        
        if (timer.remaining <= 30) {
            timerDisplay.classList.add('rd-timer-critical');
        } else if (timer.remaining <= 60) {
            timerDisplay.classList.add('rd-timer-warning');
        }
    }
}

/**
 * Appelé quand un timer est terminé
 */
function timerFinished(etapeId) {
    const timerDisplay = document.getElementById(`timer-display-${etapeId}`);
    if (timerDisplay) {
        timerDisplay.classList.remove('rd-timer-warning', 'rd-timer-critical');
        timerDisplay.classList.add('rd-timer-finished');
    }
    
    const card = document.getElementById(`etape-${etapeId}`);
    if (card) {
        card.classList.add('rd-step-timer-finished');
    }
    
    // Réinitialiser les boutons
    document.getElementById(`start-${etapeId}`).style.display = 'inline-block';
    document.getElementById(`pause-${etapeId}`).style.display = 'none';
    document.getElementById(`resume-${etapeId}`).style.display = 'none';
    
    // Notification
    showNotification('⏱️ Timer terminé !');
    
    // Son de notification (si supporté)
    try {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Timer terminé !', {
                body: 'Une étape de votre recette est prête.',
                icon: '⏱️'
            });
        }
    } catch (e) {
        // Ignore si les notifications ne sont pas supportées
    }
}

/**
 * Marque une étape comme terminée
 */
function completeStep(etapeId) {
    // Arrêter le timer s'il est actif
    if (timers[etapeId] && timers[etapeId].interval) {
        clearInterval(timers[etapeId].interval);
        timers[etapeId].interval = null;
    }
    
    completedSteps.add(etapeId);
    
    // Mettre à jour le statut
    updateStepStatus(etapeId, 'completed');
    
    // Ajouter la classe de complétion
    const card = document.getElementById(`etape-${etapeId}`);
    if (card) {
        card.classList.add('rd-step-completed');
    }
    
    // Mettre à jour la progression globale
    updateGlobalProgress();
    
    // Faire défiler jusqu'à la prochaine étape
    scrollToNextStep(etapeId);
}

/**
 * Met à jour le statut d'une étape
 */
function updateStepStatus(etapeId, status) {
    const statusBadge = document.querySelector(`#status-${etapeId} .rd-status-badge`);
    if (!statusBadge) return;
    
    // Retirer toutes les classes de statut
    statusBadge.classList.remove('rd-status-pending', 'rd-status-progress', 'rd-status-completed');
    
    switch (status) {
        case 'progress':
            statusBadge.classList.add('rd-status-progress');
            statusBadge.textContent = '⏳ En cours';
            break;
        case 'completed':
            statusBadge.classList.add('rd-status-completed');
            statusBadge.textContent = '✓ Terminée';
            break;
        default:
            statusBadge.classList.add('rd-status-pending');
            statusBadge.textContent = 'En attente';
    }
}

/**
 * Met à jour la barre de progression globale
 */
function updateGlobalProgress() {
    const totalSteps = document.querySelectorAll('.rd-step').length;
    const completed = completedSteps.size;
    const percentage = totalSteps > 0 ? (completed / totalSteps) * 100 : 0;
    
    const progressText = document.getElementById('progress-text');
    if (progressText) {
        progressText.textContent = `${completed} / ${totalSteps}`;
    }
    
    const progressBar = document.getElementById('global-progress');
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
    }
    
    // Vérifier si toutes les étapes sont terminées
    if (completed === totalSteps && totalSteps > 0) {
        showNotification('🎉 Félicitations ! Toutes les étapes sont terminées !');
    }
}

/**
 * Fait défiler jusqu'à la prochaine étape non terminée
 */
function scrollToNextStep(currentEtapeId) {
    const allSteps = document.querySelectorAll('.rd-step');
    let foundCurrent = false;
    
    for (const step of allSteps) {
        const stepId = parseInt(step.dataset.etapeId);
        
        if (foundCurrent && !completedSteps.has(stepId)) {
            // Trouver la prochaine étape non terminée
            step.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }
        
        if (stepId === currentEtapeId) {
            foundCurrent = true;
        }
    }
}

/**
 * Affiche une notification temporaire
 */
function showNotification(message) {
    const notification = document.getElementById('cooking-notification');
    if (!notification) return;
    
    notification.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    // Demander la permission pour les notifications
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Initialiser la progression
    updateGlobalProgress();
});
