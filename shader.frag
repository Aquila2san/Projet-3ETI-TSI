#version 330 core

// Variable de sortie (sera utilisé comme couleur)
out vec4 color;
uniform vec4 color_trg;
in vec3 coordonnee_3d;


//Un Fragment Shader minimaliste
void main (void) 
{ 
  //float r=gl_FragCoord.x/800.0; 
  //float g=gl_FragCoord.y/800.0; 
  //color = vec4(r,g,0.0,0.0); 
  //color = color_trg;
  color = vec4(coordonnee_3d, 1.0);
}