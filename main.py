import webview
import threading
import os
import sys
from pathlib import Path
from tray_icon import TrayIcon

class SoundboardApp:
    def __init__(self):
        self.window = None
        self.tray = None
        self.base_path = Path(__file__).parent.absolute()
        
    def get_html_path(self):
        """Get the path to the HTML file"""
        return str(self.base_path / "ui" / "index.html")
    
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
            self.get_html_path(),
            width=800,
            height=500,
            resizable=False,
            frameless=True,
            easy_drag=True,
            background_color='#FFFFFF',
            on_top=False
        )
        
        # Start webview
        webview.start(debug=False)

def main():
    app = SoundboardApp()
    app.start()

if __name__ == '__main__':
    main()
