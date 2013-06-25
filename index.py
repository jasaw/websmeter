import web
import os

from smartmeter import smartmeter
from smartmeter import logger
import diag
import drlc
import keys
import nwk
import msg

# to avoid any path issues, "cd" to the web root.
web_root = os.path.abspath(os.path.dirname(__file__))
os.chdir(web_root)

urls = (
    "/(.*)/", "redirect",
    "/diag", diag.handler,
    "/drlc", drlc.handler,
    "/keys", keys.handler,
    "/nwk", nwk.handler,
    "/msg", msg.handler,
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


def run(bin_path='smartmeter', dev_path='/dev/ttyUSB0', use_syslog=True, debug_mode=True):
    logger.Logger.use_syslog = use_syslog
    smartmeter.smeter = smartmeter.SmartMeter(bin_path, dev_path, debug_mode=debug_mode)
    smartmeter.smeter.start()
    handler.run()
    smartmeter.smeter.stop()
    smartmeter.smeter.join()
