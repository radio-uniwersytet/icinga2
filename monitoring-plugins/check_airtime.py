#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pg8000
import codecs
from sys import exit,argv

class Airtime:
    """Class for checking status and health of Airtime."""
    def __init__(self):
        super(Airtime, self).__init__()
        conn = pg8000.connect(user="airtime",password="airtime")
        self.cursor = conn.cursor()

    def critical(self,output):
        print(output)
        exit(2)

    def ok(self,output):
        print(output)
        exit(0)

    def warning(self,output):
        print(output)
        exit(1)

    def unknown(self,output):
        print(output)
        exit(3)

    def cc_pref_get(self,keystr):
        if not keystr in ('master_dj', 'live_dj'):
            self.unknown("Wrong argument, not such source {}".format(keystr))

        self.cursor.execute("SELECT valstr FROM cc_pref WHERE keystr = '{}'".format(keystr))
        if self.cursor.fetchone()[0] == 'true':
            return True
        else:
            return False

    def check_source(self,source='master_dj'):
            if self.cc_pref_get(source):
                self.ok("Source {} is online.".format(source))
            else:
                self.critical("Source {} is offline!".format(source))

airtime_instance = Airtime()

if len(argv) == 2:
    airtime_instance.check_source(argv[1])
else:
    airtime_instance.check_source()
