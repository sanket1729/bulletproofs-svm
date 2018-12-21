from ml_proof import process_cand_inner
from svm import model

def test():
    w, X, Y = model()
    n_samples = len(X)
    print('n_samples ', n_samples)
    n = 1024
    rangebits = 128

    #positive example
    for i in range(n_samples):
        if Y[i] == 1:
            x, y = X[i], Y[i]
            print(x, y)
            res = process_cand_inner(w, x, n, rangebits)
            print('y ', y, ' res ', res)
            break

    #negative example
    for i in range(n_samples):
        if Y[i] == 0:
            x, y = X[i], Y[i]
            print(x, y)
            res = process_cand_inner(w, x, n, rangebits)
            print('y ', y, ' res ', res)
            break


if __name__ == "__main__":
    test()