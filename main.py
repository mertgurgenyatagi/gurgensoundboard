import webview
import threading
import os
import sys
import base64
import winsound
import ctypes
import json
import wave
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
        self.base_path = Path(__file__).parent.absolute()
        self.slots = {}  # Store sound paths for each slot
        self.config_file = self.base_path / "config.json"
        self.load_config()
        
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
        
    def play_launch_sound(self):
        """Play the launch sound using Windows API"""
        sound_file = str(self.base_path / "assets" / "sounds" / "launch_sound.wav")
        winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
    
    def play_slot_sound(self, slot_num):
        """Play the sound assigned to a slot, return duration in ms"""
        slot_key = str(slot_num)
        if slot_key in self.slots and self.slots[slot_key].get('path'):
            sound_path = self.slots[slot_key]['path']
            if os.path.exists(sound_path):
                # Get duration
                duration = self.get_wav_duration(sound_path)
                # Play the sound
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return duration
        return 0
    
    def get_wav_duration(self, filepath):
        """Get duration of a WAV file in milliseconds"""
        try:
            with wave.open(filepath, 'r') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = (frames / float(rate)) * 1000
                return int(duration)
        except:
            return 2000  # Default 2 seconds if can't read
    
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
        if slot_key not in self.slots:
            self.slots[slot_key] = {}
        self.slots[slot_key]['hotkey'] = hotkey
        self.save_config()
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
            del self.slots[slot_key]
            self.save_config()
        return True
    
    def quit_app(self):
        """Quit the application completely"""
        self.save_config()
        if self.tray and self.tray.icon:
            self.tray.icon.stop()
        if self.window:
            self.window.destroy()
        sys.exit(0)
        
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
        return False  # Prevent window from closing
    
    def start(self):
        """Start the application"""
        # Create system tray icon
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
        
        self.window.events.loaded += on_loaded
        
        # Start webview with edgehtml backend (no pythonnet needed)
        webview.start(debug=False, gui='edgehtml')

def main():
    app = SoundboardApp()
    app.start()

if __name__ == '__main__':
    main()
