import web
import simplejson as json

import common
from smartmeter import smartmeter
from smartmeter import logger


urls = (
    "/action", "action",
    "", "diag"
)

render = web.template.render('templates/', base='base')
handler = web.application(urls, locals())



class diag(object):
    def GET(self):
        return render.diag()




class action(object):
    def GET(self):
        web.header('Content-Type', 'application/json')
        try:
            smartmeter.smeter.smctrl.diag_mgr.refresh_diag_info()
            # TODO: wait for refresh to finish?
            rsp = {}
            rsp['child'] = smartmeter.smeter.smctrl.diag_mgr.get_child_table()
            rsp['childmaxsize'] = smartmeter.smeter.smctrl.diag_mgr.child_table_max_num_entries
            rsp['neighbour'] = smartmeter.smeter.smctrl.diag_mgr.get_neighbour_table()
            rsp['neighbourmaxsize'] = smartmeter.smeter.smctrl.diag_mgr.neighbour_table_max_num_entries
            rsp['route'] = smartmeter.smeter.smctrl.diag_mgr.get_route_table()
            rsp['routemaxsize'] = smartmeter.smeter.smctrl.diag_mgr.route_table_max_num_entries
            rsp['status'] = 0
            #d = logger.Logger("diag.py")
            #d.log("rsp: %s", rsp)
            return json.dumps(rsp)

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})
