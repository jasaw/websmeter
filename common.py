import web
try:
    import json
except ImportError:
    import simplejson as json
import json_custom_decode

def getJsonArg(sArg, sDefault=""):
    """Picks out and returns a single value, regardless of GET or POST."""
    try:
        data = web.data()
        dic = None
        if data:
            dic = json.loads(data, object_hook=json_custom_decode.decode_unicode_to_str_dict)
        else:
            # maybe it was a GET?  check web.input()
            dic = dict(web.input())

        if dic:
            if dic.has_key(sArg):
                return dic[sArg]
            else:
                return sDefault
        else:
            return sDefault
    except (TypeError, ValueError), e:
        raise Exception("getJsonArg - no JSON arguments to decode: %s" % str(e))
