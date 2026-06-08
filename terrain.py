from PIL import Image, ImageDraw

image = Image.new("RGBA", (1024, 1024), (34, 139, 34, 255)) # Vert pelouse
draw = ImageDraw.Draw(image)

# Ligne extérieure du terrain
draw.rectangle([100, 50, 924, 974], outline=(255,255,255), width=8)
# Surface de réparation (en haut, vers la ligne de but du fond)
draw.rectangle([162, 50, 862, 700], outline=(255,255,255), width=8)
# Surface de but
draw.rectangle([362, 50, 662, 270], outline=(255,255,255), width=8)
# Point de penalty (coordonnée Y proportionnelle à l'emplacement -9.0 du ballon)
draw.ellipse([502, 641, 522, 661], fill=(255,255,255))
# Lunette de surface
draw.arc([352, 491, 672, 811], start=180, end=0, fill=(255,255,255), width=8)
# Nettoyage de la ligne de surface
draw.line([162, 700, 862, 700], fill=(255,255,255), width=8)

image.save("terrain.png")