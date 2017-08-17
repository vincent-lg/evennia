"""
Module containing the awarefuncs (the default actions).
"""

def cmd(obj, signal, storage, cmd):
    """
    Execute a simple command.
    """
    obj.execute_cmd(cmd)
    return True

