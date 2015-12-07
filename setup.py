import glob
import logging
import subprocess
import sys
import os
import distutils
from distutils.cmd import Command
from distutils.core import setup
from distutils.extension import Extension

import pystache
import yaml
from Cython.Build import cythonize

INC, LIB = [], []

# MacPorts
if sys.platform == 'darwin' and os.path.isdir('/opt/local/lib'):
    INC.append('/opt/local/include')
    LIB.append('/opt/local/lib')

# Homebrew
if sys.platform == 'darwin' and os.path.isdir('/usr/local/lib'):
    INC.append('/usr/local/include')
    LIB.append('/usr/local/lib')


ext_modules = [
    Extension(name='fst._fst',
              sources=['fst/_fst.pyx.tpl', 'fst/libfst.pxd.tpl', 'fst/types.yml'],
              include_dirs=INC,
              library_dirs=LIB)
]


def pystache_render(template_filename, context_filenames, rendered_filename):
    with open(rendered_filename, 'w') as rendered:
        with open(template_filename) as template:
            contexts = []
            for context_filename in context_filenames:
                with open(context_filename) as context:
                    contexts += list(yaml.load_all(context))

            rendered.write(pystache.render(template.read(), context=contexts[0]))


def mustache_cmd_render(template_filename, context_filenames, rendered_filename, mustache_cmd='mustache'):
    cmd = 'cat {yamls} | {mustache_cmd} - {template} > {rendered}'.format(yamls=' '.join(context_filenames),
                                                                          template=template_filename,
                                                                          rendered=rendered_filename,
                                                                          mustache_cmd=mustache_cmd)
    logging.info('Running command: %s' % str(cmd))
    subprocess.check_call(cmd, shell=True)


def mustachize(modules, mustache_command=''):
    """Run command."""
    for module in modules:
        sources = module.sources

        context_filenames = [source for source in sources if os.path.splitext(source)[-1] in {'.yml'}]
        templates = [source for source in sources if os.path.splitext(source)[-1] in {'.tpl'}]
        other = set(sources) - set(context_filenames) - set(templates)

        new_sources = []
        for template in templates:
            rendered, new_ext = os.path.splitext(template)

            if mustache_command:
                mustache_cmd_render(template, context_filenames, rendered, mustache_cmd=mustache_command)
            else:
                pystache_render(template, context_filenames, rendered)

            _, new_ext = os.path.splitext(rendered)
            if new_ext in {'.pyx'}:
                new_sources.append(rendered)

        module.sources[:] = list(other) + new_sources

    return modules


long_description = """
pyfst
=====

A Python interface for the OpenFst_ library.

.. _OpenFst: http://www.openfst.org

- Documentation: http://pyfst.github.io
- Source code: https://github.com/vchahun/pyfst

Example usage::

    import fst

    t = fst.Transducer()

    t.add_arc(0, 1, 'a', 'A', 0.5)
    t.add_arc(0, 1, 'b', 'B', 1.5)
    t.add_arc(1, 2, 'c', 'C', 2.5)

    t[2].final = 3.5

    t.shortest_path() # 2 -(a:A/0.5)-> 1 -(c:C/2.5)-> 0/3.5 

"""

setup(
    name='pyfst',
    version='0.2.3',
    url='http://pyfst.github.io',
    author='Victor Chahuneau',
    description='A Python interface to OpenFst.',
    long_description=long_description,
    classifiers=['Topic :: Text Processing :: Linguistic',
                 'Programming Language :: Cython',
                 'Programming Language :: C++',
                 'Intended Audience :: Education',
                 'Intended Audience :: Science/Research'],
    packages=['fst'],
    ext_modules=cythonize(mustachize(ext_modules)),
)
