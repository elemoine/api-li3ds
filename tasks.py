# -*- coding: utf-8 -*-
from os.path import join, abspath, dirname

from invoke import run, task

HERE = abspath(join(dirname(__file__)))


@task
def clean(docs=False, bytecode=False, extra=''):
    '''Cleanup all build artifacts'''
    patterns = ['build', 'dist', 'cover', 'docs/_build', '**/*.pyc', '*.egg-info', '.tox']
    for pattern in patterns:
        print('Removing {0}'.format(pattern))
        run('cd {0} && rm -rf {1}'.format(HERE, pattern))


@task
def test():
    '''Run tests suite'''
    run('cd {0} && py.test'.format(HERE), pty=True)


@task
def tox():
    '''Run test in all Python versions'''
    run('tox', pty=True)


@task
def doc():
    '''Build the documentation'''
    run('cd {0}/doc && make html'.format(HERE), pty=True)


@task
def dist():
    '''Package for distribution'''
    run('cd {0} && python setup.py sdist bdist_wheel'.format(HERE), pty=True)


@task
def release_pypi():
    '''Upload release to pypi'''
    run('echo release to pypi')


@task(tox, doc, dist, default=True)
def all():
    pass
