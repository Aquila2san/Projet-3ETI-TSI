#version 330 core

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normale;
layout (location = 2) in vec3 couleur;
layout (location = 3) in vec2 texCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 coordonnee_3d;
out vec3 coordonnee_3d_locale;
out vec3 vnormale;
out vec3 vcouleur;
out vec2 vtex;

//Un Vertex Shader minimaliste
void main (void)
{
  // Application de la matrice de modèle 4x4 unique (Rotation puis Translation intégrées)
  vec4 p = model * vec4(position, 1.0);
  coordonnee_3d_locale = p.xyz;
  
  gl_Position = projection * view * p;
  
  // Les normales ne subissent pas la translation, uniquement la rotation (W = 0.0)
  vec4 n = model * vec4(normale, 0.0);
  vnormale = n.xyz;
  
  vcouleur = couleur;
  vtex = texCoord;
}
