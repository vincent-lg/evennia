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

    def add_action(self, signal
    def add_subscriber(self, signal, subscriber, callback):
        signature = (subscriber, callback)
        if signal in self.db.subscribers:
            if signature in self.db.subscribers[signal]:
                raise AlreadyExists("{sub} is already subscribed to {signal} with that callback".format(sub=subscriber, signal=signal))
            else:
                self.db.subscribers[signal].append(signature)
        else:
            self.db.subscribers[signal] = [signature]
        return True

    def remove_subscriber(self, signal, subscriber, callback=None):
        if signal in self.db.subscribers:
            if callback:
                to_delete = [(sub, call) for sub, call in self.db.subscribers[signal] if sub is subscriber]
                for signature in to_delete:
                    del self.db.subscribers[signal][signature]
            else:
                signature = (subscriber, callback)
                if signature in self.db.subscribers[signal]:
                    del self.db.subscribers[signal][signature]

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
