#!/usr/bin/env python3
from PIL import Image, ImageDraw

def generer_texture_filet(filename="filet.png", size=256):
    # Création d'une image transparente (Alpha = 0)
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    couleur_filet = (240, 240, 240, 255) # Blanc cassé pour les cordes
    epaisseur_maille = 4
    
    # Dessin des bordures de la tuile de texture
    draw.rectangle([0, 0, size, size], outline=couleur_filet, width=epaisseur_maille)
    
    # Dessin des mailles intérieures croisées (Grille de 4x4)
    pas = size // 4
    for i in range(1, 4):
        coordonnee = i * pas
        # Lignes verticales
        draw.line([coordonnee, 0, coordonnee, size], fill=couleur_filet, width=epaisseur_maille)
        # Lignes horizontales
        draw.line([0, coordonnee, size, coordonnee], fill=couleur_filet, width=epaisseur_maille)
        
    image.save(filename)
    print(f"Texture de filet transparent générée : '{filename}'")

if __name__ == "__main__":
    generer_texture_filet()