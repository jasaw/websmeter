import web
import simplejson as json
import string

import common
from smartmeter import smartmeter
from smartmeter import logger


urls = (
    "/getinfo", "getinfo",
    "/action", "action",
    "", "nwk"
)

render = web.template.render('templates/', base='base')
handler = web.application(urls, locals())



class nwk(object):
    def GET(self):
        return render.nwk()


class getinfo(object):
    def GET(self):
        web.header('Content-Type', 'application/json')
        try:
            rsp = smartmeter.smeter.smctrl.nwk_mgr.get_nwk_info()
            rsp['status'] = 0
            return json.dumps(rsp)

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})


class action(object):
    def POST(self):
        web.header('Content-Type', 'application/json')
        try:
            status = False
            action = common.getJsonArg("action", "")
            if action == 'form' or action == 'join':
                channel = common.getJsonArg("channel", None)
                power = common.getJsonArg("power", None)
                panid = common.getJsonArg("panid", None)
                #d = logger.Logger("nwk.py")
                #d.log("%s, %s, %s", str(type(channel)), str(type(power)), str(type(panid)))
                if channel is not None and not isinstance(channel, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed channel input"})
                if power is not None and not isinstance(power, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed power input"})
                if panid is not None and not isinstance(panid, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed PAN ID input"})
                if action == 'form':
                    status = smartmeter.smeter.smctrl.nwk_mgr.form_network(radio_channel=channel, radio_power=power, pan_id=panid)
                else:
                    status = smartmeter.smeter.smctrl.nwk_mgr.join_network(radio_channel=channel, radio_power=power, pan_id=panid)

            elif action == 'pjoin':
                duration = common.getJsonArg("duration", None)
                bcast = common.getJsonArg("broadcast", None)
                if not isinstance(duration, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed duration input"})
                if not isinstance(bcast, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed broadcast input"})
                if bcast > 0:
                    broadcast = True
                else:
                    broadcast = False
                status = smartmeter.smeter.smctrl.nwk_mgr.permit_join(duration=duration, broadcast=broadcast)

            elif action == 'leave':
                status = smartmeter.smeter.smctrl.nwk_mgr.leave_network()

            elif action == 'setexpanid':
                expanid = common.getJsonArg("expanid", "")
                if not isinstance(expanid, str) or len(expanid) != 16 or not all(c in string.hexdigits for c in expanid):
                    return json.dumps({"status": -1, "errormsg": "Malformed input"})
                status = smartmeter.smeter.smctrl.nwk_mgr.set_extended_pan_id(expanid)

            else:
                return json.dumps({"status": -1, "errormsg": "Unsupported action"})

            if not status:
                return json.dumps({"status": -1, "errormsg": "Action failed"})
            return json.dumps({"status": 0})

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})
