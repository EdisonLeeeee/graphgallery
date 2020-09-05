import numpy as np
import scipy.sparse as sp

from graphgallery import floatx, intx


def sparse_tensor_to_sparse_adj(x):
    #TODO: torch
    """Converts a SparseTensor to a Scipy sparse matrix (CSR matrix)."""
    data = x.values.astype(floatx())
    indices = x.indices.numpy().T
    shape = x.shape
    return sp.csr_matrix((data, indices), shape=shape)


def sparse_adj_to_edges(adj):
    """Convert a Scipy sparse matrix to (edge_index, edge_weight) representation

    edge_index: shape [M, 2]
    edge_weight: shape [M,]

    """
    adj = adj.tocoo()
    edge_index = np.stack([adj.row, adj.col], axis=1)
    edge_weight = adj.data

    return edge_index, edge_weight


def edges_to_sparse_adj(edge_index, edge_weight):
    """Convert (edge_index, edge_weight) representation to a Scipy sparse matrix

    edge_index: shape [M, 2]
    edge_weight: shape [M,]

    """
    n = np.max(edge_index) + 1
    edge_index = edge_index.astype('int64', copy=False)
    adj = sp.csr_matrix((edge_weight, (edge_index[:, 0], edge_index[:, 1])), shape=(n, n))
    return adj


def asintarr(x, dtype=None):
    """Convert `x` to interger Numpy array.

    Parameters:
    ----------
    x: tf.Tensor, tf.Variable, Scipy sparse matrix,
        Numpy array-like, etc.

    Returns:
    ----------
        Integer Numpy array with dtype `graphgallery.intx()`

    """
    if dtype is None:
        dtype = intx()

    if is_tensor_or_variable(x) and x.dtype != dtype:
        if backend().kind == "T":
            x = tf.cast(x, dtype=dtype)
        else:
            ...
            # TODO
        return x

    if is_interger_scalar(x):
        x = np.asarray([x], dtype=dtype)
    elif is_list_like(x) or isinstance(x, (np.ndarray, np.matrix)):
        x = np.asarray(x, dtype=dtype)
    else:
        raise ValueError(f"Invalid input which should be either array-like or integer scalar, but got {type(x)}.")
    return x
