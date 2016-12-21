from time import sleep
from .errors import NoChange

def Runtime(object):
    def __init__(self, graph_souce, *rules, *, period=.5):
        """
        graph_source -- Function that generates the graphs
        rules -- Rules to run on the graph source.


        period -- Refresh frequency
        """

        self.graph = graph_source
        self.rules = rules if rules else []
        self.period = period
        self._run = False
        self.pending = []   

    def stop(self): self._run = True

    def add(self, rule): self.rules = rules.append(rule)
    def cancel(self, rule): self.remove(rule)

    def apply(self):
        results = []
        graph = self.graph()
        for rule in self.rules:
            try :
                results.append(rule(graph))
            except NoChange: pass  ##Ignore "no-change" rules

        #TODO: Composite results
        #TODO: make changes in the real world
        #TODO: Do something to mark rules as 'in-progress'


    def run(self):
        while self._run:
            self.apply()
            sleep(self.period)
