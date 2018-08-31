import numpy as np
import pygame

width, height = 800, 1000

# Tetris board is 22 down and 10 across
board_dims = [22, 10]


def clear_screen():
    screen.fill(0)
    draw_squares()
    draw_grid()


def draw_squares():
    for x in range(10):
        for y in range(22):
            if board[y, x]:
                pygame.draw.rect(grid_surface, BLUE, blue_rect.move(x*40, y*40))


def draw_grid():
    for i in range(23):
        pygame.draw.line(grid_surface, GRAY, (0, i * 40), (400, i * 40), 5)
    for i in range(11):
        pygame.draw.line(grid_surface, GRAY, (i * 40, 0), (i * 40, 880), 5)


BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
blue_rect = pygame.Rect(0, 0, 40, 40)
pygame.init()
screen = pygame.display.set_mode((width, height))

board = np.zeros(board_dims, dtype=bool)

grid_surface = pygame.Surface((401, 881))

clear_screen()

screen.blit(grid_surface, (40, 40))

pygame.display.update()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
