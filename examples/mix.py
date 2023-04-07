from typing import Callable
import erich

# if you don't want to include the stack trace information in the error output
import sys
def hook(exception_type, exception, traceback, debug_hook=sys.excepthook):
    # include stack trace for for all non enriched exceptions
    if not isinstance(exception, erich.EnrichedException):
        debug_hook(exception_type, exception, traceback)
    else:
        print(exception, file=sys.stderr)
sys.excepthook = hook 

# Print a formatted message where format field names must 
# be present in the function signature.
@erich.fmt("Tried starting task {name} ({desc})")
def start_task(name: str, prio: int, fn: Callable, desc: str = None):
    schedule(prio, fn)

# Print that this function has been called but only include the prio
# in the output
@erich.with_args("prio")
def schedule(prio: int, fn: Callable):
    can_schedule(prio)
    fn()

# add some nicer output to the final result
@erich.fmt("Cannot schedule task due to")
def can_schedule(prio: int):
    can_schedule_internal(prio)

# here the exception is actually raised with a limited
# amount of information which will be enriched by
# parent/calling functions.
def can_schedule_internal(prio: int):
    raise Exception(f"Cannot schedule something with prio {prio}. It's invalid")


start_task("test", -1, lambda: None, desc="very important")
