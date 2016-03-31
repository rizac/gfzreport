'''
Preparser adds functions (parse_file, parse_str) for pre parsing a rst file adding some markdown
functionality. As of MArch 2016, only the directives #, #, ###... etcetera are supported and will
be converted to  
Created on Mar 14, 2016

@author: riccardo
'''
import re, sys, os
from jinja2 import Template
# import ast
from types import ModuleType
from jinja2.defaults import LSTRIP_BLOCKS


def read_config(config_file, fileformat=None):
    """
        Reads a config file returning a python object representing it.
        For details, see https://martin-thoma.com/configuration-files-in-python/
        :param config_file: either one of the following:
        - python file (*.py), config file (*.ini), json file (*.json), yaml file (*.yaml, *.yml)
        file.
        :param fileformat: if None, the file will be parsed to the library matching the config_file
        extension. Otherwise, is a string denoting the library to use (starting asterix and dot
        are not mandatory, case is insensitive. Examples: "yml", "YAML", "*.py", ".json" etcetera)
        :return: a python object representing the config file, which is:
        - python (*.py) file: a python dict where each key (string) represents a module global variable
        mapped to its value. Imported modules and variables starting with "_" in the module will NOT be included
        - config file (*.ini): a python dict where each key (string) represents a config file
        section mapped to a dict of options (strings) and relative option values
        - json (*.json) file. Any kind of python object, it depends on the input
        - yaml (*.yaml) file. A python dict where each key represents the yaml key, mapped to its
        value. Note that if yaml is not installed this will raise a ValueError.
        Note also that this function does NOT support multidocument yaml file. Only the
        first one will be returned FIXME: check!
        :raises: ValueError in case of error (IO error, ValueError, OsError, ImportError)
    """

    # FIXME: how to read py config file
    # how to read yaml
    # how to read json
    # how to read ini file

    if fileformat is None:
        fileformat = os.path.splitext(config_file)[1]
    elif fileformat[0] == '*':
        fileformat = fileformat[1:]

    fileformat = fileformat.lower()

    ret = {}
    try:
        if fileformat == '.py':
            import imp
            util = imp.load_source(os.path.splitext(os.path.basename(config_file))[0],
                                   config_file)
            for key, val in util.__dict__.iteritems():
                if key[0] != "_" and not isinstance(val, ModuleType):
                    ret[key] = val
        elif fileformat == '.ini':
            import ConfigParser
            cfg = ConfigParser.ConfigParser().read(config_file)
            for sec in cfg.sections():
                dct = {}
                options = cfg.options(sec)
                for option in options:
                    val = cfg.get(sec, option)
                    dct[option] = val
                ret[sec] = dct
        elif fileformat == '.json':
            import json
            with open('data.json') as data_file:
                ret = json.load(data_file)
        elif fileformat == '.yaml' or fileformat == '.yml':
            import yaml
            with open(config_file, "r") as stream:
                ret = yaml.safe_load(stream)
        else:
            raise ValueError('Unrecognized format for config file %s. '
                             'Please specify fileformat explicitly' % config_file)
    except (ImportError, IOError, OSError, ValueError) as exc:
        raise ValueError(str(exc))

    return ret


def _read_config_and_normalize_paths(config_file,
                                     ref_file_or_dir=None,
                                     path_keys_re=re.compile("^.+_path$", re.IGNORECASE)):
    """
        Normalizes all paths found in config_file according to ref_file_or_dir
        :param conf_file: a configuration file. The file will be read with read_config and it's
            assumed to return a dict of key and values
        :param ref_file_or_dir: the reference directory. If not a directory (e.g. a file),
            it's dirname will be used
        :param path_keys_re: a regular expression which will indicate which keys of config_dict
            refer to path entries. Defaults to "^.*_path$" (all keys which end with "_path", case
            insensitive). NOTE: empty values (or evaluating to False) will not be converted even
            if their key matches a path
        :return: A dict resulting from config_file and values denoting paths modified
            and relative to ref_file_or_dir
    """
    if config_file is None:
        return {}
    dct = read_config(config_file)
    return _normalize_paths(dct, ref_file_or_dir, path_keys_re)


