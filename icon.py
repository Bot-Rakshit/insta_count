# Run this script to create a basic icon
from PIL import Image, ImageDraw

def create_icons():
    # Ensure the static directory exists
    import os
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Create icons with different sizes
    sizes = [192, 512]
    for size in sizes:
        # Create a square image with a blue background
        img = Image.new('RGB', (size, size), color='#0095f6')
        d = ImageDraw.Draw(img)
        
        # Save regular icon
        img.save(f'static/icon-{size}x{size}.png')
        
        if size == 512:
            # Create maskable icon with safe area
            safe_area = Image.new('RGB', (size, size), color='#0095f6')
            # Add a white border to make it maskable
            border = size // 8
            d = ImageDraw.Draw(safe_area)
            d.rectangle([border, border, size-border, size-border], fill='#0095f6')
            safe_area.save('static/maskable_icon.png')

if __name__ == "__main__":
    create_icons()