import numpy as np
import settings
from random import random, randint


def tanh(x):
    return np.tanh(x)


def tanh_prime(x):
    return 1.0 - x ** 2


# The fns addends_matrix and sum_matrix create the input and output
# arrays that get appened up into training matrices by the caller (in
# driver).
#
# Transform two addends into a distributed representation input array,
# e.g., for a representation of 3 + 4, the input array created by
# addends_matrix) is:
#
# Index:         0 , 1 , 2 ,   3 ,   4 , 5 , 6 , 7 , 8 , 9 , 10 ,   11 , 12 ,   13 , 14 
# Input array: [ 0 , 0 , 0.5 , 1 , 0.5 , 0 , 0 , 0 , 0 , 0 ,  0 ,  0.5 ,  1 ,  0.5 ,  0 ]
#
# The surrounding 0.5s are supposed to represent children's confusion
# about the number actually stated. (Or about how to xform the stated
# number into the exact internal representation).
#
# And the output array (created by sum_matrix) is:
#
# Index:         0 , 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 , 10 , 11 , 12 , 13 , 14 
# Output array:[ 0 , 0 , 0 , 1 , 0 , 0 , 0 , 0 , 0 , 0 ,  0 ,  0 ,  1 ,  0 ,  0 ]
#
# WWW WARNING !!! Don't confuse these with the fingers on the hands!

def addends_matrix(a1, a2):
    lis = [0] * 14
    # First addend
    lis[a1 - 1] = 1 - settings.addend_matrix_offby1_delta
    lis[a1] = 1
    lis[a1 + 1] = 1 - settings.addend_matrix_offby1_delta
    # Second addend
    lis[a2 + 6] = 1 - settings.addend_matrix_offby1_delta
    lis[a2 + 7] = 1
    lis[a2 + 8] = 1 - settings.addend_matrix_offby1_delta
    return lis


def sum_matrix(s):
    lis = [0] * (13 + len(settings.strategies))
    lis[s] = 1
    return lis


class NeuralNetwork:
    def __init__(self, layers):

        self.activation = tanh
        self.activation_prime = tanh_prime

        # Set weights

        self.weights = []

        self.target = []
        # range of weight values (-1,1)
        # input and hidden layers - random((2+1, 2+1)) : 3 x 3

        for i in range(1, len(layers) - 1):
            r = 2 * np.random.random((layers[i - 1] + 1, layers[i] + 1)) - 1
            # Special debugging fill DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
            if settings.debugging_weight_fill:
                print "!!!!!!!!!!!!!!!!! WARNING! DEBUGGING WEIGHT FILL IS ON (A) !!!!!!!!!!!!!!!!!!"
                for l in range(0,layers[i - 1] + 1):
                    for m in range(0,layers[i] + 1):
                        r[l,m]=np.random.uniform(-settings.initial_weight_delta,+settings.initial_weight_delta,1)[0]
                print str(r)

            self.weights.append(r)

        # output layer - random((2+1, 1)) : 3 x 1

        r = 2 * np.random.random((layers[i] + 1, layers[i + 1])) - 1

        # Special debugging fill DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
        if settings.debugging_weight_fill:
           print "!!!!!!!!!!!!!!!!! WARNING! DEBUGGING WEIGHT FILL IS ON (B) !!!!!!!!!!!!!!!!!!"
           for l in range(0,layers[i] + 1):
               for m in range(0,layers[i + 1]):
                   r[l,m]=np.random.uniform(-settings.initial_weight_delta,+settings.initial_weight_delta,1)[0]
           print str(r)

        self.weights.append(r)

        self.X = []
        for i in range(1, 6):
            for j in range(1, 6):
                self.X.append(addends_matrix(i, j))
        self.X = np.array(self.X)

        self.predictions = []

    # the main forward feeding/backpropagation part
    def fit(self, X, y, learning_rate, epochs):

