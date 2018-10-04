import numpy as np
from tetris import *
import pickle

n_input = checked_board_size * board_dims[1] + 1
n_hidden1 = 120
n_output = 1
pop = 50
sigma = 0.1
alpha = 0.01
point_jump = 100
highest_score = 800

try:
    w1 = pickle.load(open("w1.p", "rb"))
    b1 = pickle.load(open("b1.p", "rb"))
    w2 = pickle.load(open("w2.p", "rb"))
    print("loaded")
except FileNotFoundError:
    w1 = np.random.randn(n_input, n_hidden1)
    b1 = np.random.randn(n_hidden1)
    w2 = np.random.randn(n_hidden1, n_output)


def forward_propagate(x, w1b, b1b, w2b):
    x = np.dot(x, w1b)
    x = x + b1b
    x = np.dot(x, w2b)
    return x


def get_judge_fn(w1b=w1, b1b=b1, w2b=w2):
    def judge_fn(board, num_of_holes):
        b = [float(num_of_holes)]
        b.extend(np.array(board).flatten().astype(dtype=float))
        return forward_propagate(b, w1b, b1b, w2b)
    return judge_fn


def score(w1b, b1b, w2b, seeds=tuple([0]), adjust=point_jump):
    ave_score = 0
    set_external_pred(get_judge_fn(w1b, b1b, w2b))
    for seed in seeds:
        set_random_seed(seed)
        reset()
        main_loop()
        ave_score += get_score() / len(seeds)
    return ave_score - adjust


if __name__ == "__main__":
    epochs = 3000
    for i in range(epochs):
        if i % 10 == 0:
            set_random_seed(0)
            s = score(w1, b1, w2, adjust=0)
            print("epoch: ", i, "  score: ", s)
            if s > highest_score:
                highest_score = s
                pickle.dump(w1, open("oldWeights/" + str(n_input) + "-" + str(n_hidden1)
                                     + "-" + str(s) + "-w1.p", "wb"))
                pickle.dump(b1, open("oldWeights/" + str(n_input) + "-" + str(n_hidden1)
                                     + "-" + str(s) + "-b1.p", "wb"))
                pickle.dump(w2, open("oldWeights/" + str(n_input) + "-" + str(n_hidden1)
                                     + "-" + str(s) + "-w2.p", "wb"))
                print("\n Saved! \n")
            pickle.dump(w1, open("w1.p", "wb"))
            pickle.dump(b1, open("b1.p", "wb"))
            pickle.dump(w2, open("w2.p", "wb"))
            print("\n Saved! \n")
        w1_mutations = np.random.randn(pop, n_input, n_hidden1)
        b1_mutations = np.random.randn(pop, n_hidden1)
        w2_mutations = np.random.randn(pop, n_hidden1, n_output)
        scores = np.zeros(pop)
        rand_seeds = np.random.randint(500, size=4)
        for j in range(pop):
            w1a, b1a, w2a = w1 + sigma*w1_mutations[j], b1 + sigma*b1_mutations[j], w2 + sigma*w2_mutations[j]
            scores[j] = score(w1a, b1a, w2a, rand_seeds)
        A = (scores - np.mean(scores)) / (np.std(scores) + 1)
        for i in range(pop):
            w1 = w1 + alpha / (pop * sigma) * np.dot(w1_mutations[i], A[i])
            w2 = w2 + alpha / (pop * sigma) * np.dot(w2_mutations[i], A[i])
            b1 = b1 + alpha / (pop * sigma) * np.dot(b1_mutations[i], A[i])


