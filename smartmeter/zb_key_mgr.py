"""
zigbee key manager
"""   
import time
import string
import threading
import re

import logger
import multiline_rsp


INVALID_MAC = "F000000000000000"
INVALID_LINK_KEY = "F0000000000000000000000000000000"


class ZbLinkKey(object):

    def __init__(self, mac, linkkey, index=-1, used=False):
        self.index = index
        self.mac = mac
        self.linkkey = linkkey
        self.used = used
        self.lock = threading.Lock()

    def __repr__(self):
        return repr((self.index, self.mac, self.linkkey, self.used))

    def get_link_key(self):
        """Return link key in (mac, key, used) format"""
        self.lock.acquire()
        key = (self.mac, self.linkkey, self.used)
        self.lock.release()
        return key

    def get_indexed_link_key(self):
        """Return link key in (index, mac, key, used) format"""
        self.lock.acquire()
        key = (self.index, self.mac, self.linkkey, self.used)
        self.lock.release()
        return key

    def set_link_key(self, mac=None, linkkey=None, index=None, used=None):
        self.lock.acquire()
        if index is not None:
            self.index = index
        if mac is not None:
            self.mac = mac
        if linkkey is not None:
            self.linkkey = linkkey
        if used is not None:
            self.used = used
        self.lock.release()



class ZbNwkKey(object):

    def __init__(self, nwk_key="", sequence=0):
        self.nwk_key = nwk_key
        self.seq = sequence
        self.lock = threading.Lock()

    def __repr__(self):
        return repr((self.nwk_key, self.seq))

    def get_nwk_key(self):
        self.lock.acquire()
        key = (self.nwk_key, self.seq)
        self.lock.release()
        return key

    def set_nwk_key(self, nwk_key=None, sequence=None):
        self.lock.acquire()
        if nwk_key is not None:
            self.nwk_key = nwk_key
        if sequence is not None:
            self.seq = sequence
        self.lock.release()



