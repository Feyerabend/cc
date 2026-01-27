#!/usr/bin/env python3

import os
import sys
import importlib.util
import importlib
from typing import List, Callable, Dict, Any

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, plugin_function


class PluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.execution_order: List[str] = []
        self._dependency_resolved = False
    
    def register(self, plugin: Plugin):
        self.plugins[plugin.name] = plugin
        self._dependency_resolved = False
        if plugin.name not in self.execution_order:
            self.execution_order.append(plugin.name)
        print(f"Registered plugin: {plugin.name}")
    
    def register_function(self, name: str, func: Callable, description: str = "", 
                         version: str = "1.0", dependencies: List[str] = None):
        class FunctionPlugin(Plugin):
            def __init__(self, name, func, description, version, dependencies):
                super().__init__(name, description, version)
                self.func = func
                self.dependencies = dependencies or []
            
            def run(self, ast, context, messages):
                return self.func(ast, context, messages)
        
        plugin = FunctionPlugin(name, func, description, version, dependencies or [])
        self.register(plugin)

    def resolve_dependencies(self) -> List[str]:
        if self._dependency_resolved:
            return self.execution_order
        
        # Simple topological sort for dependency resolution
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving plugin '{plugin_name}'")
            if plugin_name in visited:
                return
            
            if plugin_name not in self.plugins:
                raise ValueError(f"Plugin '{plugin_name}' not found (required by dependencies)")
            
            temp_visited.add(plugin_name)
            plugin = self.plugins[plugin_name]
            
            # Visit dependencies first
            for dep in plugin.dependencies:
                visit(dep)
            
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            result.append(plugin_name)
        
        # Visit all plugins
        for plugin_name in list(self.plugins.keys()):
            if plugin_name not in visited:
                visit(plugin_name)
        
        self.execution_order = result
        self._dependency_resolved = True
        return result

    # manual dependency resolution
    def set_order(self, order: List[str]):
        for name in order:
            if name not in self.plugins:
                raise ValueError(f"Plugin '{name}' not found")
        self.execution_order = order
        self._dependency_resolved = True
    
    def enable_plugin(self, name: str, enabled: bool = True):
        if name in self.plugins:
            self.plugins[name].enabled = enabled
    
    def list_plugins(self) -> List[dict]:
        return [plugin.get_info() for plugin in self.plugins.values()]
    
    def run_all(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> CompilerContext:        
        try:
            execution_order = self.resolve_dependencies()
        except ValueError as e:
            messages.error(f"Plugin dependency error: {e}", source="PluginRegistry")
            return context
        
        for plugin_name in execution_order:
            plugin = self.plugins[plugin_name]
            if not plugin.enabled:
                messages.debug(f"Skipping disabled plugin: {plugin_name}")
                continue
                
            messages.info(f"Running plugin: {plugin_name}")
            try:
                result = plugin.run(ast, context, messages)
                if result:
                    context.plugin_results[plugin_name] = result
                    messages.debug(f"Plugin '{plugin_name}' completed successfully")
            except Exception as e:
                messages.error(f"Plugin '{plugin_name}' failed: {e}", source="PluginRegistry")
                # Continue with other plugins even if one fails
                import traceback
                if messages.debug_enabled:
                    messages.debug(f"Full error trace: {traceback.format_exc()}")
        
        return context
    
    def load_from_directory(self, directory: str, messages: MessageCollector = None):
        if not os.path.exists(directory):
            if messages:
                messages.warning(f"Plugin directory not found: {directory}")
            return
        
        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                filepath = os.path.join(directory, filename)
                self.load_from_file(filepath, messages)
    
    def load_from_file(self, filepath: str, messages: MessageCollector = None):
        if not os.path.exists(filepath):
            if messages:
                messages.warning(f"Plugin file not found: {filepath}")
            return
        
        try:
            # Get the module name from the file path
            module_name = os.path.splitext(os.path.basename(filepath))[0]
            
            # Create a module spec
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                if messages:
                    messages.error(f"Could not load plugin file: {filepath}")
                return
            
            # Create the module
            module = importlib.util.module_from_spec(spec)
            
            # Make our plugin system available to the module by injecting into sys.modules
            # This ensures that when the plugin imports from compiler_core,
            # it gets the right classes .. and functions
            current_module = sys.modules[__name__]
            compiler_core_module = sys.modules.get('compiler_core')
            
            # Inject all necessary classes and functions into the module's globals
            module.Plugin = Plugin
            module.plugin_function = plugin_function
            module.ASTNode = ASTNode
            module.CompilerContext = CompilerContext
            module.MessageCollector = MessageCollector
            
            # Import all AST node types and other necessary classes
            # The most important deal in this is to ensure that all
            # necessary components are available to the plugin
            if compiler_core_module:
                for attr_name in dir(compiler_core_module):
                    attr = getattr(compiler_core_module, attr_name)
                    if (isinstance(attr, type) and 
                        (attr_name.endswith('Node') or attr_name in ['Visitor', 'MessageLevel', 'CompilerMessage'])):
                        setattr(module, attr_name, attr)
            
            # Execute the module
            spec.loader.exec_module(module)
            
            # Look for plugins in the module
            loaded_count = 0
            
            # Scan the module for plugin classes and functions
            for attr_name in dir(module):
                # Skip private attributes
                if attr_name.startswith('_'):
                    continue
                    
                try:
                    attr = getattr(module, attr_name)
                    
                    # Check for plugin classes
                    if (isinstance(attr, type) and 
                        issubclass(attr, Plugin) and 
                        attr != Plugin and
                        not attr_name.startswith('_')):
                        
                        # Instantiate and register the plugin class
                        plugin_instance = attr()
                        self.register(plugin_instance)
                        loaded_count += 1
                        if messages:
                            messages.info(f"Loaded plugin class: {plugin_instance.name}")
                    
                    # Check for plugin functions
                    elif (callable(attr) and 
                        hasattr(attr, '_is_plugin') and
                        not attr_name.startswith('_')):
                        
                        # Register functions marked as plugins
                        self.register_function(
                            attr._plugin_name,
                            attr, 
                            attr._plugin_description,
                            attr._plugin_version,
                            attr._plugin_dependencies
                        )
                        loaded_count += 1
                        if messages:
                            messages.info(f"Loaded plugin function: {attr._plugin_name}")
                            
                except Exception as e:
                    if messages:
                        messages.warning(f"Failed to load plugin '{attr_name}': {e}")
                    # Print the full error for debugging
                    if messages and messages.debug_enabled:
                        import traceback
                        messages.debug(f"Full error trace: {traceback.format_exc()}")
            
            if messages:
                if loaded_count > 0:
                    messages.info(f"Successfully loaded {loaded_count} plugin(s) from {os.path.basename(filepath)}")
                else:
                    messages.warning(f"No valid plugins found in {os.path.basename(filepath)}")
                
        except Exception as e:
            if messages:
                messages.error(f"Failed to load plugin file {filepath}: {e}")
            # Print full error for debugging
            if messages and messages.debug_enabled:
                import traceback
                messages.debug(f"Full error trace: {traceback.format_exc()}")

