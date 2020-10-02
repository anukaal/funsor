# Copyright Contributors to the Pyro project.
# SPDX-License-Identifier: Apache-2.0

from collections import Hashable

import funsor.interpreter as interpreter


class Memoize(interpreter.StatefulInterpretation):

    def __init__(self, cache=None):
        self.cache = cache if cache is not None else {}

    def __call__(self, cls, *args):
        key = (cls,) + tuple(id(arg) if (type(arg).__name__ == "DeviceArray") or not isinstance(arg, Hashable)
                             else arg for arg in args)
        if key not in self.cache:
            with interpreter.interpretation(interpreter._INTERPRETATION.fallback, stack=False):
                self.cache[key] = cls(*args)
        return self.cache[key]
