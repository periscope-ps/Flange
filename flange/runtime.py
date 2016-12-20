from time import sleep
from .errors import NoChange

def Runtime(object):
    def __init__(self, *rules, period=.5):
        self.rules = rules if rules else []
        self.period = period
        self._run = False
        self.pending = []   

    def stop(self): self._run = True

    def add(self, rule): self.rules = rules.append(rule)
    def cancel(self, rule): self.remove(rule)

    def apply(self):
        results = []
        for rule in self.rules:
            try :
                results.append(rule())
            except NoChange: pass  ##Ignore "no-change" rules

        #TODO: Composite results
        #TODO: make changes in the real world
        #TODO: Do something to mark rules as 'in-progress'


    def run(self):
        while self._run:
            self.apply()
            sleep(self.period)
