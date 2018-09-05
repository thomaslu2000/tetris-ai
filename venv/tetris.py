import numpy as np
import pygame
from data import *

width, height = 800, 1000

# Tetris board is 22 down and 10 across
board_dims = [22, 10]


def clear_screen():
    screen.fill(0)
    grid_surface.fill(0)


def draw_squares():
    for x in range(board_dims[1]):
        for y in range(board_dims[0]):
            if board[y, x]:
                pygame.draw.rect(grid_surface, BLUE, blue_rect.move(x*40, y*40))
    for block in falling_blocks:
        pygame.draw.rect(grid_surface, BLUE, blue_rect.move(40 * block[1], 40 * block[0]))

    if game_ended[0]:
        for block in places[place_counter]:
            pygame.draw.rect(grid_surface, RED, blue_rect.move(40 * block[1], 40 * block[0]))


def draw_grid():
    for i in range(board_dims[0] + 1):
        pygame.draw.line(grid_surface, GRAY, (0, i * 40), (400, i * 40), 5)
    for i in range(board_dims[1] + 1):
        pygame.draw.line(grid_surface, GRAY, (i * 40, 0), (i * 40, 880), 5)


def move_blocks(dx, dy):
    new_place = np.add(falling_blocks, [dx, dy])
    if is_legal_place(new_place):
        block_pos[0] += dx
        block_pos[1] += dy
        for i in range(len(falling_blocks)):
            falling_blocks[i] = new_place[i]
        return True


def rotate_blocks():
    new_block_locs = [np.add(block_pos, [-block[1], block[0]]) for block in np.subtract(block_pos, falling_blocks)]
    if is_legal_place(new_block_locs):
        for i in range(len(falling_blocks)):
            falling_blocks[i] = new_block_locs[i]
        update()


def is_legal_place(locs):
    for loc in locs:
        if np.greater_equal(loc, board_dims).any() or np.less(loc, [0, 0]).any() or board[tuple(loc)]:
            return False
    return True


def add_to_board(locs):
    for loc in locs:
        board[tuple(loc)] = True


def new_falling_blocks():
    block_type[0] = np.random.randint(7)
    block = np.add(block_origin, rotated_orientations[block_type[0]][0])
    for i in range(4):
        falling_blocks[i] = block[i]
    block_pos[0], block_pos[1] = list(np.add((0, 1), block_origin))
    places.clear()
    for orientation in get_possible_places():
        for blocks in orientation:
            places.append(blocks)


def num_of_block_rots():
    return 1 << (2 + block_type[0]) // 3


def block_has_settled():
    for row_i in range(len(board)):
        if all(board[row_i]):
            for replaced_row in range(row_i, 0, -1):
                board[replaced_row] = board[replaced_row-1]
            board[0] = [0]*board_dims[1]
    if board[block_origin]:
        game_over()
        return
    new_falling_blocks()


def game_over():
    game_ended[0] = True
    update()


def update():
    clear_screen()
    draw_squares()
    draw_grid()
    screen.blit(grid_surface, (40, 40))
    if game_ended[0]:
        screen.blit(font.render("GAME OVER", 1, (255, 255, 255)), (100, 100))
    pygame.display.update()


def gravity():
    if not move_blocks(1, 0):
        add_to_board(falling_blocks)
        block_has_settled()
    update()


def get_possible_places():
    # gets the locations just over the top
    just_over_tops = [board_dims[0] - 1] * board_dims[1]
    for x in range(board_dims[1]):
        for y in range(board_dims[0]):
            if board[y, x]:
                just_over_tops[x] = y - 1
                break

    # record the orientation num and adjusted (0,0) loc somewhere
    all_places = []
    for rotation_num in range(len(rotated_orientations[block_type[0]])):
        rotation = rotated_orientations[block_type[0]][rotation_num]
        this_orientation = []
        for offset in range(bottom_counts[block_type[0]][rotation_num]):
            for x in range(board_dims[1]):
                next_loc = np.add([just_over_tops[x], x], rotation).tolist()
                if is_legal_place(next_loc) and next_loc not in this_orientation:
                    this_orientation += [next_loc]
            rotation = np.subtract(rotation, [0, 1])
        all_places += [this_orientation]
    return all_places


pygame.font.init()
game_ended = [False]
font = pygame.font.SysFont("normal", 40)

clock = pygame.time.Clock()
blue_rect = pygame.Rect(0, 0, 40, 40)
board = np.zeros(board_dims, dtype=bool)
grid_surface = pygame.Surface((401, 881))

falling_blocks = 4*[[0, 0]]
block_type = [0]

block_origin = (0, 3)
block_pos = [0, 0]

# TESTING
places = []
place_counter = 0

new_falling_blocks()
pygame.init()
screen = pygame.display.set_mode((width, height))

update()


running = True
falling_time = 0
while running:
    clock.tick(20)
    if game_ended[0]:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    place_counter = (place_counter + 1) % len(places)
                    update()
                if event.key == pygame.K_SPACE:
                    game_ended[0] = False
                    place_counter = 0
                    gravity()
            if event.type == pygame.QUIT:
                running = False
    else:
        falling_time += 1
        if falling_time == 20:
            gravity()
            falling_time = 0
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_LEFT]:
            move_blocks(0, -1)
            update()
        if pressed[pygame.K_RIGHT]:
            move_blocks(0, 1)
            update()
        if pressed[pygame.K_DOWN]:
            gravity()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    rotate_blocks()
                if event.key == pygame.K_SPACE:
                    game_ended[0] = True
                    update()
            if event.type == pygame.QUIT:
                running = False
