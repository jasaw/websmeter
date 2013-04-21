"""
zigbee network manager
"""   

import time
import string
import threading
import re
import random

import logger
import multiline_rsp


INVALID_NODE_ID = 0xFFFE


class ZbNwkInfo(object):

    def __init__(self, pan_id=0xFFFF, radio_channel=0, radio_power=0, expan_id=""):
        self.mac = ""
        self.node_id = INVALID_NODE_ID
        self.end_point = 1
        self.pan_id = pan_id
        self.expan_id = expan_id
        self.radio_channel = radio_channel
        self.radio_power = radio_power
        self.lock = threading.Lock()

    def __repr__(self):
        return repr((self.node_id, self.end_point, self.pan_id, self.expan_id, self.radio_channel, self.radio_power))

    def get_nwk_info(self):
        """Return network info in dictionary format"""
        nwkinfo = {}
        self.lock.acquire()
        nwkinfo['mac'] = self.mac
        nwkinfo['node_id'] = self.node_id
        nwkinfo['end_point'] = self.end_point
        nwkinfo['pan_id'] = self.pan_id
        nwkinfo['expan_id'] = self.expan_id
        nwkinfo['radio_channel'] = self.radio_channel
        nwkinfo['radio_power'] = self.radio_power
        self.lock.release()
        return nwkinfo

    def set_nwk_info(self, mac=None, node_id=None, end_point=None, pan_id=None, radio_channel=None, radio_power=None, expan_id=None):
        self.lock.acquire()
        if mac is not None:
            self.mac = mac
        if node_id is not None:
            self.node_id = node_id
        if end_point is not None:
            self.end_point = end_point
        if pan_id is not None:
            self.pan_id = pan_id
        if radio_channel is not None:
            self.radio_channel = radio_channel
        if radio_power is not None:
            self.radio_power = radio_power
        if expan_id is not None:
            self.expan_id = expan_id
        self.lock.release()



