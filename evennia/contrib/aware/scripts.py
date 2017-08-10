"""
Scripts for the aware contrib.
"""

from evennia import DefaultScript


_SIGNAL_SEPARATOR = ":"

class AlreadyExists(Exception):
    pass

def get_local_objects(location, distance):
    def recurse(location, distance, exclude_objects=[], exclude_locations=[]):
        """This could hit the recursion limit"""
        local_objects = [obj for obj in location.contents if not obj.destination and obj not in exclude_objects]
        exclude_objects.extend(local_objects)
        if distance > 0:
            for exit in location.exits:
                exclude_locations.append(exit.destination)
                found, exclude_objects, exclude_locations = recurse(
                                                            exit.destination,
                                                            distance-1,
                                                            exclude_objects,
                                                            exclude_locations)
                local_objects.extend(found)

        return (local_objects, exclude_objects, exclude_locations)

    return recurse(location, distance)[0]


class AwareStorage(DefaultScript):

    """
    Global script to store information regarding signals and actions.
    """

    def at_script_creation(self):
        self.key = " aware_storage"
        self.desc = " Aware storage global script"
        self.db.subscribers = {}
        self.db.actions = []

    def add_subscriber(self, signal, obj, action=None, callback=None, **kwarg):
        """
        Add a new link between a signal, a subscriber (object) and an action.

        Args:
            signal (str): the signal, can use sub-categories.
            obj (Object): the object wanted to subscribe to this signal.
            action (str, optional): action, as a pre-configured awarefunc.
            callback (callable): callback to be called if the signal is thrown.
            Any (any): other keywords as needed.

        Notes:
            One can use the separator in order to specify signals with
            a hierarchy.  The default separator being ":", one could
            send the signal "sound:crying:child" for instance.

            Awarefuncs are pre-configured actions to perform simple
            and generic actions.  The best example is probably "cmd",
            which allows to have the object use a command.  The key
            of the action should be specified in the `action` keyword.

            Notice that actions and callbacks are exclusive: if a
            callback object is specified, then it will be used.  Otherwise,
            the action will be used.  The default action being "cmd",
            the default behavior would be to execute a command.
        
        """
        signature = {
                "obj": obj,
                "action": action,
                "callback": callback,
                "kwargs": kwargs,
        }
        if signal in self.db.subscribers:
            if signature in self.db.subscribers[signal]:
                raise AlreadyExists("{sub} is already subscribed to {signal} with that action/callback".format(sub=obj, signal=signal))
            else:
                self.db.subscribers[signal].append(signature)
        else:
            self.db.subscribers[signal] = [signature]
        return True

    def remove_subscriber(self, signal, obj, action=None, callback=None, **kwargs):
        signature = {
                "obj": obj,
                "action": action,
                "callback": callback,
                "kwargs": kwargs,
        }

        if signal in self.db.subscribers and signature in self.db.subscribers[signal]:
            self.db.subscribers[signal].remove(signature)
        else:
            # Perhaps we should raise an error here?
            pass

        return True

    def throw_signal(self, signal, source, *args, **kwargs):
        signals = signal.split(_SIGNAL_SEPARATOR)

        if "local" in kwargs:
            local = kwargs.pop("local")
        else:
            local = True

        if "distance" in kwargs:
            distance = kwargs.pop("distance")
        else:
            distance = 3

        if hasattr(source, "location") and source.location:
            location = source.location
        else:
            location = source

        if local:
            viable_objects = get_local_objects(location, distance)

        thrown_to = []
        while signals: # loop through signals until we've popped them all out
            signal_to_check = _SIGNAL_SEPARATOR.join(signals)
            if signal_to_check in self.db.subscribers:
                to_check = self.db.subscribers[signal_to_check]
                if local:
                    to_check = [(obj, callback) for obj, callback in to_check if obj in viable_objects]

                for subscriber, callback in to_check:
                    if subscriber not in thrown_to:
                        thrown_to.append(subscriber)
                        if hasattr(subscriber, callback):
                            getattr(subscriber, callback)(signal, *args, **kwargs)
                        else:
                            raise "Subscriber does not have callback {}".format(callback)
            signals.pop()
