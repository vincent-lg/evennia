"""
`SignalHandler` and `Signal` classes.

The `SignalHandler`, available through `obj.signals`  once installed, can be used to:

- Throw signals.
- Subscribe to signals.

"""

from evennia import ObjectDB
from evennia.utils import delay

class Signal(object):

    """
    A signal.

    Signals are created when they are thrown.  They can possess several
    tags (given as positional arguments) and keywords (given as keyword
    arguments during creation).  Tags act as keys, and an object can
    subscribe to watch only one tag or a combination of them.

    """

    def __init__(self, *tags, **kwargs):
        self.tags = tags
        self.kwargs = kwargs

    def __repr__(self):
        kwargs = ", ".join(["{}={}".format(arg, value) for arg, value in self.kwargs.items()])
        return "<Signal {} ({})>".format(" & ".join(self.tags), kwargs)

    @property
    def subscribed(self):
        """ Return a list of objects subscribed to this signal.

        Note:
            This method actually performs a query in order to retrieve
            objects with various tags.

        """
        # Find the list of objects with the active tags
        queryset = ObjectDB.objects.filter()
        for tag in self.tags:
            queryset.filter(db_tags__db_key=tag, db_tags__db_key="sub_signal")

        # Execute the queryset
        return list(queryset)

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
    def subscribe(self, subscriber, callback, *signals, **kwargs):
        if callable(callback) and callback.__self__ == subscriber:
            callback = callback.__name__
        for signal in signals:
            if isinstance(signal, Signal):
                if signal.key in self.db.subscribers:
                    self.db.subscribers[signal.key].append((subscriber, callback))
                else:
                    self.db.subscribers[signal.key] = [(subscriber, callback)]
            elif isinstance(signal, (str, unicode)):
                if signal in self.db.subscribers:
                    self.db.subscribers[signal].append((subscriber, callback))
                else:
                    self.db.subscribers[signal] = [(subscriber, callback)]
            else:
                # might wanna throw error
                pass

    def is_subscribed(self, subscriber, signal):
        if isinstance(signal, Signal):
            signal = signal.key
        if signal in self.db.subscribers:
            for stored_sub, callback in self.db.subscribers[signal]:
                if subscriber == stored_sub:
                    return True
        # if we get here we either didn't find the subscriber or the signal
        return False

    def unsubscribe(self, subscriber, *signals, **kwargs):
        keys_to_remove = []
        for signal in signals:
            if isinstance(signal, Signal):
                keys_to_remove.append(signal.key)
