/**
 * cuisiner.js - Gestion du mode cuisine interactif
 * VERSION OPTIMISÉE - Timers précis résistants au throttling des onglets
 * 
 * OPTIMISATIONS :
 * ✅ Utilisation de Date.now() au lieu de compteur décrémental
 * ✅ Intervalle de 100ms pour fluidité (au lieu de 1000ms)
 * ✅ Page Visibility API pour mise à jour au retour sur l'onglet
 * ✅ Gestion précise des pauses avec timestamp
 * ✅ Code factorisé et optimisé
 */

// ============================================
// ÉTAT GLOBAL
// ============================================

const timers = {};
const completedSteps = new Set();

// ============================================
// GESTION DES TIMERS - VERSION OPTIMISÉE
// ============================================

/**
 * Démarre un timer pour une étape
 * Utilise Date.now() pour éviter les problèmes de throttling
 */
function startTimer(etapeId, minutes) {
    // Arrêter le timer existant s'il y en a un
    if (timers[etapeId]?.interval) {
        clearInterval(timers[etapeId].interval);
    }
    
    const totalSeconds = minutes * 60;
    const endTime = Date.now() + (totalSeconds * 1000);
    
    timers[etapeId] = {
        endTime: endTime,
        total: totalSeconds,
        interval: null,
        isPaused: false,
        pausedRemaining: null,
        startTime: Date.now(),
        warningSoundPlayed: false // Flag pour éviter de rejouer le son d'avertissement
    };
    
    // Mise à jour de l'interface
    updateTimerButtons(etapeId, 'running');
    updateStepStatus(etapeId, 'progress');
    
    // Lancer la boucle de mise à jour
    runTimerLoop(etapeId);
    
    // Mise à jour immédiate
    updateTimerFromTimestamp(etapeId);
}

/**
 * Boucle de mise à jour du timer
 * Utilise un intervalle de 100ms pour plus de fluidité
 */
function runTimerLoop(etapeId) {
    timers[etapeId].interval = setInterval(() => {
        if (!timers[etapeId] || timers[etapeId].isPaused) {
            return;
        }
        
        const remaining = Math.max(0, Math.ceil((timers[etapeId].endTime - Date.now()) / 1000));
        
        if (remaining > 0) {
            updateTimerDisplay(etapeId, remaining, timers[etapeId].total);
        } else {
            // Timer terminé
            stopTimerLoop(etapeId);
            updateTimerDisplay(etapeId, 0, timers[etapeId].total);
            timerFinished(etapeId);
        }
    }, 100); // 100ms pour fluidité et réactivité
}

/**
 * Arrête la boucle d'un timer
 */
function stopTimerLoop(etapeId) {
    if (timers[etapeId]?.interval) {
        clearInterval(timers[etapeId].interval);
        timers[etapeId].interval = null;
    }
}

/**
 * Met à jour le timer depuis le timestamp (appelé au retour sur l'onglet)
 */
function updateTimerFromTimestamp(etapeId) {
    if (!timers[etapeId] || timers[etapeId].isPaused) {
        return;
    }
    
    const remaining = Math.max(0, Math.ceil((timers[etapeId].endTime - Date.now()) / 1000));
    updateTimerDisplay(etapeId, remaining, timers[etapeId].total);
    
    // Vérifier si le timer est terminé
    if (remaining === 0 && timers[etapeId].interval) {
        stopTimerLoop(etapeId);
        timerFinished(etapeId);
    }
}

/**
 * Met en pause un timer
 */
function pauseTimer(etapeId) {
    if (!timers[etapeId]?.interval) {
        return;
    }
    
    // Calculer et sauvegarder le temps restant
    const remaining = Math.max(0, Math.ceil((timers[etapeId].endTime - Date.now()) / 1000));
    timers[etapeId].pausedRemaining = remaining;
    timers[etapeId].isPaused = true;
    
    // Arrêter la boucle
    stopTimerLoop(etapeId);
    
    // Mise à jour de l'interface
    updateTimerButtons(etapeId, 'paused');
}

/**
 * Reprend un timer en pause
 */
function resumeTimer(etapeId) {
    if (!timers[etapeId]?.isPaused || timers[etapeId].pausedRemaining === null) {
        return;
    }
    
    // Recalculer l'heure de fin basée sur le temps restant sauvegardé
    timers[etapeId].endTime = Date.now() + (timers[etapeId].pausedRemaining * 1000);
    timers[etapeId].isPaused = false;
    timers[etapeId].pausedRemaining = null;
    
    // Mise à jour de l'interface
    updateTimerButtons(etapeId, 'running');
    
    // Relancer la boucle
    runTimerLoop(etapeId);
}

/**
 * Réinitialise un timer
 */
