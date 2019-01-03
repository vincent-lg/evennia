"""
`SignalHandler` and `Signal` classes.

The `SignalHandler`, available through `obj.signals` once installed, can be used to:

- Throw signals.
- Subscribe to signals.

"""

from evennia import ObjectDB, ScriptDB
from evennia.utils.create import create_script
from evennia.utils import delay
from evennia.contrib.aware.scripts import AwareStorage
from evennia.contrib.aware.utils import Signal, _get_script

class SignalHandler(object):

    """
    SignalHandler accessible through `obj.signals`.
    """

    def __init__(self, obj):
        self.obj = obj

    def subscribe(self, signal, *actions, **kwargs):
        """
        Subscribe the object to a signal, handling one or several actions.

        Args:
            signal (str): the signal name.
            any (dict, optional): a chain of actions to react to this signal.

        Kwargs:
            priority (int): the action(s) priority.
            any: any keyword arguments.

        This method can be used to subscribe an object to a signal and react to it with only one action:
            obj.signals.subscribe("gunfire", action="flee", priority=10)
        Or to several actions:
            obj.signals.subscribe("gunfire", {"cmd": "say HO NO!"}, {"cmd": "north"}, priority=15)

        If you want to react with a chain of actions, specify their keyword
        arguments in a list of dictionaries, as additional positional
        arguments after the signal name.

        Returns:
            subscribed (bool): has the subscription worked?

        """
        script = _get_script()
        print script
        if script is None:
            return False

        print actions
        if actions:
            statuses = []
            for action in actions:
                action.update(kwargs)
                statuses.append(script.add_subscriber(signal, self.obj, **action))

            return statuses

        return script.add_subscriber(signal, self.obj, *args, **kwargs)

    def unsubscribe(self, signal, action="cmd", callback=None, **kwargs):
        script = _get_script()
        if script is None:
            return False

        return script.remove_subscriber(signal, self.obj, action, callback, **kwargs)

    def throw(self, signal, **kwargs):
        script = _get_script()
        if script is None:
            return False

        if "from_obj" not in kwargs:
            kwargs["from_obj"] = self.obj
        if "location" not in kwargs:
            kwargs["location"] = self.obj
        signal = Signal(signal, **kwargs)
        signal.throw(script)

