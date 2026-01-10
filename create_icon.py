from PIL import Image

# Open PNG and save as ICO with multiple sizes
img = Image.open('assets/images/app_logo.png')
icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save('assets/images/app_logo.ico', sizes=icon_sizes)
print("Icon created successfully!")

