#!/usr/bin/env python

import web
import os

from smartmeter import smartmeter
from smartmeter import logger
import drlc
import keys
import nwk

# to avoid any path issues, "cd" to the web root.
web_root = os.path.abspath(os.path.dirname(__file__))
os.chdir(web_root)

urls = (
    "/(.*)/", "redirect",
    "/drlc", drlc.handler,
    "/keys", keys.handler,
    "/nwk", nwk.handler,
    "/", "index"
)

render = web.template.render('templates/', base='base')
handler = web.application(urls, locals())


class redirect(object):
    def GET(self, path):
        web.seeother('/' + path)


class index(object):
    def GET(self):
        return render.index()


if __name__ == "__main__":
    #logger.Logger.use_syslog = True
    smartmeter.smeter = smartmeter.SmartMeter('smartmeter', '/dev/ttyUSB0')
    smartmeter.smeter.start()
    handler.run()
    smartmeter.smeter.stop()
    smartmeter.smeter.join()
