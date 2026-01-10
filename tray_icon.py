import pystray
from PIL import Image
from pathlib import Path
import threading
import sys
import os

class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = None
        # Use sys._MEIPASS for bundled app, otherwise use script directory
        if getattr(sys, 'frozen', False):
            self.base_path = Path(sys._MEIPASS)
        else:
            self.base_path = Path(__file__).parent.absolute()
        
    def create_icon(self):
        """Create system tray icon"""
        try:
            # Load logo image for tray icon
            logo_path = self.base_path / "assets" / "images" / "app_logo.png"
            image = Image.open(logo_path)
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Exit", self.quit_app)
            )
            
            # Create icon
            self.icon = pystray.Icon("gurgenSoundboard", image, "gurgenSoundboard", menu)
        except Exception as e:
            print(f"Error creating tray icon: {e}")
            import traceback
            traceback.print_exc()
        
    def show_window(self, icon, item):
        """Show the application window"""
        if self.app.window:
            self.app.window.show()
    
    def quit_app(self, icon, item):
        """Quit the application"""
        # Stop the tray icon first
        if self.icon:
            self.icon.stop()
        # Then quit the app
        self.app.quit_app()
    
    def run(self):
        """Run the system tray icon"""
        try:
            self.create_icon()
            if self.icon:
                print("Starting tray icon...")
                self.icon.run()
        except Exception as e:
            print(f"Error running tray icon: {e}")
            import traceback
            traceback.print_exc()
    
    def start_in_background(self):
        """Start tray icon in a separate thread"""
        tray_thread = threading.Thread(target=self.run, daemon=False)
        tray_thread.start()
