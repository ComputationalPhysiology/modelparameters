__author__ = "Johan Hake <hake.dev@gmail.com>"
__date__ = "2012-07-05 -- 2012-07-05"
__copyright__ = "Copyright (C) 2012 " + __author__
__license__  = "GNU LGPL Version 3.0 or later"

formats = dict(
    float="g",
    num_decimals=2)

def float_format():
    return dict(ff=formats["float"]+formats["num_decimals"])
