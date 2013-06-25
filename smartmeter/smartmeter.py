""" Wrapper for running the smartmeterctrl in a thread """

import sys
#import exceptions
import threading

import logger
import smartmeterctrl


class SmartMeter(threading.Thread):

    def __init__(self, bin_path, device_path, debug_mode=True):
        threading.Thread.__init__(self)
        self.debug_mode = debug_mode
        self.daemon = True
        self.terminate = False
        self.smctrl = smartmeterctrl.SmartMeterCtrl(bin_path, device_path, debug_mode=debug_mode)
        self.smctrl.start()

    def run(self):
        while not self.terminate:
            try:
                self.smctrl.run_once()
            except Exception, e:
                logger.print_trace(e)
                if self.debug_mode:
                    sys.exit(1)

    def stop(self):
        self.terminate = True
        self.smctrl.stop()



smeter = None
