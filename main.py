#!/usr/bin/env python3

import OpenGL.GL as GL
import glfw
import numpy as np
import os
import pyrr
from ctypes import *
from PIL import Image

class Game(object):
    """ fenêtre GLFW avec openGL """

    def __init__(self):
        self.window = self.init_window()
        self.init_context()
        self.init_programs()
        self.init_data()
        
        # Etat possible
        self.game_state = "VISER"
        
        # Position intiale du ballon
        self.initial_ball_pos = np.array([0.0, -0.2, -5.0], dtype=np.float32)
        self.pos = np.copy(self.initial_ball_pos)
        self.radius = 1.0
        
        # Variables de visée (Oscillation de l'angle)
        self.aim_angle_Y = 0.0      # Angle actuel de la flèche de visée
        self.aim_speed = 2.0        # Vitesse d'oscillation de la visée
        self.angle_Y = 0.0          # Angle final verrouillé pour la rotation du ballon
        
        # Physique du ballon
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32) # Vitesse initiale
        self.gravity = np.array([0.0, -9.81, 0.0], dtype=np.float32) # Accélération g = (0, -9.81, 0)
        self.shot_force = 12.0      # Puissance de propulsion du ballon
        


    def init_window(self):
        # initialisation de la librairie glfw et du context opengl associé
        glfw.init()
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        # création et parametrage de la fenêtre
        glfw.window_hint(glfw.RESIZABLE, False)
        window = glfw.create_window(800, 800, 'OpenGL', None, None)
        # parametrage de la fonction de gestion des évènements
        glfw.set_key_callback(window, self.key_callback)
        return window

    def init_context(self):
        # activation du context OpenGL pour la fenêtre
        glfw.make_context_current(self.window)
        glfw.swap_interval(1)
        # activation de la gestion de la profondeur
        GL.glEnable(GL.GL_DEPTH_TEST)
        
    def compile_shader(shader_content, shader_type): 
        # compilation d'un shader donn´e selon son type 
        shader_id = GL.glCreateShader(shader_type) 
        GL.glShaderSource(shader_id, shader_content) 
        GL.glCompileShader(shader_id) 
        success = GL.glGetShaderiv(shader_id, GL.GL_COMPILE_STATUS) 
        if not success: 
            log = GL.glGetShaderInfoLog(shader_id).decode('ascii') 
            print(f'{25*"-"}\nError compiling shader: \n\
                {shader_content}\n{5*"-"}\n{log}\n{25*"-"}') 
        return shader_id 
    
    def create_program(vertex_source, fragment_source): 
        # cr´eation d'un programme GPU 
        vs_id = Game.compile_shader(vertex_source, GL.GL_VERTEX_SHADER)
        fs_id = Game.compile_shader(fragment_source, GL.GL_FRAGMENT_SHADER) 
        if vs_id and fs_id: 
            program_id = GL.glCreateProgram() 
            GL.glAttachShader(program_id, vs_id) 
            GL.glAttachShader(program_id, fs_id) 
            GL.glLinkProgram(program_id) 
            success = GL.glGetProgramiv(program_id, GL.GL_LINK_STATUS) 
            if not success: 
                log = GL.glGetProgramInfoLog(program_id).decode('ascii') 
                print(f'{25*"-"}\nError linking program:\n{log}\n{25*"-"}') 
                GL.glDeleteShader(vs_id) 
                GL.glDeleteShader(fs_id) 
            return program_id 
    
    def create_program_from_file(vs_file, fs_file): 
        # cr´eation d'un programme GPU `a partir de fichiers 
        vs_content = open(vs_file, 'r').read() if os.path.exists(vs_file)\
            else print(f'{25*"-"}\nError reading file:\n{vs_file}\n{25*"-"}') 
        fs_content = open(fs_file, 'r').read() if os.path.exists(fs_file)\
            else print(f'{25*"-"}\nError reading file:\n{fs_file}\n{25*"-"}') 
        return Game.create_program(vs_content, fs_content)

    def init_programs(self):
        program = Game.create_program_from_file('phong.vert', 'phong.frag')
        GL.glUseProgram(program)
        
    def init_data(self):
        from ctypes import sizeof, c_float, c_void_p

        stride = 11 * sizeof(c_float)

        # --- Cage de foot ---
        # Format: [x, y, z, nx, ny, nz, r, g, b, u, v]
        sommets_cage = np.array([
            -1.5, 0.0, 0.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  0.0, 0.0,  # Sommet 0 : Bas Gauche
            -1.5, 1.0, 0.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  0.0, 1.0,  # Sommet 1 : Haut Gauche
            1.5, 0.0, 0.0,   0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  1.0, 0.0,  # Sommet 2 : Bas Droite
            1.5, 1.0, 0.0,   0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  1.0, 1.0   # Sommet 3 : Haut Droite
        ], dtype=np.float32)
        # Indices pour former les deux triangles du rectangle
        index_cage = np.array([0, 1, 2,  1, 2, 3], dtype=np.uint32)
        self.nb_indices_cage = index_cage.size

        self.vao_cage = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao_cage)
        vbo_cage = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_cage)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sommets_cage, GL.GL_STATIC_DRAW)
        vboi_cage = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, vboi_cage)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, index_cage, GL.GL_STATIC_DRAW)
        
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(0))
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(3 * sizeof(c_float)))
        GL.glEnableVertexAttribArray(2)
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(6 * sizeof(c_float)))
        GL.glEnableVertexAttribArray(3)
        GL.glVertexAttribPointer(3, 2, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(9 * sizeof(c_float)))

        # --- Variables d'état ---
        self.angle_y = 0.0
        self.angle_x = 0.0
        self.trans_x = 0.0
        self.trans_y = 0.0
        self.trans_z = -5.0 # Reculé un peu plus pour voir toute la hauteur (3.0)

        # 1. Maillage du ballon
        donnees_sphere = Game.generate_sphere(radius=1.0, lat_segments=16, lon_segments=32)
        sommets_sphere = donnees_sphere['interlaced']
        index_sphere = donnees_sphere['faces']
        self.nb_indices_ballon = index_sphere.size

        self.vao_ballon = GL.glGenVertexArrays(1) 
        GL.glBindVertexArray(self.vao_ballon) 
        vbo_sphere = GL.glGenBuffers(1) 
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_sphere)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sommets_sphere, GL.GL_STATIC_DRAW)
        
        GL.glEnableVertexAttribArray(0) 
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, None)
        GL.glEnableVertexAttribArray(1) 
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(3 * sizeof(c_float)))
        GL.glEnableVertexAttribArray(2) 
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(6 * sizeof(c_float)))
        GL.glEnableVertexAttribArray(3) 
        GL.glVertexAttribPointer(3, 2, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(9 * sizeof(c_float)))

        vboi_sphere = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, vboi_sphere)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, index_sphere, GL.GL_STATIC_DRAW)

        # Maillage de la flèche
        donnees_fleche = Game.generate_arrow_mesh()
        sommets_fleche = donnees_fleche['interlaced']
        index_fleche = donnees_fleche['faces']
        self.nb_indices_fleche = index_fleche.size

        self.vao_fleche = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao_fleche)
        vbo_fleche = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_fleche)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sommets_fleche, GL.GL_STATIC_DRAW)

        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, None)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(3 * sizeof(c_float)))
        GL.glEnableVertexAttribArray(2)
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(6 * sizeof(c_float)))
        GL.glEnableVertexAttribArray(3)
        GL.glVertexAttribPointer(3, 2, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(9 * sizeof(c_float)))

        vboi_fleche = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, vboi_fleche)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, index_fleche, GL.GL_STATIC_DRAW)

        # Chargement des textures
        self.texture_id1 = Game.load_texture('texture.png')
        self.texture_id2 = Game.load_texture('texture2.png')

    def load_texture(filename):
        if not os.path.exists(filename):
            print(f'{25*"-"}\nError reading file:\n{filename}\n{25*"-"}')
            return 0
        im = Image.open(filename).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGBA')
        texture_id = GL.glGenTextures(1)
        # s´election de la texture courante `a partir de son identifiant
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)
        # param´etrisation de la texture
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, im.width, im.height, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, im.tobytes())
        return texture_id

    def generate_sphere(radius=1.0, lat_segments=16, lon_segments=32):
        vertices = []
        indices = []
        
        for i in range(lat_segments + 1):
            theta = np.pi * i / lat_segments
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)
            
            for j in range(lon_segments + 1):
                phi = 2 * np.pi * j / lon_segments
                sin_phi = np.sin(phi)
                cos_phi = np.cos(phi)
                
                # Position (x, y, z)
                x = radius * sin_theta * cos_phi
                y = radius * cos_theta
                z = radius * sin_theta * sin_phi
                
                # Normale
                nx = sin_theta * cos_phi
                ny = cos_theta
                nz = sin_theta * sin_phi
                
                # Coordonnées de texture (u, v)
                u = j / lon_segments
                v = i / lat_segments
                
                # Couleur blanche par défaut (r, g, b)
                r, g, b = 1.0, 1.0, 1.0
                
                # Sommet entrelacé complet
                vertex = [x, y, z, nx, ny, nz, r, g, b, u, v]
                vertices.append(vertex)
                
        for i in range(lat_segments):
            for j in range(lon_segments):
                a = i * (lon_segments + 1) + j
                b = a + lon_segments + 1
                
                indices.append((a, b, a + 1))
                indices.append((a + 1, b, b + 1))
                
        return {
            'interlaced': np.array(vertices, dtype=np.float32),
            'faces': np.array(indices, dtype=np.uint32) # Forcé en uint32 pour correspondre à notre pipeline
        }

    def generate_arrow_mesh():
        """ Construit un maillage 3D propre de flèche plane horizontale (Corps + Pointe) """
        # Format d'un sommet: [x, y, z, nx, ny, nz, r, g, b, u, v]
        # Normale orientée vers le haut constant (0, 1, 0)
        vertices = [
            # Corps de la flèche (Rectangle de Z=-0.5 à Z=-2.5)
            [-0.2, -1.15, -0.5,  0.0, 1.0, 0.0,  1.0, 0.5, 0.0,  0.0, 0.0], # 0 : Base Arrière Gauche
            [ 0.2, -1.15, -0.5,  0.0, 1.0, 0.0,  1.0, 0.5, 0.0,  1.0, 0.0], # 1 : Base Arrière Droite
            [ 0.2, -1.15, -2.5,  0.0, 1.0, 0.0,  1.0, 0.5, 0.0,  1.0, 0.8], # 2 : Jonction Devant Droite
            [-0.2, -1.15, -2.5,  0.0, 1.0, 0.0,  1.0, 0.5, 0.0,  0.0, 0.8], # 3 : Jonction Devant Gauche
            
            # Pointe de la flèche (Triangle de Z=-2.5 à Z=-4.0)
            [-0.6, -1.15, -2.5,  0.0, 1.0, 0.0,  1.0, 0.2, 0.0,  0.0, 0.8], # 4 : Aile Gauche
            [ 0.6, -1.15, -2.5,  0.0, 1.0, 0.0,  1.0, 0.2, 0.0,  1.0, 0.8], # 5 : Aile Droite
            [ 0.0, -1.15, -4.0,  0.0, 1.0, 0.0,  1.0, 0.0, 0.0,  0.5, 1.0]  # 6 : Pointe Extrême
        ]
        indices = [
            0, 1, 2,  0, 2, 3,  # Triangles du corps
            4, 5, 6             # Triangle de la pointe
        ]
        return {'interlaced': np.array(vertices, dtype=np.float32), 'faces': np.array(indices, dtype=np.uint32)}

    def run(self):
        last_time = glfw.get_time()
        # boucle d'affichage
        while not glfw.window_should_close(self.window):
            current_time = glfw.get_time()
            dt = current_time - last_time
            last_time = current_time
            dt = min(dt, 0.1)
            GL.glClearColor(0.2, 0.5, 0.2, 1.0) # Fond vert terrain
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            
            prog = GL.glGetIntegerv(GL.GL_CURRENT_PROGRAM) 
            loc_model = GL.glGetUniformLocation(prog, "model")
            loc_view = GL.glGetUniformLocation(prog, "view")
            loc_proj = GL.glGetUniformLocation(prog, "projection")
            
            # Etat VISER ou TIR
            if self.game_state == "VISER":
                # Oscillation automatique de la flèche entre -45° et +45° devant le ballon
                self.aim_angle_Y = np.sin(current_time * self.aim_speed) * (np.pi / 4.0)
                self.pos = np.copy(self.initial_ball_pos)
                self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                
            elif self.game_state == "TIR":
                # Application de la gravité et mise à jour physique (Schéma d'Euler)
                self.velocity += self.gravity * dt
                self.pos += self.velocity * dt
                
                # Gestion de collision avec le sol
                sol_y = -1.2
                if self.pos[1] - self.radius <= sol_y:
                    self.pos[1] = sol_y + self.radius
                    self.velocity[1] = -self.velocity[1] * 0.5 # Rebond 
                    self.velocity[0] *= 0.98                   # Friction au sol
                    self.velocity[2] *= 0.98
            
            # Configuration de la caméra
            camera_pos = np.array([0.0, 6.0, 0.0], dtype=np.float32)
            target_look = np.array([0.0, -1.0, -12.0], dtype=np.float32)
            view_matrix = pyrr.matrix44.create_look_at(camera_pos, target_look, np.array([0.0, 1.0, 0.0], dtype=np.float32))
            proj_matrix = pyrr.matrix44.create_perspective_projection_matrix(45.0, 1.0, 0.5, 60.0)
            
            GL.glUniformMatrix4fv(loc_proj, 1, GL.GL_FALSE, proj_matrix)
            GL.glUniformMatrix4fv(loc_view, 1, GL.GL_FALSE, view_matrix)
            
            # Affichage du ballon
            GL.glBindVertexArray(self.vao_ballon)
            model_ballon = pyrr.matrix44.create_from_translation(self.pos) # Aucune rotation liée à la visée
            
            GL.glUniformMatrix4fv(loc_model, 1, GL.GL_FALSE, model_ballon)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id1)
            GL.glDrawElements(GL.GL_TRIANGLES, self.nb_indices_ballon, GL.GL_UNSIGNED_INT, None)
          
            # Affichage de la cage
            GL.glBindVertexArray(self.vao_cage)
            
            # 1. On translate la cage au fond du terrain (Z = -12.0)
            # Et on la pose sur le sol (Y = -1.2 pour correspondre à votre sol_y)
            pos_cage = np.array([0.0, -1.2, -12.0], dtype=np.float32)
            model_cage = pyrr.matrix44.create_from_translation(pos_cage)
            
            GL.glUniformMatrix4fv(loc_model, 1, GL.GL_FALSE, model_cage)
            
            # 2. On lie une texture ! (Mettez texture_id1 ou chargez une texture de filet)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id1)
            
            # 3. On dessine (avec c_void_p(0) pour éviter les bugs liés à None)
            from ctypes import c_void_p
            GL.glDrawElements(GL.GL_TRIANGLES, self.nb_indices_cage, GL.GL_UNSIGNED_INT, c_void_p(0))
            # Affichage de la flèche
            if self.game_state == "VISER":
                GL.glBindVertexArray(self.vao_fleche)
                
                rot_arrow = pyrr.matrix44.create_from_y_rotation(self.aim_angle_Y)
                # Positionnement au centre du ballon d'origine
                trans_ball_origin = pyrr.matrix44.create_from_translation(self.pos)
                
                # Multiplication : Pivote à l'origine locale puis se positionne au ballon
                model_arrow = pyrr.matrix44.multiply(rot_arrow, trans_ball_origin)
                
                GL.glUniformMatrix4fv(loc_model, 1, GL.GL_FALSE, model_arrow)
                GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id2) 
                GL.glDrawElements(GL.GL_TRIANGLES, self.nb_indices_fleche, GL.GL_UNSIGNED_INT, None)
            
            glfw.swap_buffers(self.window)
            glfw.poll_events()
            
                
                
             
    
    def key_callback(self, win, key, scancode, action, mods):
        # sortie du programme si appui sur la touche 'echap'
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(win, glfw.TRUE)
        # Appui sur ESPACE : Verrouille la cible et déclenche le tir
        if key == glfw.KEY_SPACE and action == glfw.PRESS:
            if self.game_state == "VISER":
                self.game_state = "TIR"
                self.angle_Y = self.aim_angle_Y # Sauvegarde de l'angle précis au moment du clic
                
                # Calcul du vecteur de direction
                dir_x = np.sin(self.angle_Y)
                dir_z = -np.cos(self.angle_Y)
                dir_y = 0.6  # Donne une impulsion vers le haut pour créer une trajectoire en cloche (lob)
                
                launch_vector = np.array([dir_x, dir_y, dir_z], dtype=np.float32)
                # Normalisation du vecteur pour appliquer une force constante
                launch_vector = launch_vector / np.linalg.norm(launch_vector)
                
                # Application de la vitesse initiale
                self.velocity = launch_vector * self.shot_force
                
            elif self.game_state == "TIR":
                # Si le ballon est déjà lancé, un nouvel appui sur Espace réinitialise le tir pour rejouer
                self.game_state = "VISER"

def main():
    g = Game()
    g.run()
    glfw.terminate()

if __name__ == '__main__':
    main()