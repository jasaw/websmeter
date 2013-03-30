""" Wrapper for running the smartmeterctrl in a thread """

import sys
#import exceptions
import threading

import logger
import smartmeterctrl


class SmartMeter(threading.Thread):

    def __init__(self, bin_path, device_path):
        threading.Thread.__init__(self)
        self.daemon = True
        self.terminate = False
        self.smctrl = smartmeterctrl.SmartMeterCtrl(bin_path, device_path)
        self.smctrl.start()

    def run(self):
        try:
            while not self.terminate:
                self.smctrl.run_once()
        except Exception, e:
            logger.print_trace(e)
            sys.exit(1)

    def stop(self):
        self.terminate = True
        self.smctrl.stop()



smeter = None


#if __name__ == "__main__":
#    smeter = SmartMeter('smartmeter', '/dev/ttyUSB0')
#    smeter.start()
#    smeter.join(5)
#    smeter.smctrl.key_mgr.add_link_key("8CEEC60101000051", "BD29ED98237F6B7B8D02C15D04DE1EDB")
#    smeter.join(5)
#    smeter.smctrl.key_mgr.rm_link_key("8CEEC60101000051")
#    smeter.join(20)
#    smeter.stop()
#    smeter.join()
