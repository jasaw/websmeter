"""
zigbee time manager
"""   

import time

import logger
import multiline_rsp



class ZbTimeMgr(object):

    def __init__(self):
        self.logger = logger.Logger('zbtimemgr')
        self.last_set = 0
        self.valid_duration = 60*60
        zb_epoch = (2000,1,1,0,0,0,5,1,0)
        self.zb_epoch_offset_seconds = int(time.mktime(zb_epoch))

    def force_time_set(self):
        self.last_set = 0

    def process(self):
        cmds = []
        now = time.time()
        if now - self.last_set > self.valid_duration:
            self.last_set = now
            zbtime = int(time.mktime(time.gmtime())) - self.zb_epoch_offset_seconds
            cmds.append('zcl time %d\n' % zbtime)
            #cmds.append('print time\n')
        return cmds