class ZbKeyMgr(object):

    #smartmeter>keys print
    #EMBER_SECURITY_LEVEL: 05
    #NWK Key out FC: 00001000
    #NWK Key seq num: 0x00
    #NWK Key: 2C AD 31 4A 00 94 69 38  D2 70 C6 E1 87 D3 05 B7
    #Link Key out FC: FFFFFFFF
    #TC Link Key
    #Link Key Table
    #Entry 0     (>)F000000000000000  00000000  L     n     F0 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
    #1/6 entries used.

    #test-harness key-update now
    #cbke start <nodeid> <dst endpoint>

    def __init__(self, max_num_keys=6):
        self.logger = logger.Logger('zbkeymgr')
        self.max_num_keys = max_num_keys
        self.min_rsp_lines = 9
        self.last_req = 0
        self.cache_duration = 60*5
        # FIXME: refresh_cache not used yet
        self.refresh_cache = False
        self.ready = False
        self.nwkkey = ZbNwkKey()
        self.link_keys = []
        self.link_keys_to_add = []
        self.lock = threading.Lock()
        start_tag = r'EMBER_SECURITY_LEVEL: .*'
        entries_tag = r'[0-9]*/([0-9]*) entries used.'
        self.mrsp = multiline_rsp.MultilineResponseBuilder(start_tag, entries_tag, self.min_rsp_lines + self.max_num_keys, self._extract_multiline_response)

    def _expire_cache(self):
        self.last_req = 0

    def _find_link_key_in_list(self, key_list, mac):
        for k in key_list:
            if k.mac == mac:
                return k
        return None

    def _get_next_free_link_key_index(self):
        all_keys = self.link_keys + self.link_keys_to_add
        all_keys.sort(key=lambda k: k.index)
        for i, k in enumerate(all_keys):
            if i != k.index:
                return i
        return len(all_keys)

    def get_nwk_key(self):
        """Return network key in (key, sequence) format"""
        return self.nwkkey.get_nwk_key()

    def get_link_keys(self):
        """Return all link keys in [(mac, key, used)] format"""
        all_keys = []
        self.lock.acquire()
        for k in self.link_keys:
            all_keys.append(k.get_link_key())
        self.lock.release()
        return all_keys

    def add_link_key(self, mac, linkkey):
        """Add a preconfigured link key

        mac and linkkey must be string
        """
        if self.ready and \
           len(mac) == 16 and all(c in string.hexdigits for c in mac) and \
           len(linkkey) == 32 and all(c in string.hexdigits for c in linkkey) and \
           self._mac_link_key_are_valid(mac, linkkey):
            self.lock.acquire()
            if len(self.link_keys) + len(self.link_keys_to_add) < self.max_num_keys:
                k = self._find_link_key_in_list(self.link_keys, mac)
                if k is not None:
                    k.set_link_key(linkkey=linkkey, used=False)
                    self.link_keys_to_add.append(k)
                    self.link_keys.remove(k)
                    self.lock.release()
                    return True
                k = self._find_link_key_in_list(self.link_keys_to_add, mac)
                if k is not None:
                    k.set_link_key(linkkey=linkkey)
                    self.lock.release()
                    return True
                index = self._get_next_free_link_key_index()
                k = ZbLinkKey(mac, linkkey, index=index)
                self.link_keys_to_add.append(k)
                self.lock.release()
                return True
            self.lock.release()
        return False

    def rm_link_key(self, mac):
        if self.ready and len(mac) == 16 and all(c in string.hexdigits for c in mac):
            self.lock.acquire()
            k = self._find_link_key_in_list(self.link_keys, mac)
            if k is not None:
                # there is no way to remove a link key, so just overwrite it with rubbish
                k.set_link_key(mac=INVALID_MAC, linkkey=INVALID_LINK_KEY, used=False)
                self.link_keys_to_add.append(k)
                self.link_keys.remove(k)
                self.lock.release()
                return True
            k = self._find_link_key_in_list(self.link_keys_to_add, mac)
            if k is not None:
                # there is no way to remove a link key, so just overwrite it with rubbish
                k.set_link_key(mac=INVALID_MAC, linkkey=INVALID_LINK_KEY, used=False)
                self.lock.release()
                return True
            self.lock.release()
        return False

    # TODO: support switch network key
    #test-harness key-update now

    def _mac_link_key_are_valid(self, mac, linkkey):
        return mac != INVALID_MAC and linkkey != INVALID_LINK_KEY

    def _update_link_key(self, index, mac, used, linkkey):
        if len(mac) == 16 and all(c in string.hexdigits for c in mac) and \
           len(linkkey) == 32 and all(c in string.hexdigits for c in linkkey) and \
           self._mac_link_key_are_valid(mac, linkkey):
            self.lock.acquire()
            k = self._find_link_key_in_list(self.link_keys, mac)
            if k is not None:
                k.set_link_key(linkkey=linkkey, index=index, used=used)
            else:
                k = ZbLinkKey(mac, linkkey, index=index, used=used)
                self.link_keys.append(k)
            self.link_keys.sort(key=lambda k: k.index)
            self.lock.release()
            #self.logger.log('link key %s updated', mac)

    def _extract_nwk_key_seq(self, match):
        seq = int(match.group(1), 16)
        self.nwkkey.set_nwk_key(sequence=seq)
        #self.logger.log('found nwk key seq %s', seq)

    def _extract_nwk_key(self, match):
        k = match.group(1).replace(' ', '')
        self.nwkkey.set_nwk_key(nwk_key=k)
        #self.logger.log('found nwk key %s', k)

    def _extract_link_key(self, match):
        #self.logger.log('found link key: %s, %s, %s, %s', match.group(1).strip(), match.group(2), match.group(3), match.group(4).replace(' ', ''))
        key_used = False
        if 'y' in match.group(3):
            key_used = True
        self._update_link_key(int(match.group(1).strip()), match.group(2), key_used, match.group(4).replace(' ', ''))

    def _extract_entries_used(self, match):
        self.max_num_keys = int(match.group(1))
        self.mrsp.max_num_line = self.min_rsp_lines + self.max_num_keys
        self.ready = True
        #self.logger.log('found max entries %d', self.max_num_keys)

    def _extract_multiline_response(self, start_match, end_match, rsp):
        nwk_key_seq_tag = r'NWK Key seq num: (0x[a-fA-F0-9]*)'
        nwk_key_tag = r'NWK Key: ([a-fA-F0-9 ]*)'
        link_key_tag = r'([0-9 ]*)\(>\)([a-fA-F0-9]{16}).*([y|n])([a-fA-F0-9 ]*)'
        tags = [(nwk_key_seq_tag, self._extract_nwk_key_seq),
                (nwk_key_tag,     self._extract_nwk_key),
                (link_key_tag,    self._extract_link_key),]
        tag_index = 0
        t, f = tags[tag_index]
        self._extract_entries_used(end_match)
        for line in rsp:
            #self.logger.log('%s', line)
            match = re.search(t, line)
            if match:
                #self.logger.log('*** MATCH !!!')
                f(match)
                if tag_index + 1 < len(tags):
                    tag_index = tag_index + 1
                    t, f = tags[tag_index]

    def handle_rsp(self, rsp_line):
        return self.mrsp.process_one_response_line(rsp_line)

    def process(self):
        cmds = []
        if self.ready:
            self.lock.acquire()
            if len(self.link_keys_to_add) > 0:
                for k in self.link_keys_to_add:
                    index, mac, linkkey, used = k.get_indexed_link_key()
                    cmds.append('option link %d {%s} {%s}\n' % (index, re.sub(r'(..)', r'\1 ', mac), re.sub(r'(..)', r'\1 ', linkkey)))
                    if self._mac_link_key_are_valid(mac, linkkey):
                        self.link_keys.append(k)
                self.link_keys.sort(key=lambda k: k.index)
                self.link_keys_to_add = []
            self.lock.release()

        now = time.time()
        if self.refresh_cache or now - self.last_req > self.cache_duration:
            self.last_req = now
            cmds.append('keys print\n')
        return cmds
