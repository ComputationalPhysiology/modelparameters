#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Johan Hake (hake.dev@gmail.com)"
__copyright__ = "Copyright (C) 2012-2015 " + __author__
__date__ = "2012-05-07 -- 2015-01-09"
__license__  = "GNU LGPL Version 3.0 or later"

# System imports
from setuptools import setup, Command

class run_tests(Command):
    """
    Runs all tests under the modelparameters/ folder
    """

    description = "run all tests"
    user_options = []  # distutils complains if this is not here.

    def __init__(self, *args):
        self.args = args[0] # so we can pass it to other classes
        Command.__init__(self, *args)

    def initialize_options(self):  # distutils wants this
        pass

    def finalize_options(self):    # this too
        pass

    def run(self):
        import os
        os.system("python utils/run_tests.py")
        
class clean(Command):
    """
    Cleans *.pyc so you should get the same copy as is in the VCS.
    """

    description = "remove build files"
    user_options = [("all","a","the same")]

    def initialize_options(self):
        self.all = None

    def finalize_options(self):
        pass

    def run(self):
        import os
        os.system("utils/clean-files")


# Version number
major = 1
minor = 0

setup(name = "modelparameters",
      version = "{0}.{1}".format(major, minor),
      description = """
A module providing parameter structure for physical modeling
      """,
      author = __author__.split("(")[0],
      author_email = __author__.split("(")[1][:-1],
      install_requires=["sympy<=0.7.7",
                        "numpy>=1.5",
                        "six"],
      packages = ["modelparameters", "modelparameters.tests"],
      cmdclass = {'test' : run_tests,
                  'clean' : clean,
                  },
      )
