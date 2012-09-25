#!/usr/bin/env python
from setuptools import setup, Command

class PyTest(Command):
	user_options = []
	def initialize_options(self):
		pass
	def finalize_options(self):
		pass
	def run(self):
		import sys, subprocess
		errno = subprocess.call([sys.executable, 'runtests.py'])
		raise SystemExit(errno)

def get_version():
	build_version = 1
	return build_version

setup(
	name='leptoid',
	version='0.0.%s' % get_version(),
	url = 'https://wiki.knewton.net/index.php/Tech',
	author='Alejandro Companioni',
	author_email='alejandro@knewton.com',
	license = 'Proprietary',
	packages=['leptoid'],
	cmdclass = {'test': PyTest},
	description = ('Library for automatically scaling instance size up or down'+
	' depending on host metrics.'),
	long_description = '\n' + open('README').read(),
)
