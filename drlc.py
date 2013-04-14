import web
import simplejson as json

import common
from smartmeter import smartmeter
from smartmeter import logger


urls = (
    "/event", "event",
    "", "drlc"
)

render = web.template.render('templates/', base='base')
handler = web.application(urls, locals())



class drlc(object):
    def GET(self):
        return render.drlc()




class event(object):
    def POST(self):
        web.header('Content-Type', 'application/json')
        try:
            status = False
            action = common.getJsonArg("action", "")
            if action == 'add':
                #device_class=[], ueg=['ALL'],
                #start_time=0, duration=0, criticality='GREEN',
                #cto=TEMPERATURE_OFFSET_NOT_USED, hto=TEMPERATURE_OFFSET_NOT_USED,
                #ctsp=TEMPERATURE_SET_POINT_NOT_USED, htsp=TEMPERATURE_SET_POINT_NOT_USED,
                #avgload=AVERAGE_LOAD_NOT_USED, dutycycle=DUTY_CYCLE_NOT_USED,
                #ectrl=[]
                

            elif action == 'rm':
                event_id = common.getJsonArg("eid", None)
                if event_id is not None and not isinstance(event_id, (int,long)):
                    return json.dumps({"status": -1, "errormsg": "Malformed event ID input"})

            elif action == 'clear':
                status = smartmeter.smeter.smctrl.drlc_mgr.rm_all_events()

            else:
                return json.dumps({"status": -1, "errormsg": "Unsupported action"})

            if not status:
                return json.dumps({"status": -1, "errormsg": "Action failed"})
            return json.dumps({"status": 0})

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})