def _normalize_paths(conf_dict,
                     ref_file_or_dir=None,
                     path_keys_re=re.compile("^.+_path$", re.IGNORECASE)):
    """
        Normalizes all paths found in config_dict according to ref_file_or_dir
        :param conf_dict: a configuration dictionary of keys and values
        :param ref_file_or_dir: the reference directory. If not a directory (e.g. a file),
            it's dirname will be used
        :param path_keys_re: a regular expression which will indicate which keys of config_dict
            refer to path entries. Defaults to "^.*_path$" (all keys which end with "_path", case
            insensitive). NOTE: empty values (or evaluating to False) will not be converted even
            if their key matches a path
        :return: conf_dict with values denoting paths modified and relative to ref_file_or_dir
    """
    if ref_file_or_dir is None:
        return conf_dict
    if not os.path.isdir(ref_file_or_dir):
        ref_file_or_dir = os.path.dirname(ref_file_or_dir)
    ref_file_or_dir = os.path.abspath(ref_file_or_dir)

    ret = {}  # instantiate new dict (modifying inside loop is safe?)
    for key, value in conf_dict.iteritems():
        if value and path_keys_re.match(key):
            try:
                if not os.path.isabs(value):
                    value = os.path.abspath(value)
                value = os.path.relpath(value, ref_file_or_dir)
                # value = os.path.abspath(os.path.join(os.path.dirname(sourcefile), value))
            except TypeError:
                pass
        ret[key] = value
    return ret


# def normalize_paths(file_path, rst_content=None,
#                     new_file_path,
#                      ref_file_or_dir=None,
#                      path_keys_re=re.compile("^.+_path$", re.IGNORECASE)):
#     """
#         Normalizes all paths found in config_dict according to ref_file_or_dir
#         :param conf_dict: a configuration dictionary of keys and values
#         :param ref_file_or_dir: the reference directory. If not a directory (e.g. a file),
#             it's dirname will be used
#         :param path_keys_re: a regular expression which will indicate which keys of config_dict
#             refer to path entries. Defaults to "^.*_path$" (all keys which end with "_path", case
#             insensitive). NOTE: empty values (or evaluating to False) will not be converted even
#             if their key matches a path
#         :return: conf_dict with values denoting paths modified and relative to ref_file_or_dir
#     """
# 
#     if rst_content is None:
#         with open(file_path, 'r') as fopen:
#             rst_content = fopen.read()
# 
#     reg = re.compile("^\\.\\. (image|figure|include)\\:\\:\\s+(.*)$")
# 
#     for matchobj in list(reg.finditer(rst_content))[::-1]:
#         repl = matchobj.group()
# 
#         filepath = matchobj.group(2)
# 
#         if filepath[0] == '.':
#             
#         # replace img and src, BACKWARDS!
#         start_ = matchobj.start(4) - matchobj.start()
#         end_ = matchobj.end(4) - matchobj.start()
#         repl = repl[:start_] + "></object>" + repl[end_:]
# 
#         start_ = matchobj.start(2) - matchobj.start()
#         end_ = matchobj.end(2) - matchobj.start()
#         repl = repl[:start_] + "data" + repl[end_:]
# 
#         start_ = matchobj.start(1) - matchobj.start()
#         end_ = matchobj.end(1) - matchobj.start()
#         repl = repl[:start_] + "object type='application/pdf'" + repl[end_:]
# 
#         rst_content = rst_content[:matchobj.start()] + repl + rst_content[matchobj.end():]
# 
# 
#     if ref_file_or_dir is None:
#         return conf_dict
#     if not os.path.isdir(ref_file_or_dir):
#         ref_file_or_dir = os.path.dirname(ref_file_or_dir)
#     ref_file_or_dir = os.path.abspath(ref_file_or_dir)
# 
#     ret = {}  # instantiate new dict (modifying inside loop is safe?)
#     for key, value in conf_dict.iteritems():
#         if value and path_keys_re.match(key):
#             try:
#                 if not os.path.isabs(value):
#                     value = os.path.abspath(value)
#                 value = os.path.relpath(value, ref_file_or_dir)
#                 # value = os.path.abspath(os.path.join(os.path.dirname(sourcefile), value))
#             except TypeError:
#                 pass
#         ret[key] = value
#     return ret

