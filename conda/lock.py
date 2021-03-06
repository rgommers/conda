# (c) 2012-2013 Continuum Analytics, Inc. / http://continuum.io
# All Rights Reserved
#
# conda is distributed under the terms of the BSD 3-clause license.
# Consult LICENSE.txt or http://opensource.org/licenses/BSD-3-Clause.

"""
Tools for working with locks

A lock is just an empty directory. We use directories because this lets us use
the race condition-proof os.makedirs.

For now, there is one global lock for all of conda, because some things happen
globally (such as downloading packages).

We don't raise an error if the lock is named with the current PID
"""

import os
from os.path import join
import glob


LOCKFN = '.conda_lock'


class Locked(object):
    """
    Context manager to handle locks.
    """
    def __init__(self, path):
        self.path = path
        self.end = "-" + str(os.getpid())
        self.lock_path = join(self.path, LOCKFN + self.end)
        self.pattern = join(self.path, LOCKFN + '-*')
        self.remove = True

    def __enter__(self):
        files = glob.glob(self.pattern)
        if files and not files[0].endswith(self.end):
            # Keep the string "LOCKERROR" in this string so that external
            # programs can look for it.
            raise RuntimeError("""\
LOCKERROR: It looks like conda is already doing something.
The lock %s was found. Wait for it to finish before continuing.
If you are sure that conda is not running, remove it and try again.
You can also use: $ conda clean --lock""" % self.lock_path)

        if not files:
            try:
                os.makedirs(self.lock_path)
            except OSError:
                pass
        else: # PID lock already here --- someone else will remove it.
            self.remove = False

    def __exit__(self, exc_type, exc_value, traceback):
        if self.remove:
            for path in self.lock_path, self.path:
                try:
                    os.rmdir(path)
                except OSError:
                    pass
