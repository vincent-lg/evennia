"""
`ActionHandler` and default actions classes.

The `ActionHandler`, available through `obj.actions`  once installed,
can be used to create actions with various priorities.  The `AwareStorage`
script is used to store actions and retain priority orders.

"""

from evennia import ScriptDB
from evennia.utils.create import create_script

class Action(object):

    """Class to represent an action.

    An action is to connect an object and a signal.  This class will
    determine what the object should do if this signal is thrown.
    Basic actions are just commands, that could be demonstrated as:
    "If you receive the signal 'enemy', attack it."  More complex
    actions can be defined through custom awarefuncs (see below) or callbackss.

    """

    def __init__(self, action="cmd", callback=None, **kwargs):
        self.action = action
        self.callback = callback
        self.kwargs = kwargs

    def __repr__(self):
        return "<Action {}>".format(self.name)

    @property
    def name(self):
        """Return a prettier name for the action."""
        kwargs = ", ".join(["{}={}".format(key, value) for key, value in self.kwargs.items()])
        msg = ""
        if self.callback:
            msg += "with callback {}".format(self.callback)
        else:
            msg += self.action

        msg += " (" + kwargs + ")>"
        return msg


class ActionHandler(object):

    """
    Action handler accessible through `obj.actions`.

    This handler allows to add actions per priority, get current
    actions, and remove an action from this priority list.

    """

    script = None
    
    def __init__(self, obj):
        self.obj = obj

    def _get_script(self):
        """Retrieve or create the storage script."""
        if type(self).script:
            return type(self).script

        try:
            script = ScriptDB.objects.get(db_key="aware_storage")
        except ScriptDB.DoesNotExist:
            # Create the script
            script = create_script("evennia.contrib.aware.scripts.AwareStorage")
        
        # Place the script in the class variable to retrieve it later
        type(self).script = script
        return script

    def all(self):
        """
        Return the sorted list of all actions on this object.

        Note:
            The list is already sorted by priorities.  The element
            of indice 0 is always the current action.  This list can
            be empty if no action has been set on this object.

        Returns:
            actions (list): the list of actions.

        """
        script = self._get_script()
        return script.db.actions.get(self.obj, [])

    def add(self):
        pass

    def remove(self):
        pass

