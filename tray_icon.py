import pystray
from PIL import Image
from pathlib import Path
import threading

class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self.base_path = Path(__file__).parent.absolute()
        
    def create_icon(self):
        """Create system tray icon"""
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
        
    def show_window(self, icon, item):
        """Show the application window"""
        if self.app.window:
            self.app.window.show()
    
    def quit_app(self, icon, item):
        """Quit the application"""
        if self.icon:
            self.icon.stop()
        if self.app.window:
            self.app.window.destroy()
    
    def run(self):
        """Run the system tray icon"""
        self.create_icon()
        self.icon.run()
    
    def start_in_background(self):
        """Start tray icon in a separate thread"""
        tray_thread = threading.Thread(target=self.run, daemon=True)
        tray_thread.start()
