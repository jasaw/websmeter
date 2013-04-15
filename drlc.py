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
    def GET(self):
        web.header('Content-Type', 'application/json')
        try:
            rsp = {}
            rsp['events'] = smartmeter.smeter.smctrl.drlc_mgr.get_all_events()
            rsp['maxnumevents'] = smartmeter.smeter.smctrl.drlc_mgr.max_num_events
            rsp['status'] = 0
            return json.dumps(rsp)

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})

    def POST(self):
        web.header('Content-Type', 'application/json')
        try:
            status = False
            action = common.getJsonArg("action", "")
            if action == 'add':
                # mandatory inputs
                device_class = common.getJsonArg("dev", None)
                if not isinstance(device_class, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed device class input"})
                ueg = common.getJsonArg("ueg", None)
                if not isinstance(ueg, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed utility enrolment group input"})
                start_time = common.getJsonArg("start", None)
                if not isinstance(start_time, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed start time input"})
                duration = common.getJsonArg("duration", None)
                if not isinstance(duration, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed duration input"})
                criticality = common.getJsonArg("criticality", None)
                if not isinstance(criticality, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed criticality input"})
                event_control = common.getJsonArg("ectrl", None)
                if not isinstance(event_control, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed event control input"})
                # optional inputs
                cto = common.getJsonArg("cto", None)
                if cto is not None and not isinstance(cto, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed cooling temp offset input"})
                hto = common.getJsonArg("hto", None)
                if hto is not None and not isinstance(hto, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed heating temp offset input"})
                ctsp = common.getJsonArg("ctsp", None)
                if ctsp is not None and not isinstance(ctsp, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed cooling temp set point input"})
                htsp = common.getJsonArg("htsp", None)
                if htsp is not None and not isinstance(htsp, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed heating temp set point input"})
                avgload = common.getJsonArg("avgload", None)
                if avgload is not None and not isinstance(avgload, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed average load input"})
                dutycycle = common.getJsonArg("dutycycle", None)
                if dutycycle is not None and not isinstance(dutycycle, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed duty cycle input"})
                # add event
                status = smartmeter.smeter.smctrl.drlc_mgr.add_event(
                    device_class=device_class, ueg=ueg, start_time=start_time,
                    duration=duration, criticality=criticality, ectrl=event_control,
                    cto=cto, hto=hto, ctsp=ctsp, htsp=htsp,
                    avgload=avgload, dutycycle=dutycycle)

            elif action == 'rm':
                event_id = common.getJsonArg("eid", None)
                if event_id is not None and not isinstance(event_id, (int,long)):
                    return json.dumps({"status": -1, "errormsg": "Malformed event ID input"})
                status = smartmeter.smeter.smctrl.drlc_mgr.rm_event(event_id)

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
