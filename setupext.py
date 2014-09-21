import os.path

from distutils import dir_util
import setuptools


class Janitor(setuptools.Command):
    _top_dir = os.path.abspath(os.path.dirname(__file__))

    description = 'remove generated and/or temporary files'
    user_options = [
        ('all', 'a', 'remove all generated files'),
        ('dist', 'd', 'remove distribution directory'),
        ('eggs', 'e', 'remove egg and egg-info directories'),
        ('pycache', 'p', 'remove __pycache__ directories'),
        ('environment', 'E', 'remove environment'),
    ]
    boolean_options = ['all', 'dist', 'eggs', 'pycache', 'environment']

    def initialize_options(self):
        for name in self.boolean_options:
            setattr(self, name, False)

    def finalize_options(self):
        if self.all:
            for name in self.boolean_options:
                setattr(self, name, True)

    def run(self):
        self._remove_tree('build')
        if self.dist:
            self._remove_tree('dist')
        if self.environment:
            self._remove_tree('env')
        if self.eggs:
            for name in os.listdir(self._top_dir):
                if name.endswith('.egg') or name.endswith('.egg-info'):
                    self._remove_tree(name)
        if self.pycache:
            for root, dirs, _ in os.walk(self._top_dir):
                if '__pycache__' in dirs:
                    self._remove_tree(os.path.join(root, '__pycache__'))

    def _remove_tree(self, sub_dir):
        path = os.path.join(self._top_dir, sub_dir)
        if os.path.exists(path):
            dir_util.remove_tree(path, verbose=self.verbose,
                                 dry_run=self.dry_run)
