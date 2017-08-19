"""
Module containing the awarefuncs (the default actions).
"""

def cmd(obj, signal, storage, cmd):
    """
    Execute a simple command.
    """
    obj.execute_cmd(cmd)
    return True

def move(obj, signal, storage, exit):
    """Ask the object to move in the specified direction."""
    if isinstance(exit, basestring):
        exits = obj.search(exit, quiet=True)
        exits = [ex for ex in exits if ex.destination]
        if len(exits) == 1:
            exit = exits[0]
        else:
            raise ValueError("ambiguous exit name: {}".format(exit))

    obj.move_to(exit)
    return True

