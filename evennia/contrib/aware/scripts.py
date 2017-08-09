"""
Scripts for the aware contrib.
"""

from evennia import DefaultScript

class AlreadyExists(Exception):
    pass

class AwareStorage(DefaultScript):

    """
    Global script to store information regarding signals and actions.
    """

    def at_script_creation(self):
        self.key = " aware_storage"
        self.desc = " Aware storage global script"
        self.db.subscribers = []
        self.db.actions = []

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
