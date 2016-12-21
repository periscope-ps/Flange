from flange.actions import *
from flange.combiners import *
from flange.conditions import *
from flange.graphs import *
from flange.locations import *
from flange.transforms import *
from flange.roots import *
from flange.runtime import *
from flange.utils import *

# Firewall
flangelet = place(set_att("firewall", True), 
                  between(sub("port1"), sub("port4")) << contract(nodes))
g = show(flangelet, graph("linear"))


#Assert

#Black hole



#Routing

#Time-of-day routing


#Rule merging

