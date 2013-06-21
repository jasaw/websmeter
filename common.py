import web
import simplejson as json

def getJsonArg(sArg, sDefault=""):
    """Picks out and returns a single value, regardless of GET or POST."""
    try:
        data = web.data()
        dic = None
        if data:
            dic = json.loads(data)
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