#        print "================ FIT ==============="
#        print str(X)
#        print str(y)

        # Add column of ones to X
        # This is to add the bias unit to the input layer

        ones = np.atleast_2d(np.ones(X.shape[0]))
        X = np.concatenate((ones.T, X), axis=1)
        for k in range(epochs):

            # if k % (epochs/10) == 0: print 'epochs:', k

            # choose a random training set

            i = np.random.randint(X.shape[0])
            a = [X[i]]
            for l in range(len(self.weights)):
                dot_value = np.dot(a[l], self.weights[l])
                activation = self.activation(dot_value)
                a.append(activation)

            # output layer

            error = y[i] - a[-1]
            deltas = [error * self.activation_prime(a[-1])]

            # we need to begin at the second to last layer 
            # (a layer before the output layer)

            for l in range(len(a) - 2, 0, -1):
                deltas.append(deltas[-1].dot(self.weights[l].T) * self.activation_prime(a[l]))

            # reverse
            # [level3(output)->level2(hidden)]  => [level2(hidden)->level3(output)]

            deltas.reverse()

            # backpropagation
            # 1. Multiply its output delta and input activation 
            #    to get the gradient of the weight.
            # 2. Subtract a ratio (percentage) of the gradient from the weight.

            for i in range(len(self.weights)):
                layer = np.atleast_2d(a[i])
                delta = np.atleast_2d(deltas[i])
                self.weights[i] += learning_rate * layer.T.dot(delta)

    # Outputs a matrix given an input matrix, this is used heavily
    # when we want to "know" what is in the kid's mind

    def predict(self, x):
        a = np.concatenate((np.ones(1).T, np.array(x)), axis=1)
        for l in range(0, len(self.weights)):
            a = self.activation(np.dot(a, self.weights[l]))
        return a

    # Returns a function that picks a random result from a list of
    # results above the confidence criterion this is used for the
    # retrieval. when we want to try to retrieve a sum, for example 3
    # + 4 = 7, we pass in a1 = 3, a2 = 4, beg = 0, and end = 13 guess
    # loops through [beg,end) to see the values that are above the cc,
    # and chooses a random number from those values. if there are
    # none, it returns none.  it does the same thing for when we want
    # to retrieve a strategy, except beg = 13, and end = 13 +
    # len(strategies)

    def try_memory_retrieval(self, sub_nn):
        import ADD

        a1 = ADD.ADDEND.ad1
        a2 = ADD.ADDEND.ad2
        index = y_index(a1, a2)
        if (a1 > 5) or (a2 > 5):
            return None
        # Collect the values that come above cc.
        results_above_cc = [x for x in range(sub_nn.beg, sub_nn.end) if self.predictions[index][x] > sub_nn.cc]
        l = len(results_above_cc)
        if l > 0:
            return int(results_above_cc[randint(0, l - 1)])
        return None

    # Used for analysis output, this just gets the prediction values
    # for a particular sum. FFF Maybe this could be used inside guess?
    # FFF Anyway, see notes for guess to explain the begin and end
    # things.

    def guess_vector(self, a1, a2, beg, end):
        vec = []
        self.predict(addends_matrix(a1, a2))
        for i in range(beg, end):
            vec.append(round(self.predictions[y_index(a1, a2)][i], 5))
        return (vec)

    def update_predictions(self):
        self.predictions = []
        for i in range(1, 6):
            for j in range(1, 6):
                self.predictions.append(self.predict(addends_matrix(i, j)))

    ####targets require change
    # what target does for now is create a square matrix filled with 0.5, and for the 1d matrix at
    # y_index(a1, a2) it will have everything but the correct answer be -= DECR_RIGHT/WRONG and the correct answer
    # will have INCR_RIGHT/WRONG added to it
    def reset_target(self):
        self.target = []
        for i in range(25):
            self.target.append([0.5] * (13 + len(settings.strategies)))
        self.target = np.array(self.target)

    def update_target(self, sub_nn, our_ans, ans):

    # We change what we fit the neural network to (which is y) after
    # each update the last step of the learning process, the part
    # where y becomes our updated prediction

    def update_y(self):
        self.y = []
        for i in range(1, 6):
            for j in range(1, 6):
                self.y.append(self.predict(addends_matrix(i, j)))


    # This version creates a vector that's 1 at the correct point, if
    # the answer was correct, or else 0 at the incorrect point, if the
    # answer was incorrect, and 0.5 everywhere else. (Jeff's version
    # of 20150815)

    def create_update_in_range(self, beg, end):
        import ADD

        a1 = ADD.ADDEND.ad1
        a2 = ADD.ADDEND.ad2

        index = y_index(a1, a2)

        if a1 + a2 == our_ans:
            self.target[index][ans] += settings.INCR_RIGHT
        else:
            self.target[index][ans] += settings.INCR_WRONG
        for i in range(sub_nn.beg, sub_nn.end):
            if i != ans:
                if a1 + a2 == our_ans:
                    self.target[index][i] -= settings.DECR_RIGHT
                else:
                    self.target[index][i] -= settings.DECR_WRONG

# JS20150815: I have no idea what this means!!!???
# The index in y is this because the list is generated such that
# it goes from index = 0 a1: 1 a2 : 1
#              index = 1 a1: 1 a2:  2 ... etc

def y_index(a1, a2):
    return 5 * (a1 - 1) + (a2 - 1)
