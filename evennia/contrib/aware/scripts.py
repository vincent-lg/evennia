"""
Scripts for the aware contrib.
"""

from evennia import DefaultScript


_SIGNAL_SEPARATOR = ":"

class AlreadyExists(Exception):
    pass

def get_local_objects(location, distance):
    def recurse(location, distance, exclude_objects=[], exclude_locations=[]):
        """Self-limiting - will not hit recursion limit due to excluding already visited locations"""
        local_objects = [obj for obj in location.contents if not obj.destination and obj not in exclude_objects]
        exclude_objects.extend(local_objects)
        if distance > 0:
            locations_to_search = [exit.destination for exit in location.exits if exit.destination not in exclude_locations]
            for location in locations_to_search:
                exclude_locations.append(location)
                found, exclude_objects, exclude_locations = recurse(
                                                            location,
                                                            distance-1,
                                                            exclude_objects,
                                                            exclude_locations)
                local_objects.extend(found)

        return (local_objects, exclude_objects, exclude_locations)

    return recurse(location, distance)[0]


def make_storable_callback(callback, call_on=None):
    # TODO: Extend this definition to allow non-instance callbacks
    if callable(callback) and getattr(callback, "__self__", None):
        callback = (callback.__self__, callback.__name__)
    elif isinstance(callback, (str, unicode)):
        callback = (call_on, callback)
    return callback


class AwareStorage(DefaultScript):

    """
    Global script to store information regarding signals and actions.
    """

    def at_script_creation(self):
        self.key = "aware_storage"
        self.desc = "Aware storage global script"
        self.db.subscribers = {}
        self.db.actions = []
        self.ndb.traces = {}

    def at_start(self):
        self.ndb.traces = {}

    def add_subscriber(self, signal, obj, action=None, callback=None, **kwargs):
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
        callback = make_storable_callback(callback, obj)

        signature = {
                "action": action,
                "callback": callback,
                "kwargs": kwargs,
        }
        if signal not in self.db.subscribers:
            self.db.subscribers[signal] = {}
        subscribers = self.db.subscribers[signal]
        if obj not in subscribers:
            subscribers[obj] = []
        signatures = subscribers[obj]
        if signature in signatures:
            raise AlreadyExists("{sub} is already subscribed to {signal} with that action/callback".format(sub=obj, signal=signal))
        else:
            signatures.append(signature)

        # Add the tag on the object
        if not obj.tags.get(signal, category="signal"):
            obj.tags.add(signal, category="signal")

        return True

    def remove_subscriber(self, signal, obj, action="cmd", callback=None, **kwargs):
        callback = make_storable_callback(callback, obj)
        signature = {
                "action": action,
                "callback": callback,
                "kwargs": kwargs,
        }
        if not signal in self.db.subscribers:
            return False
        
        subscribers = self.db.subscribers[signal]
        if obj not in subscribers:
            return False
        
        signatures = subscribers[obj]
        if signature in signatures:
            signatures.remove(signature)
        else:
            # Perhaps we should raise an error here?
            return False
        
        # Remove the tag if necessary
        if obj.tags.get(signal, category="signal"):
            obj.tags.remove(signal, category="signal")

        return True

    def throw_signal(self, signal, source, **kwargs):
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
                    to_check = [signature for signature in to_check if signature['obj'] in viable_objects]

                for signature in to_check:
                    subscriber = signature['obj']
                    if subscriber not in thrown_to:
                        thrown_to.append(subscriber)
                        if signature['callback']:
                            call_on, callback = signature['callback']
                            if hasattr(call_on, callback):
                                kwargs['signal'] = signal
                                getattr(call_on, callback)(**kwargs)
                            else:
                                print "Subscriber does not have callback {}".format(callback)
                        else:
                            action = signature['action']
                            print("Not implemented")
            signals.pop()

        return thrown_to
