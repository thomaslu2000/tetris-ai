import numpy as np
import pygame
from data import *
AI_mode = True
external_ai = False

if __name__ != "__main__":
    AI_mode = False
    external_ai = True

judge_fn = None
if AI_mode:
    from EvolutionaryAI import get_judge_fn
    judge_fn = get_judge_fn()

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
        for block in places[place_counter[1]][place_counter[0]]:
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
        block_type[1] = (block_type[1] + 1) % 4
        for i in range(len(falling_blocks)):
            falling_blocks[i] = new_block_locs[i]
        update()
        return True
    return False


def is_legal_place(locs):
    for loc in locs:
        if np.greater_equal(loc, board_dims).any() or np.less(loc, [0, 0]).any() or board[tuple(loc)]:
            return False
    return True


def add_to_board(locs):
    for loc in locs:
        board[tuple(loc)] = True


def new_falling_blocks():
    block_type[0], block_type[1] = np.random.randint(7), 0
    block = np.add(block_origin, rotated_orientations[block_type[0]][0])
    for i in range(4):
        falling_blocks[i] = block[i]
    block_pos[0], block_pos[1] = list(np.add((0, 1), block_origin))
    places.clear()
    for orientation in get_possible_places():
        places.append(orientation)


def block_has_settled():
    tet_ai[0] = None
    global score
    score += 1
    for row_i in range(len(board)):
        if all(board[row_i]):
            score += 5
            for replaced_row in range(row_i, 0, -1):
                board[replaced_row] = board[replaced_row-1]
            board[0] = [0]*board_dims[1]
    new_falling_blocks()
    if any(board[0]) or sum([len(ori) for ori in places]) == 0:
        game_over()
        return
    if external_ai or AI_mode:
        tet_ai[0] = get_new_ai()


def game_over():
    game_ended[0] = True
    update()


def get_score():
    return score


def update():
    if show_display:
        clear_screen()
        draw_squares()
        draw_grid()
        screen.blit(grid_surface, (40, 40))
        if game_ended[0]:
            screen.blit(font.render("GAME PAUSED" if paused else "GAME OVER", 1, (255, 255, 255)), (100, 100))
        pygame.display.update()


def gravity():
    if not move_blocks(1, 0):
        add_to_board(falling_blocks)
        return True
    update()
    return False


def move_left():
    move_blocks(0, -1)
    update()


def move_right():
    move_blocks(0, 1)
    update()


def over_tops(blocks):
    for block in blocks:
        if block[0] > just_over_tops[block[1]]:
            return False
    return True


def reachable(blocks):
    if not is_legal_place(blocks):
        return False
    movement = [0, 1] if is_legal_place(np.add([0, 1], blocks)) else [0, -1]
    end_place = blocks[0]
    while not over_tops(blocks):
        blocks = np.add(movement, blocks)
        if not is_legal_place(blocks):
            return False
    return list(blocks[0]), end_place


def get_possible_places():
    # gets the locations just over the top
    just_over_tops.clear()
    just_over_tops.extend([board_dims[0] - 1] * board_dims[1])
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

        for block_displacement in rotation:
            if np.add(block_displacement, [1, 0]).tolist() in rotation:
                continue
            for x in range(board_dims[1]):
                next_loc = np.subtract(np.add([just_over_tops[x], x], rotation), block_displacement).tolist()
                if reachable(next_loc) and next_loc not in this_orientation:
                    this_orientation += [next_loc]

        all_places += [this_orientation]
    return all_places


def gen_ai(ori=None, place=None):
    if ori is None:
        place, ori = place_counter
    offset = offsets[block_type[0]][ori]
    end_blocks = places[ori][place]
    first_loc, end_loc = np.subtract(reachable(end_blocks), offset)
    under = False
    if first_loc is not end_loc:
        under = True
    move = move_right if end_loc[1] > first_loc[1] else move_left
    if __name__ != "__main__":
        def ex_ai():
            add_to_board(places[ori][place])
            return True
        return ex_ai

    def ai():
        b = falling_blocks[0]
        while block_type[1] != ori:
            if not rotate_blocks():
                break
        if under and b[0] == first_loc[0]:
            if b[1] == end_loc[1] and gravity():
                return True
            move()
        elif b[1] < first_loc[1]:
            move_right()
        elif b[1] > first_loc[1]:
            move_left()
        elif gravity():
            return True
    return ai


def get_new_ai():
    highest_score = None
    best_ori, best_place = None, None
    for ori in range(len(places)):
        for place in range(len(places[ori])):
            if external_ai:
                s = external_pred(*get_relevant_projected_board(ori, place))
            else:
                s = judge_fn(*get_relevant_projected_board(ori, place))
            if highest_score is None or s >= highest_score:
                highest_score, best_ori, best_place = s, ori, place
    return gen_ai(best_ori, best_place)