class ZbNwkMgr(object):

    #smartmeter>info
    #MFG String: Telegesis
    #node [(>)8CEEC60101000050] chan [18] pwr [3]
    #panID [0xF00D] nodeID [0xFFFE] xpan [0x(>)A77D2583AB2EFA28]
    #ezsp ver 0x04 stack type 0x02 stack ver. [4.7.2.0 GA build 88]
    #nodeType [0x00]
    #Security level [05]SE Security Info [RealEcc RealCbke GoodCert]
    #network state [00] Buffs: 162 / 171
    #Ep cnt: 1
    #ep 1 [endpoint enabled, device enabled] nwk [0] profile [0x0109] devId [0x0500] ver [0x00]
    #    in (server) cluster: 0x0000 (Basic)
    #    in (server) cluster: 0x000A (Time)
    #    in (server) cluster: 0x0019 (Over the Air Bootloading Cluster)
    #    in (server) cluster: 0x0701 (Demand Response and Load Control)
    #    out(client) cluster: 0x0702 (Simple Metering)
    #    in (server) cluster: 0x0702 (Simple Metering)
    #    in (server) cluster: 0x0700 (Price)
    #    in (server) cluster: 0x0703 (Messaging)
    #    out(client) cluster: 0x0800 (Key establishment)
    #    in (server) cluster: 0x0800 (Key establishment)
    #Nwk cnt: 1
    #nwk 0 [Primary]
    #  nodeType [0x01]
    #  securityProfile [0x04]

    #smartmeter>network form 18 3 0xF00D
    #set state to: 0x0A00
    #set extended security to: 0x0100
    #Ezsp Policy: set TC Key Request to "Deny":Success: set
    #Ezsp Policy: set App. Key Request to "Allow":Success: set
    #Ezsp Policy: set Trust Center Policy to "Allow preconfigured key joins":Success: set
    #Forming on ch 18, panId 0xF00D
    #form 0x00
    #smartmeter>EMBER_NETWORK_UP

    #network pjoin 60
    #network broad-pjoin 60

    #network find joinable

    #smartmeter>network leave
    #leave 0x00
    #smartmeter>EMBER_NETWORK_DOWN

    #network extpanid {b7 61 d8 e6 92 60 48 92}

    def __init__(self):
        self.logger = logger.Logger('zbnwkmgr')
        self.nwk_is_up = False
        self.last_req = 0
        self.cache_duration = 60
        self.my_zb_nwk_info = ZbNwkInfo()
        self.need_nwk_info = True
        self.pending_cmd = None
        self.lock = threading.Lock()
        self.mrsp = []
        nwk_up_tag = r'EMBER_NETWORK_UP'
        nwk_down_tag = r'EMBER_NETWORK_DOWN'
        nwk_info_start_tag = r'MFG String: Telegesis'
        # FIXME: look for a better line as nwk_info_end_tag
        nwk_info_end_tag = r'[ ]*securityProfile \[.*\]'
        # only expecting 1 end point on device
        self.mrsp.append(multiline_rsp.MultilineResponseBuilder(nwk_info_start_tag, nwk_info_end_tag, 25, self._extract_nwk_info))
        self.mrsp.append(multiline_rsp.MultilineResponseBuilder(nwk_up_tag, None, 1, self._set_network_is_up))
        self.mrsp.append(multiline_rsp.MultilineResponseBuilder(nwk_down_tag, None, 1, self._set_network_is_down))

    def _expire_cache(self):
        self.last_req = 0

    def _extract_matched_node_info(self, match):
        self.my_zb_nwk_info.set_nwk_info(mac=match.group(1).upper(), radio_channel=int(match.group(2)), radio_power=int(match.group(3)))

    def _extract_matched_nwk_info(self, match):
        self.my_zb_nwk_info.set_nwk_info(pan_id=int(match.group(1),16), node_id=int(match.group(2),16), expan_id=match.group(3).upper())

    def _extract_matched_endpoint_info(self, match):
        self.my_zb_nwk_info.set_nwk_info(end_point=int(match.group(1)))

    def _extract_nwk_info(self, start_match, end_match, rsp):
        #node [(>)8CEEC60101000050] chan [18] pwr [3]
        #panID [0xF00D] nodeID [0xFFFE] xpan [0x(>)A77D2583AB2EFA28]
        #ep 1 [endpoint enabled, device enabled] nwk [0] profile [0x0109] devId [0x0500] ver [0x00]
        node_tag = r'node \[\(>\)([a-fA-F0-9]{16})\] chan \[([0-9]+)\] pwr \[([0-9])\]'
        nwk_tag = r'panID \[(0x[a-fA-F0-9]+)\] nodeID \[(0x[a-fA-F0-9]+)\] xpan \[0x\(>\)([a-fA-F0-9]{16})\]'
        ep_tag = r'^ep ([0-9]+) .*'
        tags = [(node_tag, self._extract_matched_node_info),
                (nwk_tag,  self._extract_matched_nwk_info),
                (ep_tag,   self._extract_matched_endpoint_info),]
        tag_index = 0
        t, f = tags[tag_index]
        for line in rsp:
            #self.logger.log('%s', line)
            match = re.search(t, line)
            if match:
                #self.logger.log('*** MATCH !!!')
                f(match)
                if tag_index + 1 < len(tags):
                    tag_index = tag_index + 1
                    t, f = tags[tag_index]

    def _set_network_is_up(self, start_match, end_match, rsp):
        self.nwk_is_up = True
        self._expire_cache()
        self.refresh_network_info()

    def _set_network_is_down(self, start_match, end_match, rsp):
        self.nwk_is_up = False
        self._expire_cache()
        self.refresh_network_info()

    def get_nwk_info(self):
        rsp = self.my_zb_nwk_info.get_nwk_info()
        if self.nwk_is_up:
            rsp['nwk_is_up'] = 1
        else:
            rsp['nwk_is_up'] = 0
        return rsp

    def form_network(self, radio_channel=None, radio_power=None, pan_id=None):
        """all params must be integer"""
        status = False
        self.lock.acquire()
        if not self.nwk_is_up and self.pending_cmd is None:
            if radio_channel is None:
                radio_channel = 11 + random.randrange(16)
            if radio_power is None:
                radio_power = 3
            if pan_id is None:
                pan_id = 1 + random.randrange(0xFFF0 - 1)
            if 11 <= radio_channel <= 26 and 0 <= radio_power <= 3 and pan_id != 0xFFFF:
                self.pending_cmd = 'network form %d %d 0x%X\n' % (radio_channel, radio_power, pan_id)
                self._expire_cache()
                status = True
        self.lock.release()
        return status

    def join_network(self, radio_channel=None, radio_power=None, pan_id=None):
        """all params must be integer"""
        status = False
        self.lock.acquire()
        if not self.nwk_is_up and self.pending_cmd is None:
            if radio_power is None:
                radio_power = 3
            if radio_channel is None or pan_id is None:
                self.pending_cmd = 'network find joinable\n'
                self._expire_cache()
                status = True
            elif radio_channel is not None and pan_id is not None:
                if 11 <= radio_channel <= 26 and 0 <= radio_power <= 3 and pan_id != 0xFFFF:
                    self.pending_cmd = 'network join %d %d 0x%X\n' % (radio_channel, radio_power, pan_id)
                    self._expire_cache()
                    status = True
        self.lock.release()
        return status

    def leave_network(self):
        status = False
        self.lock.acquire()
        if self.nwk_is_up and self.pending_cmd is None:
            self.pending_cmd = 'network leave\n'
            self._expire_cache()
            status = True
        self.lock.release()
        return status

    def permit_join(self, duration, broadcast=True):
        status = False
        self.lock.acquire()
        if self.nwk_is_up and self.my_zb_nwk_info.node_id == 0 and self.pending_cmd is None:
            if duration > 255:
                duration = 255
            if duration < 0:
                duration = 0
            b = ""
            if broadcast:
                b = "broad-"
            self.pending_cmd = 'network %spjoin %d\n' % (b, duration)
            status = True
        self.lock.release()
        return status

    def set_extended_pan_id(self, new_expan_id):
        status = False
        self.lock.acquire()
        if self.pending_cmd is None and len(new_expan_id) == 16 and all(c in string.hexdigits for c in new_expan_id):
            self.pending_cmd = 'network extpanid {%s}\n' % (re.sub(r'(..)', r'\1 ', new_expan_id))
            self._expire_cache()
            status = True
        self.lock.release()
        return status

    def refresh_network_info(self):
        now = time.time()
        if now - self.last_req > self.cache_duration:
            self.need_nwk_info = True

    def handle_rsp(self, rsp_line):
        accepted = False
        for m in self.mrsp:
            accepted = m.process_one_response_line(rsp_line)
            if accepted:
                break
        return accepted

    def process(self):
        cmds = []
        self.lock.acquire()
        if self.need_nwk_info:
            self.need_nwk_info = False
            cmds.append('info\n')
            self.last_req = time.time()
        if self.pending_cmd is not None:
            cmds.append(self.pending_cmd)
            self.pending_cmd = None
        self.lock.release()
        return cmds
