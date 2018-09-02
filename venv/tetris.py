import numpy as np
import pygame

width, height = 800, 1000

# Tetris board is 22 down and 10 across, but we must make it reversed so we can do x, y instead of y, x
board_dims = [10, 22]


def clear_screen():
    screen.fill(0)
    grid_surface.fill(0)


def print_board():
    print(np.transpose(board))


def draw_squares():
    for x in range(10):
        for y in range(22):
            if board[x, y]:
                pygame.draw.rect(grid_surface, BLUE, blue_rect.move(x*40, y*40))
    for block in falling_blocks:
        pygame.draw.rect(grid_surface, BLUE, blue_rect.move(*np.multiply(40, block)))


def draw_grid():
    for i in range(23):
        pygame.draw.line(grid_surface, GRAY, (0, i * 40), (400, i * 40), 5)
    for i in range(11):
        pygame.draw.line(grid_surface, GRAY, (i * 40, 0), (i * 40, 880), 5)


def move_blocks(dx, dy):
    new_place = np.add(falling_blocks, [dx, dy])
    if is_legal_place(new_place):
        for i in range(4):
            falling_blocks[i] = new_place[i]
        return True


def is_legal_place(locs):
    for loc in locs:
        if np.greater_equal(loc, [10, 22]).any() or np.less(loc, [0, 0]).any() or board[tuple(loc)]:
            return False
    return True


def add_to_board(locs):
    for loc in locs:
        board[tuple(loc)] = True


def new_falling_blocks():
    block = possible_block_locs[np.random.randint(7)]
    for i in range(4):
        falling_blocks[i] = block[i]


def update():
    clear_screen()
    draw_squares()
    draw_grid()
    screen.blit(grid_surface, (40, 40))
    pygame.display.update()


def gravity():
    if not move_blocks(0, 1):
        add_to_board(falling_blocks)
        new_falling_blocks()
    update()


BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
clock = pygame.time.Clock()
blue_rect = pygame.Rect(0, 0, 40, 40)
board = np.zeros(board_dims, dtype=bool)
possible_block_locs = [
    [[4, -1], [4, 0], [5, 0], [6, 0]],  # backwards L
    [[3, 0], [4, 0], [5, 0], [5, -1]],  # L
    [[4, -1], [4, 0], [5, 0], [5, -1]],  # Square
    [[3, 0], [4, 0], [4, -1], [5, -1]],  # S
    [[3, 0], [4, 0], [4, -1], [5, 0]],  # T
    [[4, -1], [5, -1], [5, 0], [6, 0]],  # Other S
    [[3, 0], [4, 0], [5, 0], [6, 0]]  # Line
]

grid_surface = pygame.Surface((401, 881))

falling_blocks = 4*[[0,0]]
new_falling_blocks()

pygame.init()
screen = pygame.display.set_mode((width, height))

update()

running = True
falling_time = 0
while running:
    clock.tick(20)
    falling_time += 1
    if falling_time == 20:
        gravity()
        falling_time = 0
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_LEFT]:
        move_blocks(-1, 0)
        update()
    if pressed[pygame.K_RIGHT]:
        move_blocks(1, 0)
        update()
    if pressed[pygame.K_DOWN]:
        gravity()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