function resetTimer(etapeId, minutes) {
    // Arrêter le timer existant
    stopTimerLoop(etapeId);
    
    const totalSeconds = minutes * 60;
    
    // Réinitialiser l'état
    timers[etapeId] = {
        endTime: null,
        total: totalSeconds,
        interval: null,
        isPaused: false,
        pausedRemaining: null,
        startTime: null,
        warningSoundPlayed: false
    };
    
    // Mise à jour de l'affichage
    updateTimerDisplay(etapeId, totalSeconds, totalSeconds);
    
    // Réinitialiser l'interface
    updateTimerButtons(etapeId, 'stopped');
    
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
function updateTimerDisplay(etapeId, remaining, total) {
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    
    const timeDisplay = document.getElementById(`timer-time-${etapeId}`);
    if (timeDisplay) {
        timeDisplay.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    
    // Mettre à jour la barre de progression
    const progressFill = document.getElementById(`progress-${etapeId}`);
    if (progressFill) {
        const percentage = total > 0 ? ((total - remaining) / total) * 100 : 0;
        progressFill.style.width = `${percentage}%`;
    }
    
    // Changer la couleur selon le temps restant
    const timerDisplay = document.getElementById(`timer-display-${etapeId}`);
    if (timerDisplay) {
        timerDisplay.classList.remove('rd-timer-warning', 'rd-timer-critical');
        
        // Mode critique : <= 30 secondes
        if (remaining <= 30) {
            timerDisplay.classList.add('rd-timer-critical');
            
            // 🔊 Son d'avertissement à exactement 30 secondes (une seule fois)
            if (remaining === 30 && !timers[etapeId].warningSoundPlayed) {
                NotificationSound.playWarning();
                timers[etapeId].warningSoundPlayed = true;
            }
        } 
        // Mode avertissement : <= 60 secondes
        else if (remaining <= 60) {
            timerDisplay.classList.add('rd-timer-warning');
        }
    }
}

/**
 * Met à jour les boutons du timer selon l'état
 * @param {number} etapeId - ID de l'étape
 * @param {string} state - 'stopped' | 'running' | 'paused'
 */
function updateTimerButtons(etapeId, state) {
    const startBtn = document.getElementById(`start-${etapeId}`);
    const pauseBtn = document.getElementById(`pause-${etapeId}`);
    const resumeBtn = document.getElementById(`resume-${etapeId}`);
    
    if (!startBtn || !pauseBtn || !resumeBtn) return;
    
    // Masquer tous les boutons
    startBtn.style.display = 'none';
    pauseBtn.style.display = 'none';
    resumeBtn.style.display = 'none';
    
    // Afficher le bouton approprié
    switch (state) {
        case 'stopped':
            startBtn.style.display = 'inline-block';
            break;
        case 'running':
            pauseBtn.style.display = 'inline-block';
            break;
        case 'paused':
            resumeBtn.style.display = 'inline-block';
            break;
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
    updateTimerButtons(etapeId, 'stopped');
    
    // Notification
    showNotification('⏱️ Timer terminé !');
    
    // Notification système (si autorisé)
    sendSystemNotification('Timer terminé !', 'Une étape de votre recette est prête.');
    
    // 🔊 JOUER LA MÉLODIE DE FIN
    NotificationSound.playMelody();
}

// ============================================
// GESTION DES ÉTAPES
// ============================================

/**
 * Marque une étape comme terminée
 */
function completeStep(etapeId) {
    // Arrêter le timer s'il est actif
    if (timers[etapeId]?.interval) {
        stopTimerLoop(etapeId);
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
        sendSystemNotification('Recette terminée !', 'Félicitations, vous avez terminé toutes les étapes !');
        
        // 🎵 JOUER LE SON DE CÉLÉBRATION
        NotificationSound.playCelebration();
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

// ============================================
// GESTION DES SONS - OPTION 3
// ============================================

/**
 * Gestionnaire de sons pour les notifications
 */
const NotificationSound = {
    /**
     * Joue un bip simple avec Web Audio API
     */
    playBeep() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Créer un oscillateur (générateur de son)
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Configuration du son
            oscillator.frequency.value = 800; // Fréquence en Hz (800 = son aigu)
            oscillator.type = 'sine'; // Onde sinusoïdale pour un son doux
            
            // Envelope du volume (fade out)
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            // Jouer le son
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
            
        } catch (err) {
            console.log('Web Audio API non supportée:', err);
        }
    },
    
    /**
     * Joue un triple bip pour attirer l'attention
     */
    playTripleBeep() {
        this.playBeep();
        setTimeout(() => this.playBeep(), 200);
        setTimeout(() => this.playBeep(), 400);
    },
    
    /**
     * Joue une mélodie agréable de fin (Do - Mi - Sol)
     * Version sophistiquée avec harmoniques
     */
    playMelody() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Définition de la mélodie (fréquences en Hz)
            const notes = [
                { freq: 523.25, start: 0, duration: 0.15 },    // Do (C5)
                { freq: 659.25, start: 0.15, duration: 0.15 }, // Mi (E5)
                { freq: 783.99, start: 0.3, duration: 0.4 }    // Sol (G5) - plus long
            ];
            
            notes.forEach(note => {
                // Note principale
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = note.freq;
                oscillator.type = 'sine';
                
                // Envelope du volume
                const startTime = audioContext.currentTime + note.start;
                const endTime = startTime + note.duration;
                
                gainNode.gain.setValueAtTime(0, startTime);
                gainNode.gain.linearRampToValueAtTime(0.2, startTime + 0.02); // Attack
                gainNode.gain.exponentialRampToValueAtTime(0.01, endTime); // Decay
                
                oscillator.start(startTime);
                oscillator.stop(endTime);
                
                // Ajouter une harmonique pour enrichir le son
                const harmonic = audioContext.createOscillator();
                const harmonicGain = audioContext.createGain();
                
                harmonic.connect(harmonicGain);
                harmonicGain.connect(audioContext.destination);
                
                harmonic.frequency.value = note.freq * 2; // Octave supérieure
                harmonic.type = 'sine';
                
                harmonicGain.gain.setValueAtTime(0, startTime);
                harmonicGain.gain.linearRampToValueAtTime(0.1, startTime + 0.02);
                harmonicGain.gain.exponentialRampToValueAtTime(0.01, endTime);
                
                harmonic.start(startTime);
                harmonic.stop(endTime);
            });
            
        } catch (err) {
            console.log('Mélodie non supportée:', err);
            // Fallback vers un bip simple
            this.playBeep();
        }
    },
    
    /**
     * Joue une célébration sonore (pour toutes les étapes terminées)
     */
    playCelebration() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Arpège ascendant joyeux : Do - Mi - Sol - Do
            const notes = [
                { freq: 523.25, start: 0, duration: 0.12 },      // Do
                { freq: 659.25, start: 0.12, duration: 0.12 },   // Mi
                { freq: 783.99, start: 0.24, duration: 0.12 },   // Sol
                { freq: 1046.50, start: 0.36, duration: 0.3 }    // Do (octave supérieure)
            ];
            
            notes.forEach(note => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = note.freq;
                oscillator.type = 'triangle'; // Son plus doux et chaleureux
                
                const startTime = audioContext.currentTime + note.start;
                const endTime = startTime + note.duration;
                
                gainNode.gain.setValueAtTime(0, startTime);
                gainNode.gain.linearRampToValueAtTime(0.25, startTime + 0.02);
                gainNode.gain.exponentialRampToValueAtTime(0.01, endTime);
                
                oscillator.start(startTime);
                oscillator.stop(endTime);
            });
            
        } catch (err) {
            console.log('Célébration sonore non supportée:', err);
            this.playMelody();
        }
    },
    
    /**
     * Joue un son d'avertissement (30 secondes restantes)
     */
    playWarning() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Son plus grave pour l'avertissement
            oscillator.frequency.value = 400;
            oscillator.type = 'square';
            
            gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
            
        } catch (err) {
            console.log('Son d\'avertissement non supporté:', err);
        }
    }
};

