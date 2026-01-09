import pygame
import random


class Particle:
    """
    A simple particle for explosion effects.
    """
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-12, -2)
        self.gravity = 0.3
        self.life = 1.0  # 1.0 = full, 0.0 = dead
        self.decay = random.uniform(0.01, 0.03)
        self.size = random.randint(4, 12)
    
    def update(self):
        """Update particle position and life."""
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= self.decay
        self.size = max(1, self.size - 0.1)
    
    def draw(self, screen):
        """Draw the particle with fading alpha."""
        if self.life <= 0:
            return
        alpha = int(255 * self.life)
        # Create a surface for alpha blending
        surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        color_with_alpha = (*self.color, alpha)
        pygame.draw.circle(surf, color_with_alpha, (int(self.size), int(self.size)), int(self.size))
        screen.blit(surf, (int(self.x - self.size), int(self.y - self.size)))
    
    def is_alive(self):
        return self.life > 0
