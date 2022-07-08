#!/usr/bin/env python3
import sys
import os
from os.path import join as pjoin
from glob import glob
from setuptools import setup
from distutils.core import Command
from distutils.spawn import spawn
import msv


class BuildLib(Command):
    description = 'Call Nuitka to build lib'
    user_options = []

    initialize_options = finalize_options = lambda self: None

    def run(self):
        spawn([sys.executable, '-m', 'nuitka', '--output-dir=build', '--show-modules', '--lto=yes', '--module', 'msv', '--include-package=msv', '--no-pyi-file'])


class BuildQt(Command):
    description = 'build Qt files(.ui .rc)'
    user_options = [('ui', 'u', 'compile ui files only'),
                    ('rc', 'r', 'compile rc files only')]

    def initialize_options(self):
        # noinspection PyAttributeOutsideInit
        self.ui = self.rc = False
        self.force = False

    def finalize_options(self): pass

    def run(self):
        methods = ('ui', 'rc')
        opts = tuple(filter(lambda x: getattr(self, x), methods))
        if opts:
            self.force = True
        else:
            opts = methods  # run all methods if no options passed

        for i in opts:
            getattr(self, 'compile_'+i)()

    def compile_ui(self):
        for src in glob(pjoin('msv', 'ui', '*.ui')):
            dst = src.replace('.ui', '_ui.py')
            if self.force or (not os.path.isfile(dst) or
                              os.path.getmtime(src) > os.path.getmtime(dst)):
                spawn(['pyuic5', '--from-imports', '-o', dst, src])

    @staticmethod
    def compile_rc():
        spawn(['pyrcc5', pjoin('msv', 'resources', 'resources.qrc'), '-o',
               pjoin('msv', 'resources_rc.py')])



#nuitka --standalone --output-dir=out --windows-uac-admin --windows-icon-from-ico=msv/resources/appicon.ico --plugin-enable=pyside2 --plugin-enable=numpy --plugin-enable=multiprocessing --show-modules --nofollow-import-to=ipython,setuptools,cffi,pycparser --python-flag=no_site --lto msv.py
# nuitka --output-dir=build --show-modules --lto --module msv --include-package=msv --no-pyi-file

# fix env variables for PySide tools
# if sys.platform == 'win32':
#     os.environ['PATH'] += (';' + pjoin(sys.exec_prefix, 'Scripts') +
#                            ';' + pjoin(sys.exec_prefix, 'lib', 'site-packages', 'PySide'))


# PySide installed by linux package manager will not recognized by setuptools, so requires not added.
setup(name='MSV',
      author='krrr',
      author_email='guogaishiwo@gmail.com',
      version=msv.__version__,
      description='',
      url='https://blog.hazama.cc',
      packages=['msv', 'hazama.ui'],
      cmdclass={'build_lib': BuildLib, 'build_qt': BuildQt},
      zip_safe=False,
      entry_points={'gui_scripts': ['msv = msv:main_entry']})