// ============================================
// NOTIFICATIONS
// ============================================

/**
 * Affiche une notification temporaire dans la page
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

/**
 * Envoie une notification système (si autorisé)
 */
function sendSystemNotification(title, body) {
    try {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: body,
                icon: '⏱️',
                badge: '⏱️'
            });
        }
    } catch (e) {
        // Ignorer si les notifications ne sont pas supportées
        console.log('Notifications système non supportées:', e);
    }
}

/**
 * Demande la permission pour les notifications système
 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('Notifications système activées');
            }
        });
    }
}

// ============================================
// PAGE VISIBILITY API - OPTIMISATION ONGLETS
// ============================================

/**
 * Gère le retour sur l'onglet pour mettre à jour les timers
 * Évite les problèmes de désynchronisation quand l'onglet est inactif
 */
function handleVisibilityChange() {
    if (!document.hidden) {
        // L'utilisateur revient sur l'onglet
        console.log('Retour sur l\'onglet - mise à jour des timers');
        
        // Mettre à jour tous les timers actifs
        Object.keys(timers).forEach(etapeId => {
            if (timers[etapeId] && !timers[etapeId].isPaused && timers[etapeId].endTime) {
                updateTimerFromTimestamp(parseInt(etapeId));
            }
        });
    }
}

// ============================================
// INITIALISATION
// ============================================

/**
 * Initialisation au chargement de la page
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initialisation du mode cuisine optimisé');
    
    // Demander la permission pour les notifications système
    requestNotificationPermission();
    
    // Initialiser la progression globale
    updateGlobalProgress();
    
    // Écouter les changements de visibilité de l'onglet
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    console.log('Mode cuisine prêt ✅');
});

// ============================================
// NETTOYAGE À LA FERMETURE
// ============================================

/**
 * Nettoie les timers avant de quitter la page
 */
window.addEventListener('beforeunload', () => {
    Object.keys(timers).forEach(etapeId => {
        stopTimerLoop(parseInt(etapeId));
    });
});
