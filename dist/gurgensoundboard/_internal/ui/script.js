// Opening animation controller
document.addEventListener('DOMContentLoaded', function() {
    const openingAnimation = document.getElementById('opening-animation');
    const mainContent = document.getElementById('main-content');
    const closeBtn = document.querySelector('.close-btn');
    const soundSlots = document.querySelectorAll('.sound-slot');
    
    // Sound slot data storage
    const slotData = {};
    // Hotkey to slot mapping
    const hotkeyMap = {};
    // Slot waiting for hotkey assignment
    let pendingHotkeySlot = null;
    // Currently playing sounds
    const playingSounds = {};
    
    // Set removal icon sources
    document.querySelectorAll('.slot-remove, .hotkey-remove').forEach(img => {
        img.src = window.SLOT_REMOVAL_ICON;
    });
    
    // Close button functionality
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            if (window.pywebview) {
                window.pywebview.api.hide_window();
            }
        });
    }
    
    // Load saved slot data
    function loadSlotData() {
        if (window.pywebview) {
            window.pywebview.api.get_slots().then(slots => {
                if (slots) {
                    Object.keys(slots).forEach(slotNum => {
                        const slotInfo = slots[slotNum];
                        slotData[slotNum] = slotInfo;
                        
                        const slot = document.querySelector(`.sound-slot[data-slot="${slotNum}"]`);
                        if (slot) {
                            if (slotInfo.name) {
                                const nameEl = slot.querySelector('.slot-name');
                                nameEl.textContent = slotInfo.name;
                                const iconEl = slot.querySelector('.slot-icon');
                                iconEl.setAttribute('src', window.SLOT_FILLED_ICON);
                                iconEl.style.opacity = '0.8';
                            }
                            if (slotInfo.hotkey) {
                                const hotkeyEl = slot.querySelector('.slot-hotkey .hotkey-text');
                                hotkeyEl.textContent = slotInfo.hotkey.toUpperCase();
                                hotkeyMap[slotInfo.hotkey.toLowerCase()] = slotNum;
                            }
                        }
                    });
                }
            });
        }
    }
    
    // Sound slot click handlers
    soundSlots.forEach(slot => {
        // Left click - play sound
        slot.addEventListener('click', function(e) {
            // Don't play if clicking hotkey badge or remove buttons
            if (e.target.closest('.slot-hotkey') || e.target.closest('.slot-remove')) return;
            
            const slotNum = this.dataset.slot;
            playSlotSound(slotNum, this);
        });
        
        // Right click - assign sound
        slot.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            const slotNum = this.dataset.slot;
            assignSound(slotNum, this);
        });
        
        // Hotkey badge click - assign hotkey
        const hotkeyBadge = slot.querySelector('.slot-hotkey');
        hotkeyBadge.addEventListener('click', function(e) {
            e.stopPropagation();
            // If clicking the remove button, don't assign hotkey
            if (e.target.closest('.hotkey-remove')) return;
            const slotNum = slot.dataset.slot;
            startHotkeyAssignment(slotNum, slot);
        });
        
        // Hotkey remove button
        const hotkeyRemove = slot.querySelector('.hotkey-remove');
        hotkeyRemove.addEventListener('click', function(e) {
            e.stopPropagation();
            const slotNum = slot.dataset.slot;
            removeHotkey(slotNum, slot);
        });
        
        // Slot remove button
        const slotRemove = slot.querySelector('.slot-remove');
        slotRemove.addEventListener('click', function(e) {
            e.stopPropagation();
            const slotNum = slot.dataset.slot;
            clearSlot(slotNum, slot);
        });
    });
    
    // Keyboard handler
    document.addEventListener('keydown', function(e) {
        const key = e.key.toLowerCase();
        
        // If waiting for hotkey assignment
        if (pendingHotkeySlot) {
            e.preventDefault();
            assignHotkey(pendingHotkeySlot.slotNum, pendingHotkeySlot.element, key);
            return;
        }
        
        // Check if this key is mapped to a slot
        if (hotkeyMap[key]) {
            const slotNum = hotkeyMap[key];
            const slot = document.querySelector(`.sound-slot[data-slot="${slotNum}"]`);
            if (slot) {
                // If sound is already playing, stop it
                if (playingSounds[slotNum]) {
                    stopSlotSound(slotNum, slot);
                } else {
                    playSlotSound(slotNum, slot);
                    // Visual feedback for keypress
                    slot.style.transform = 'translateY(-2px) scale(0.98)';
                    setTimeout(() => {
                        slot.style.transform = '';
                    }, 100);
                }
            }
        }
    });
    
    // Start hotkey assignment mode
    function startHotkeyAssignment(slotNum, slotElement) {
        // Remove previous pending state
        if (pendingHotkeySlot) {
            pendingHotkeySlot.element.classList.remove('awaiting-hotkey');
        }
        
        pendingHotkeySlot = { slotNum, element: slotElement };
        slotElement.classList.add('awaiting-hotkey');
        
        const hotkeyEl = slotElement.querySelector('.slot-hotkey .hotkey-text');
        hotkeyEl.textContent = '?';
    }
    
    // Remove hotkey from slot
    function removeHotkey(slotNum, slotElement) {
        // Remove from mapping
        Object.keys(hotkeyMap).forEach(k => {
            if (hotkeyMap[k] === slotNum) {
                delete hotkeyMap[k];
            }
        });
        
        // Update display
        const hotkeyEl = slotElement.querySelector('.slot-hotkey .hotkey-text');
        hotkeyEl.textContent = '-';
        
        // Update backend
        if (window.pywebview) {
            window.pywebview.api.set_hotkey(slotNum, null);
        }
    }
    
    // Clear slot (remove sound)
    function clearSlot(slotNum, slotElement) {
        // Stop sound if playing
        if (playingSounds[slotNum]) {
            stopSlotSound(slotNum, slotElement);
        }
        
        // Clear data
        delete slotData[slotNum];
        
        // Update display
        const nameEl = slotElement.querySelector('.slot-name');
        nameEl.textContent = 'Empty Slot';
        const iconEl = slotElement.querySelector('.slot-icon');
        iconEl.setAttribute('src', window.SLOT_EMPTY_ICON);
        iconEl.style.opacity = '0.6';
        
        // Update backend
        if (window.pywebview) {
            window.pywebview.api.clear_slot(slotNum);
        }
    }
    
    // Assign hotkey to slot
    function assignHotkey(slotNum, slotElement, key) {
        // Remove old mapping if exists
        Object.keys(hotkeyMap).forEach(k => {
            if (hotkeyMap[k] === slotNum) {
                delete hotkeyMap[k];
            }
        });
        
        // Check if key is already used by another slot
        if (hotkeyMap[key]) {
            const oldSlotNum = hotkeyMap[key];
            const oldSlot = document.querySelector(`.sound-slot[data-slot="${oldSlotNum}"]`);
            if (oldSlot) {
                oldSlot.querySelector('.slot-hotkey .hotkey-text').textContent = '-';
            }
            // Update old slot in backend
            if (window.pywebview) {
                window.pywebview.api.set_hotkey(oldSlotNum, null);
            }
        }
        
        // Set new mapping
        hotkeyMap[key] = slotNum;
        
        const hotkeyEl = slotElement.querySelector('.slot-hotkey .hotkey-text');
        hotkeyEl.textContent = key.toUpperCase();
        
        slotElement.classList.remove('awaiting-hotkey');
        pendingHotkeySlot = null;
        
        // Save to backend
        if (window.pywebview) {
            window.pywebview.api.set_hotkey(slotNum, key);
        }
    }
    
    // Stop sound for a slot
    function stopSlotSound(slotNum, slotElement) {
        if (window.pywebview) {
            window.pywebview.api.stop_sound();
        }
        
        // Clear playing state
        delete playingSounds[slotNum];
        slotElement.classList.remove('playing');
        
        // Reset progress bar
        const progressBar = slotElement.querySelector('.slot-progress');
        progressBar.style.transition = 'none';
        progressBar.style.width = '0%';
    }
    
    // Play sound for a slot
    function playSlotSound(slotNum, slotElement) {
        if (window.pywebview) {
            // Add playing class
            slotElement.classList.add('playing');
            playingSounds[slotNum] = true;
            
            window.pywebview.api.play_slot_sound(slotNum).then(duration => {
                if (duration > 0) {
                    // Animate progress bar
                    const progressBar = slotElement.querySelector('.slot-progress');
                    progressBar.style.transition = `width ${duration}ms linear`;
                    progressBar.style.width = '100%';
                    
                    setTimeout(() => {
                        delete playingSounds[slotNum];
                        slotElement.classList.remove('playing');
                        progressBar.style.transition = 'none';
                        progressBar.style.width = '0%';
                    }, duration);
                } else {
                    delete playingSounds[slotNum];
                    slotElement.classList.remove('playing');
                    // No sound assigned, prompt to assign
                    assignSound(slotNum, slotElement);
                }
            });
        }
    }
    
    // Assign sound to a slot
    function assignSound(slotNum, slotElement) {
        if (window.pywebview) {
            window.pywebview.api.open_file_dialog().then(result => {
                if (result && result.path) {
                    slotData[slotNum] = result;
                    
                    // Save to Python backend
                    window.pywebview.api.assign_sound(slotNum, result.path, result.name);
                    
                    // Update slot display
                    const nameEl = slotElement.querySelector('.slot-name');
                    nameEl.textContent = result.name;
                    
                    // Update icon to show it has a sound
                    const iconEl = slotElement.querySelector('.slot-icon');
                    iconEl.setAttribute('src', window.SLOT_FILLED_ICON);
                    iconEl.style.opacity = '0.8';
                }
            });
        }
    }
    
    // Cancel hotkey assignment on click outside
    document.addEventListener('click', function(e) {
        if (pendingHotkeySlot && !e.target.closest('.sound-slot')) {
            pendingHotkeySlot.element.classList.remove('awaiting-hotkey');
            const hotkeyEl = pendingHotkeySlot.element.querySelector('.slot-hotkey');
            const slotNum = pendingHotkeySlot.slotNum;
            // Restore previous hotkey or show dash
            const previousKey = Object.keys(hotkeyMap).find(k => hotkeyMap[k] === slotNum);
            hotkeyEl.textContent = previousKey ? previousKey.toUpperCase() : '-';
            pendingHotkeySlot = null;
        }
    });
    
    // After 2 seconds, hide opening animation and show main content
    setTimeout(() => {
        openingAnimation.classList.add('fade-out');
        
        // Wait for fade-out transition to complete
        setTimeout(() => {
            openingAnimation.style.display = 'none';
            mainContent.classList.remove('hidden');
            mainContent.classList.add('visible');
            
            // Load saved slot data after main content is visible
            loadSlotData();
        }, 300);
    }, 2000); // 2 second animation duration
});
