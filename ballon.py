#!/usr/bin/env python3
from PIL import Image, ImageDraw

def create_ultra_dense_ballon(filename="ballon_texture.png", size=1024):
    # Image de base blanche haute résolution (1024x1024)
    image = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    rows = 4
    cols = 8
    dx = size / cols
    dy = size / rows
    
    for r in range(rows + 1):
        for c in range(cols + 1):
            if (r + c) % 2 == 0:
                x = c * dx
                y = r * dy
                radius = min(dx, dy) * 0.5
                # Petits hexagones noirs nets
                draw.regular_polygon((x, y, radius), n_sides=6, rotation=30, fill=(30, 30, 30, 255))
                
    # Coutures fines grises entre les facettes
    for i in range(cols):
        draw.line([i * dx, 0, i * dx, size], fill=(210, 210, 210, 255), width=1)
    for i in range(rows):
        draw.line([0, i * dy, size, i * dy], fill=(210, 210, 210, 255), width=1)

    image.save(filename)
    print(f"Texture ultra-dense générée : '{filename}'")

if __name__ == "__main__":
    create_ultra_dense_ballon()