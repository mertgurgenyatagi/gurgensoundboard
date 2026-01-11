"""
gurgenSoundboard - Main Application
Completely rewritten from scratch for reliability
"""

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

# ============================================
# SINGLE INSTANCE ENFORCEMENT - AT THE VERY TOP
# ============================================
SINGLE_INSTANCE_MUTEX = None

def enforce_single_instance():
    """Prevent multiple instances using a mutex. Must be called before anything else."""
    global SINGLE_INSTANCE_MUTEX
    
    try:
        import win32event
        import win32api
        import win32gui
        import win32con
        from winerror import ERROR_ALREADY_EXISTS
        
        mutex_name = 'Global\\gurgenSoundboard_SingleInstance_Mutex_v2'
        SINGLE_INSTANCE_MUTEX = win32event.CreateMutex(None, True, mutex_name)
        last_error = win32api.GetLastError()
        
        if last_error == ERROR_ALREADY_EXISTS:
            print("Another instance is already running!")
            
            # Try to bring existing window to front
            def find_window(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if 'gurgensoundboard' in title.lower():
                        extra.append(hwnd)
                return True
            
            windows = []
            try:
                win32gui.EnumWindows(find_window, windows)
                if windows:
                    win32gui.ShowWindow(windows[0], win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(windows[0])
            except:
                pass
            
            # EXIT IMMEDIATELY
            os._exit(0)
            
        print("Single instance check passed - we are the only instance")
        return True
        
    except ImportError as e:
        print(f"Warning: pywin32 not available, single instance check disabled: {e}")
        return True
    except Exception as e:
        print(f"Warning: Single instance check failed: {e}")
        return True

# Run single instance check IMMEDIATELY at module load
enforce_single_instance()

# ============================================
# DPI AWARENESS
# ============================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# ============================================
# MAIN APPLICATION CLASS
# ============================================
class SoundboardApp:
    def __init__(self):
        self.window = None
        self.tray = None
        self.is_running = True
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Paths
        if getattr(sys, 'frozen', False):
            self.base_path = Path(sys._MEIPASS)
            config_dir = Path(os.getenv('APPDATA')) / 'gurgenSoundboard'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file = config_dir / 'config.json'
        else:
            self.base_path = Path(__file__).parent.absolute()
            self.config_file = self.base_path / "config.json"
        
        # Simple, clean state
        self.slots = {}  # {slot_num_str: {path, name, hotkey}}
        self.hotkey_hooks = {}  # {hotkey_str: hook_id}
        self.playing = {}  # {slot_num_str: bool}
        
        self.load_config()
    
    # ========================================
    # CONFIG MANAGEMENT - SIMPLE AND RELIABLE
    # ========================================
    def load_config(self):
        """Load config from file"""
        self.slots = {}
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, dict):
                                self.slots[str(k)] = {
                                    'path': str(v.get('path', '')),
                                    'name': str(v.get('name', '')),
                                    'hotkey': str(v.get('hotkey', ''))
                                }
                print(f"Loaded {len(self.slots)} slots from config")
        except Exception as e:
            print(f"Config load error: {e}")
            self.slots = {}
    
    def save_config(self):
        """Save config to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.slots, f, indent=2)
            print(f"Saved {len(self.slots)} slots to config")
        except Exception as e:
            print(f"Config save error: {e}")
    
    # ========================================
    # HOTKEY MANAGEMENT - SIMPLE AND RELIABLE
    # ========================================
    def setup_hotkeys(self):
        """Setup all hotkeys from config"""
        # Clear existing
        self.clear_all_hotkeys()
        
        # Register new ones
        for slot_num, data in self.slots.items():
            hk = data.get('hotkey', '')
            if hk:
                self.register_hotkey(slot_num, hk)
    
    def clear_all_hotkeys(self):
        """Remove all hotkey registrations"""
        for hk, hook in list(self.hotkey_hooks.items()):
            try:
                keyboard.remove_hotkey(hook)
            except:
                pass
        self.hotkey_hooks.clear()
    
    def register_hotkey(self, slot_num, hotkey_str):
        """Register a single hotkey"""
        try:
            # Remove if exists
            if hotkey_str in self.hotkey_hooks:
                try:
                    keyboard.remove_hotkey(self.hotkey_hooks[hotkey_str])
                except:
                    pass
            
            # Create callback with captured slot_num
            sn = str(slot_num)
            def make_callback(s):
                return lambda: self.on_hotkey_pressed(s)
            
            hook = keyboard.add_hotkey(hotkey_str, make_callback(sn), suppress=True)
            self.hotkey_hooks[hotkey_str] = hook
            print(f"Registered hotkey '{hotkey_str}' for slot {slot_num}")
        except Exception as e:
            print(f"Hotkey registration error: {e}")
    
    def unregister_hotkey(self, hotkey_str):
        """Unregister a single hotkey"""
        if hotkey_str in self.hotkey_hooks:
            try:
                keyboard.remove_hotkey(self.hotkey_hooks[hotkey_str])
                del self.hotkey_hooks[hotkey_str]
            except:
                pass
    
    def on_hotkey_pressed(self, slot_num):
        """Handle hotkey press"""
        print(f"Hotkey pressed for slot {slot_num}")
        slot_num = str(slot_num)
        
        if slot_num not in self.slots:
            return
        
        path = self.slots[slot_num].get('path', '')
        if not path or not os.path.exists(path):
            return
        
        # If playing, stop
        if self.playing.get(slot_num, False):
            pygame.mixer.music.stop()
            self.playing[slot_num] = False
            return
        
        # Play
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.playing[slot_num] = True
            
            # Monitor for completion
            def monitor():
                while pygame.mixer.music.get_busy():
                    threading.Event().wait(0.1)
                self.playing[slot_num] = False
            
            threading.Thread(target=monitor, daemon=True).start()
        except Exception as e:
            print(f"Playback error: {e}")
            self.playing[slot_num] = False
    
    # ========================================
    # API METHODS - CALLED FROM JAVASCRIPT
    # ========================================
    def get_slots(self):
        """Get all slots"""
        return self.slots
    
    def play_sound(self, slot_num):
        """Play/stop sound for slot"""
        slot_num = str(slot_num)
        
        if slot_num not in self.slots:
            return {'status': 'no_slot'}
        
        path = self.slots[slot_num].get('path', '')
        if not path:
            return {'status': 'no_sound'}
        
        if not os.path.exists(path):
            return {'status': 'file_missing'}
        
        # If playing, stop
        if self.playing.get(slot_num, False):
            pygame.mixer.music.stop()
            self.playing[slot_num] = False
            return {'status': 'stopped'}
        
        # Play
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.playing[slot_num] = True
            
            def monitor():
                while pygame.mixer.music.get_busy():
                    threading.Event().wait(0.1)
                self.playing[slot_num] = False
            
            threading.Thread(target=monitor, daemon=True).start()
            return {'status': 'playing'}
        except Exception as e:
            self.playing[slot_num] = False
            return {'status': 'error', 'message': str(e)}
    
    def browse_for_sound(self):
        """Open file browser - using webview native dialog"""
        try:
            if self.window:
                result = self.window.create_file_dialog(
                    webview.OPEN_DIALOG,
                    allow_multiple=False,
                    file_types=('Audio Files (*.mp3;*.wav;*.ogg;*.flac;*.m4a;*.wma;*.aac)', 'All Files (*.*)')
                )
                
                if result and len(result) > 0:
                    filepath = result[0]
                    filename = os.path.basename(filepath)
                    name = os.path.splitext(filename)[0]
                    return {'path': filepath, 'name': name}
            
            return None
        except Exception as e:
            print(f"File dialog error: {e}")
            return None
    
    def assign_sound_to_slot(self, slot_num, path, name):
        """Assign sound to slot"""
        slot_num = str(slot_num)
        
        # Preserve existing hotkey
        existing_hotkey = ''
        if slot_num in self.slots:
            existing_hotkey = self.slots[slot_num].get('hotkey', '')
        
        self.slots[slot_num] = {
            'path': path,
            'name': name,
            'hotkey': existing_hotkey
        }
        
        self.save_config()
        return True
    
    def set_slot_hotkey(self, slot_num, hotkey):
        """Set hotkey for slot"""
        slot_num = str(slot_num)
        
        # Remove old hotkey if exists
        if slot_num in self.slots:
            old_hk = self.slots[slot_num].get('hotkey', '')
            if old_hk:
                self.unregister_hotkey(old_hk)
        
        # Ensure slot exists
        if slot_num not in self.slots:
            self.slots[slot_num] = {'path': '', 'name': '', 'hotkey': ''}
        
        # Set new hotkey
        self.slots[slot_num]['hotkey'] = hotkey if hotkey else ''
        self.save_config()
        
        # Register if provided
        if hotkey:
            self.register_hotkey(slot_num, hotkey)
        
        return True
    
    def clear_slot(self, slot_num):
        """Clear a slot completely"""
        slot_num = str(slot_num)
        
        if slot_num in self.slots:
            # Stop if playing
            if self.playing.get(slot_num, False):
                pygame.mixer.music.stop()
                self.playing[slot_num] = False
            
            # Unregister hotkey
            hk = self.slots[slot_num].get('hotkey', '')
            if hk:
                self.unregister_hotkey(hk)
            
            # Remove slot
            del self.slots[slot_num]
            self.save_config()
        
        return True
    
    def stop_all_sounds(self):
        """Stop all playing sounds"""
        pygame.mixer.music.stop()
        for k in self.playing:
            self.playing[k] = False
        return True
    
    def hide_window(self):
        """Hide to tray"""
        if self.window:
            self.window.hide()
        return True
    
    def quit_app(self):
        """Quit immediately"""
        print("Quitting...")
        self.save_config()
        
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except:
            pass
        
        try:
            keyboard.unhook_all()
        except:
            pass
        
        os._exit(0)
    
    # ========================================
    # LAUNCH SOUND
    # ========================================
    def play_launch_sound(self):
        """Play startup sound"""
        try:
            sound_path = self.base_path / "assets" / "sounds" / "launch_sound.wav"
            if sound_path.exists():
                sound = pygame.mixer.Sound(str(sound_path))
                sound.play()
        except Exception as e:
            print(f"Launch sound error: {e}")
    
    # ========================================
    # HTML CONTENT GENERATION
    # ========================================
    def get_html_content(self):
        """Build HTML with embedded assets"""
        html_path = self.base_path / "ui" / "index.html"
        css_path = self.base_path / "ui" / "style.css"
        js_path = self.base_path / "ui" / "script.js"
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
        with open(js_path, 'r', encoding='utf-8') as f:
            js = f.read()
        
        # Load and encode images
        def encode_file(path):
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        
        logo_b64 = encode_file(self.base_path / "assets" / "images" / "app_logo.svg")
        close_b64 = encode_file(self.base_path / "assets" / "images" / "close.svg")
        empty_b64 = encode_file(self.base_path / "assets" / "images" / "slot_empty.svg")
        filled_b64 = encode_file(self.base_path / "assets" / "images" / "slot_filled.svg")
        removal_b64 = encode_file(self.base_path / "assets" / "images" / "slot_removal.svg")
        sound_b64 = encode_file(self.base_path / "assets" / "sounds" / "launch_sound.wav")
        
        logo_uri = f'data:image/svg+xml;base64,{logo_b64}'
        close_uri = f'data:image/svg+xml;base64,{close_b64}'
        empty_uri = f'data:image/svg+xml;base64,{empty_b64}'
        filled_uri = f'data:image/svg+xml;base64,{filled_b64}'
        removal_uri = f'data:image/svg+xml;base64,{removal_b64}'
        sound_uri = f'data:audio/wav;base64,{sound_b64}'
        
        # Inject CSS and JS
        html = html.replace('<link rel="stylesheet" href="style.css">', f'<style>{css}</style>')
        
        js_globals = f'''
        window.SLOT_EMPTY_ICON = "{empty_uri}";
        window.SLOT_FILLED_ICON = "{filled_uri}";
        window.SLOT_REMOVAL_ICON = "{removal_uri}";
        '''
        html = html.replace('<script src="script.js"></script>', f'<script>{js_globals}\n{js}</script>')
        
        # Replace image sources
        html = html.replace('src="../assets/images/app_logo.svg"', f'src="{logo_uri}"')
        html = html.replace('src="../assets/images/close.svg"', f'src="{close_uri}"')
        html = html.replace('src="../assets/images/slot_empty.svg"', f'src="{empty_uri}"')
        html = html.replace('src="../assets/sounds/launch_sound.wav"', f'src="{sound_uri}"')
        
        return html
    
    # ========================================
    # WINDOW EVENTS
    # ========================================
    def on_closing(self):
        """Minimize to tray instead of closing"""
        if self.window:
            self.window.hide()
        return False
    
    # ========================================
    # START APPLICATION
    # ========================================
    def start(self):
        """Start the application"""
        # Create tray icon
        self.tray = TrayIcon(self)
        self.tray.start_in_background()
        
        # Create window
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
        
        def on_loaded():
            self.play_launch_sound()
            threading.Timer(0.5, self.setup_hotkeys).start()
        
        self.window.events.loaded += on_loaded
        self.window.events.closing += self.on_closing
        
        webview.start(debug=False, gui='edgechromium')


# ============================================
# ENTRY POINT
# ============================================
def main():
    app = SoundboardApp()
    app.start()

if __name__ == '__main__':
    main()