def render_file(filepath, config_file=None, **subs):
    """
        Parses a file to produce an rst string
        :param filepath: the path to a file. The file must be written in
            rst format (with optional markdown titles preceeded by #)
            and optional jinja2 expressions aor statements
        :param config_file: a configuration file defining expressions and statement variable to be
            rendered in filepath
        :param subs: a set of keyword arguments defining expressions and statements variables to be
            rendered in filepath. For the same keys, if any, subs value will override config_file
            values
        :return: the rst file read from filepath, with all potential rendering according to
            config_file and subs. Moreover, if filepath has
    """
    with open(filepath, 'r') as opn:
        config = {} if not config_file else read_config(config_file)
        config.update(subs)
        return render(opn.read(), config)


def render(obj, **config):
    """Renders obj via a jinja templating system
    :param obj either a string or a file object or a string. In case of file object, use the with
        statement:
        with(open(file, 'r')) as opn:
            render(opn, ...)
    :param config_dict: the dict holding the configuration values to be replaced in obj
    :param subs: a keyword argument holding additional values
    """
    try:
        string = Template(obj.read(), trim_blocks=True, lstrip_blocks=True).render(config)
    except AttributeError:
        try:
            string = obj.render(**config)
        except AttributeError:
            string = Template(str(obj)).render(config)

    return normalize_sections(string)


def normalize_sections(string):
    """Normalizes section titles of the string representing an rst document by adding rst
    decorations to them. Returns the normalized string.
    Long explanation (http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#sections):
    rst understands the nesting level of sections by means of clustering the same
    symbols, thus:

    title
    =====

    chapter
    -------

    another chapter
    ---------------

    But this is complex to organize when we provide a template file to be filled with the values of
    a config file (where we might in turn change title, chapter etcetera). Thus we make use in the
    template of the github markdown syntax with #:
    # title
    ## section
    ### subsection
    And we convert it here according to the following convention
    (as in http://www.sphinx-doc.org/en/stable/rest.html#sections)
    = with overline, for titles
    - with overline, for chapters
    = for sections
    - for subsections
    ^ for subsubsections
    " for paragraphs
    """
    reg = re.compile("^(#+)\\s+(.*?)$", re.MULTILINE)
    decorators = [("=", "="), ("-", "-"), ("=", None), ("-", None), ("^", None), ('"', None)]
    for matchobj in list(reg.finditer(string))[::-1]:
        grp = matchobj.groups()
        if len(grp) == 2:  # groups count starts from group 0
            indx = len(grp[0])-1
            decorator = decorators[-1] if indx >= len(decorators) else decorators[indx]
            str_to_decorate = grp[1]
            start_ = matchobj.start()
            end_ = matchobj.end()
            string = string[:start_] + decorate_title(str_to_decorate, decorator) + string[end_:]

    return string


def decorate_title(string, tuple_of_under_and_overline):
    """
        Decorates a string title as in rst format
        :param string: the string represetning the title
        :param tuple_of_under_and_overline: a tuple or list of two 1-character strings, representing
        the decorator character for under (element 0) and overline (element 1). None is allowed (and
        it's self explanatory)

        :Examples:
        decorate_string("sea", ("=", None)) returns:
        ===
        sea

        decorate_string("abc", ("=", "-")) returns:
        ===
        sea
        ---
    """
    lens = len(string)
    if tuple_of_under_and_overline[0] is not None:
        string = (lens * tuple_of_under_and_overline[0] + "\n") + string
    if tuple_of_under_and_overline[1] is not None:
        string += "\n" + (lens * tuple_of_under_and_overline[0])
    return string
