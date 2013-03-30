import web
import simplejson as json

import common
from smartmeter import smartmeter
from smartmeter import logger


urls = (
    "/mkdrlc", "mkdrlc",
    "", "drlc"
)

render = web.template.render('templates/', base='base')
handler = web.application(urls, locals())



class drlc(object):
    def GET(self):
        return render.drlc()



class mkdrlc(object):
    def POST(self):
        web.header('Content-Type', 'application/json')
        try:
            avgload = getJsonArg("avgload", "255")
            if not avgload.isdigit():
                return json.dumps({"status": -1, "errormsg": "Average load must be a number"})
            if not (0 <= int(avgload) <= 100) and int(avgload) != 255:
                return json.dumps({"status": -1, "errormsg": "Average load must be between 0 to 100"})
            return json.dumps({"status": 0})

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})

