import tensorflow as tf
import numpy as np
from math import exp
import pickle

learning_rate = 0.00001
model_path = "/home/thomas/PycharmProjects/tetris-ai/tetModel.ckpt"
epochs = 500

n_hidden_1 = 100
n_hidden_2 = 100
n_hidden_3 = 100
n_input = 60
n_output = 1

num_goods = 10
num_bad = 20
hand_trained_constant_score = 100

x = tf.placeholder(tf.float32, [None, n_input])
y = tf.placeholder(tf.float32, [None, n_output])

# rewrite so you use some arbitrary judging function for a 6x10 Board


def multilayer_perceptron(x, weights, biases):
    layer_1 = tf.add(tf.matmul(x, weights['h1']), biases['b1'])
    layer_1 = tf.nn.relu(layer_1)
    # layer_2 = tf.add(tf.matmul(layer_1, weights['h2']), biases['b2'])
    # layer_2 = tf.nn.relu(layer_2)
    # layer_3 = tf.add(tf.matmul(layer_2, weights['h3']), biases['b3'])
    # layer_3 = tf.nn.relu(layer_3)
    out_layer = tf.matmul(layer_1, weights['out']) + biases['out']
    # out_layer = tf.nn.sigmoid(out_layer)
    return out_layer


weights = {
    'h1': tf.Variable(tf.random_normal([n_input, n_hidden_1])),
    'h2': tf.Variable(tf.random_normal([n_hidden_1, n_hidden_2])),
    'h3': tf.Variable(tf.random_normal([n_hidden_2, n_hidden_3])),
    'out': tf.Variable(tf.random_normal([n_hidden_2, n_output]))
}

biases = {
    'b1': tf.Variable(tf.random_normal([n_hidden_1])),
    'b2': tf.Variable(tf.random_normal([n_hidden_2])),
    'b3': tf.Variable(tf.random_normal([n_hidden_3])),
    'out': tf.Variable(tf.random_normal([n_output]))
}

pred = multilayer_perceptron(x, weights, biases)

cost = tf.reduce_mean(tf.square(tf.subtract(pred, y)))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
init = tf.global_variables_initializer()

saver = tf.train.Saver()


def adjusted_sigmoid(x1):
    return 1 / (1 + exp(-x1/128))  # 500 is like .98


def gen_board_and_score(bad=False):
    score = 100
    filled_rows = 1 + np.random.randint(6)
    score += 50 * filled_rows  # score will be turned negative if bad
    if bad:
        score = 0
        if np.random.choice([True, False]):
            filled_rows = 0
            score = 100
    b = []
    for i in range(filled_rows):
        row = [1] * 10
        if bad:
            for index in np.random.choice(10, size=(1 + np.random.randint(4)), replace=False):
                row[index] = 0
                score += 2
        b += [row]

    left_end = np.random.randint(10)
    right_end = np.random.randint(10 - left_end)

    while filled_rows < 6:  # , based on old left_end etc
        row = [1]*left_end + [0] * (10 - left_end - right_end) + [1] * right_end
        score += 2 * left_end + 2 * right_end
        if bad:
            if left_end > 1:
                for index in np.random.choice(left_end, size=(1 + np.random.randint(left_end//2)), replace=False):
                    row[index] = 0
                    score += 2
            if right_end > 1:
                for index in np.random.choice(right_end, size=(1 + np.random.randint(right_end//2)), replace=False):
                    row[10 - right_end + index] = 0
                    score += 2
        b = [row] + b
        filled_rows += 1
        left_end, right_end = np.random.randint(left_end+1), np.random.randint(right_end+1)
    if bad:
        score *= -1
    return b, score  # FIX BAD STUFF, ADD HOLES TO SIDE EDGES, FIX SCORE


def train_once(s, b, raw_score):
        train_x, train_y = b, [[raw_score]]
        train_x = np.reshape(train_x, (1, 60))
        p, _, c = s.run([pred, optimizer, cost], feed_dict={x: train_x, y: train_y})
        return p, c


if __name__ == "__main__":
    hand_trained = []
    try:
        hand_trained = pickle.load(open("hand_trained.p", "rb"))
    except FileNotFoundError:
        print("No hand trained boards found")
        pass
    num_hand_trained = len(hand_trained)

    with tf.Session() as sess:
        sess.run(init)
        try:
            load_path = saver.restore(sess, model_path)
            print("restored")
        except ValueError:
            pass

        going = True
        while going:
            for epoch in range(1, epochs + 1):
                # Hand Trained
                avg_cost = 0
                for board in hand_trained:
                    prediction, cost_val = train_once(sess, board, hand_trained_constant_score)
                    avg_cost += cost_val/num_hand_trained
                if epoch % 10 == 0:
                    print("Hand Trained Boards | Step ", epoch, " Cost: ", avg_cost)

                # Good
                avg_cost = 0
                for good in range(1, num_goods + 1):
                    prediction, cost_val = train_once(sess, *gen_board_and_score())
                    avg_cost += cost_val / num_goods
                if epoch % 10 == 0:
                    print("Good Boards | Step ", epoch, " Cost: ", avg_cost)

                # Bad
                avg_cost = 0
                for bad in range(1, num_bad + 1):
                    prediction, cost_val = train_once(sess, *gen_board_and_score(bad=True))
                    avg_cost += cost_val / num_goods
                if epoch % 10 == 0:
                    print("Bad Boards | Step ", epoch, " Cost: ", avg_cost)

            print()
            save_path = saver.save(sess, model_path)
            print("saved")
            # going = False
