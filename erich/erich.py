import inspect
import functools

from string import Formatter
from collections import ChainMap
from typing import List
from operator import itemgetter

class EnrichedException(Exception):
    """Exception which wraps the actual exception which is thrown

    Args:
        Exception: Exception which is the cause of 'everything'
    """

    def __init__(self, cause: Exception):
        super().__init__(cause)
        self.cause = cause
        self.stack = []

    def __str__(self) -> str:
        output = self.stack[-1] + "\n"
        level = 0

        for level, msg in enumerate(self.stack[-2::-1]):
            output += (" " * level) + "↳ " + msg + "\n"

        output += (" " * (level+1)) + "↳ " + str(self.cause)
        return output

class InvalidEnrichDecoratorUsage(Exception):
    pass

def fmt(template: str):
    """ When a exception is raised, it is caught and wrapped
    in an EnrichedException. The template is formatted using
    the arguments of the decorated function and will be printed
    alongside the actual exception which was caught

    Args:
        template (str): The template string which will be formatted
        using the paramteres of the decorated
        function

    Raises:
        InvalidEnrichDecoratorUsage: when the template string contains
                                     fields which are not part of 
                                     the decorated function's signature
        ex: EnrichedException which just wraps the actual exception
            which was raised

    Returns:
        any: whatever the decorated function returns
    """

    # filter out None (no more format fields found)
    # but not empty strings (positional format field)
    tpl_fields = list(filter(None, map(itemgetter(1), Formatter().parse(template))))
    if any(map(lambda s: s is not None and len(s) == 0 , tpl_fields)):
        raise InvalidEnrichDecoratorUsage(
            f"Template contains positional format placeholders. "
            f"This is not allowed: '{template}'"
        )

    def _inner(fn):
        signature = inspect.signature(fn)
        # validate that all args are actually part of the function signature

        for field in tpl_fields:
            if field not in signature.parameters:
                raise InvalidEnrichDecoratorUsage(
                    f"template field {field} not in fn signature: {fn.__qualname__}"
                )

        @functools.wraps(fn)
        def _wrapper(*call_args, **call_kwargs):
            try:
                return fn(*call_args, **call_kwargs)
            except Exception as ex:
                bound = signature.bind(*call_args, **call_kwargs)
                bound.apply_defaults()

                if not isinstance(ex, EnrichedException):
                    ex = EnrichedException(ex)

                # the k can either be in args or kwargs
                lookup = ChainMap(bound.arguments, bound.kwargs)

                msg = Formatter().vformat(template, [], lookup)
                ex.stack.append(msg)

                # re-raise otherwise it is
                # "during handling of exception .. another one occured"
                raise ex from ex

        return _wrapper
    return _inner


def signature(*args: List[str]):
    """ When a exception is raised, it is caught and wrapped
    in an EnrichedException. The exception message will contain
    the signature of the decorated function and printed
    alongside the actual exception which was caught

    Args:
        args (List[str]): the parameters which should be printed
                          as signature instead of the full function
                          signature of the decorated function 

    Raises:
        InvalidEnrichDecoratorUsage: args contains paramters which
                                     which are not part of 
                                     the decorated function's signature
        ex: EnrichedException which just wraps the actual exception
            which was raised

    Returns:
        any: whatever the decorated function returns
    """
    def _inner(fn):
        spec = inspect.signature(fn)
        # validate that all args are actually part of the function signature
        for arg in args:
            if arg not in spec.parameters:
                raise InvalidEnrichDecoratorUsage(
                    f"arg {arg} not in fn signature: {fn.__qualname__}"
                )

        @functools.wraps(fn)
        def _wrapper(*call_args, **call_kwargs):
            try:
                return fn(*call_args, **call_kwargs)
            except Exception as ex:
                bound = spec.bind(*call_args, *call_kwargs)
                bound.apply_defaults()

                if not isinstance(ex, EnrichedException):
                    ex = EnrichedException(ex)

                # the k can either be in args or kwargs
                lookup = ChainMap(bound.arguments, bound.kwargs)

                kvs = [f"{arg} = {lookup[arg]}" for arg in (args or spec.parameters.keys())]
                msg = f"during call of {fn.__qualname__}({', '.join(kvs)})"
                ex.stack.append(msg)

                # re-raise otherwise it is
                # "during handling of exception .. another one occured"
                raise ex from ex

        return _wrapper
    return _inner

def fname():
    """ When a exception is raised, it is caught and wrapped
    in an EnrichedException. The exception message will contain
    the name  of the decorated function and printed
    alongside the actual exception which was caught

    Raises:
        ex: EnrichedException which just wraps the actual exception
            which was raised

    Returns:
        any: whatever the decorated function returns
    """

    def _inner(fn):
        @functools.wraps(fn)
        def _wrapper(*call_args, **call_kwargs):
            try:
                return fn(*call_args, **call_kwargs)
            except Exception as ex:
                if not isinstance(ex, EnrichedException):
                    ex = EnrichedException(ex)

                ex.stack.append(f"during call of {fn.__qualname__}")

                # re-raise otherwise it is
                # "during handling of exception .. another one occured"
                raise ex from ex

        return _wrapper
    return _inner
