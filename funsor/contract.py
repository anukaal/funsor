from __future__ import absolute_import, division, print_function

import opt_einsum

import funsor.ops as ops
from funsor.registry import BinaryRegistry
from funsor.terms import Funsor, Tensor

contract = BinaryRegistry()


class Contract(Funsor):
    def __init__(self, sum_op, prod_op, lhs, rhs, reduce_dims):
        assert callable(sum_op)
        assert callable(prod_op)
        assert isinstance(lhs, Funsor)
        assert isinstance(rhs, Funsor)
        assert isinstance(reduce_dims, frozenset)
        schema = lhs.schema.copy()
        schema.update(rhs.schema)
        assert reduce_dims.issubset(schema)
        for dim in reduce_dims:
            del schema[dim]
        dims = tuple(schema)
        shape = tuple(schema.values())
        super(Contract, self).__init__(dims, shape)
        self.sum_op = sum_op
        self.prod_op = prod_op
        self.lhs = lhs
        self.rhs = rhs
        self.reduce_dims = reduce_dims

    def materialize(self):
        lhs = self.lhs.materialize()
        rhs = self.rhs.materialize()
        key = (self.sum_op, self.prod_op)
        try:
            return contract(key, lhs, rhs, self.sum_op, self.prod_op, self.reduce_dims)
        except KeyError:
            return Contract(self.sum_op, self.prod_op, lhs, rhs, self.reduce_dims)


@contract.register((ops.add, ops.mul), Tensor, Tensor)
def _sumproduct_tensor_tensor(lhs, rhs, reduce_dims):
    schema = lhs.schema.copy()
    schema.update(rhs.schema)
    for dim in reduce_dims:
        del schema[dim]
    dims = tuple(schema)
    data = opt_einsum.contract(lhs.data, lhs.dims, rhs.data, rhs.dims, dims,
                               backend='torch')
    return Tensor(dims, data)


@contract.register((ops.logaddexp, ops.add), Tensor, Tensor)
def _logsumproductexp_tensor_tensor(lhs, rhs, reduce_dims):
    schema = lhs.schema.copy()
    schema.update(rhs.schema)
    for dim in reduce_dims:
        del schema[dim]
    dims = tuple(schema)
    data = opt_einsum.contract(lhs.data, lhs.dims, rhs.data, rhs.dims, dims,
                               backend='pyro.ops.einsum.torch_log')
    return Tensor(dims, data)


__all__ = [
    'Contract',
    'contract',
]
