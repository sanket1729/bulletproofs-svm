import numpy as np
from sklearn.metrics.pairwise import chi2_kernel
from sklearn.svm import SVC

modulus = int('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141', 16)

def sign(x):
    threshold = int(1 << 128)
    if x < threshold:
        return 1
    return 0

def read_data():
    cut = 70

    print('reading data...')

    Data = np.loadtxt('./data.csv', delimiter=',')
    Data = Data[:cut]
    X, y = Data[:, :-1] / 255., Data[:, -1].astype(int) % 2

    #padding
    z = np.zeros((X.shape[0], 1023 - X.shape[1]))
    X = np.concatenate((X, z), axis=1)

    print('processed dataset')

    return X, y

def compute_kernel(X):
    print('computing kernel...')

    K = chi2_kernel(X)

    print('precomputed kernel')

def split_data(X, y):
    size = X.shape[0]
    tsize = size - int(size / 7)

    X_test = X[tsize:]
    y_test = y[tsize:]

    return X_test, y_test

def mod(value):
    return int(value) % modulus

def scale(vector, scaling):
    ret = []
    for item in vector:
        item = int(item * scaling)
        if item < 0:
            item += modulus
        ret.append(item)
    return np.array(ret)

def dot(X, Y):
    ret = int(0)
    for i in range(X.shape[0]):
        x = X[i]
        y = Y[i]
        ret = mod(ret + mod(int(x) * int(y)))
    return ret

def model():
    X, y = read_data()
    print(X.shape, y.shape)

    X_test, y_test = split_data(X, y)
    print(X_test.shape, y_test.shape)

    print('training...')
    svm = SVC(kernel='linear').fit(X, y)
    print(np.concatenate((svm.coef_[0], svm.intercept_)))

    #y_predict = svm.predict(X_test)
    #print('prediction ', y_predict)
    print('golden ', y_test)

    for j in [3]:
        scaling = 10**j
        x_compute = []
        y_compute = []
        for i in range(X_test.shape[0]):
            w = scale(np.concatenate((svm.coef_[0], svm.intercept_)), scaling)
            sample = scale(np.concatenate((X_test[i], np.array([1]))), scaling)
            result = mod(int(dot(sample, w)))
            x_compute.append(sample)
            y_compute.append(sign(result))
        y_compute = np.array(y_compute)
        print(scaling, 1. * np.sum(y_compute == y_test) / y_compute.shape[0])

    score = svm.score(X_test, y_test)
    print('score ', score)

    return w, x_compute, y_compute

if __name__ == "__main__":
    model()