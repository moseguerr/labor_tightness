/**
 * Bucket Sort Game Engine
 *
 * Phrases fall from top of screen. Player clicks a bucket to catch them.
 * Speed ramps up over 5 minutes. Missed phrases re-enter the queue.
 * Hard/boundary phrases appear twice in the queue.
 * After 30% of game time, ~25% of spawns are dual-phrase (two at once).
 */
(function () {
    'use strict';

    // -- Configuration --------------------------------------------------------
    var GAME_DURATION_MS = 4 * 60 * 1000; // default 4 minutes, overridden by config
    const FALL_START_MS = 3500;
    const FALL_END_MS = 1200;
    const MAX_ATTEMPTS = 3;
    const PAUSE_BETWEEN_MS = 400;
    const MIN_READ_MS = 600;
    const DUAL_START_PROGRESS = 0.3;   // dual mode begins after 30% of game time
    const DUAL_CHANCE = 0.25;          // 25% chance of dual spawn once eligible

    const BUCKETS = [
        { id: 'purpose', label: 'Organizational Purpose', shortLabel: 'Purpose', color: '#4a7c8a', description: 'What they stand for beyond making money \u2014 what motivates them, what they are trying to build or change' },
        { id: 'good_employer', label: 'Good Employer', shortLabel: 'Good Employer', color: '#6a8a4a', description: 'The work environment they create for people inside it to make the experience of working there better' },
        { id: 'compensation', label: 'Compensation & Benefits', shortLabel: 'Comp & Benefits', color: '#8a6a4a', description: 'The return for your work \u2014 what you receive in exchange for your time and effort' },
        { id: 'job_tasks', label: 'Job Tasks & Requirements', shortLabel: 'Job Tasks', color: '#7a4a8a', description: 'What the role actually involves \u2014 responsibilities, skills required, and what the work looks like day to day' },
        { id: 'not_sure', label: 'Not Sure', shortLabel: 'Not Sure', color: '#6b7280', description: 'Could belong in more than one category, or you cannot tell what it is communicating' },
    ];

    // -- State ----------------------------------------------------------------
    let phrases = [];
    let queue = [];
    let results = [];
    let attemptCounts = {};
    let gameStartTime = null;
    let timerIntervalId = null;
    let gameActive = false;
    let caught = 0;
    let streak = 0;
    let bestStreak = 0;

    // Slot-based: two slots for simultaneous phrases
    var slots = [
        { el: null, phrase: null, startTime: null, animId: null },
        { el: null, phrase: null, startTime: null, animId: null },
    ];

    // DOM references
    let scoreEl, timerEl, streakEl, bucketContainer;
    let gameArea, gameOverlay, countdownEl;

    // -- Queue Building -------------------------------------------------------
    function buildQueue(phraseData, seed) {
        phrases = phraseData;
        attemptCounts = {};

        var items = phraseData.map(function (p) { return p.phrase_id; });

        phraseData.forEach(function (p) {
            if (p.difficulty === 'hard') {
                items.push(p.phrase_id);
            }
        });

        var rng = mulberry32(seed);
        for (var i = items.length - 1; i > 0; i--) {
            var j = Math.floor(rng() * (i + 1));
            var tmp = items[i];
            items[i] = items[j];
            items[j] = tmp;
        }

        queue = items;
        phraseData.forEach(function (p) { attemptCounts[p.phrase_id] = 0; });
    }

    function mulberry32(a) {
        return function () {
            a |= 0; a = a + 0x6D2B79F5 | 0;
            var t = Math.imul(a ^ a >>> 15, 1 | a);
            t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
            return ((t ^ t >>> 14) >>> 0) / 4294967296;
        };
    }

    // -- Speed Ramp -----------------------------------------------------------
    function getFallDuration() {
        var elapsed = Date.now() - gameStartTime;
        var progress = Math.min(elapsed / GAME_DURATION_MS, 1);
        var eased = progress * progress;
        return FALL_START_MS - (FALL_START_MS - FALL_END_MS) * eased;
    }

    // -- Phrase Lookup --------------------------------------------------------
    function getPhraseById(id) {
        for (var i = 0; i < phrases.length; i++) {
            if (phrases[i].phrase_id === id) return phrases[i];
        }
        return null;
    }

    // -- Game Timer -----------------------------------------------------------
    function updateTimer() {
        var elapsed = Date.now() - gameStartTime;
        var remaining = Math.max(0, GAME_DURATION_MS - elapsed);
        var mins = Math.floor(remaining / 60000);
        var secs = Math.floor((remaining % 60000) / 1000);
        timerEl.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;

        if (remaining <= 0) {
            endGame();
        }
    }

    // -- Dual-phrase logic ----------------------------------------------------
    function shouldSpawnDual() {
        var elapsed = Date.now() - gameStartTime;
        var progress = elapsed / GAME_DURATION_MS;
        if (progress < DUAL_START_PROGRESS) return false;
        return Math.random() < DUAL_CHANCE;
    }

    function activeSlotCount() {
        var n = 0;
        if (slots[0].phrase) n++;
        if (slots[1].phrase) n++;
        return n;
    }

    // Find the slot whose phrase is closest to the bottom (most urgent)
    function getTargetSlot() {
        if (slots[0].phrase && !slots[1].phrase) return 0;
        if (slots[1].phrase && !slots[0].phrase) return 1;
        if (!slots[0].phrase && !slots[1].phrase) return -1;

        // Both active: pick the one with more progress (lower on screen)
        var y0 = parseFloat(slots[0].el.style.top) || 0;
        var y1 = parseFloat(slots[1].el.style.top) || 0;
        return y0 >= y1 ? 0 : 1;
    }

    function updateTargetHighlight() {
        var target = getTargetSlot();
        for (var i = 0; i < 2; i++) {
            if (slots[i].phrase) {
                if (i === target) {
                    slots[i].el.classList.add('falling-phrase--target');
                } else {
                    slots[i].el.classList.remove('falling-phrase--target');
                }
            }
        }
    }

    // -- Core Game Loop -------------------------------------------------------
    function showNextPhrase() {
        if (!gameActive) return;

        if (queue.length === 0 && activeSlotCount() === 0) {
            endGame();
            return;
        }

        if (queue.length === 0) return; // wait for active phrases to resolve

        // Determine how many to spawn
        var slotsToFill = 1;
        if (activeSlotCount() === 0 && queue.length >= 2 && shouldSpawnDual()) {
            slotsToFill = 2;
        }

        for (var s = 0; s < slotsToFill; s++) {
            // Find a free slot
            var slotIdx = -1;
            if (!slots[0].phrase) slotIdx = 0;
            else if (!slots[1].phrase) slotIdx = 1;
            if (slotIdx === -1) break;
            if (queue.length === 0) break;

            spawnInSlot(slotIdx, slotsToFill === 2);
        }

        updateTargetHighlight();
    }

    function spawnInSlot(slotIdx, isDual) {
        var phraseId = queue.shift();
        var phrase = getPhraseById(phraseId);
        if (!phrase) {
            // Skip invalid, try next
            if (queue.length > 0) spawnInSlot(slotIdx, isDual);
            return;
        }

        attemptCounts[phraseId] = (attemptCounts[phraseId] || 0) + 1;

        var slot = slots[slotIdx];
        slot.phrase = {
            id: phraseId,
            attempt: attemptCounts[phraseId],
            data: phrase,
        };
        slot.startTime = Date.now();

        // Set up element
        var el = slot.el;
        el.textContent = phrase.phrase_text;
        el.className = 'falling-phrase falling-phrase--active';
        el.style.top = '-60px';
        el.style.opacity = '1';
        el.style.display = 'block';

        // Position: center if solo, left/right if dual
        if (isDual) {
            el.classList.add(slotIdx === 0 ? 'falling-phrase--left' : 'falling-phrase--right');
        }
        // If only one slot active and not dual, center (default CSS)

        // Start fall animation
        var fallDuration = getFallDuration();
        // Stagger: second slot starts higher so they don't overlap vertically
        var startY = isDual && slotIdx === 1 ? -160 : -60;
        var endY = gameArea.offsetHeight - 80;
        var startTime = performance.now();

        function animate(now) {
            if (!gameActive || !slot.phrase) return;
            var progress = (now - startTime) / fallDuration;

            if (progress >= 1) {
                handleMiss(slotIdx);
                return;
            }

            var y = startY + (endY - startY) * progress;
            el.style.top = y + 'px';
            slot.animId = requestAnimationFrame(animate);

            updateTargetHighlight();
        }

        slot.animId = requestAnimationFrame(animate);
    }

    function handleCatch(bucketId) {
        if (!gameActive) return;

        var slotIdx = getTargetSlot();
        if (slotIdx === -1) return;

        var slot = slots[slotIdx];
        if (!slot.phrase) return;

        var elapsed = Date.now() - slot.startTime;
        if (elapsed < MIN_READ_MS) return;

        cancelAnimationFrame(slot.animId);
        var gameElapsed = Date.now() - gameStartTime;

        results.push({
            phraseId: slot.phrase.id,
            attempt: slot.phrase.attempt,
            bucket: bucketId,
            wasMissed: false,
            timeOnPhraseMs: elapsed,
            gameElapsedMs: gameElapsed,
        });

        caught++;
        streak++;
        if (streak > bestStreak) bestStreak = streak;
        updateScore();

        var bucketEl = document.querySelector('[data-bucket="' + bucketId + '"]');
        animateCatch(slot.el, bucketEl);

        slot.phrase = null;
        slot.startTime = null;

        updateTargetHighlight();

        // If the other slot is still active, don't spawn yet
        if (activeSlotCount() === 0) {
            setTimeout(showNextPhrase, PAUSE_BETWEEN_MS);
        }
    }

    function handleMiss(slotIdx) {
        var slot = slots[slotIdx];
        if (!slot.phrase) return;

        var gameElapsed = Date.now() - gameStartTime;
        var elapsed = Date.now() - slot.startTime;

        results.push({
            phraseId: slot.phrase.id,
            attempt: slot.phrase.attempt,
            bucket: '',
            wasMissed: true,
            timeOnPhraseMs: elapsed,
            gameElapsedMs: gameElapsed,
        });

        streak = 0;
        updateScore();

        if (slot.phrase.attempt < MAX_ATTEMPTS) {
            var insertAt = Math.floor(Math.random() * (queue.length + 1));
            queue.splice(insertAt, 0, slot.phrase.id);
        }

        animateMiss(slot.el);
        slot.phrase = null;
        slot.startTime = null;

        updateTargetHighlight();

        if (activeSlotCount() === 0) {
            setTimeout(showNextPhrase, PAUSE_BETWEEN_MS);
        }
    }

    // -- Animations -----------------------------------------------------------
    function animateCatch(el, bucketEl) {
        el.classList.remove('falling-phrase--active');
        el.classList.add('falling-phrase--caught');

        if (bucketEl) {
            bucketEl.classList.add('bucket-zone--flash');
            setTimeout(function () {
                bucketEl.classList.remove('bucket-zone--flash');
            }, 400);
        }

        setTimeout(function () {
            el.style.display = 'none';
            el.classList.remove('falling-phrase--caught');
        }, 300);
    }

    function animateMiss(el) {
        el.classList.remove('falling-phrase--active');
        el.classList.add('falling-phrase--missed');
        setTimeout(function () {
            el.style.display = 'none';
            el.classList.remove('falling-phrase--missed');
        }, 400);
    }

    // -- Score Display --------------------------------------------------------
    function updateScore() {
        scoreEl.textContent = caught;
        streakEl.textContent = streak;
    }

    // -- Game Start / End -----------------------------------------------------
    function startCountdown(callback) {
        gameOverlay.style.display = 'flex';
        var count = 3;
        countdownEl.textContent = count;

        var interval = setInterval(function () {
            count--;
            if (count > 0) {
                countdownEl.textContent = count;
            } else {
                clearInterval(interval);
                gameOverlay.style.display = 'none';
                callback();
            }
        }, 800);
    }

    function startGame() {
        startCountdown(function () {
            gameActive = true;
            gameStartTime = Date.now();
            caught = 0;
            streak = 0;
            bestStreak = 0;
            results = [];
            updateScore();

            timerIntervalId = setInterval(updateTimer, 200);
            showNextPhrase();
        });
    }

    function endGame() {
        gameActive = false;
        for (var i = 0; i < 2; i++) {
            slots[i].phrase = null;
            cancelAnimationFrame(slots[i].animId);
            slots[i].el.style.display = 'none';
        }
        clearInterval(timerIntervalId);

        submitResults();
    }

    // -- Submit Results -------------------------------------------------------
    function submitResults() {
        var inconsistent = findInconsistentPhrases();

        var payload = {
            results: results,
            caught: caught,
            best_streak: bestStreak,
            game_duration_ms: Date.now() - gameStartTime,
            inconsistent: inconsistent,
        };

        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch(submitUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(payload),
        })
        .then(function (resp) { return resp.json(); })
        .then(function (data) {
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        })
        .catch(function (err) {
            console.error('Submit failed:', err);
            showGameOver('Something went wrong. Please refresh and try again.');
        });
    }

    function findInconsistentPhrases() {
        var byPhrase = {};
        results.forEach(function (r) {
            if (r.wasMissed) return;
            if (!byPhrase[r.phraseId]) byPhrase[r.phraseId] = [];
            byPhrase[r.phraseId].push(r.bucket);
        });

        var inconsistent = [];
        Object.keys(byPhrase).forEach(function (pid) {
            var buckets = byPhrase[pid];
            if (buckets.length < 2) return;
            var unique = [];
            buckets.forEach(function (b) {
                if (unique.indexOf(b) === -1) unique.push(b);
            });
            if (unique.length > 1) {
                inconsistent.push({
                    phraseId: pid,
                    phraseText: getPhraseById(pid).phrase_text,
                    buckets: unique,
                });
            }
        });
        return inconsistent;
    }

    function showGameOver(message) {
        gameOverlay.style.display = 'flex';
        countdownEl.innerHTML = '<div class="text-2xl font-bold mb-2">Game Over!</div>' +
            '<div class="text-lg">' + (message || 'Submitting your responses...') + '</div>' +
            '<div class="mt-4 text-base text-slate-500">Caught: ' + caught + ' | Best streak: ' + bestStreak + '</div>';
    }

    // -- Keyboard Support -----------------------------------------------------
    function handleKeypress(e) {
        if (!gameActive || activeSlotCount() === 0) return;
        var key = e.key;
        if (key >= '1' && key <= '5') {
            var idx = parseInt(key) - 1;
            if (idx < BUCKETS.length) {
                handleCatch(BUCKETS[idx].id);
            }
        }
    }

    // -- Initialization -------------------------------------------------------
    var submitUrl = '';

    function init(config) {
        submitUrl = config.submitUrl;
        if (config.gameDuration) {
            GAME_DURATION_MS = config.gameDuration * 1000;
        }
        var seed = config.seed || Math.floor(Math.random() * 999999);

        gameArea = document.getElementById('game-area');
        slots[0].el = document.getElementById('falling-phrase-0');
        slots[1].el = document.getElementById('falling-phrase-1');
        scoreEl = document.getElementById('score-caught');
        timerEl = document.getElementById('score-timer');
        streakEl = document.getElementById('score-streak');

        // Set initial timer display
        var initMins = Math.floor(GAME_DURATION_MS / 60000);
        var initSecs = Math.floor((GAME_DURATION_MS % 60000) / 1000);
        timerEl.textContent = initMins + ':' + (initSecs < 10 ? '0' : '') + initSecs;
        bucketContainer = document.getElementById('bucket-container');
        gameOverlay = document.getElementById('game-overlay');
        countdownEl = document.getElementById('countdown');

        BUCKETS.forEach(function (bucket, idx) {
            var el = document.createElement('button');
            el.className = 'bucket-zone';
            el.setAttribute('data-bucket', bucket.id);
            el.style.setProperty('--bucket-color', bucket.color);
            el.innerHTML = '<span class="bucket-zone__label">' + bucket.shortLabel + '</span>' +
                '<span class="bucket-zone__key">' + (idx + 1) + '</span>' +
                '<span class="bucket-zone__tooltip">' + bucket.description + '</span>';
            el.addEventListener('click', function () {
                handleCatch(bucket.id);
            });
            bucketContainer.appendChild(el);
        });

        document.addEventListener('keydown', handleKeypress);

        buildQueue(config.phrases, seed);
        startGame();
    }

    window.BucketGame = { init: init };
})();
