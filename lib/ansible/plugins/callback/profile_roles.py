# (C) 2017, Tennis Smith, http://github.com/gamename
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# File is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See <http://www.gnu.org/licenses/> for a copy of the
# GNU General Public License

#
# This will track the use of each role during the life of a playbook's
# execution.  The total time spent in each role will be printed at the
# end.
#
# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import collections
import time

from ansible.plugins.callback import CallbackBase
from ansible.module_utils.six import reduce

# define start time
t0 = tn = time.time()


def secondsToStr(t):
    # http://bytes.com/topic/python/answers/635958-handy-short-cut-formatting-elapsed-time-floating-point-seconds
    rediv = lambda ll, b: list(divmod(ll[0], b)) + ll[1:]
    return "%d:%02d:%02d.%03d" % tuple(
        reduce(rediv, [[t * 1000, ], 1000, 60, 60]))


def filled(msg, fchar="*"):
    if len(msg) == 0:
        width = 79
    else:
        msg = "%s " % msg
        width = 79 - len(msg)
    if width < 3:
        width = 3
    filler = fchar * width
    return "%s%s " % (msg, filler)


def timestamp(self):
    if self.current is not None:
        self.stats[self.current] = time.time() - self.stats[self.current]
        self.totals[self.current] += self.stats[self.current]


def tasktime():
    global tn
    time_current = time.strftime('%A %d %B %Y  %H:%M:%S %z')
    time_elapsed = secondsToStr(time.time() - tn)
    time_total_elapsed = secondsToStr(time.time() - t0)
    tn = time.time()
    return filled('%s (%s)%s%s' %
                  (time_current, time_elapsed, ' ' * 7, time_total_elapsed))


class CallbackModule(CallbackBase):
    """
    This callback module provides profiling for ansible roles.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'profile_roles'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        self.stats = collections.Counter()
        self.totals = collections.Counter()
        self.current = None
        super(CallbackModule, self).__init__()

    def _record_task(self, task):
        """
        Logs the start of each task
        """
        self._display.display(tasktime())
        timestamp(self)

        if task._role:
            self.current = task._role._role_name
        else:
            self.current = task.action

        self.stats[self.current] = time.time()

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._record_task(task)

    def v2_playbook_on_handler_task_start(self, task):
        self._record_task(task)

    def playbook_on_setup(self):
        self._display.display(tasktime())

    def playbook_on_stats(self, stats):
        self._display.display(tasktime())
        self._display.display(filled("", fchar="="))

        timestamp(self)
        total_time = sum(self.totals.values())

        # Print the timings starting with the largest one
        for result in self.totals.most_common():
            msg = u"{0:-<70}{1:->9}".format(result[0] + u' ',
                                            u' {0:.02f}s'.format(result[1]))
            self._display.display(msg)

        msg_total = u"{0:-<70}{1:->9}".format(u'total ',
                                              u' {0:.02f}s'.format(total_time))
        self._display.display(filled("", fchar="~"))
        self._display.display(msg_total)

