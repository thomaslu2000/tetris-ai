import numpy as np
import pygame
from data import *
import pickle
hand_train_mode = False
AI_mode = True

if AI_mode:
    hand_train_mode = False
    import tensorflow as tf
    from train import pred, x, model_path

width, height = 800, 1000

# Tetris board is 22 down and 10 across
board_dims = [22, 10]

if hand_train_mode:
    AI_mode = False
    try:
        hand_trained_models = pickle.load(open("hand_trained.p", "rb"))
    except FileNotFoundError:
        hand_trained_models = []
        pickle.dump(hand_trained_models, open("hand_trained.p", "wb"))


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


def num_of_block_rots():
    return 1 << (2 + block_type[0]) // 3


def block_has_settled():
    tet_ai[0] = None
    if hand_train_mode:
        global hand_trained_models
        hand_trained_models += [get_relevant_board(falling_blocks)]  # save the models
    for row_i in range(len(board)):
        if all(board[row_i]):
            for replaced_row in range(row_i, 0, -1):
                board[replaced_row] = board[replaced_row-1]
            board[0] = [0]*board_dims[1]
    if board[block_origin]:
        game_over()
        return
    new_falling_blocks()
    if AI_mode:
        tet_ai[0] = get_new_ai()


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


def gen_ai(ori=None, place=0):  # rotate
    if ori is None:
        place, ori = place_counter
    first_loc, end_loc = np.subtract(reachable(places[ori][place]),
                                     offsets[block_type[0]][ori])
    under = False
    if first_loc is not end_loc:
        under = True
    move = move_right if end_loc[1] > first_loc[1] else move_left

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
    highest_score = -9999
    best_ori, best_place = 0, 0
    for ori in range(len(places)):
        for place in range(len(places[ori])):
            score = sess.run(pred, feed_dict={x: np.reshape(get_relevant_projected_board(ori, place), (1, 60))})
            if score > highest_score:
                highest_score, best_ori, best_place = score, ori, place
    return gen_ai(best_ori, best_place)


def get_relevant_projected_board(ori, place):
    b = board.copy()
    blocks = places[ori][place]
    for block in blocks:
        b[block[0]][block[1]] = True
    lowest = np.amax(blocks, axis=0)[0] + 2
    bottom = max(6, min(22, lowest))
    return b[bottom - 6:bottom].copy()


def get_relevant_board(blocks):  # of where the block goes, not
    lowest = np.amax(blocks, axis=0)[0] + 2
    if lowest < 6:
        return [[0]*10] * (6 - lowest) + board[:lowest].copy()
    if lowest > 22:
        return board[lowest-6:22].copy() + [[1]*10] * lowest-22
    bottom = max(6, min(22, lowest))
    return board[bottom-6:bottom].copy()


pygame.font.init()
game_ended = [False]
font = pygame.font.SysFont("normal", 40)

clock = pygame.time.Clock()
blue_rect = pygame.Rect(0, 0, 40, 40)
board = np.zeros(board_dims, dtype=bool)
grid_surface = pygame.Surface((401, 881))

falling_blocks = 4*[[0, 0]]
block_type = [0, 0]  # first is the kind of block, second is the rotation # assuming it starts at 0
just_over_tops = []

block_origin = (0, 3)
block_pos = [0, 0]

# TESTING
places = []
place_counter = [0, 0]  # first is place index, second is rotation index
tet_ai = [None]

if AI_mode:
    saver = tf.train.Saver()
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    try:
        load_path = saver.restore(sess, model_path)
        print("restored")
    except ValueError:
        pass

# new_falling_blocks()
block_has_settled()  # init method
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
                    place_counter[0] = 0
                    place_counter[1] = 0
                    gravity()
                if event.key == pygame.K_DOWN:
                    tet_ai = [gen_ai()]
                    game_ended[0] = False
            if event.type == pygame.QUIT:
                running = False
    else:
        falling_time += 1
        if falling_time == 20:
            gravity()
            falling_time = 0
        if tet_ai[0]:
            tet_ai[0]()
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
                gravity()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        rotate_blocks()
                    if event.key == pygame.K_SPACE:
                        game_ended[0] = True
                        place_counter[0] = 0
                        place_counter[1] = 0
                        update()
                    if hand_train_mode and event.key == pygame.K_s:
                        pickle.dump(hand_trained_models, open("hand_trained.p", "wb"))
                        print("Saved!")
                if event.type == pygame.QUIT:
                    running = False

if AI_mode:
    sess.close()
