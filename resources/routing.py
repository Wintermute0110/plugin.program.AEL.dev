# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division
from urlparse import parse_qs
from inspect import getargspec

# --- Kodi stuff ---
import xbmc
import xbmcgui

# --- Modules/packages in this addon ---
from resources.utils import *

# -------------------------------------------------------------------------------------------------
# Make AEL to run only 1 single instance
# See http://forum.kodi.tv/showthread.php?tid=310697
# -------------------------------------------------------------------------------------------------
g_monitor = xbmc.Monitor()
g_main_window = xbmcgui.Window(10000)
AEL_LOCK_PROPNAME = 'AEL_instance_lock'
AEL_LOCK_VALUE    = 'True'
class SingleInstance:
    def __enter__(self):
        # --- If property is True then another instance of AEL is running ---
        if g_main_window.getProperty(AEL_LOCK_PROPNAME) == AEL_LOCK_VALUE:
            log_warning('SingleInstance::__enter__() Lock in use. Aborting AEL execution')
            # >> Apparently this message pulls the focus out of the launcher app. Disable it.
            # >> Has not effect. Kodi steals the focus from the launched app even if not message.
            kodi_dialog_OK('Another instance of AEL is running! Wait until the scraper finishes '
                           'or close the launched application before launching a new one and try '
                           'again.')
            raise SystemExit
        if g_monitor.abortRequested(): 
            log_info('g_monitor.abortRequested() is True. Exiting plugin ...')
            raise SystemExit

        # --- Acquire lock for this instance ---
        log_debug('SingleInstance::__enter__() Lock not in use. Setting lock')
        g_main_window.setProperty(AEL_LOCK_PROPNAME, AEL_LOCK_VALUE)
        return True

    def __exit__(self, type, value, traceback):
        # --- Print information about exception if any ---
        # >> If type == value == tracebak == None no exception happened
        if type:
            log_error('SingleInstance::__exit__() Unhandled excepcion in protected code')

        # --- Release lock even if an exception happened ---
        log_debug('SingleInstance::__exit__() Releasing lock')
        g_main_window.setProperty(AEL_LOCK_PROPNAME, '')

class RoutingError(Exception):
    pass

class Router(object):
        
    def __init__(self):
        self._rules = {}  # function to list of rules
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            self.handle = int(sys.argv[1])
        else:
            self.handle = -1
        
        self.base_url = sys.argv[0]
        self.args = {}
    
    def action(self, command, protected=False):
        """ Register a route. """
        def decorator(func):
            self.add_route(func, command, protected)
            return func
        return decorator
    
    def add_route(self, func, command, protected=False):
        """ Register a route. """
        
        arg_specs = getargspec(func)
        argument_names = arg_specs.args
        
        rule = CommandRule(command, argument_names, protected)
        if func not in self._rules:
            self._rules[func] = []
        self._rules[func].append(rule)

    def create_url(self, command, **kwargs):
        url = '{0}?com={1}'.format(self.base_url, command)
        if kwargs is not None:
            # python 3: for key in kwargs.items():
            for key, value in kwargs.iteritems():
                url = url + '&{0}={1}'.format(key, value)
                
        return url

    def run(self, argv=None):
        if argv is None:
            argv = sys.argv
        if len(argv) > 2:
            self.args = parse_qs(argv[2].lstrip('?'))
        
        command = self.args['com'][0] if 'com' in self.args else ''
        log_debug('run() Processing command = "{0}"'.format(command))
        #path = urlsplit(argv[0]).path or '/'
        return self._dispatch(command)

    def run_command(self, command, **kwargs):        
        self.args = kwargs
        log_debug('run() Processing command = "{0}"'.format(command))
        return self._dispatch(command)
        
    def _dispatch(self, command):
        
        if 'catID' in self.args:
            self.args['categoryID'] = self.args['catID'][0]
        if 'launID' in self.args:
            self.args['launcherID'] = self.args['launID'][0]
        if 'romID' in self.args:
            self.args['romID'] = self.args['romID'][0]

        applicable_rules = []
        arg_set = set(self.args.keys())
        log_debug('run() Arguments set: {}'.format(arg_set))
        
        for view_func, rules in iter(list(self._rules.items())):
            for rule in rules:
                if command == rule.command:
                    matching_arguments = len(arg_set.intersection(rule.arguments))
                    applicable_rules.append(MatchingRule(rule, view_func, matching_arguments))
                
        if len(applicable_rules) == 0:
            raise RoutingError('No route for command "%s"' % command)
        
        elif len(applicable_rules) == 1:
            log_debug("Found 1 applicable route: %s" % (applicable_rules[0].view_func.__name__))
            return self._execute(applicable_rules[0].view_func, applicable_rules[0].rule)
        
        log_debug("Found %s applicable routes" % (len(applicable_rules)))
        sorted_rules = sorted(applicable_rules, key=lambda r: (-r.match, -r.amount_arguments))        
        
        return self._execute(sorted_rules[0].view_func, sorted_rules[0].rule)
    
    def _execute(self, view_func, rule):
        
        kwargs = {}
        # add matching arguments
        for arg_name in rule.arguments:
            kwargs[arg_name] = self.args[arg_name] if arg_name in self.args else None
            
        if rule.protected:
            with SingleInstance():
                log_debug("Protected executing '%s', args: %s" % (view_func.__name__, kwargs))
                return view_func(**kwargs)
        else:
            log_debug("Executing '%s', args: %s" % (view_func.__name__, kwargs))
            return view_func(**kwargs)        


class CommandRule(object):
    
    def __init__(self, command, arguments, protected):
        self.command = command
        self.arguments = arguments
        self.protected = protected
        
class MatchingRule(object):
    
    def __init__(self, rule, view_func, amount_matching_arguments):
        self.rule = rule
        self.view_func = view_func
        self.amount_matching_arguments = amount_matching_arguments
        self.amount_arguments = len(rule.arguments)
        self.match = amount_matching_arguments / (self.amount_arguments / 100) if self.amount_arguments > 0 else 0