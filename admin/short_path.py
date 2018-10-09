from flange.compiler import flange
from pprint import pprint
import json

program="""
exists {x|x.name=='client'}~>{x|x.name=='server'}
exists {x|x.name=='server'}~>{x|x.name=='client'}
"""
pprint([json.loads(s) for s in flange(program, loglevel=3, db='http://localhost:8888', env={'usr': 'programmer'})])
