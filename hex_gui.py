import pygame
import random
import time
import sys
import math

# --- CONFIGURATION ---
HEX_SIDE = 3
TARGET_DELAY = 50 # ms between steps (controls visual speed)

# Colors (RGB)
# Colors (RGB)
BG_COLOR = (15, 15, 20) # Dark, modern
GRID_COLOR = (60, 60, 70) # Increased contrast
TEXT_COLOR = (200, 200, 200)
BUTTON_COLOR = (50, 150, 50)
BUTTON_HOVER_COLOR = (70, 180, 70)
BUTTON_TEXT_COLOR = (255, 255, 255)
INVENTORY_BG_COLOR = (20, 20, 25)

# UI Config
INVENTORY_RATIO = 0.4 # 40% of screen width for inventory

PIECE_COLORS_RGB = [
    (255, 107, 107), (78, 205, 196), (255, 230, 109), (26, 83, 92), 
    (247, 255, 247), (255, 50, 50), (100, 100, 255), (100, 255, 100),
    (255, 100, 255), (100, 255, 255), (255, 150, 50), (150, 50, 255),
    (50, 250, 150), (250, 50, 150), (50, 150, 250), (200, 200, 200)
]

class HexGame:
    """
    A class to represent and solve a Hexagon tiling puzzle using a backtracking algorithm with visual representation.
    """
    def __init__(self):
        """
        Initialize the HexGame, setting up the Pygame window, grid, pieces, and solver.
        """
        pygame.init()
        
        # Setup Fullscreen
        info = pygame.display.Info()
        self.width = info.current_w
        self.height = info.current_h
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("HEXED: One Piece Left")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        
        # Solver Logic
        self.side = HEX_SIDE
        self.grid = {}
        self.pieces = []
        self.dragging_piece = None
        self.hovered_piece = None
        self.drag_offset = (0, 0)
        self.solving = False # Flag to indicate if solver is running
        
        self.init_hexagon_grid()
        self.generate_random_pieces() 
        
        # Calculate graphic dimensions and layout inventory iteratively to fit
        self.fit_graphics_and_layout()
        
        # Solver Generator
        self.solver_iter = self.solve_generator()
        self.solved = False
        self.start_time = 0 # Will be set when solving starts
        self.solution_time = 0
        
        # UI Elements
        button_w, button_h = 160, 50
        self.solve_button_rect = pygame.Rect(
            self.width - button_w - 20, 
            self.height - button_h - 20, 
            button_w, button_h
        )
        
        self.reset_button_rect = pygame.Rect(
            self.width - button_w - 20,
            self.height - button_h - 20 - button_h - 20, # Above solve button
            button_w, button_h
        )

    def calc_metrics(self, scale_h=None):
        """
        Calculate the scaling and offsets to center the hexagon grid on the screen.
        """
        # Calculate scale to center hexagon on screen
        # Grid goes from 'side' vertically
        grid_h_units = self.side * 2  # num rows
        grid_w_units = self.side * 4 # approx width
        
        # Margins & Layout
        # Grid takes up left portion
        grid_width_px = self.width * (1 - INVENTORY_RATIO)
        
        avail_h = scale_h if scale_h else self.height * 0.8
        avail_w = grid_width_px * 0.8
        
        self.tri_h = avail_h / grid_h_units
        # In an equilateral/similar triangle, w = h * 2 / sqrt(3) for equilateral, but here we use w=base
        # We use simple aspect ratio to fill
        self.tri_w = self.tri_h * 1.2 
        
        # Centering Offset
        # Logical Bounding box
        min_r = min(k[0] for k in self.grid)
        max_r = max(k[0] for k in self.grid)
        min_c = min(k[1] for k in self.grid)
        max_c = max(k[1] for k in self.grid)
        
        center_y = self.height / 2
        grid_pixel_h = (max_r - min_r) * self.tri_h
        
        # Center in Game Area
        # The game area width is the portion not taken by inventory.
        game_area_width = self.width * (1 - INVENTORY_RATIO)
        game_area_center_x = game_area_width / 2
        
        # We want the logical center of the grid to align with game_area_center_x
        grid_pixel_w = (max_c - min_c) * (self.tri_w / 2)
        
        self.offset_x = game_area_center_x - grid_pixel_w / 2 - (min_c * self.tri_w / 2)
        self.offset_y = center_y - grid_pixel_h / 2 - (min_r * self.tri_h)

    def fit_graphics_and_layout(self):
        """
        Iteratively adjusts the scale to ensure both the grid and the inventory pieces fit on screen.
        """
        # Initial available size
        avail_h = self.height * 0.9
        
        # Loop to reduce size if inventory overflows
        valid_layout = False
        scale_factor = 1.0
        min_scale = 0.3
        
        while not valid_layout and scale_factor >= min_scale:
            self.calc_metrics(scale_h=avail_h * scale_factor)
            valid_layout = self.layout_inventory()
            if not valid_layout:
                scale_factor -= 0.05
        
        if not valid_layout:
            print("Warning: Could not fit pieces perfectly even at minimum scale.")

    def layout_inventory(self):
        """
        Calculates screen positions for all unplaced pieces in the inventory area.
        Returns True if they all fit, False otherwise.
        """
        inv_start_x = self.width * (1 - INVENTORY_RATIO) + 30
        inv_width = self.width * INVENTORY_RATIO - 60
        inv_start_y = 50
        
        current_inv_x = inv_start_x
        current_inv_y = inv_start_y
        current_row_h = 0
        
        for piece in self.pieces:
            if piece['placed']: continue
            
            # Calculate piece dimensions using current self.tri_w/h
            normalized = piece['shape']
            drs = [p[0] for p in normalized]
            dcs = [p[1] for p in normalized]
            p_h = (max(drs) - min(drs) + 1) * self.tri_h
            p_w = (max(dcs) - min(dcs) + 1) * (self.tri_w / 2)
            
            # Check width fit
            if current_inv_x + p_w > inv_start_x + inv_width:
                 # New row
                current_inv_x = inv_start_x
                current_inv_y += current_row_h + 10 # reduced padding
                current_row_h = 0
            
            # Assign position
            px, py = current_inv_x, current_inv_y
            
            # Piece specific: Update its reset_pos and screen_pos
            piece['reset_pos'] = (px, py)
            if not piece['placed'] and piece is not self.dragging_piece:
                piece['screen_pos'] = (px, py)
            
            # Advance cursors
            current_inv_x += p_w + 10 # reduced padding
            current_row_h = max(current_row_h, p_h)
            
        # Check if we overflowed height
        total_h = current_inv_y + current_row_h
        if total_h > self.height - 20:
            return False
        return True

    def init_hexagon_grid(self):
        """
        Initialize the hexagonal grid coordinates.
        The grid is represented as a dictionary where keys are (row, col) tuples.
        """
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
        """
        Get the neighbors of a given cell in the grid.
        
        Args:
            r (int): Row index.
            c (int): Column index.
            
        Returns:
            list: List of (row, col) tuples representing neighbor coordinates.
        """
        neighs = [(r, c-1), (r, c+1)]
        if (r + c) % 2 == 0: 
            neighs.append((r + 1, c))
        else:
            neighs.append((r - 1, c))
        return neighs

    def generate_random_pieces(self):
        """
        Generate random puzzle pieces to fill the grid.
        Ensures that the total area of pieces matches the grid area.
        """
        # Logic identical to previous script...
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
                    
                    anchor_parity = (ref_r + ref_c) % 2

                    # Store piece object - Positions will be set by layout_inventory later
                    piece_obj = {
                        'id': piece_id_counter, 
                        'shape': normalized, 
                        'color': color, 
                        'placed': False,
                        'anchor_parity': anchor_parity,
                        'screen_pos': (0, 0),
                        'reset_pos': (0, 0),
                        'rect': None
                    }
                    self.pieces.append(piece_obj)
                    piece_id_counter += 1
            
            if not generation_failed: break
        
        for k in self.grid: self.grid[k] = None

    def screen_to_grid(self, x, y, required_parity=None):
        """
        Convert screen coordinates to approximate grid coordinates.
        This is a heuristic approach finding the closest cell center.
        
        Args:
            x (float): Screen x coordinate.
            y (float): Screen y coordinate.
            required_parity (int, optional): If set, only returns cells with (r+c)%2 == parity.
        """
        best_dist = float('inf')
        best_cell = None
        
        # Optimize by only checking valid grid centers
        for r, c in self.grid.keys():
            # Filter by parity to prevent shape mutation
            if required_parity is not None and (r + c) % 2 != required_parity:
                continue
                
            # Get center of this cell
            points = self.get_triangle_points(r, c)
            # Centroid approx
            cx = sum(p[0] for p in points) / 3
            cy = sum(p[1] for p in points) / 3
            
            dist = math.hypot(x - cx, y - cy)
            if dist < self.tri_w: # Threshold
                if dist < best_dist:
                    best_dist = dist
                    best_cell = (r, c)
        
        return best_cell

    def reset_grid(self):
        """
        Resets the grid and puts all pieces back in inventory.
        """
        for k in self.grid: self.grid[k] = None
        for p in self.pieces:
            p['placed'] = False
            p['screen_pos'] = p['reset_pos']
        self.solved = False
        self.dragging_piece = None
        # Re-layout inventory just in case
        self.layout_inventory()
        
    def start_solving(self):
        """
        Resets the puzzle and starts the automatic solver.
        """
        self.reset_grid()
        self.solving = True
        self.start_time = time.time()
        self.solver_iter = self.solve_generator()

    def can_place(self, shapes, r, c):
        """
        Check if a piece can be placed at the specified coordinates.
        
        Args:
            shapes (list): List of relative coordinates (dr, dc) for the piece shape.
            r (int): Target row.
            c (int): Target column.
            
        Returns:
            bool: True if the piece can be placed, False otherwise.
        """
        for dr, dc in shapes:
            nr, nc = r + dr, c + dc
            if (nr, nc) not in self.grid or self.grid[(nr, nc)] is not None: return False
        return True

    def place_piece(self, piece, r, c, remove=False):
        """
        Place or remove a piece from the grid.
        
        Args:
            piece (dict): The piece object to place/remove.
            r (int): Row coordinate.
            c (int): Column coordinate.
            remove (bool): If True, removes the piece (sets grid cells to None).
        """
        for dr, dc in piece['shape']:
            self.grid[(r+dr, c+dc)] = None if remove else piece['id']
        piece['placed'] = not remove
        if not remove:
            piece['grid_pos'] = (r, c)

    def solve_generator(self):
        """
        Coroutine generator for the backtracking solver.
        Yields control back to the main loop to allow for GUI updates.
        
        Yields:
            bool: True if solved, False if continuing search.
        """
        # Find empty cell
        empty_spot = None
        # Stable sorting for determinism
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
                    yield False # Step done, continue
                    
                    # Recursion via 'yield from'
                    yield from self.solve_generator()
                    
                    if self.is_solved(): # Helper check
                        return 
                    
                    self.place_piece(piece, r, c, remove=True)
                    yield False # Backtrack step

    def is_solved(self):
        """
        Check if the puzzle is completely solved.
        
        Returns:
            bool: True if all grid cells are filled, False otherwise.
        """
        return all(v is not None for v in self.grid.values())

    def get_triangle_points(self, r, c):
        """
        Calculate the screen coordinates for the vertices of a triangular cell.
        
        Args:
            r (int): Row index.
            c (int): Column index.
            
        Returns:
            list: List of (x, y) tuples for the triangle vertices.
        """
        half_w = self.tri_w / 2
        x_base = self.offset_x + c * half_w
        y_top = self.offset_y + r * self.tri_h
        y_bot = self.offset_y + (r + 1) * self.tri_h
        
        if (r + c) % 2 == 0: # Point UP
            p1 = (x_base + half_w, y_top)      # Top
            p2 = (x_base, y_bot)               # Bot Left
            p3 = (x_base + self.tri_w, y_bot)  # Bot Right
        else: # Point DOWN
            p1 = (x_base, y_top)               # Top Left
            p2 = (x_base + self.tri_w, y_top)  # Top Right
            p3 = (x_base + half_w, y_bot)      # Bot
        return [p1, p2, p3]

    def draw(self):
        """
        Render the game state to the screen.
        """
        self.screen.fill(BG_COLOR)
        
        # Draw Inventory Background
        # Draw Inventory Background
        inv_rect = pygame.Rect(self.width * (1 - INVENTORY_RATIO), 0, self.width * INVENTORY_RATIO, self.height)
        pygame.draw.rect(self.screen, INVENTORY_BG_COLOR, inv_rect)
        
        # Draw Divider Line
        line_x = self.width * (1 - INVENTORY_RATIO)
        pygame.draw.line(self.screen, GRID_COLOR, (line_x, 0), (line_x, self.height), 3)
        
        # Draw Grid Cells
        for (r, c), pid in self.grid.items():
            points = self.get_triangle_points(r, c)
            
            if pid is not None:
                color = self.pieces[pid]['color']
                pygame.draw.polygon(self.screen, color, points)
            else:
                pygame.draw.polygon(self.screen, GRID_COLOR, points, 1)

        # Draw Pieces (Inventory or Dragging)
        for piece in self.pieces:
            if piece['placed']: continue
            
            # Position to draw: mouse pos if dragging, else inventory pos
            if piece is self.dragging_piece:
                dx, dy = self.drag_offset
                mx, my = pygame.mouse.get_pos()
                px, py = mx + dx, my + dy
            else:
                px, py = piece['screen_pos']
            
            # Construct shape polygon for drawing relative to (px, py)
            # We need to reconstruct the visual shape from logical 'shape'
            # This is tricky because logic is (dr, dc) but pixels depend on orientation.
            # We will use a simplified relative drawing: treat (px,py) as center of piece(0,0)
            
            # Update rect for collision detection (only if not dragging, or update while dragging too)
            # Calculate bounding box
            min_x, max_x, min_y, max_y = float('inf'), float('-inf'), float('inf'), float('-inf')

            for dr, dc in piece['shape']:
                # Calculate proper visual offset for each triangle
                off_x = dc * (self.tri_w * 0.5)
                off_y = dr * self.tri_h
                
                # Determine orientation based on original grid parity
                # logic: if (r+c)%2 == 0 it's point UP. using relative coords:
                # relative parity = (dr + dc) % 2.
                # Combined with anchor parity: (anchor_parity + relative_parity) % 2
                # But wait, (ref_r + ref_c + dr + dc) % 2 = (parity + dr + dc) % 2
                
                is_point_up = (piece['anchor_parity'] + dr + dc) % 2 == 0
                
                base_x = px + off_x
                base_y = py + off_y
                
                # Draw Triangle for UI
                # We need points relative to base_x, base_y (which is roughly top-left of specific cell space)
                # Let's reuse get_triangle_points logic but adapted for arbitrary screen pos
                
                half_w = self.tri_w / 2
                
                if is_point_up: # Point UP
                    p1 = (base_x + half_w, base_y)           # Top
                    p2 = (base_x, base_y + self.tri_h)       # Bot Left
                    p3 = (base_x + self.tri_w, base_y + self.tri_h) # Bot Right
                else: # Point DOWN
                    p1 = (base_x, base_y)                    # Top Left
                    p2 = (base_x + self.tri_w, base_y)       # Top Right
                    p3 = (base_x + half_w, base_y + self.tri_h)   # Bot
                
                pygame.draw.polygon(self.screen, piece['color'], [p1, p2, p3])
                # Optional border for pieces
                pygame.draw.polygon(self.screen, BG_COLOR, [p1, p2, p3], 1)
                
                # Update Bounding Box
                xs = [p[0] for p in [p1, p2, p3]]
                ys = [p[1] for p in [p1, p2, p3]]
                min_x = min(min_x, min(xs))
                max_x = max(max_x, max(xs))
                min_y = min(min_y, min(ys))
                max_y = max(max_y, max(ys))

            # Update bounding rect for interaction
            piece['rect'] = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

        # Draw "Solve It" Button
        color = BUTTON_HOVER_COLOR if self.solve_button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(self.screen, color, self.solve_button_rect, border_radius=10)
        
        btn_txt = self.font.render("SOLVE IT", True, BUTTON_TEXT_COLOR)
        txt_rect = btn_txt.get_rect(center=self.solve_button_rect.center)
        self.screen.blit(btn_txt, txt_rect)

        # Draw "Reset" Button
        color_r = (200, 70, 70) # Red
        color_r_hover = (220, 90, 90)
        draw_color_r = color_r_hover if self.reset_button_rect.collidepoint(pygame.mouse.get_pos()) else color_r
        pygame.draw.rect(self.screen, draw_color_r, self.reset_button_rect, border_radius=10)
        
        reset_txt = self.font.render("RESET", True, BUTTON_TEXT_COLOR)
        reset_rect = reset_txt.get_rect(center=self.reset_button_rect.center)
        self.screen.blit(reset_txt, reset_rect)

        # Info text
        status = "SOLVED!" if self.solved else ("Solving..." if self.solving else "Manual Mode")
        if self.solved:
            ts = f"Time: {self.solution_time:.2f}s"
            txt = self.font.render(f"{status} {ts}", True, (50, 255, 50))
        else:
            txt = self.font.render(status, True, TEXT_COLOR)
        
        self.screen.blit(txt, (20, 20))
        
        # Draw Tooltip if dragging or hovering
        active_piece = self.dragging_piece if self.dragging_piece else self.hovered_piece
        if active_piece and not active_piece['placed']:
            msg = "Rotations: Arrow UP/DOWN (Horizontal Axis) | Arrow LEFT/RIGHT (Vertical Axis)"
            
            # Setup tooltip box
            text_surf = self.font.render(msg, True, (0, 0, 0)) # Black text
            bg_rect = text_surf.get_rect(center=(self.width/2, 30))
            bg_rect.inflate_ip(20, 10)
            
            pygame.draw.rect(self.screen, (255, 255, 0), bg_rect, border_radius=5)
            self.screen.blit(text_surf, text_surf.get_rect(center=bg_rect.center))

        pygame.display.flip()


    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            
            # Rotation Logic
            if event.type == pygame.KEYDOWN:
                target_piece = self.dragging_piece if self.dragging_piece else self.hovered_piece
                # Prevent rotating placed pieces to avoid grid/visual desync
                if target_piece and not target_piece['placed']:
                    modified = False
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        # Flip Vertical Axis (Horizontal Reflection)
                        # (dr, dc) -> (-dr, dc). 
                        target_piece['shape'] = [(-r, c) for r, c in target_piece['shape']]
                        # Toggle parity to ensure visual flip matches logical flip (Up <-> Down)
                        target_piece['anchor_parity'] = 1 - target_piece['anchor_parity']
                        modified = True
                        
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                         # Flip Horizontal Axis (Vertical Reflection)
                         # (dr, dc) -> (dr, -dc). Parity Preserved visually (Up stays Up).
                         target_piece['shape'] = [(r, -c) for r, c in target_piece['shape']]
                         modified = True
                    
                    if modified:
                        pass
            
            # Mouse Interaction
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                
                # 1. Check Button
                if self.solve_button_rect.collidepoint(mx, my):
                    self.start_solving()
                    continue
                
                if self.reset_button_rect.collidepoint(mx, my):
                    self.reset_grid()
                    # Also stop solving if running
                    self.solving = False
                    continue
                
                # 2. Check Pieces (only if not solving)
                if not self.solving:
                    piece = self.get_piece_under_mouse(mx, my)
                    if piece:
                         self.dragging_piece = piece
                         
                         # Handle pickup from grid (already placed)
                         if piece['placed']:
                             # Remove from grid
                             if 'grid_pos' in piece:
                                 self.place_piece(piece, *piece['grid_pos'], remove=True)
                         
                         # Calculate drag offset
                         px, py = piece['screen_pos']
                         self.drag_offset = (px - mx, py - my)
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging_piece:
                    # Try to place
                    mx, my = event.pos
                    
                    px, py = self.dragging_piece['screen_pos']
                    
                    # Calculate Anchor Center
                    anchor_cx = px + self.tri_w / 2
                    anchor_cy = py + self.tri_h / 2

                    # Enforce parity to prevent shape mutation
                    required_p = self.dragging_piece['anchor_parity']
                    target_cell = self.screen_to_grid(anchor_cx, anchor_cy, required_parity=required_p)
                    
                    placed = False
                    if target_cell:
                        tr, tc = target_cell
                        if self.can_place(self.dragging_piece['shape'], tr, tc):
                            self.place_piece(self.dragging_piece, tr, tc)
                            placed = True
                    
                    if not placed:
                        # Return to inventory (reset pos)
                        self.dragging_piece['screen_pos'] = self.dragging_piece['reset_pos']
                    
                    self.dragging_piece = None
            
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if self.dragging_piece:
                    pass
                else:
                    self.hovered_piece = self.get_piece_under_mouse(mx, my)

        return True

    def get_piece_under_mouse(self, mx, my):
        """
        Finds a piece under the mouse cursor.
        Prioritizes pieces in inventory, then grid.
        """
        # Iterate all pieces
        for p in self.pieces:
            if p['rect'] and p['rect'].collidepoint(mx, my):
                return p
        return None

    def run(self):
        """
        Main game loop. Handles events and updates the solver.
        """
        running = True
        last_step = 0
        
        while running:
            running = self.handle_input()
            now = pygame.time.get_ticks()
            
            if self.solving and not self.solved:
                # Run solver step if enough time has passed
                if now - last_step > TARGET_DELAY:
                    try:
                        res = next(self.solver_iter)
                        if res is True:
                            self.solved = True
                            self.solution_time = time.time() - self.start_time
                            self.solving = False
                        elif self.is_solved(): # Check double catch
                            self.solved = True
                            self.solution_time = time.time() - self.start_time
                            self.solving = False
                    except StopIteration:
                        # Backtracking finished without solution (should not happen here)
                        self.solving = False
                    last_step = now
            
            # Update position of dragging piece to follow mouse
            if self.dragging_piece:
                mx, my = pygame.mouse.get_pos()
                dx, dy = self.drag_offset
                self.dragging_piece['screen_pos'] = (mx + dx, my + dy)

            self.draw()
            self.clock.tick(60) # 60 FPS rendering

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = HexGame()
    game.run()
