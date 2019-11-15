
TOKEN_TTL = 3600
MIME = {
    'HTML': 'text/html',
    'JSON': 'application/json',
    'BSON': 'application/bson',
    'PLAIN': 'text/plain',
    'SSE': 'text/event-stream',
    'PSJSON': 'application/perfsonar+json',
    'PSBSON': 'application/perfsonar+bson',
    'PSXML': 'application/perfsonar+xml',
}

DEFAULT_CONFIG = {
    'unis': None,
    'port': 8000,
    'debug': 1,
    'size': 0,
    'push': False,
    'layout': '',
    'ryu_controller': '',
    'community': ''
}
