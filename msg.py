import web
import simplejson as json
import string

import common
from smartmeter import smartmeter
from smartmeter import logger


urls = (
    "/action", "action",
    "", "msg"
)

render = web.template.render('templates/', base='base')
handler = web.application(urls, locals())



class msg(object):
    def GET(self):
        return render.msg()


class action(object):
    def GET(self):
        web.header('Content-Type', 'application/json')
        try:
            smartmeter.smeter.smctrl.msg_mgr.refresh_message_cache()
            rsp = smartmeter.smeter.smctrl.msg_mgr.get_message()
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
            if action == 'set':
                kwargs = {}
                msg_ctrl = common.getJsonArg("ctrl", None)
                if not isinstance(msg_ctrl, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed message control input"})
                kwargs['msg_ctrl'] = msg_ctrl
                start_time = common.getJsonArg("start", None)
                if not isinstance(start_time, (int,long)):
                    return json.dumps({"status": -1, "errormsg": "Malformed start time input"})
                kwargs['start_time'] = start_time
                duration = common.getJsonArg("duration", None)
                if not isinstance(duration, (int)):
                    return json.dumps({"status": -1, "errormsg": "Malformed duration input"})
                kwargs['duration'] = duration
                message_string = common.getJsonArg("message", None)
                # Need to check max string length?
                if not isinstance(message_string, str):
                    return json.dumps({"status": -1, "errormsg": "Malformed message input"})
                kwargs['message_string'] = message_string
                # add message
                #d = logger.Logger("msg.py")
                #d.log("going to add message")
                status = smartmeter.smeter.smctrl.msg_mgr.set_message(**kwargs)
                #d.log("status %s", status)

            elif action == 'send':
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
                for i in range(len(nodes)):
                    tmp_status = smartmeter.smeter.smctrl.msg_mgr.display_message(nodes[i], eps[i])
                    if not tmp_status:
                        status = False

            elif action == 'cancel':
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
                for i in range(len(nodes)):
                    tmp_status = smartmeter.smeter.smctrl.msg_mgr.cancel_message(nodes[i], eps[i])
                    if not tmp_status:
                        status = False

            elif action == 'clear':
                status = smartmeter.smeter.smctrl.msg_mgr.rm_message()

            else:
                return json.dumps({"status": -1, "errormsg": "Unsupported action"})

            if not status:
                return json.dumps({"status": -1, "errormsg": "Action failed"})
            return json.dumps({"status": 0})

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})
