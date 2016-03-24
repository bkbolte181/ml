import textwrap
import theano
import numpy as np
import math

from keras.models import Sequential, slice_X
from keras.layers.core import Activation, TimeDistributedDense, RepeatVector
from keras.layers import recurrent


class colors:
    ok = '\033[92m'
    fail = '\033[91m'
    close = '\033[0m'


class NumberGenerator:
    def __init__(self, function, size=8):
        self.rng = np.random.RandomState(42)
        self.function = function
        self.bsize = size
        self.size = int(math.ceil(math.log(function(2 ** size, 2 ** size), 2)))

    #  some helper functions for converting to and from binary string representations
    def to_binary(self, x):
        m = ('{0:b}').format(x)
        y = [int(s) for s in reversed(m + '0' * (self.size - len(m)))]
        return np.asarray(y, theano.config.floatX)

    def as_binary_string(self, x):
        return [s[::-1] for s in textwrap.wrap(''.join('1' if i > 0.5 else '0' for i in x.T.flatten()), self.size)]

    def as_digits(self, x):
        return [int(i, 2) for i in self.as_binary_string(x)]

    def generate_data(self, n, size=1):
        """ Generator to generate `n` data instances, each consisting of two input strings and one output string """
        for i in range(n):
            a, b = [self.rng.randint(0, 2 ** self.bsize) for j in range(size)], [self.rng.randint(0, 2 ** self.bsize) for j in range(size)]

            nums = np.asarray([[self.to_binary(x), self.to_binary(y)] for x, y in zip(a, b)])
            sums = np.asarray([[self.to_binary(self.function(x, y)) for x, y in zip(a, b)]])

            yield np.asarray([nums]).transpose(3,1,0,2), np.asarray([sums]).transpose(3,2,1,0)

def build_net():
    ng = NumberGenerator(lambda x, y: x + y)

    # parameters
    n_epochs = 10
    training_size = 50000

    rnn = recurrent.LSTM
    hidden_size = 128
    batch_size = 128
    layers = 1

    print('Building model...')
    model = Sequential()
    model.add(rnn(hidden_size))

    for _ in range(layers):
        model.add(rnn(hidden_size, return_sequences=True))

    model.add(TimeDistributedDense(2))
    model.add(Activation('softmax'))

    model.compile(loss='categorical_crossentropy', optimizer='adam')

    for epoch, epoch_data in enumerate(ng.generate_data(n_epochs, size=training_size)):
        print('\n' + '-' * 50 + '\nIteration %d', epoch)
        model.fit(epoch_data[0], epoch_data[1], batch_size=batch_size, show_accuracy=True)