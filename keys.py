import web
import simplejson as json
import string

import common
from smartmeter import smartmeter
from smartmeter import logger


urls = (
    "/getkeys", "getkeys",
    "/addkey", "addkey",
    "/rmkey", "rmkey",
    "", "keys"
)

render = web.template.render('templates/', base='base')
handler = web.application(urls, locals())



class keys(object):
    def GET(self):
        return render.keys()


class getkeys(object):
    def GET(self):
        web.header('Content-Type', 'application/json')
        try:
            rsp = {}
            nwkkey = smartmeter.smeter.smctrl.key_mgr.get_nwk_key()
            k = {}
            k['key'], k['seq'] = nwkkey
            rsp['nwkkey'] = k
            linkkeys = smartmeter.smeter.smctrl.key_mgr.get_link_keys()
            rsp['linkkey'] = []
            for mac, key, used in linkkeys:
                k = {}
                k['mac'] = mac
                k['key'] = key
                if used:
                    k['used'] = 1
                else:
                    k['used'] = 0
                rsp['linkkey'].append(k)
            tclinkkey = smartmeter.smeter.smctrl.key_mgr.get_tc_link_key()
            if tclinkkey is not None:
                k = {}
                k['mac'] = tclinkkey[0]
                k['key'] = tclinkkey[1]
                if tclinkkey[2]:
                    k['used'] = 1
                else:
                    k['used'] = 0
                rsp['tclinkkey'] = k
            rsp['maxlinkkeys'] = smartmeter.smeter.smctrl.key_mgr.max_num_keys
            rsp['status'] = 0
            return json.dumps(rsp)

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})


class addkey(object):
    def POST(self):
        web.header('Content-Type', 'application/json')
        try:
            mac = common.getJsonArg("mac", "")
            if not isinstance(mac, str) or len(mac) != 16 or not all(c in string.hexdigits for c in mac):
                return json.dumps({"status": -1, "errormsg": "Invalid MAC address"})
            linkkey = common.getJsonArg("key", "")
            if not isinstance(linkkey, str) or len(linkkey) != 32 or not all(c in string.hexdigits for c in linkkey):
                return json.dumps({"status": -1, "errormsg": "Invalid link key"})
            status = smartmeter.smeter.smctrl.key_mgr.add_link_key(mac, linkkey)
            if not status:
                return json.dumps({"status": -1, "errormsg": "Failed to add link key"})
            return json.dumps({"status": 0})

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})


class rmkey(object):
    def POST(self):
        web.header('Content-Type', 'application/json')
        try:
            mac = common.getJsonArg("mac", "")
            if not isinstance(mac, str) or len(mac) != 16 or not all(c in string.hexdigits for c in mac):
                return json.dumps({"status": -1, "errormsg": "Invalid MAC address"})
            status = smartmeter.smeter.smctrl.key_mgr.rm_link_key(mac)
            if not status:
                return json.dumps({"status": -1, "errormsg": "Failed to remove link key"})
            return json.dumps({"status": 0})

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})
