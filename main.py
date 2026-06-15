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
        # Etat possible
        self.game_state = "VISER"
        
        # Position intiale du ballon
        self.radius = 0.4
        self.initial_ball_pos = np.array([0.0, -1.2 + self.radius, -9.0], dtype=np.float32)
        self.pos = np.copy(self.initial_ball_pos)
        
        # Variables de visée (Oscillation de l'angle)
        self.aim_angle_Y = 0.0      # Angle actuel de la flèche de visée
        self.aim_speed = 2.5        # Vitesse d'oscillation de la visée
        self.angle_Y = 0.0          # Angle final verrouillé pour la rotation du ballon
        
        # Physique du ballon
        self.current_shot_force = 0.0
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32) # Vitesse initiale
        self.gravity = np.array([0.0, -9.81, 0.0], dtype=np.float32) # Accélération g = (0, -9.81, 0)
        
        # Variables d'état de translation/rotation de la scène
        self.angle_y = 0.0
        self.angle_y = 0.0
        self.angle_x = 0.0
        self.trans_x = 0.0
        self.trans_y = 0.0
        self.trans_z = -5.0
        
        # Appel des fonctions OpenGL qui dépendent de ces variables
        self.window = self.init_window()
        self.init_context()
        self.init_programs()
        self.init_data() 
        

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
        # activation de la transparence
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
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

        # --- Cage de foot : Poteaux Blancs + Filet Transparent ---
        # Format: [x, y, z, nx, ny, nz, r, g, b, u, v]
        sommets_cage = np.array([
            # --- POTEAU GAUCHE (Blanc opaque, pas de texture) ---
            -7.32, 0.00, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 0 : Bas Gauche
            -7.32, 4.88, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 1 : Haut Gauche
            -7.02, 4.88, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 2 : Haut Droit
            -7.02, 0.00, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 3 : Bas Droit

            # --- POTEAU DROIT (Blanc opaque, pas de texture) ---
             7.02, 0.00, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 4 : Bas Gauche
             7.02, 4.88, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 5 : Haut Gauche
             7.32, 4.88, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 6 : Haut Droit
             7.32, 0.00, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 7 : Bas Droite

            # --- BARRE TRANSVERSALE (Blanc opaque, pas de texture) ---
            -7.02, 4.58, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 8 : Bas Gauche
            -7.02, 4.88, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 9 : Haut Gauche
             7.02, 4.88, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 10: Haut Droit
             7.02, 4.58, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 11: Bas Droit

            # --- LE FILET CENTRAL (Texturé avec filet.png) ---
            -7.02, 0.00, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,0.0, # 12: Bas Gauche
            -7.02, 4.58, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  0.0,3.0, # 13: Haut Gauche
             7.02, 0.00, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  8.0,0.0, # 14: Bas Droit
             7.02, 4.58, 0.0,  0.0,0.0,1.0,  1.0,1.0,1.0,  8.0,3.0  # 15: Haut Droit
        ], dtype=np.float32)

        # Triangles : 2 pour le poteau G, 2 pour le poteau D, 2 pour la barre, 2 pour le filet
        index_cage = np.array([
            0, 1, 2,   0, 2, 3,     # Poteau Gauche
            4, 5, 6,   4, 6, 7,     # Poteau Droit
            8, 9, 10,  8, 10, 11,   # Barre transversale
            12, 13, 15, 12, 15, 14  # Filet central
        ], dtype=np.uint32)
        
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


        # Maillage du ballon
        donnees_sphere = Game.generate_sphere(radius=self.radius,lat_segments=16, lon_segments=32)
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

        # Maillage du sol
        donnees_sol = Game.generate_floor_mesh()
        sommets_sol = donnees_sol['interlaced']
        index_sol = donnees_sol['faces']
        self.nb_indices_sol = index_sol.size

        self.vao_sol = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao_sol)
        vbo_sol = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_sol)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sommets_sol, GL.GL_STATIC_DRAW)

        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, None)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(3 * sizeof(c_float)))
        GL.glEnableVertexAttribArray(2)
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(6 * sizeof(c_float)))
        GL.glEnableVertexAttribArray(3)
        GL.glVertexAttribPointer(3, 2, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(9 * sizeof(c_float)))

        vboi_sol = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, vboi_sol)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, index_sol, GL.GL_STATIC_DRAW)

        # Le triangle noir (Fond fixe sur la droite de l'écran)
        sommets_jauge_noire = np.array([
            # X, Y, Z,        Nx, Ny, Nz,   R, G, B,     U, V
            0.80, -0.6, 0.0,  0.0,0.0,1.0,  0.0,0.0,0.0, 0.0,0.0, # Bas gauche
            0.95, -0.6, 0.0,  0.0,0.0,1.0,  0.0,0.0,0.0, 0.0,0.0, # Bas droite
            0.875, 0.6, 0.0,  0.0,0.0,1.0,  0.0,0.0,0.0, 0.0,0.0  # Haut centre
        ], dtype=np.float32)

        # Le triangle rouge (Construit autour de l'origine locale pour pouvoir l'étirer vers le haut)
        sommets_jauge_rouge = np.array([
            -0.06,  0.00, 0.0,  0.0,0.0,1.0,  1.0,0.0,0.0, 0.0,0.0, # Bas gauche
             0.06,  0.00, 0.0,  0.0,0.0,1.0,  1.0,0.0,0.0, 0.0,0.0, # Bas droite
             0.00,  1.16, 0.0,  0.0,0.0,1.0,  1.0,0.0,0.0, 0.0,0.0  # Haut centre
        ], dtype=np.float32)

        # Création du VAO Noir
        self.vao_jauge_noire = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao_jauge_noire)
        vbo_noir = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_noir)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sommets_jauge_noire, GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(0))
        GL.glEnableVertexAttribArray(2) # Pointeur de couleur
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(6 * sizeof(c_float)))

        # Création du VAO Rouge
        self.vao_jauge_rouge = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao_jauge_rouge)
        vbo_rouge = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_rouge)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sommets_jauge_rouge, GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(0))
        GL.glEnableVertexAttribArray(2) # Pointeur de couleur
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, stride, c_void_p(6 * sizeof(c_float)))

        # Variable de puissance
        self.power = 0.0

        # Chargement des textures
        self.texture_id1 = Game.load_texture('ballon_texture.png')  # Ballon
        self.texture_id2 = Game.load_texture('texture2.png') # Flèche
        self.texture_id3 = Game.load_texture('terrain.png')  # Pelouse / Lignes du terrain
        self.texture_id4 = Game.load_texture('filet.png')    # Filet

        self.texture_blanche = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_blanche)
        # b'\xff\xff\xff\xff' crée un pixel BLANC et opaque (A=255)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 1, 1, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, b'\xff\xff\xff\xff')
        
        self.texture_noire = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_noire)
        # b'\x00\x00\x00\xff' crée un pixel Noir et opaque (A=255)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 1, 1, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, b'\x00\x00\x00\xff')

    def load_texture(filename):
        if not os.path.exists(filename):
            print(f'{25*"-"}\nError reading file:\n{filename}\n{25*"-"}')
            return 0
        im = Image.open(filename).transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGBA')
        texture_id = GL.glGenTextures(1)
        # sélection de la texture courante à partir de son identifiant
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)
        # paramétrisation de la texture
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, im.width, im.height, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, im.tobytes())
        return texture_id

    def generate_sphere(radius=1, lat_segments=16, lon_segments=32):
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
        """ Maillage de flèche horizontale ajusté pour le ballon de rayon 0.4 """
        vertices = [
            [-0.1, -0.38, -0.6,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  0.0, 0.0], 
            [ 0.1, -0.38, -0.6,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  1.0, 0.0], 
            [ 0.1, -0.38, -2.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  1.0, 0.8], 
            [-0.1, -0.38, -2.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  0.0, 0.8], 
            
            [-0.3, -0.38, -2.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  0.0, 0.8], 
            [ 0.3, -0.38, -2.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  1.0, 0.8], 
            [ 0.0, -0.38, -3.2,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  0.5, 1.0]  
        ]
        indices = [0, 1, 2,  0, 2, 3,  4, 5, 6]
        return {'interlaced': np.array(vertices, dtype=np.float32), 'faces': np.array(indices, dtype=np.uint32)}
    
    def generate_floor_mesh():
        """ Grand plan horizontal à Y = -1.2 pour accueillir le terrain """
        # Couvre une large zone pour le fond du décor (X de -20 à 20, Z de +5 à -35)
        vertices = [
            [-25.0, -1.2,   5.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  0.0, 0.0],
            [ 25.0, -1.2,   5.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  1.0, 0.0],
            [ 25.0, -1.2, -35.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  1.0, 1.0],
            [-25.0, -1.2, -35.0,  0.0, 1.0, 0.0,  1.0, 1.0, 1.0,  0.0, 1.0]
        ]
        indices = [0, 1, 2,  0, 2, 3]
        return {'interlaced': np.array(vertices, dtype=np.float32), 'faces': np.array(indices, dtype=np.uint32)}

    def run(self):
        last_time = glfw.get_time()
        # boucle d'affichage
        while not glfw.window_should_close(self.window):
            current_time = glfw.get_time()
            dt = current_time - last_time
            last_time = current_time
            dt = min(dt, 0.1)
            # --- GESTION DE LA COULEUR DE FOND ---
            if self.game_state == "BUT":
                # Effet clignotant pendant le but !
                # On utilise des sinus avec des vitesses différentes pour mélanger les couleurs RGB
                r = (np.sin(current_time * 15.0) + 1.0) / 2.0
                g = (np.sin(current_time * 20.0 + 2.0) + 1.0) / 2.0
                b = (np.sin(current_time * 25.0 + 4.0) + 1.0) / 2.0
                GL.glClearColor(r, g, b, 1.0)
            else:
                # Ciel bleu normal pour le reste du jeu
                GL.glClearColor(0.5, 0.7, 1.0, 1.0)
                
            # Nettoyage de l'écran avec la couleur choisie ci-dessus
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

                # --- COLLISION AVEC LE BUT ---
                # On définit la zone du but (basé sur les coordonnées de la cage)
                cage_z = -32.9
                cage_x_min = -7.32
                cage_x_max = 7.32
                cage_y_min = -1.2
                cage_y_max = -1.2 + 4.88 # = 3.68

                # On utilise self.pos[2] - self.radius pour vérifier si le bord du ballon franchit la ligne
                if self.pos[2] - self.radius <= cage_z:
                    
                    # On vérifie si il est dans le cadre 
                    if (cage_x_min <= self.pos[0] <= cage_x_max) and (cage_y_min <= self.pos[1] <= cage_y_max):
                        print("\n=====================")
                        print("     BUUUUUUT !!!    ")
                        print("=====================\n")
                        
                        # On change l'état pour arrêter la physique
                        self.game_state = "BUT"
                        self.chrono_but = current_time # On mémorise l'heure du but
                    else:
                        # Si on dépasse Z mais qu'on n'est pas dans le cadre, c'est raté
                        print("Sortie de but...")
                        self.game_state = "VISER"
           
            elif self.game_state == "BUT":
                # Le ballon est figé dans le but. On attend 2 secondes.
                if current_time - self.chrono_but > 2.0:
                    # Après 2 secondes, on réinitialise pour le prochain tir
                    self.game_state = "VISER"
                   
                    
            # Configuration de la caméra
            camera_pos = np.array([0.0, 5.5, 1.0], dtype=np.float32)
            target_look = np.array([0.0, -0.2, -22.0], dtype=np.float32)
            view_matrix = pyrr.matrix44.create_look_at(camera_pos, target_look, np.array([0.0, 1.0, 0.0], dtype=np.float32))
            proj_matrix = pyrr.matrix44.create_perspective_projection_matrix(45.0, 1.0, 0.5, 100.0)
            
            GL.glUniformMatrix4fv(loc_proj, 1, GL.GL_FALSE, proj_matrix)
            GL.glUniformMatrix4fv(loc_view, 1, GL.GL_FALSE, view_matrix)
            
            # On s'assure que le Blending est DÉSACTIVÉ pour les objets opaques
            GL.glDisable(GL.GL_BLEND)

            # Rendu du terrain
            GL.glBindVertexArray(self.vao_sol)
            model_sol = pyrr.matrix44.create_from_translation(np.array([0.0, 0.0, 0.0], dtype=np.float32))
            GL.glUniformMatrix4fv(loc_model, 1, GL.GL_FALSE, model_sol)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id3)
            GL.glDrawElements(GL.GL_TRIANGLES, self.nb_indices_sol, GL.GL_UNSIGNED_INT, None)
            
            # Rendu du ballon (Rotation dynamique selon la direction)
            GL.glBindVertexArray(self.vao_ballon)
            
            if self.game_state == "TIR":
                # On récupère la direction horizontale du déplacement (axes X et Z)
                dir_x = self.velocity[0]
                dir_z = self.velocity[2]
                norme_horizontale = np.sqrt(dir_x**2 + dir_z**2)
                
                if norme_horizontale > 0.001:
                    # Calcul de l'axe perpendiculaire au déplacement (Produit vectoriel)
                    # Si le ballon va vers l'avant (-Z), l'axe sera l'axe X (1, 0, 0)
                    axe = np.cross(np.array([dir_x, 0.0, dir_z]), np.array([0.0, 1.0, 0.0]))
                    # Normalisation de l'axe
                    if np.linalg.norm(axe) > 0.001:
                        axe = axe / np.linalg.norm(axe)
                    
                    # Plus le ballon va vite, plus il tourne vite sur lui-même
                    angle_rotation = current_time * (self.current_shot_force * 0.5)
                    
                    # Création de la matrice de rotation autour de cet axe
                    rot_ballon = pyrr.matrix44.create_from_axis_rotation(axe, angle_rotation)
                else:
                    rot_ballon = pyrr.matrix44.create_identity(dtype=np.float32)
            else:
                # Au repos (phase VISER ou CHARGER), le ballon ne tourne pas
                rot_ballon = pyrr.matrix44.create_identity(dtype=np.float32)
            trans_ballon = pyrr.matrix44.create_from_translation(self.pos)
            model_ballon = pyrr.matrix44.multiply(rot_ballon, trans_ballon)
            
            GL.glUniformMatrix4fv(loc_model, 1, GL.GL_FALSE, model_ballon)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id1)
            GL.glDrawElements(GL.GL_TRIANGLES, self.nb_indices_ballon, GL.GL_UNSIGNED_INT, None)
            
            # Rendu de la flèche
            if self.game_state == "VISER":
                GL.glBindVertexArray(self.vao_fleche)
                rot_arrow = pyrr.matrix44.create_from_y_rotation(self.aim_angle_Y)
                trans_ball_origin = pyrr.matrix44.create_from_translation(self.pos)
                model_arrow = pyrr.matrix44.multiply(rot_arrow, trans_ball_origin)
                
                GL.glUniformMatrix4fv(loc_model, 1, GL.GL_FALSE, model_arrow)
                GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_noire) 
                GL.glDrawElements(GL.GL_TRIANGLES, self.nb_indices_fleche, GL.GL_UNSIGNED_INT, None)
          
            # ON ACTIVE LE BLENDING UNIQUEMENT POUR LA CAGE ET LE FILET
            GL.glEnable(GL.GL_BLEND)

            # Rendu de la cage
            GL.glBindVertexArray(self.vao_cage)
            pos_cage = np.array([0.0, -1.2, -32.7], dtype=np.float32)
            model_cage = pyrr.matrix44.create_from_translation(pos_cage)
            GL.glUniformMatrix4fv(loc_model, 1, GL.GL_FALSE, model_cage)
            
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id4)
            GL.glDrawElements(GL.GL_TRIANGLES, self.nb_indices_cage, GL.GL_UNSIGNED_INT, c_void_p(0))
            
            # On coupe le blending après la cage pour ne pas perturber le HUD
            GL.glDisable(GL.GL_BLEND)

            # Jauge HUD
            if self.game_state == "CHARGER" or True: # Modifié pour toujours laisser le fond noir visible si besoin
                GL.glDisable(GL.GL_DEPTH_TEST)
                mat_identite = pyrr.matrix44.create_identity(dtype=np.float32)
                GL.glUniformMatrix4fv(loc_proj, 1, GL.GL_FALSE, mat_identite)
                GL.glUniformMatrix4fv(loc_view, 1, GL.GL_FALSE, mat_identite)
                
                GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_blanche)
                
                GL.glBindVertexArray(self.vao_jauge_noire)
                GL.glUniformMatrix4fv(loc_model, 1, GL.GL_FALSE, mat_identite)
                GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
                
                if self.game_state == "CHARGER":
                    self.power += dt * 1.5
                    if self.power > 1.0:
                        self.power = 1.0
                    
                    GL.glBindVertexArray(self.vao_jauge_rouge)
                    trans_rouge = pyrr.matrix44.create_from_translation(np.array([0.875, -0.58, 0.0], dtype=np.float32))
                    scale_rouge = pyrr.matrix44.create_from_scale(np.array([1.0, self.power, 1.0], dtype=np.float32))
                    model_rouge = pyrr.matrix44.multiply(scale_rouge, trans_rouge)
                    
                    GL.glUniformMatrix4fv(loc_model, 1, GL.GL_FALSE, model_rouge)
                    GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
                
                GL.glEnable(GL.GL_DEPTH_TEST)

            glfw.swap_buffers(self.window)
            glfw.poll_events()
            
                
                
             
    
    def key_callback(self, win, key, scancode, action, mods):
        # Appui sur ESPACE : Verrouille la cible et commence à charger la jauge
        if key == glfw.KEY_SPACE:
            if action == glfw.PRESS and self.game_state == "VISER":
                self.game_state = "CHARGER"
                self.angle_Y = self.aim_angle_Y
                self.power = 0.0 # On réinitialise la puissance
                
            # Relâchement de ESPACE : On déclenche le tir !
            elif action == glfw.RELEASE and self.game_state == "CHARGER":
                self.game_state = "TIR"
                
                # Le tir dépend maintenant de la jauge (entre 5.0 et 25.0 de puissance par exemple)
                actual_force = 5.0 + (self.power * 25.0) 
                self.current_shot_force = actual_force
                
                dir_x = np.sin(self.angle_Y)
                dir_z = -np.cos(self.angle_Y)

                dir_y = 0.1  # Donne une impulsion vers le haut pour créer une trajectoire en cloche (lob)
                dir_y = 0.6  

                
                launch_vector = np.array([dir_x, dir_y, dir_z], dtype=np.float32)
                launch_vector = launch_vector / np.linalg.norm(launch_vector)
                
                self.velocity = launch_vector * actual_force
                
            elif action == glfw.PRESS and self.game_state == "TIR":
                self.game_state = "VISER"

def main():
    g = Game()
    g.run()
    glfw.terminate()

if __name__ == '__main__':
    main()