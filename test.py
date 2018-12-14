from ml_proof import process_cand_inner
from svm import model

def test():
    w, X, Y = model()
    n_samples = len(X)
    print(n_samples)
    n = 1024
    for i in [5]:
        x, y = X[i], Y[i]
        print(x, y)
        res = process_cand_inner(w, x, n)
        print('y ', y, ' res ', res)
        break

if __name__ == "__main__":
    test()