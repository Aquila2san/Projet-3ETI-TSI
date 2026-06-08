#version 330 core

// Variable d'entrée, ici la position
layout (location = 0) in vec3 position;
uniform vec4 translation;
uniform mat4 rotation;
uniform mat4 projection;
out vec3 coordonnee_3d;

//Un Vertex Shader minimaliste
void main (void)
{
  //Coordonnees du sommet
  coordonnee_3d = position;
  vec4 p = rotation * vec4(position,1.0) + translation;
  gl_Position = projection * p;
}
