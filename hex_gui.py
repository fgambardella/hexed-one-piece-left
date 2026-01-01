import pygame
import random
import time
import sys
import math

# --- CONFIGURAZIONE ---
HEX_SIDE = 3
TARGET_DELAY = 50 # ms tra gli step (controlla la velocità visiva)

# Colori (RGB)
BG_COLOR = (15, 15, 20) # Scuro, moderno
GRID_COLOR = (40, 40, 50)
TEXT_COLOR = (200, 200, 200)

PIECE_COLORS_RGB = [
    (255, 107, 107), (78, 205, 196), (255, 230, 109), (26, 83, 92), 
    (247, 255, 247), (255, 50, 50), (100, 100, 255), (100, 255, 100),
    (255, 100, 255), (100, 255, 255), (255, 150, 50), (150, 50, 255),
    (50, 250, 150), (250, 50, 150), (50, 150, 250), (200, 200, 200)
]

class HexGame:
    def __init__(self):
        pygame.init()
        
        # Setup Fullscreen
        info = pygame.display.Info()
        self.width = info.current_w
        self.height = info.current_h
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Hex Solver GPU")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        
        # Logica del Solver
        self.side = HEX_SIDE
        self.grid = {}
        self.pieces = []
        self.init_hexagon_grid()
        self.generate_random_pieces()
        
        # Generator del solver
        self.solver_iter = self.solve_generator()
        self.solved = False
        self.start_time = time.time()
        self.solution_time = 0
        
        # Calcolo dimensioni grafiche
        self.calc_metrics()

    def calc_metrics(self):
        # Calcola la scala per centrare l'esagono nello schermo
        # Griglia va da 'side' verticalmente
        grid_h_units = self.side * 2  # num righe
        grid_w_units = self.side * 4 # approx larghezza
        
        # Margini
        avail_h = self.height * 0.8
        avail_w = self.width * 0.8
        
        self.tri_h = avail_h / grid_h_units
        # In un triangolo equilatero/simile, w = h * 2 / sqrt(3) per equilatero, ma qui usiamo w=base
        # Usiamo aspect ratio semplice per riempire
        self.tri_w = self.tri_h * 1.2 
        
        # Offset Centramento
        # Bounding box logico
        min_r = min(k[0] for k in self.grid)
        max_r = max(k[0] for k in self.grid)
        min_c = min(k[1] for k in self.grid)
        max_c = max(k[1] for k in self.grid)
        
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Centriamo il punto (max_r/2, max_c/2) approx
        grid_pixel_w = (max_c - min_c) * (self.tri_w / 2) 
        grid_pixel_h = (max_r - min_r) * self.tri_h
        
        self.offset_x = center_x - grid_pixel_w / 2 - (min_c * self.tri_w / 2)
        self.offset_y = center_y - grid_pixel_h / 2 - (min_r * self.tri_h)

        # Correzione offset specifica per la forma
        self.offset_x -= self.tri_w * 2

    def init_hexagon_grid(self):
        self.grid = {}
        max_width = (2 * self.side + 1) + 2 * (self.side - 1)
        for r in range(self.side * 2):
            if r < self.side:
                count = (2 * self.side + 1) + 2 * r
            else:
                dist_from_bottom = (2 * self.side - 1) - r
                count = (2 * self.side + 1) + 2 * dist_from_bottom
            offset = (max_width - count) // 2
            for k in range(count):
                c = offset + k
                self.grid[(r, c)] = None

    def get_neighbors(self, r, c):
        neighs = [(r, c-1), (r, c+1)]
        if (r + c) % 2 == 0: 
            neighs.append((r + 1, c))
        else:
            neighs.append((r - 1, c))
        return neighs

    def generate_random_pieces(self):
        # Logica identica allo script precedente...
        while True:
            for k in self.grid: self.grid[k] = None
            self.pieces = []
            coords = list(self.grid.keys())
            random.shuffle(coords)
            temp_grid = {k: None for k in coords}
            piece_id_counter = 0
            generation_failed = False
            working_coords = list(coords)
            
            while working_coords:
                start_node = working_coords.pop()
                while start_node not in temp_grid or temp_grid[start_node] is not None:
                    if not working_coords: break
                    start_node = working_coords.pop()
                if temp_grid.get(start_node) is not None: continue
    
                piece_size = random.randint(6, 9)
                new_piece_coords = [start_node]
                temp_grid[start_node] = piece_id_counter
                candidates = set()
                
                def add_candidates(r, c):
                    for n in self.get_neighbors(r, c):
                        if n in temp_grid and temp_grid[n] is None: candidates.add(n)
    
                add_candidates(*start_node)
                while len(new_piece_coords) < piece_size and candidates:
                    next_node = random.choice(list(candidates))
                    candidates.remove(next_node)
                    if temp_grid[next_node] is None:
                        temp_grid[next_node] = piece_id_counter
                        new_piece_coords.append(next_node)
                        add_candidates(*next_node)
                        if next_node in working_coords: working_coords.remove(next_node)
                
                if len(new_piece_coords) < 3:
                     generation_failed = True; break

                if new_piece_coords:
                    ref_r, ref_c = min(new_piece_coords)
                    normalized = [(r-ref_r, c-ref_c) for r, c in new_piece_coords]
                    color = PIECE_COLORS_RGB[piece_id_counter % len(PIECE_COLORS_RGB)]
                    self.pieces.append({'id': piece_id_counter, 'shape': normalized, 'color': color, 'placed': False})
                    piece_id_counter += 1
            
            if not generation_failed: break
        
        for k in self.grid: self.grid[k] = None

    def can_place(self, shapes, r, c):
        for dr, dc in shapes:
            nr, nc = r + dr, c + dc
            if (nr, nc) not in self.grid or self.grid[(nr, nc)] is not None: return False
        return True

    def place_piece(self, piece, r, c, remove=False):
        for dr, dc in piece['shape']:
            self.grid[(r+dr, c+dc)] = None if remove else piece['id']
        piece['placed'] = not remove

    def solve_generator(self):
        """ Generatore coroutine per il backtracking """
        # Trova cella vuota
        empty_spot = None
        # Sorting stabile per determinismo
        sorted_cells = sorted(self.grid.keys())
        for cell in sorted_cells:
            if self.grid[cell] is None:
                empty_spot = cell
                break
        
        if empty_spot is None:
            yield True # Solved
            return

        r, c = empty_spot

        for piece in self.pieces:
            if not piece['placed']:
                if self.can_place(piece['shape'], r, c):
                    self.place_piece(piece, r, c)
                    yield False # Step fatto, continua
                    
                    # Recursion via 'yield from'
                    yield from self.solve_generator()
                    
                    if self.is_solved(): # Helper check
                        return 
                    
                    self.place_piece(piece, r, c, remove=True)
                    yield False # Backtrack step

    def is_solved(self):
        return all(v is not None for v in self.grid.values())

    def get_triangle_points(self, r, c):
        half_w = self.tri_w / 2
        x_base = self.offset_x + c * half_w
        y_top = self.offset_y + r * self.tri_h
        y_bot = self.offset_y + (r + 1) * self.tri_h
        
        if (r + c) % 2 == 0: # Punta SU
            p1 = (x_base + half_w, y_top)      # Top
            p2 = (x_base, y_bot)               # Bot Left
            p3 = (x_base + self.tri_w, y_bot)  # Bot Right
        else: # Punta GIÙ
            p1 = (x_base, y_top)               # Top Left
            p2 = (x_base + self.tri_w, y_top)  # Top Right
            p3 = (x_base + half_w, y_bot)      # Bot
        return [p1, p2, p3]

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Disegna celle
        for (r, c), pid in self.grid.items():
            points = self.get_triangle_points(r, c)
            
            if pid is not None:
                color = self.pieces[pid]['color']
                pygame.draw.polygon(self.screen, color, points)
                # Bordo leggero per distacco visivo?
                # pygame.draw.polygon(self.screen, (0,0,0), points, 1)
            else:
                pygame.draw.polygon(self.screen, GRID_COLOR, points, 1)

        # Info testo
        status = "SOLVED!" if self.solved else "Solving..."
        if self.solved:
            ts = f"Time: {self.solution_time:.2f}s"
            txt = self.font.render(f"{status} {ts}", True, (50, 255, 50))
        else:
            txt = self.font.render(status, True, TEXT_COLOR)
        
        self.screen.blit(txt, (20, 20))
        
        pygame.display.flip()

    def run(self):
        running = True
        last_step = 0
        
        while running:
            now = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            if not self.solved:
                # Esegui step del solver se passato abbastanza tempo
                if now - last_step > TARGET_DELAY:
                    try:
                        res = next(self.solver_iter)
                        if res is True:
                            self.solved = True
                            self.solution_time = time.time() - self.start_time
                        elif self.is_solved(): # Check double catch
                            self.solved = True
                            self.solution_time = time.time() - self.start_time
                    except StopIteration:
                        # Backtracking finito senza soluzione (impossibile con questo generatore, ma...)
                        running = False 
                    last_step = now
            
            self.draw()
            self.clock.tick(60) # 60 FPS rendering

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = HexGame()
    game.run()
