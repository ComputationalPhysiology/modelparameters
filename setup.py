#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Johan Hake (hake.dev@gmail.com)"
__copyright__ = "Copyright (C) 2010 " + __author__
__date__ = "2012-05-07 -- 2012-06-30"
__license__  = "GNU LGPL Version 3.0 or later"


# System imports
from distutils.core import setup

# Version number
major = 0
minor = 1

setup(name = "modelparameters",
      version = "{0}.{1}".format(major, minor),
      description = """
      A module providing parameter structure for physical modeling
      """,
      author = __author__.split("(")[0],
      author_email = __author__.split("(")[1][:-1],
      packages = ["modelparameters"],
#      package_dir = {"pulse": "src"},
#      scripts = scripts,
      )
