# 3D Penalty Shootout Simulation & Graphics Engine

A real-time 3D Penalty Shootout simulation built with Python and PyOpenGL, developed as part of the Computer Graphics curriculum at CPE Lyon. The project demonstrates a programmable graphics pipeline, custom shader implementations, and kinematic collision physics.

![Gameplay Screenshot](image.png)

## Overview

The engine renders an interactive 3D Penalty Shootout scene maintaining a steady 60 FPS. It features realistic ball dynamics (gravity, projectile trajectories), physical rebounds on ground boundaries and net structures, as well as a decoupled user-controlled camera.

## Key Technical Features

- **Programmable Graphics Pipeline:** Implemented using PyOpenGL and modern OpenGL conventions (VAO, VBO, shaders).
- **Custom GLSL Shaders:** Vertex and fragment shaders executing the **Phong illumination model** (ambient, diffuse, and specular components) alongside 2D texture mapping.
- **Real-Time Physics Engine:**
  - Parabolic projectile motion with continuous gravity integration.
  - Sphere-plane collision detection and impulse response for the court floor and bounds.
  - Sphere-box collision detection for the volleyball net with momentum damping and restitution coefficients.
- **Decoupled Game Loop:** Separation of input polling, matrix transformations (Model-View-Projection), physics calculations, and rendering passes to avoid frame drops.
- **Interactive Camera:** Configurable camera controls supporting both free and orbit view modes.

## Project Structure

```text
├── main.py              # Main execution loop, event handling & scene setup
├── ballon.py            # Ball physics, trajectory integration & collision logic
├── terrain.py           # Court geometry, vertex buffers & texture mapping
├── filet.py             # Net geometry and bounding collision volumes
├── phong.vert           # GLSL Vertex Shader (transforms, normals, UVs)
├── phong.frag           # GLSL Fragment Shader (Phong lighting computation)
├── shader.vert/frag     # Basic fallback shaders
├── textures/            # Textures (ball, court, net)
└── RAPPORT.md           # Technical project report
