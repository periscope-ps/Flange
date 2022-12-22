import argparse, configparser, copy, csv, os, logging, logging.config, io, sys
from collections import namedtuple

class ConfigError(Exception): pass

Argument = namedtuple('Argument', ['short', 'long', 'default', 'ty', 'help'])
def _expandvar(x, default):
    v = os.path.expandvars(x)
    return default if v == x else v

def parser_from_template(template):
    parser = argparse.ArgumentParser()
    for s,l,d,ty,h in template:
        flags = [s, l] if s else [l]
        if ty is list: parser.add_argument(*flags, nargs='+', help=h)
        elif ty is bool: parser.add_argument(*flags, action='store_true', help=h)
        else: parser.add_argument(*flags, type=ty, help=h)
    return parser

def config_from_template(template, desc, *, filevar=None, version=None):
    defaults = {}
    for _,l,d,_,_ in template:
        block = defaults
        for p in l.lstrip('-').split('.')[:-1]:
            block = block.setdefault(p, {})
        block[l.lstrip('-').split('.')[-1]] = d
    return MultiConfig(defaults, desc, filevar=filevar, version=version)

def from_template(template, desc=None, *,
                  default_filepath=None, filevar=None,
                  include_logging=True,
                  general_tag="general",
                  version=None):
    parser = parser_from_template(template)
    confg = config_from_template(template, desc, filevar=filevar, version=version)
    return config.from_parser(parser, include_logging=include_logging, general_tag=general_tag)

class MultiConfig(object):
    CONFIG_FILE_VAR = "$PYTHON_CONFIG_FILENAME"

    def __init__(self, defaults, desc=None, *, filevar=None, version=None):
        self.CONFIG_FILE_VAR = filevar or self.CONFIG_FILE_VAR
        self.defaults, self._desc = defaults, (desc or "")
        self.loglevels = {'NOTSET': logging.NOTSET, 'ERROR': logging.ERROR,
                          'WARN': logging.WARNING, 'INFO': logging.INFO,
                          'DEBUG': logging.DEBUG}
        self.version = version

    def _lift(self, ty, v):
        if v is None: return ty
        if ty is not None and not isinstance(v, type(ty)):
            return csv.reader(io.StringIO(v)) if isinstance(ty, list) else type(ty)(v)
        return v

    def _from_file(self, path):
        result, tys = {}, { "true": True, "false": False, "none": None, "": None }
        if path:
            parser = configparser.ConfigParser(allow_no_value=True)
            try:
                parser.read(path)
                for section,body in parser.items():
                    if not body: continue
                    result[section] = {}
                    for k,v in body.items():
                        result[section][k] = tys.get(v, v)
            except OSError: pass
        return result

    def _setup_logging(self, level, filename):
        levels = sorted([v for v in self.loglevels.values()], reverse=True)
        llevel = levels[min(level, len(levels) - 1)]
        if filename: logging.config.fileConfig(filename)
        else:
            class _DebugOnly(logging.Filter):
                def filter(self, record):
                    return record.levelno <= logging.DEBUG
            root = logging.getLogger()
            root.setLevel(llevel)
            debug = logging.StreamHandler(sys.stderr)
            info = logging.StreamHandler(sys.stdout)
            form = logging.Formatter("[{levelname[0]}] {name} - {message}", style='{')
            info.setLevel(logging.INFO)
            debug.setLevel(llevel)
            debug.addFilter(_DebugOnly())
            info.setFormatter(form)
            debug.setFormatter(form)
            root.addHandler(info)
            root.addHandler(debug)
        return level

    def add_loglevel(self, n, v): self.loglevels[n] = v

    def display(self, log):
        if not hasattr(self, "args"): log.error("Cannot display args before parsing, "
                                                "call from_parser or from_file first")
        blocks = {}
        for sec,opt in self.args.items():
            if isinstance(opt, dict): blocks[sec] = opt
            else: log.debug(f"{sec:>10}: {opt}")

        for sec,opt in blocks.items():
            log.debug(f"[{sec}]")
            [log.debug(f"  {k:>10}: {v}") for k,v in opt.items()]

    def from_file(self, include_logging=True, default_filepath=None, general_tag="general"):
        result = copy.deepcopy(self.defaults)
        filepath = _expandvar(self.CONFIG_FILE_VAR, "") or default_filepath or ""
        for section,body in self._from_file(filepath).items():
            if section not in result: result[section] = {k:v for k,v in body.items()}
            if section == general_tag:
                for k,v in body.items():
                    result[k] = self._lift(result.get(k, ""), v)
            else:
                for k,v in body.items():
                    result[section][k] = self._lift(result[section].get(k, ""), v)
        if include_logging:
            self._setup_logging(0, result.get('logfile', None))
        self.args = result
        return result

    def from_parser(self, parsers, *, include_logging=True, general_tag="general"):
        parsers = parsers if isinstance(parsers, list) else [parsers]
        internal = argparse.ArgumentParser(description=self._desc, parents=parsers, add_help=False)
        internal.add_argument('-c', '--configfile', type=str, help='Path to the program configuration file')
        internal.add_argument('-V', '--version', action='store_true', help="Print application version")
        if include_logging:
            internal.add_argument('--logfile', type=str, help='Path to the logging configuration file')
            internal.add_argument('-v', '--verbose', action='count', default=0, help="Set verbosity of the root logger")

        args = internal.parse_args()
        filepath = args.configfile or _expandvar(self.CONFIG_FILE_VAR, "")
        result = copy.deepcopy(self.defaults)
        for section,body in self._from_file(filepath).items():
            if section not in result:
                raise ConfigError(f"Unknown section '{section.upper()}' in config file")
            if section == general_tag: [result.__setitem__(k, v) for k,v in body.items()]
            else: [result[section].__setitem__(k, v) for k,v in body.items()]
        for k,v in args.__dict__.items():
            block, path = result, k.split('.')
            for section in path[:-1]:
                if section not in block:
                    raise ConfigError(f"Invalid section '{section}' in '{k}'")
                block = block[section]
            if v is not None and v is not False: block[path[-1]] = v

        if include_logging:
            result['verbose'] = self._setup_logging(result['verbose'], result.get('logfile', None))
        if result.get('version', False):
            print(self.version)
            exit(0)
        self.args = result
        return result
