"Run all tests"

__author__ = "Johan Hake (hake.dev@gmail.com)"
__date__ = "2012-08-15 -- 2012-08-15"
__copyright__ = "Copyright (C) 2012 " + __author__
__license__  = "GNU LGPL version 3.0"

from modelparameters.commands import get_status_output

import re, sys, os

failed = []

num_tests = 0
timing = 0.0

python3 = sys.version.startswith('3')

# Run tests
for dirpath, dirnames, filenames in os.walk("../modelparameters"):
    if '.tox' in dirpath:
        continue
    
    if os.path.basename(dirpath) == "tests":
        
        print("")
        print("Running tests in: %s" % dirpath)
        print("----------------------------------------------------------------------")
        for test in filenames:
            if "test_" not in test:
                continue
            fail, output = get_status_output("python %s" % os.path.join(dirpath, test))
            if python3:
                output = output.decode()
            if output == '':
                continue
            
            num_tests += int(re.findall("Ran (\d+) tests", output)[0])
            timing += float(re.findall("tests in ([\d\.]+)s", output)[0])
            if fail:
                failed.append(output)

print()
print("----------------------------------------------------------------------")
print("Ran %d tests in %.3fs" % (num_tests, timing))
if failed:
    for output in failed:
        print(output)

sys.exit(len(failed))
