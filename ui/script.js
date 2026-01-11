/**
 * gurgenSoundboard - UI Script
 * Completely rewritten from scratch for reliability
 * 
 * RULES:
 * - Left click on slot: ONLY plays sound (if assigned)
 * - Right click on slot: ONLY opens file browser (if slot is empty)
 * - Click on hotkey badge: Enter hotkey assignment mode
 * - Click on X button: Clear the slot
 */

document.addEventListener('DOMContentLoaded', function() {
    // ========================================
    // ELEMENTS
    // ========================================
    const openingAnimation = document.getElementById('opening-animation');
    const mainContent = document.getElementById('main-content');
    const closeBtn = document.querySelector('.close-btn');
    const soundSlots = document.querySelectorAll('.sound-slot');
    
    // ========================================
    // STATE - Simple and clear
    // ========================================
    const slotData = {};        // {slotNum: {path, name, hotkey}}
    const hotkeyMap = {};       // {key: slotNum} for visual feedback
    let awaitingHotkey = null;  // {slotNum, element} or null
    
    // ========================================
    // INITIALIZATION
    // ========================================
    
    // Set removal icons
    document.querySelectorAll('.slot-remove, .hotkey-remove').forEach(function(img) {
        if (window.SLOT_REMOVAL_ICON) {
            img.src = window.SLOT_REMOVAL_ICON;
        }
    });
    
    // Close button - hide window
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.hide_window();
            }
        });
    }
    
    // ========================================
    // LOAD SAVED DATA
    // ========================================
    function loadSavedSlots() {
        if (!window.pywebview || !window.pywebview.api) {
            console.log('pywebview not ready, retrying...');
            setTimeout(loadSavedSlots, 100);
            return;
        }
        
        window.pywebview.api.get_slots().then(function(slots) {
            if (!slots) return;
            
            Object.keys(slots).forEach(function(slotNum) {
                const info = slots[slotNum];
                slotData[slotNum] = info;
                
                const slotEl = document.querySelector('.sound-slot[data-slot="' + slotNum + '"]');
                if (!slotEl) return;
                
                // Update name
                if (info.name) {
                    slotEl.querySelector('.slot-name').textContent = info.name;
                    slotEl.querySelector('.slot-icon').src = window.SLOT_FILLED_ICON;
                    slotEl.querySelector('.slot-icon').style.opacity = '0.8';
                }
                
                // Update hotkey display
                if (info.hotkey) {
                    slotEl.querySelector('.slot-hotkey .hotkey-text').textContent = info.hotkey.toUpperCase();
                    hotkeyMap[info.hotkey.toLowerCase()] = slotNum;
                }
            });
            
            console.log('Loaded slots:', Object.keys(slotData).length);
        });
    }
    
    // ========================================
    // SLOT EVENT HANDLERS - COMPLETELY SEPARATE
    // ========================================
    soundSlots.forEach(function(slot) {
        const slotNum = slot.dataset.slot;
        
        // ----------------------------------------
        // LEFT CLICK - PLAY SOUND ONLY
        // ----------------------------------------
        slot.addEventListener('click', function(e) {
            // Ignore if clicking on hotkey badge or remove button
            if (e.target.closest('.slot-hotkey')) return;
            if (e.target.closest('.slot-remove')) return;
            
            // Only play if slot has a sound
            if (!slotData[slotNum] || !slotData[slotNum].path) {
                console.log('Slot ' + slotNum + ' has no sound');
                return;
            }
            
            // Play the sound
            playSound(slotNum, slot);
        });
        
        // ----------------------------------------
        // RIGHT CLICK - BROWSE FOR SOUND ONLY
        // ----------------------------------------
        slot.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Check if slot already has a sound
            if (slotData[slotNum] && slotData[slotNum].path) {
                // Slot is filled - show error feedback
                console.log('Slot ' + slotNum + ' already has a sound. Clear it first.');
                slot.style.boxShadow = '0 0 20px rgba(255, 50, 50, 0.6)';
                setTimeout(function() {
                    slot.style.boxShadow = '';
                }, 300);
                return;
            }
            
            // Browse for sound
            browseForSound(slotNum, slot);
        });
        
        // ----------------------------------------
        // HOTKEY BADGE CLICK - ASSIGN HOTKEY
        // ----------------------------------------
        const hotkeyBadge = slot.querySelector('.slot-hotkey');
        if (hotkeyBadge) {
            hotkeyBadge.addEventListener('click', function(e) {
                e.stopPropagation();
                
                // Ignore if clicking remove button
                if (e.target.closest('.hotkey-remove')) return;
                
                startHotkeyAssignment(slotNum, slot);
            });
        }
        
        // ----------------------------------------
        // HOTKEY REMOVE BUTTON
        // ----------------------------------------
        const hotkeyRemove = slot.querySelector('.hotkey-remove');
        if (hotkeyRemove) {
            hotkeyRemove.addEventListener('click', function(e) {
                e.stopPropagation();
                removeHotkey(slotNum, slot);
            });
        }
        
        // ----------------------------------------
        // SLOT REMOVE BUTTON (CLEAR SLOT)
        // ----------------------------------------
        const slotRemove = slot.querySelector('.slot-remove');
        if (slotRemove) {
            slotRemove.addEventListener('click', function(e) {
                e.stopPropagation();
                clearSlot(slotNum, slot);
            });
        }
    });
    
    // ========================================
    // KEYBOARD HANDLER
    // ========================================
    document.addEventListener('keydown', function(e) {
        // If waiting for hotkey assignment
        if (awaitingHotkey) {
            e.preventDefault();
            e.stopPropagation();
            
            const key = e.key.toLowerCase();
            assignHotkey(awaitingHotkey.slotNum, awaitingHotkey.element, key);
            return;
        }
        
        // Visual feedback for registered hotkeys (actual playing is done by Python)
        const key = e.key.toLowerCase();
        if (hotkeyMap[key]) {
            const slotNum = hotkeyMap[key];
            const slot = document.querySelector('.sound-slot[data-slot="' + slotNum + '"]');
            if (slot) {
                slot.style.transform = 'translateY(-2px) scale(0.98)';
                setTimeout(function() {
                    slot.style.transform = '';
                }, 100);
            }
        }
    });
    
    // Cancel hotkey assignment on outside click
    document.addEventListener('click', function(e) {
        if (awaitingHotkey && !e.target.closest('.sound-slot')) {
            cancelHotkeyAssignment();
        }
    });
    
    // ========================================
    // FUNCTIONS
    // ========================================
    
    function playSound(slotNum, slotEl) {
        if (!window.pywebview || !window.pywebview.api) return;
        
        window.pywebview.api.play_sound(slotNum).then(function(result) {
            console.log('Play result:', result);
            if (result.status === 'playing') {
                slotEl.classList.add('playing');
            } else {
                slotEl.classList.remove('playing');
            }
        });
    }
    
    function browseForSound(slotNum, slotEl) {
        if (!window.pywebview || !window.pywebview.api) return;
        
        window.pywebview.api.browse_for_sound().then(function(result) {
            if (!result || !result.path) {
                console.log('No file selected');
                return;
            }
            
            console.log('Selected file:', result);
            
            // Update local state
            slotData[slotNum] = slotData[slotNum] || {};
            slotData[slotNum].path = result.path;
            slotData[slotNum].name = result.name;
            
            // Update UI
            slotEl.querySelector('.slot-name').textContent = result.name;
            slotEl.querySelector('.slot-icon').src = window.SLOT_FILLED_ICON;
            slotEl.querySelector('.slot-icon').style.opacity = '0.8';
            
            // Save to backend
            window.pywebview.api.assign_sound_to_slot(slotNum, result.path, result.name);
        });
    }
    
    function startHotkeyAssignment(slotNum, slotEl) {
        // Cancel any previous assignment
        if (awaitingHotkey) {
            awaitingHotkey.element.classList.remove('awaiting-hotkey');
        }
        
        awaitingHotkey = { slotNum: slotNum, element: slotEl };
        slotEl.classList.add('awaiting-hotkey');
        slotEl.querySelector('.slot-hotkey .hotkey-text').textContent = '?';
    }
    
    function cancelHotkeyAssignment() {
        if (!awaitingHotkey) return;
        
        const slotNum = awaitingHotkey.slotNum;
        const slotEl = awaitingHotkey.element;
        
        slotEl.classList.remove('awaiting-hotkey');
        
        // Restore previous hotkey display
        const existingHotkey = slotData[slotNum] && slotData[slotNum].hotkey;
        slotEl.querySelector('.slot-hotkey .hotkey-text').textContent = existingHotkey ? existingHotkey.toUpperCase() : '-';
        
        awaitingHotkey = null;
    }
    
    function assignHotkey(slotNum, slotEl, key) {
        // Remove from old slot if this key was used elsewhere
        if (hotkeyMap[key] && hotkeyMap[key] !== slotNum) {
            const oldSlotNum = hotkeyMap[key];
            const oldSlot = document.querySelector('.sound-slot[data-slot="' + oldSlotNum + '"]');
            if (oldSlot) {
                oldSlot.querySelector('.slot-hotkey .hotkey-text').textContent = '-';
            }
            if (slotData[oldSlotNum]) {
                slotData[oldSlotNum].hotkey = '';
            }
            // Update backend for old slot
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.set_slot_hotkey(oldSlotNum, null);
            }
        }
        
        // Remove old hotkey from this slot
        if (slotData[slotNum] && slotData[slotNum].hotkey) {
            delete hotkeyMap[slotData[slotNum].hotkey];
        }
        
        // Set new hotkey
        slotData[slotNum] = slotData[slotNum] || {};
        slotData[slotNum].hotkey = key;
        hotkeyMap[key] = slotNum;
        
        // Update UI
        slotEl.classList.remove('awaiting-hotkey');
        slotEl.querySelector('.slot-hotkey .hotkey-text').textContent = key.toUpperCase();
        
        awaitingHotkey = null;
        
        // Save to backend
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.set_slot_hotkey(slotNum, key);
        }
    }
    
    function removeHotkey(slotNum, slotEl) {
        // Remove from map
        if (slotData[slotNum] && slotData[slotNum].hotkey) {
            delete hotkeyMap[slotData[slotNum].hotkey];
            slotData[slotNum].hotkey = '';
        }
        
        // Update UI
        slotEl.querySelector('.slot-hotkey .hotkey-text').textContent = '-';
        
        // Save to backend
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.set_slot_hotkey(slotNum, null);
        }
    }
    
    function clearSlot(slotNum, slotEl) {
        // Remove hotkey from map
        if (slotData[slotNum] && slotData[slotNum].hotkey) {
            delete hotkeyMap[slotData[slotNum].hotkey];
        }
        
        // Clear local state
        delete slotData[slotNum];
        
        // Update UI
        slotEl.querySelector('.slot-name').textContent = 'Empty Slot';
        slotEl.querySelector('.slot-icon').src = window.SLOT_EMPTY_ICON;
        slotEl.querySelector('.slot-icon').style.opacity = '0.6';
        slotEl.querySelector('.slot-hotkey .hotkey-text').textContent = '-';
        slotEl.classList.remove('playing');
        
        // Save to backend
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.clear_slot(slotNum);
        }
    }
    
    // ========================================
    // OPENING ANIMATION
    // ========================================
    setTimeout(function() {
        if (openingAnimation) {
            openingAnimation.classList.add('fade-out');
            
            setTimeout(function() {
                openingAnimation.style.display = 'none';
                if (mainContent) {
                    mainContent.classList.remove('hidden');
                    mainContent.classList.add('visible');
                }
                
                // Load saved data after animation
                loadSavedSlots();
            }, 300);
        }
    }, 2000);
});
