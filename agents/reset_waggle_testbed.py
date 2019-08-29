from pymongo import MongoClient

import requests,json

client = MongoClient('localhost', 27017)
client.drop_database('unis_waggle_db')

ports = [{'id': str(i+1)} for i in range(5 * 2)]

nodes = [
    { 'type': 'waggle_node', 'properties': { 'executes': '*' },
      'id': '1',
      'name': 'waggle_node_1',
      'usage': 0.2,
      'ports': [{'rel': 'full', 'href': 'http://localhost:8888/ports/1'}],
      'cpu_util': 0.3,
      'functions': {
          'create': [],
          'delete': [],
          'active': [{'name': 'traffic_plugin', 'configuration': {}}],
          'modified': []
      }
    },
    {'type': 'waggle_node', 'properties': { 'executes': '*' },
     'id': '2',
     'name': 'waggle_node_2',
     'usage': 0.7,
     'ports': [{'rel': 'full', 'href': 'http://localhost:8888/ports/3'}],
     'functions': {
         'create': [],
         'delete': [],
         'active': [{'name': 'traffic_plugin', 'configuration': {}}],
         'modified': []
     }
    },
    {'type': 'waggle_node', 'properties': { 'executes': '*' },
     'id': '3',
     'name': 'waggle_node_3',
     'usage': 0.3,
     'ports': [{'rel': 'full', 'href': 'http://localhost:8888/ports/5'}],
     'functions': {
         'create': [],
         'delete': [],
         'active': [{'name': 'traffic_plugin', 'configuration': {}}],
         'modified': []
     }
    },
    {'type': 'waggle_node', 'properties': { 'executes': '*' },
     'id': '4',
     'name': 'waggle_node_4',
     'usage': 0.5,
     'ports': [{'rel': 'full', 'href': 'http://localhost:8888/ports/7'}],
     'functions': {
         'create': [],
         'delete': [],
         'active': [{'name': 'traffic_plugin', 'configuration': {}}],
         'modified': []
     }
    },
    {'type': 'waggle_node', 'properties': { 'executes': '*' },
     'id': '5',
     'name': 'waggle_node_5',
     'usage': 0.5,
     'ports': [{'rel': 'full', 'href': 'http://localhost:8888/ports/9'}],
     'functions': {
         'create': [],
         'delete': [],
         'active': [],
         'modified': []
     }
    },
    { 'type': 'waggle_beehive',
      'name': 'waggle_beehive_1',
      'ports': [{'rel': 'full', 'href': 'http://localhost:8888/ports/{}'.format(p+1)} for p in range(1, len(ports), 2)],
      'id': '6'
    }
]

links = [{'directed': False, 'endpoints': [{'rel': 'full', 'href': 'http://localhost:8888/ports/{}'.format(i+1)},
                                          {'rel': 'full', 'href': 'http://localhost:8888/ports/{}'.format(i+2)}]} for i in range(0, len(ports), 2)]

requests.post('http://localhost:8888/nodes', data=json.dumps(nodes))
requests.post('http://localhost:8888/ports', data=json.dumps(ports))
requests.post('http://localhost:8888/links', data=json.dumps(links))

