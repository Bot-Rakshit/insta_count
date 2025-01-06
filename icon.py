# Run this script to create a basic icon
from PIL import Image, ImageDraw

def create_icon():
    # Create a 192x192 image with a blue background
    img = Image.new('RGB', (192, 192), color='#0095f6')
    d = ImageDraw.Draw(img)
    
    # Ensure the static directory exists
    import os
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Save it
    img.save('static/icon-192x192.png')

if __name__ == "__main__":
    create_icon() p