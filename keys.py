import web
import simplejson as json
import string

import common
from smartmeter import smartmeter
from smartmeter import logger

try:
    import zigbeehashing
    zb_install_code_support = True
except ImportError:
    zb_install_code_support = False


urls = (
    "/action", "action",
    "", "keys"
)

render = web.template.render('templates/', base='base')
handler = web.application(urls, locals())



class keys(object):
    def GET(self):
        return render.keys()


class action(object):
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

    def POST(self):
        web.header('Content-Type', 'application/json')
        try:
            action = common.getJsonArg("action", "")
            if action == 'addlinkkey':
                mac = common.getJsonArg("mac", "")
                if not isinstance(mac, str) or len(mac) != 16 or not all(c in string.hexdigits for c in mac):
                    return json.dumps({"status": -1, "errormsg": "Invalid MAC address"})
                pckey = None
                if zb_install_code_support:
                    icode = common.getJsonArg("icode", "")
                    if isinstance(icode, str) and len(icode) >= 8 and all(c in string.hexdigits for c in icode):
                        try:
                            pckey = zigbeehashing.installcode_to_preconfkey(icode[:-4], icode[-4:])
                        except RuntimeError:
                            return json.dumps({"status": -1, "errormsg": "Invalid install code"})
                if pckey is None:
                    pckey = common.getJsonArg("pckey", "")
                    if not isinstance(pckey, str) or len(pckey) != 32 or not all(c in string.hexdigits for c in pckey):
                        return json.dumps({"status": -1, "errormsg": "Invalid preconfigured key"})
                status = smartmeter.smeter.smctrl.key_mgr.add_link_key(mac, pckey)
                if not status:
                    return json.dumps({"status": -1, "errormsg": "Failed to add preconfigured key"})

            elif action == 'rmlinkkey':
                mac = common.getJsonArg("mac", "")
                if not isinstance(mac, str) or len(mac) != 16 or not all(c in string.hexdigits for c in mac):
                    return json.dumps({"status": -1, "errormsg": "Invalid MAC address"})
                status = smartmeter.smeter.smctrl.key_mgr.rm_link_key(mac)
                if not status:
                    return json.dumps({"status": -1, "errormsg": "Failed to remove link key"})

            elif action == 'updatenwkkey':
                status = smartmeter.smeter.smctrl.key_mgr.update_nwk_key()
                if not status:
                    return json.dumps({"status": -1, "errormsg": "Failed to update network key"})

            else:
                return json.dumps({"status": -1, "errormsg": "Unsupported action"})

            return json.dumps({"status": 0})

        except Exception, ex:
            logger.print_trace(ex)
            return json.dumps({"status": -1, "errormsg": "Server error"})
