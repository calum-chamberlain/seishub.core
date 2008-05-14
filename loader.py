# -*- coding: utf-8 -*-

import os
import sys

from glob import glob
import imp
import pkg_resources #@UnresolvedImport 
from pkg_resources import working_set, DistributionNotFound #@UnresolvedImport
from pkg_resources import VersionConflict, UnknownExtra #@UnresolvedImport

__all__ = ['ComponentLoader']


class ComponentLoader(object):
    """Load all plugin components found on the given search path."""
    
    def __init__(self, env):
        self.env = env
        extra_path = env.config.get('seishub', 'plugins_dir')
        # add plug-in directory
        plugins_dir = os.path.join(env.config.path, 'plugins')
        search_path = [plugins_dir,]
        # add user defined paths
        if extra_path:
            search_path += list((extra_path,))
        
        self._loadPyFiles(search_path)
        self._loadEggs('seishub.plugins', search_path)
    
    def _enablePlugin(self, module):
        """Enable the given plugin module by adding an entry to the 
        configuration.
        """
        if module + '.*' not in self.env.config['components']:
            self.env.config['components'].set(module + '.*', 'enabled')

    def _loadEggs(self, entry_point_name, search_path):
        """Loader that loads any eggs on the search path and `sys.path`."""
        # add system paths
        search_path += list(sys.path)
        
        distributions, errors = working_set.find_plugins(
            pkg_resources.Environment(search_path)
        )
        for dist in distributions:
            self.env.log.debug('Processing egg %s from %s' % 
                               (dist, dist.location))
            working_set.add(dist)
        
        def _logError(item, e):
            if isinstance(e, DistributionNotFound):
                self.env.log.warn('Skipping "%s": ("%s" not found)' % 
                                  (item, e), e)
            elif isinstance(e, VersionConflict):
                self.env.log.error('Skipping "%s": (version conflict "%s")' 
                                   % (item, e), e)
            elif isinstance(e, UnknownExtra):
                self.env.log.error('Skipping "%s": (unknown extra "%s")' % 
                                   (item, e), e)
            elif isinstance(e, ImportError):
                self.env.log.error('Skipping "%s": (can\'t import "%s")' % 
                                   (item, e), e)
            else:
                self.env.log.error('Skipping "%s": (error "%s")' % 
                                   (item, e), e)
        
        for dist, e in errors.iteritems():
            _logError(dist, e)
        
        for entry in working_set.iter_entry_points(entry_point_name):
            self.env.log.info('Loading egg %s from %s' % (entry.name,
                              entry.dist.location))
            try:
                entry.load(require=True)
            except (ImportError, DistributionNotFound, VersionConflict,
                    UnknownExtra), e:
                _logError(entry, e)
    
    def _loadPyFiles(self, search_path):
        """Loader that look for Python source files in the plug-in directories,
        which simply get imported, thereby registering them with the component
        manager if they define any components.
        """
        for path in search_path:
            plugin_files = glob(os.path.join(path, '*'))
            for plugin_file in plugin_files:
                if not os.path.isdir(plugin_file):
                    continue
                try:
                    plugin_name = os.path.basename(plugin_file)
                    plugin_file += os.sep+'__init__.py'
                    self.env.log.info('Loading plug-in %s from %s' % 
                                      (plugin_name, plugin_file))
                    if plugin_name not in sys.modules:
                        imp.load_source(plugin_name, plugin_file)
                except Exception, e:
                    self.env.log.error('Failed to load plug-in from %s' % 
                                       plugin_file, e)
