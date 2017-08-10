"""
`SignalHandler` and `Signal` classes.

The `SignalHandler`, available through `obj.signals`  once installed, can be used to:

- Throw signals.
- Subscribe to signals.

"""

from evennia import ObjectDB
from evennia import ScriptDB
from evennia.utils import delay
from evennia.utils.create import create_script

_SIGNAL_SEPARATOR = ":"

class Signal(object):

    """
    A signal.

    Signals are created when they are thrown.  They can possess several
    tags (given as positional arguments) and keywords (given as keyword
    arguments during creation).  Tags act as keys, and an object can
    subscribe to watch only one tag or a combination of them.

    """

    def __init__(self, tag, *args, **kwargs):
        self.tag = tag
        self.kwargs = kwargs

    def __repr__(self):
        kwargs = ", ".join(["{}={}".format(arg, value) for arg, value in self.kwargs.items()])
        return "<Signal {} ({})>".format(" & ".join(self.tags), kwargs)

    def throw(self):
        """Throw this signal to all subscribed objects.

        """
        for obj in self.subscirbed:
            # Execute the callback
            pass


class SignalHandler(object):

    """
    SignalHandler accessible through `obj.signals`.
    """

    script = None

    def __init__(self, subscriber):
        script = self._get_script()
        self.subscriber = subscriber

    def _get_script(self):
        """Retrieve or create the storage script."""
        if type(self).script:
            return type(self).script

        try:
            script = ScriptDB.objects.get(db_typeclass_path="evennia.contrib.aware.scripts.AwareStorage")
        except ScriptDB.DoesNotExist:
            # Create the script
            script = create_script("evennia.contrib.aware.scripts.AwareStorage")

        # Place the script in the class variable to retrieve it later
        type(self).script = script
        return script

    #NOTE This section is to be edited once we have agreed on the tag/inheritance nature of signals.  The script should also be created/restored here, probably in a class variable.
    def subscribe(self, signal, action="cmd", callback=None, **kwargs):
        """Add subscriber to script - raises scripts.AlreadyExists"""
        if callable(callback) and getattr(callback, "__self__, None):
            callback = (callback.__self__, callback.__name__)

        return self.script.add_subscriber(signal, self.subscriber, action, callback, kwargs)

    def unsubscribe(self, signal, action="cmd", callback=None, **kwargs):
        return self.script.remove_subscriber(signal, self.subscriber, action, callback, kwargs)

    def throw(self, signal, **kwargs):
        thrown_to = self.script.throw_signal(signal, self.subscriber, **kwargs)
        return thrown_to
