import hashlib
import binascii
import os

from jmbitcoin import (multiply, add_pubkeys, encode, decode, N)
from utils import (modinv, inner_product, halves, getNUMS, ecmult, Vector, ecadd_pubkeys)
from vectorpedersen import VPC, PC
from rangeproof import RangeProof
from innerproduct import IPC


def range_prover(value, rangebits):
    print("Starting rangeproof test for value: ", value,
          " in range from 0 to 2^", rangebits)
    negetive = False
    if not (0 < value and value < 2**rangebits):
        print("Value is NOT in range; we want verification to FAIL.")
        negetive = True
        #To attempt to forge a rangeproof for a not-in-range value,
        #we'll do the following: make a *valid* proof for the truncated
        #bits of our overflowed value, and then apply a V pedersen commitment
        #to our actual value, which will (should!) fail.
        #Obviously, there are a near-infinite number of ways to create
        #invalid proofs, TODO look into others.
        proofval = value & (2**rangebits -1)
        print("Using truncated bits, value: ", proofval, " to create fake proof.")
    else:
        proofval = value
    rp = RangeProof(rangebits)
    rp.generate_proof(proofval)
    proof = rp.get_proof_serialized()
    #now simulating: the serialized proof passed to the validator/receiver;
    #note that it is tacitly assumed that in the expected application (CT
    #or similar), the V value is a pedersen commitment which already exists
    #in the transaction; it's what we're validating *against*, so it's not
    #part of the proof itself. Hence we just pass rp.V into the verify call,
    #for the case of valid rangeproofs.
    print("Got rangeproof: ", binascii.hexlify(proof))
    print("Its length is: ", len(proof))
    return proof, negetive, rp

def range_verifier(proof, negetive, V, rangebits):
    rp2 = RangeProof(rangebits)
    A, S, T1, T2, tau_x, mu, t, iproof = rp2.deserialize_proof(proof)
    print("Now attempting to verify a proof in range: 0 -", 2**rangebits)
    if negetive:
        #As mentioned in comments above, here create a Pedersen commitment
        #to our actual value, which is out of range, with the same blinding
        #value.
        Varg = PC(encode(2**128 + decode(os.urandom(32), 256), 256, minlen=32), blinding=os.urandom(32)).get_commitment()
    else:
        Varg = V
    if not rp2.verify(A, S, T1, T2, tau_x, mu, t, iproof, Varg):
        if not negetive:
            print('Rangeproof should have verified but is invalid; bug.')
            return False
        else:
            print("Rangeproof fail, as it should because value is not in range.")
            return True
    else:
        if not negetive:
            print('Rangeproof verified correctly, as expected.')
            return False
        else:
            print("Rangeproof succeeded but it should not have, value is not in range; bug.")
            return True
    return negetive

def inner_product_prover(w, xi, n, V, gamma):
    w_vec = Vector(w)
    xi_vec = Vector(xi)
    value = xi_vec.inner_product(w_vec)


    randints = [decode(os.urandom(32), 256) for _ in range(n)]
    b_vec = Vector(randints)

    # Simulate a challenge e, TODO: use fiat shamir later
    e = hashlib.sha256(V).digest()
    e = decode(e,256)


    w_blind_vec = w_vec.scalar_mult(e).add(b_vec)
    blinded_commit_product = xi_vec.inner_product(b_vec)
    blinded_final_product = xi_vec.inner_product(w_blind_vec)

    r0 = os.urandom(32)
    pc2 = PC(blinded_commit_product, blinding=r0)

    r2 = (decode(gamma, 256)*e + decode(r0,256)) %N

    r2_enc = encode(r2, 256, 32)
    final_pc = PC(blinded_final_product, blinding = r2)

    w_blind_enc = [encode(x, 256, 32) for x in w_blind_vec.v]
    xi_enc = [encode(x, 256, 32) for x in xi_vec.v]

    ipc1 = IPC(w_blind_enc, xi_enc)
    comm1 = ipc1.get_commitment()
    # print('generated commitment: ', binascii.hexlify(comm1))
    proof = ipc1.generate_proof()
    a, b, L, R = proof
    print('generated proof: ')
    # print('a: ', binascii.hexlify(a))
    # print('b: ', binascii.hexlify(b))
    # print('L: ', [binascii.hexlify(_) for _ in L])
    # print('R: ', [binascii.hexlify(_) for _ in R])
    print('Total byte length is: ',
          len(a) + len(b) + len(L) * len(L[0]) + len(R) * len(R[0]) + len(comm1) 
          + len(final_pc.get_commitment()) + len(pc2.get_commitment()))
    print('Length of L, R array: ', len(L))

    prf = final_pc.get_commitment(),pc2.get_commitment(), a,b,L,R,comm1

    return prf

def inner_product_verifier(n, V, prf):
    final_pc, pc2, a,b,L,R,comm1 = prf
    
    # Simulate a challenge e, TODO: use fiat shamir later
    e = hashlib.sha256(V).digest()
    e = decode(e,256)

    lhs = final_pc
    rhs = ecmult(e, V, False)
    rhs_2 = pc2
    rhs = ecadd_pubkeys([rhs,rhs_2], False)


    print("**Verifying Inner product: **")
    #Note that the 'a' and 'b' vectors in the following constructor are dummy
    #values, they only set the length:
    verifier_ipc = IPC(["\x01"]*n, ["\x02"]*n)
    result = verifier_ipc.verify_proof(a, b, comm1, L, R)
    print("Verification result: ", result)

    if lhs == rhs:
        print("Positive Number")
        return True
    else:
        print("Negetive Number")
        return False


def process_cand_inner(w,xi,n):
    rangebits = 128
    w_vec = Vector(w)
    xi_vec = Vector(xi)
    value = xi_vec.inner_product(w_vec)

    # rp = run_test_rangeproof(value, rangebits)
    print("Starting range proof prover: Generating proof")
    prf, negetive, rp = range_prover(value, rangebits)
    V = rp.V 
    gamma = rp.gamma
    print("Lenght of Range Proof is :", len(prf))
    print("Starting Inner Product proof generation: Generating proof")
    prf2 = inner_product_prover(w, xi, n, V, gamma)
    final_pc, pc2, a,b,L,R,comm1 = prf2
    len2 = len(a) + len(b) + len(L) * len(L[0]) + len(R) * len(R[0]) + len(comm1) + len(final_pc) + len(pc2) + len(final_pc) + len(pc2)
    print("Generated Inner Product proof: len " + str(len2))
    print("\n\n")
    print("Proof Generation complete: It's total length is " + str(len(prf) + len2))
    range_verifier(prf, negetive, V, rangebits)

    return inner_product_verifier(n,V,prf2)


if __name__ == "__main__":
    n = 32
    w = [x for x in range(1234 + 1, 1234+ n + 1)]
    xi = [x for x in range(123 + 1, 123+ n + 1)]
    process_cand_inner(w,xi, n)