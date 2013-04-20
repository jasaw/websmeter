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
            #d = logger.Logger("drlc.py")
            #d.log("rsp: %s", rsp)
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
                kwargs = {}
                # mandatory inputs
                device_class = common.getJsonArg("dev", None)
                if not isinstance(device_class, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed device class input"})
                kwargs['dev'] = device_class
                ueg = common.getJsonArg("ueg", None)
                if not isinstance(ueg, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed utility enrolment group input"})
                kwargs['ueg'] = ueg
                start_time = common.getJsonArg("start", None)
                if not isinstance(start_time, (int,long)):
                    return json.dumps({"status": -1, "errormsg": "Malformed start time input"})
                kwargs['start_time'] = start_time
                duration = common.getJsonArg("duration", None)
                if not isinstance(duration, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed duration input"})
                kwargs['duration'] = duration
                criticality = common.getJsonArg("criticality", None)
                if not isinstance(criticality, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed criticality input"})
                kwargs['criticality'] = criticality
                event_control = common.getJsonArg("ectrl", None)
                if not isinstance(event_control, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed event control input"})
                kwargs['ectrl'] = event_control
                # optional inputs
                cto = common.getJsonArg("cto", None)
                if cto is not None:
                    if not isinstance(cto, (int)):
                        return json.dumps({"status": -1, "errormsg": "Malformed cooling temp offset input"})
                    else:
                        kwargs['cto'] = cto
                hto = common.getJsonArg("hto", None)
                if hto is not None:
                    if not isinstance(hto, (int)):
                        return json.dumps({"status": -1, "errormsg": "Malformed heating temp offset input"})
                    else:
                        kwargs['hto'] = hto
                ctsp = common.getJsonArg("ctsp", None)
                if ctsp is not None:
                    if not isinstance(ctsp, (int)):
                        return json.dumps({"status": -1, "errormsg": "Malformed cooling temp set point input"})
                    else:
                        kwargs['ctsp'] = ctsp
                htsp = common.getJsonArg("htsp", None)
                if htsp is not None:
                    if not isinstance(htsp, (int)):
                        return json.dumps({"status": -1, "errormsg": "Malformed heating temp set point input"})
                    else:
                        kwargs['htsp'] = htsp
                avgload = common.getJsonArg("avgload", None)
                if avgload is not None:
                    if not isinstance(avgload, (int)):
                        return json.dumps({"status": -1, "errormsg": "Malformed average load input"})
                    else:
                        kwargs['avgload'] = avgload
                dutycycle = common.getJsonArg("dutycycle", None)
                if dutycycle is not None:
                    if not isinstance(dutycycle, (int)):
                        return json.dumps({"status": -1, "errormsg": "Malformed duty cycle input"})
                    else:
                        kwargs['dutycycle'] = dutycycle
                # add event
                #d = logger.Logger("drlc.py")
                #d.log("going to add event")
                status = smartmeter.smeter.smctrl.drlc_mgr.add_event(**kwargs)
                #d.log("status %s", status)

            elif action == 'send':
                event_ids = common.getJsonArg("eids", None)
                if not isinstance(event_ids, list):
                    return json.dumps({"status": -1, "errormsg": "Malformed event ID input"})
                for eid in event_ids:
                    if not isinstance(eid, (int,long)):
                        return json.dumps({"status": -1, "errormsg": "Malformed event ID input"})
                nodes = common.getJsonArg("nodes", None)
                if not isinstance(nodes, list):
                    return json.dumps({"status": -1, "errormsg": "Malformed Node ID input"})
                for n in nodes:
                    if not isinstance(n, (int)):
                        return json.dumps({"status": -1, "errormsg": "Malformed Node ID input"})
                eps = common.getJsonArg("eps", None)
                if not isinstance(eps, list):
                    return json.dumps({"status": -1, "errormsg": "Malformed End Point input"})
                for ep in eps:
                    if not isinstance(ep, (int)):
                        return json.dumps({"status": -1, "errormsg": "Malformed End Point input"})
                if len(nodes) != len(eps):
                    return json.dumps({"status": -1, "errormsg": "Malformed Node ID and End Point input"})

                status = True
                for eid in event_ids:
                    for i in range(len(nodes)):
                        tmp_status = smartmeter.smeter.smctrl.drlc_mgr.send_event(eid, nodes[i], eps[i])
                        if not tmp_status:
                            status = False

            elif action == 'rm':
                event_ids = common.getJsonArg("eids", None)
                if not isinstance(event_ids, list):
                    return json.dumps({"status": -1, "errormsg": "Malformed event ID input"})
                for eid in event_ids:
                    if not isinstance(eid, (int,long)):
                        return json.dumps({"status": -1, "errormsg": "Malformed event ID input"})
                status = True
                for eid in event_ids:
                    tmp_status = smartmeter.smeter.smctrl.drlc_mgr.rm_event(eid)
                    if not tmp_status:
                        status = False

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
