import base64
from pathlib import Path

class API:
    def __init__(self, base_path):
        self._logo_path = base_path / "assets" / "images" / "app_logo.png"
        
    def get_logo_base64(self):
        """Get logo as base64 string"""
        with open(self._logo_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