def set_external_pred(p):
    global external_pred
    external_pred = p


def get_relevant_projected_board(ori, place):
    b = board.copy()
    blocks = places[ori][place]
    for block in blocks:
        b[block[0]][block[1]] = True
    return get_relevant_board(blocks, b=b), count_holes(b)


def count_holes(b):
    total = 0
    for x in range(board_dims[1]):
        found_top = False
        for y in range(board_dims[0]):
            if found_top and not b[y][x]:
                total += 1
            elif not found_top and b[y][x]:
                found_top = True
    return total


def get_relevant_board(blocks, b=None):  # of where the block goes, not
    if b is None:
        b = board
    if checked_board_size == board_dims[0]:
        return b.copy()
    lowest = np.amax(blocks, axis=0)[0] + checked_board_size - 4
    if lowest < checked_board_size:
        return [[False]*board_dims[1]] * (checked_board_size - lowest) + b[:lowest].tolist()
    if lowest > board_dims[0]:
        return b[lowest-checked_board_size:board_dims[0]].tolist() + [[True]*board_dims[1]] * (lowest-board_dims[0])
    return b[lowest-checked_board_size:lowest]


def reset():
    global score, board, running
    score = 0
    board = np.zeros(board_dims, dtype=bool)
    running, game_ended[0] = True, False
    block_has_settled()


def set_random_seed(seed):
    np.random.seed(seed)


def get_running():
    return running


def no_player_input():
    global falling_time
    falling_time += 1
    if falling_time == 20:
        falling_time = 0
        return gravity()
    if tet_ai[0]:
        return tet_ai[0]()
    else:
        return False


def main_loop():
    while running:
        if game_ended[0]:
            break
        else:
            try:
                if no_player_input():
                    block_has_settled()
            except IndexError:
                break


game_ended = [False]
blue_rect = pygame.Rect(0, 0, 40, 40)
board = np.zeros(board_dims, dtype=bool)
external_pred = None

falling_blocks = 4*[[0, 0]]
block_type = [0, 0]  # first is the kind of block, second is the rotation # assuming it starts at 0
just_over_tops = []

block_origin = (0, 3)
block_pos = [0, 0]

places = []
place_counter = [0, 0]  # first is place index, second is rotation index
tet_ai = [None]

score = 0
falling_time = 0

# unsupervised data
show_display = False

if __name__ == "__main__":
    # normal game data
    show_display = True

    paused = False
    np.random.seed(1)
    block_has_settled()  # init method

    pygame.font.init()
    font = pygame.font.SysFont("normal", 40)

    clock = pygame.time.Clock()
    grid_surface = pygame.Surface((401, 881))

    pygame.init()
    screen = pygame.display.set_mode((width, height))

    update()

    running = True

    while running:
        clock.tick(20)
        if game_ended[0]:
            # running = False
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    orientation_length = len(places[place_counter[1]])
                    if event.key == pygame.K_RIGHT:
                        place_counter[0] = (place_counter[0] + 1) % orientation_length
                        update()
                    if event.key == pygame.K_LEFT:
                        place_counter[0] = (place_counter[0] - 1 + orientation_length) % orientation_length
                        update()
                    if event.key == pygame.K_UP:
                        place_counter[0] = 0
                        place_counter[1] = (place_counter[1] + 1) % len(places)
                        update()
                    if event.key == pygame.K_SPACE:
                        game_ended[0] = False
                        paused = False
                        place_counter[0] = 0
                        place_counter[1] = 0
                        gravity()
                    if event.key == pygame.K_DOWN:
                        tet_ai = [gen_ai()]
                        game_ended[0] = False
                        paused = False
                    if event.key == pygame.K_r:
                        reset()
                if event.type == pygame.QUIT:
                    running = False
        else:
            if no_player_input():
                block_has_settled()
            if tet_ai[0]:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
            else:
                pressed = pygame.key.get_pressed()
                if pressed[pygame.K_LEFT]:
                    move_left()
                if pressed[pygame.K_RIGHT]:
                    move_right()
                if pressed[pygame.K_DOWN]:
                    if gravity():
                        block_has_settled()
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP:
                            rotate_blocks()
                        if event.key == pygame.K_SPACE:
                            game_ended[0] = True
                            paused = True
                            place_counter[0] = 0
                            place_counter[1] = 0
                            update()
                    if event.type == pygame.QUIT:
                        running = False
