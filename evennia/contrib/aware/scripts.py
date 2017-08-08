"""
Scripts for the aware contrib.
"""

from evennia import DefaultScript

class AwareStorage(DefaultScript):

    """
    Global script to store information regarding signals and actions.
    """

    def at_script_creation(self):
        self.key = " aware_storage" 
        self.desc = " Aware storage global script" 
        self.db.subscribers = []
        self.db.actions = []

