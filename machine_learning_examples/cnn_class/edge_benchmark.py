# Vanilla deep network
# https://deeplearningcourses.com/c/deep-learning-convolutional-neural-networks-theano-tensorflow
# https://udemy.com/deep-learning-convolutional-neural-networks-theano-tensorflow
from __future__ import print_function, division
from builtins import range
# Note: you may need to update your version of future
# sudo pip install -U future

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from scipy.signal import convolve2d
from scipy.io import loadmat
from sklearn.utils import shuffle

from benchmark import error_rate


Hx = np.array([
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1],
], dtype=np.float32)

# Sobel operator - approximate gradient in Y dir
Hy = np.array([
    [-1, -2, -1],
    [0, 0, 0],
    [1, 2, 1],
], dtype=np.float32)


def convolve_flatten(X):
    # input will be (32, 32, 3, N)
    # output will be (N, 32*32)
    N = X.shape[-1]
    flat = np.zeros((N, 32*32))
    for i in range(N):
        #flat[i] = X[:,:,:,i].reshape(3072)
        bw = X[:,:,:,i].mean(axis=2) # make it grayscale
        Gx = convolve2d(bw, Hx, mode='same')
        Gy = convolve2d(bw, Hy, mode='same')
        G = np.sqrt(Gx*Gx + Gy*Gy)
        G /= G.max() # normalize it
        flat[i] = G.reshape(32*32)
    return flat


def main():
    train = loadmat('../large_files/train_32x32.mat')
    test  = loadmat('../large_files/test_32x32.mat')

    # Need to scale! don't leave as 0..255
    # Y is a N x 1 matrix with values 1..10 (MATLAB indexes by 1)
    # So flatten it and make it 0..9
    # Also need indicator matrix for cost calculation
    Xtrain = convolve_flatten(train['X'].astype(np.float32))
    Ytrain = train['y'].flatten() - 1
    Xtrain, Ytrain = shuffle(Xtrain, Ytrain)

    Xtest  = convolve_flatten(test['X'].astype(np.float32))
    Ytest  = test['y'].flatten() - 1

    # gradient descent params
    max_iter = 15
    print_period = 10
    N, D = Xtrain.shape
    batch_sz = 500
    n_batches = N // batch_sz

    # initial weights
    M1 = 1000 # hidden layer size
    M2 = 500
    K = 10
    W1_init = np.random.randn(D, M1) / np.sqrt(D + M1)
    b1_init = np.zeros(M1)
    W2_init = np.random.randn(M1, M2) / np.sqrt(M1 + M2)
    b2_init = np.zeros(M2)
    W3_init = np.random.randn(M2, K) / np.sqrt(M2 + K)
    b3_init = np.zeros(K)

    # define variables and expressions
    X = tf.placeholder(tf.float32, shape=(None, D), name='X')
    T = tf.placeholder(tf.int32, shape=(None,), name='T')
    W1 = tf.Variable(W1_init.astype(np.float32))
    b1 = tf.Variable(b1_init.astype(np.float32))
    W2 = tf.Variable(W2_init.astype(np.float32))
    b2 = tf.Variable(b2_init.astype(np.float32))
    W3 = tf.Variable(W3_init.astype(np.float32))
    b3 = tf.Variable(b3_init.astype(np.float32))

    Z1 = tf.nn.relu( tf.matmul(X, W1) + b1 )
    Z2 = tf.nn.relu( tf.matmul(Z1, W2) + b2 )
    Yish = tf.matmul(Z2, W3) + b3

    cost = tf.reduce_sum(
        tf.nn.sparse_softmax_cross_entropy_with_logits(
            logits=Yish,
            labels=T
        )
    )

    train_op = tf.train.RMSPropOptimizer(0.0001, decay=0.99, momentum=0.9).minimize(cost)

    # we'll use this to calculate the error rate
    predict_op = tf.argmax(Yish, 1)

    LL = []
    init = tf.global_variables_initializer()
    with tf.Session() as session:
        session.run(init)

        for i in range(max_iter):
            for j in range(n_batches):
                Xbatch = Xtrain[j*batch_sz:(j*batch_sz + batch_sz),]
                Ybatch = Ytrain[j*batch_sz:(j*batch_sz + batch_sz),]

                session.run(train_op, feed_dict={X: Xbatch, T: Ybatch})
                if j % print_period == 0:
                    test_cost = session.run(cost, feed_dict={X: Xtest, T: Ytest})
                    prediction = session.run(predict_op, feed_dict={X: Xtest})
                    err = error_rate(prediction, Ytest)
                    print("Cost / err at iteration i=%d, j=%d: %.3f / %.3f" % (i, j, test_cost, err))
                    LL.append(test_cost)

    plt.plot(LL)
    plt.show()


if __name__ == '__main__':
    main()
