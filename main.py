import webview
import threading
import os
import sys
import base64
import ctypes
import json
import keyboard
import pygame
from pathlib import Path
from tray_icon import TrayIcon
from tkinter import Tk, filedialog

# Enable DPI awareness for sharper rendering
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Fallback for older Windows
    except:
        pass

class SoundboardApp:
    def __init__(self):
        self.window = None
        self.tray = None
        self.is_running = True
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Use sys._MEIPASS for bundled app, otherwise use script directory
        if getattr(sys, 'frozen', False):
            self.base_path = Path(sys._MEIPASS)
            # Store config in user's AppData for persistence
            config_dir = Path(os.getenv('APPDATA')) / 'gurgenSoundboard'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file = config_dir / 'config.json'
        else:
            self.base_path = Path(__file__).parent.absolute()
            self.config_file = self.base_path / "config.json"
        self.slots = {}  # Store sound paths for each slot
        self.registered_hotkeys = {}  # Track registered global hotkeys
        self.currently_playing = {}  # Track which slots are currently playing
        self.load_config()
        self.setup_global_hotkeys()
        
    def load_config(self):
        """Load saved slot configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.slots = json.load(f)
        except:
            self.slots = {}
    
    def save_config(self):
        """Save slot configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.slots, f)
        except:
            pass
    
    def setup_global_hotkeys(self):
        """Setup all global hotkeys from saved configuration"""
        print(f"Setting up global hotkeys for {len(self.slots)} slots...")
        for slot_num, slot_data in self.slots.items():
            if 'hotkey' in slot_data and slot_data['hotkey']:
                print(f"Registering hotkey {slot_data['hotkey']} for slot {slot_num}")
                self.register_global_hotkey(slot_num, slot_data['hotkey'])
    
    def register_global_hotkey(self, slot_num, hotkey):
        """Register a global hotkey for a slot"""
        try:
            # Remove existing registration if any
            if hotkey in self.registered_hotkeys:
                try:
                    keyboard.remove_hotkey(self.registered_hotkeys[hotkey])
                except:
                    pass
            
            # Register the hotkey globally with suppress=True to prevent key from reaching the window
            # Note: May require admin privileges depending on system configuration
            def callback():
                self.trigger_slot(slot_num)
            
            hook_id = keyboard.add_hotkey(hotkey, callback, suppress=True)
            self.registered_hotkeys[hotkey] = hook_id
            print(f"Successfully registered hotkey {hotkey} with hook_id {hook_id}")
        except Exception as e:
            print(f"Error registering hotkey {hotkey}: {e}")
            import traceback
            traceback.print_exc()
    
    def trigger_slot(self, slot_num):
        """Trigger a slot sound from global hotkey (stop-on-press functionality)"""
        print(f"HOTKEY TRIGGERED! Slot {slot_num}")  # Debug output
        try:
            slot_key = str(slot_num)
            
            # If this slot is currently playing, stop it
            if slot_key in self.currently_playing and self.currently_playing[slot_key]:
                pygame.mixer.music.stop()
                self.currently_playing[slot_key] = False
                print(f"Stopped playing slot {slot_num}")
                return
            
            # Otherwise, play the sound
            if slot_key in self.slots and 'path' in self.slots[slot_key]:
                sound_path = self.slots[slot_key]['path']
                # Mark as playing
                self.currently_playing[slot_key] = True
                # Play sound
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
                print(f"Playing slot {slot_num}: {sound_path}")
                
                # Schedule cleanup when sound finishes
                def check_finished():
                    while pygame.mixer.music.get_busy():
                        threading.Event().wait(0.1)
                    self._mark_slot_stopped(slot_key)
                
                threading.Thread(target=check_finished, daemon=True).start()
        except Exception as e:
            print(f"Error triggering slot {slot_num}: {e}")
            import traceback
            traceback.print_exc()
    
    def _mark_slot_stopped(self, slot_key):
        """Mark a slot as stopped playing"""
        if slot_key in self.currently_playing:
            self.currently_playing[slot_key] = False
        
    def play_launch_sound(self):
        """Play the launch sound when app starts"""
        try:
            sound_path = self.base_path / "assets" / "sounds" / "launch_sound.wav"
            if sound_path.exists():
                # Use a Sound object for one-off sounds so they don't interfere with music channel
                sound = pygame.mixer.Sound(str(sound_path))
                sound.play()
        except Exception as e:
            print(f"Error playing launch sound: {e}")
    
    def play_slot_sound(self, slot_num):
        """Play the sound assigned to a slot"""
        try:
            slot_key = str(slot_num)
            
            # Check if currently playing - if so, stop it (stop-on-press)
            if slot_key in self.currently_playing and self.currently_playing[slot_key]:
                pygame.mixer.music.stop()
                self.currently_playing[slot_key] = False
                return {'status': 'stopped'}
            
            # Play the sound if slot has a sound assigned
            if slot_key in self.slots and 'path' in self.slots[slot_key]:
                sound_path = self.slots[slot_key]['path']
                
                if not os.path.exists(sound_path):
                    return {'status': 'file_not_found'}
                
                # Mark as currently playing
                self.currently_playing[slot_key] = True
                
                # Play sound
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
                
                # Schedule cleanup when sound finishes
                def check_finished():
                    while pygame.mixer.music.get_busy():
                        threading.Event().wait(0.1)
                    self._mark_slot_stopped(slot_key)
                
                threading.Thread(target=check_finished, daemon=True).start()
                
                return {'status': 'playing'}
            
            return {'status': 'no_sound'}
        except Exception as e:
            print(f"Error playing sound: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': str(e)}
    

    
    def open_file_dialog(self):
        """Open file dialog to select a sound file using tkinter"""
        try:
            # Create a hidden tkinter root window
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            filepath = filedialog.askopenfilename(
                title='Select Sound File',
                filetypes=[
                    ('Audio Files', '*.wav *.mp3 *.ogg'),
                    ('WAV Files', '*.wav'),
                    ('MP3 Files', '*.mp3'),
                    ('All Files', '*.*')
                ]
            )
            
            root.destroy()
            
            if filepath:
                filename = os.path.basename(filepath)
                name_without_ext = os.path.splitext(filename)[0]
                return {'path': filepath, 'name': name_without_ext}
        except Exception as e:
            print(f"File dialog error: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def assign_sound(self, slot_num, path, name):
        """Assign a sound to a slot"""
        self.slots[str(slot_num)] = {'path': path, 'name': name}
        self.save_config()
        return True
    
    def get_slots(self):
        """Get all slot configurations"""
        return self.slots
    
    def set_hotkey(self, slot_num, hotkey):
        """Set hotkey for a slot"""
        slot_key = str(slot_num)
        
        # Unregister old hotkey if exists
        if slot_key in self.slots and 'hotkey' in self.slots[slot_key]:
            old_hotkey = self.slots[slot_key]['hotkey']
            if old_hotkey and old_hotkey in self.registered_hotkeys:
                try:
                    keyboard.remove_hotkey(self.registered_hotkeys[old_hotkey])
                    del self.registered_hotkeys[old_hotkey]
                except:
                    pass
        
        # Update slot configuration
        if slot_key not in self.slots:
            self.slots[slot_key] = {}
        self.slots[slot_key]['hotkey'] = hotkey
        self.save_config()
        
        # Register new global hotkey
        if hotkey:
            self.register_global_hotkey(slot_num, hotkey)
        
        return True
    
    def stop_sound(self):
        """Stop currently playing sound"""
        try:
            winsound.PlaySound(None, winsound.SND_ASYNC)
            return True
        except Exception as e:
            print(f"Error stopping sound: {e}")
            return False
    
    def clear_slot(self, slot_num):
        """Clear a slot (remove sound assignment)"""
        slot_key = str(slot_num)
        if slot_key in self.slots:
            # Unregister hotkey if exists
            if 'hotkey' in self.slots[slot_key]:
                hotkey = self.slots[slot_key]['hotkey']
                if hotkey and hotkey in self.registered_hotkeys:
                    try:
                        keyboard.remove_hotkey(self.registered_hotkeys[hotkey])
                        del self.registered_hotkeys[hotkey]
                    except:
                        pass
            del self.slots[slot_key]
            self.save_config()
        return True
    
    def quit_app(self):
        """Quit the application completely"""
        self.is_running = False
        self.save_config()
        
        # Stop any playing sounds
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except:
            pass
        
        # Unregister all hotkeys
        try:
            keyboard.unhook_all()
        except:
            pass
        
        # Stop tray icon
        if self.tray and self.tray.icon:
            self.tray.icon.stop()
        
        # Destroy window
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
        
        # Force exit
        os._exit(0)
        
    def get_html_content(self):
        """Get HTML content with embedded assets"""
        html_path = self.base_path / "ui" / "index.html"
        css_path = self.base_path / "ui" / "style.css"
        js_path = self.base_path / "ui" / "script.js"
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
            
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Convert logo to base64
        logo_file = self.base_path / "assets" / "images" / "app_logo.svg"
        with open(logo_file, 'rb') as f:
            logo_base64 = base64.b64encode(f.read()).decode('utf-8')
        logo_data_uri = f'data:image/svg+xml;base64,{logo_base64}'
        
        # Convert close icon to base64
        close_file = self.base_path / "assets" / "images" / "close.svg"
        with open(close_file, 'rb') as f:
            close_base64 = base64.b64encode(f.read()).decode('utf-8')
        close_data_uri = f'data:image/svg+xml;base64,{close_base64}'
        
        # Convert slot icons to base64
        slot_empty_file = self.base_path / "assets" / "images" / "slot_empty.svg"
        with open(slot_empty_file, 'rb') as f:
            slot_empty_base64 = base64.b64encode(f.read()).decode('utf-8')
        slot_empty_data_uri = f'data:image/svg+xml;base64,{slot_empty_base64}'
        
        slot_filled_file = self.base_path / "assets" / "images" / "slot_filled.svg"
        with open(slot_filled_file, 'rb') as f:
            slot_filled_base64 = base64.b64encode(f.read()).decode('utf-8')
        slot_filled_data_uri = f'data:image/svg+xml;base64,{slot_filled_base64}'
        
        # Convert slot removal icon to base64
        slot_removal_file = self.base_path / "assets" / "images" / "slot_removal.svg"
        with open(slot_removal_file, 'rb') as f:
            slot_removal_base64 = base64.b64encode(f.read()).decode('utf-8')
        slot_removal_data_uri = f'data:image/svg+xml;base64,{slot_removal_base64}'
        
        # Convert sound to base64
        sound_file = self.base_path / "assets" / "sounds" / "launch_sound.wav"
        with open(sound_file, 'rb') as f:
            sound_base64 = base64.b64encode(f.read()).decode('utf-8')
        sound_data_uri = f'data:audio/wav;base64,{sound_base64}'
        
        # Replace external references with inline content
        html = html.replace('<link rel="stylesheet" href="style.css">', f'<style>{css_content}</style>')
        html = html.replace('<script src="script.js"></script>', f'<script>window.SLOT_EMPTY_ICON="{slot_empty_data_uri}";window.SLOT_FILLED_ICON="{slot_filled_data_uri}";window.SLOT_REMOVAL_ICON="{slot_removal_data_uri}";{js_content}</script>')
        html = html.replace('src="../assets/images/app_logo.svg"', f'src="{logo_data_uri}"')
        html = html.replace('src="../assets/images/close.svg"', f'src="{close_data_uri}"')
        html = html.replace('src="../assets/images/slot_empty.svg"', f'src="{slot_empty_data_uri}"')
        html = html.replace('src="../assets/sounds/launch_sound.wav"', f'src="{sound_data_uri}"')
        
        return html
    
    def on_closing(self):
        """Handle window close event - minimize to tray instead of closing"""
        if self.window:
            self.window.hide()
        return False  # Prevent window from actually closing/destroying
    
    def hide_window(self):
        """Hide window to tray (called from UI)"""
        if self.window:
            self.window.hide()
        return True
    
    def start(self):
        """Start the application"""
        # Create system tray icon first
        self.tray = TrayIcon(self)
        self.tray.start_in_background()
        
        # Create window with headless style (frameless)
        self.window = webview.create_window(
            'gurgenSoundboard',
            html=self.get_html_content(),
            width=800,
            height=500,
            resizable=False,
            frameless=True,
            easy_drag=True,
            background_color='#04020f',
            on_top=False,
            js_api=self
        )
        
        # Play launch sound when window is ready
        def on_loaded():
            self.play_launch_sound()
            # Setup global hotkeys after window loads in a separate thread
            # This ensures keyboard hooks can process properly
            threading.Timer(0.5, self.setup_global_hotkeys).start()
        
        self.window.events.loaded += on_loaded
        
        # Connect closing event to minimize to tray
        self.window.events.closing += self.on_closing
        
        # Start webview - this blocks until window actually closes (not just hides)
        webview.start(debug=False, gui='edgehtml')

def main():
    app = SoundboardApp()
    app.start()

if __name__ == '__main__':
    main()
