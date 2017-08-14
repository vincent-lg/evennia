"""
`SignalHandler` and `Signal` classes.

The `SignalHandler`, available through `obj.signals`  once installed, can be used to:

- Throw signals.
- Subscribe to signals.

"""

from Queue import Queue

from evennia import ObjectDB, ScriptDB
from evennia.utils.create import create_script
from evennia.utils import delay

_SIGNAL_SEPARATOR = ":"

class Signal(object):

    """
    A signal.

    Signals are created when they are thrown.  They possess a name
    with optional sub-categories using the defined separator.
    They also have keywords (given as keyword
    arguments during creation).

    """

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.local = kwargs.get("local", True)
        self.from_obj = kwargs.get("from_obj")
        self.location = kwargs.get("location", self.from_obj)
        self.propagation = kwargs.get("propagation", 0)
        self.args = args
        self.kwargs = kwargs.get("kwargs", {})

    def __repr__(self):
        kwargs = ", ".join(["{}={}".format(arg, value) for arg, value in self.kwargs.items()])
        return "<Signal {} ({})>".format(self.name, kwargs)

    def throw(self):
        """Throw the signal, replacing keyword arguments."""
        script = SignalHandler._get_script()
        trace = [{"source": self.__dict__}]
        script.ndb.traces[self.name] = trace
      
        # If a local signal, get the possible locations
        if self.local:
            graph = Queue()
            visited = [self.location]
            locations = {self.location: (0, None)}
            graph.put((0, self.location))
            while not graph.empty():
                distance, location = graph.get()
                if distance > self.propagation:
                    continue

                trace.append({"explore": {"location": location, "distance": distance}})
                for exit in ObjectDB.objects.filter(db_destination__isnull=False).exclude(
                            db_destination__in=locations.keys()):
                    destination = exit.destination
                    visited.append(destination)
                    return_exits = ObjectDB.objects.filter(db_location=destination, db_destination=location)
                    return_exit = return_exits[0] if return_exits else None
                    graph.put((distance + 1, destination))
                    locations[destination] = (distance + 1, return_exit)

            # We now have a list of locations with distance and exit
            # Get the objects with the signal name as tag
            subscribed = ObjectDB.objects.filter(db_location__in=visited,
                    db_tags__db_key=self.name, db_tags__db_category="signal")
            
            # Browse the list of objects and send them the signal
            # Sort by distance from location
            subscribed = sorted(subscribed, key=lambda obj: locations[obj.location][0])
            for obj in subscribed:
                location = obj.location
                distance, exit = locations[location]
                self.distance = distance
                self.exit = exit
                trace.append({"throw": {"obj": obj, "distance": distance, "exit": exit}})

                # Get the list of actions to which this object is subscribed for this signal
                signatures = script.db.subscribers.get(self.name, {}).get(obj, [])
                for signature in signatures:
                    cmd = signature["kwargs"]["cmd"]
                    trace.append({"signature": signature})
                    obj.execute_cmd(cmd)


class SignalHandler(object):

    """
    SignalHandler accessible through `obj.signals`.
    """

    script = None

    def __init__(self, obj):
        self.obj = obj

    @classmethod
    def _get_script(cls):
        """Retrieve or create the storage script."""
        if cls.script:
            return cls.script

        try:
            script = ScriptDB.objects.get(db_typeclass_path="evennia.contrib.aware.scripts.AwareStorage")
        except ScriptDB.DoesNotExist:
            # Create the script
            script = create_script("evennia.contrib.aware.scripts.AwareStorage")

        # Place the script in the class variable to retrieve it later
        cls.script = script
        return script

    def subscribe(self, signal, action="cmd", callback=None, **kwargs):
        """Add subscriber to script - raises scripts.AlreadyExists"""
        script = self._get_script()

        return script.add_subscriber(signal, self.obj, action, callback, **kwargs)

    def unsubscribe(self, signal, action="cmd", callback=None, **kwargs):
        script = self._get_script()

        return script.remove_subscriber(signal, self.obj, action, callback, **kwargs)

    def throw(self, signal, *args, **kwargs):
        signal = Signal(signal, *args, **kwargs)
        signal.throw()

