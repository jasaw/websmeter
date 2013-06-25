"""
zigbee message manager
"""   
import time
import string
import threading
import re

import error
import logger
import multiline_rsp


# bit map
MESSAGE_CONTROL = {
    'NONE'               : 0x00,
    'NORMAL_TX'          : 0x00,
    'NORMAL_INTERPAN_TX' : 0x01,
    'INTERPAN_TX'        : 0x02,
    'PRIORITY_LOW'       : 0x00,
    'PRIORITY_MEDIUM'    : 0x04,
    'PRIORITY_HIGH'      : 0x08,
    'PRIORITY_CRITICAL'  : 0x0C,
    'CONFIRMATION'       : 0x80
}
MESSAGE_CONTROL_TX_MODE_MASK = 0x03
MESSAGE_CONTROL_PRIORITY_MASK = 0x0C


INFINITE_DURATION = 0xFFFF

current_message_id = 0
MAX_MESSAGE_ID = 0xFFFFFFFF


class Error(error.Generic):
    """Base class for message manager exceptions"""
    pass

class BadArgumentError(Error):
    """Bad input error"""
    pass

def get_next_message_id():
    global current_message_id
    current_message_id = current_message_id + 1
    if current_message_id > MAX_MESSAGE_ID:
        current_message_id = 1
    return current_message_id



class ZbMessage(object):

    def __init__(self, msg_id=0, msg_ctrl=MESSAGE_CONTROL['NONE'], start_time=0,
                 duration=0, message_string=""):
        """Create a text message
        - msg_id is message id (unsigned 32bits)
        - msg_ctrl is message control (example: MESSAGE_CONTROL['PRIORITY_HIGH'] | MESSAGE_CONTROL['CONFIRMATION'])
        - start_time in zigbee utc (unsigned 32bits)
        - duration in minutes
        """
        self.lock = threading.Lock()
        self.valid = False
        self.active = False
        self.set_message(msg_id=msg_id, msg_ctrl=msg_ctrl, start_time=start_time,
                         duration=duration, message_string=message_string)

    def __repr__(self):
        return repr((self.valid, self.active, self.msg_id, self.msg_ctrl,
                     self.start_time, self.duration, self.message_string))

    def _check_message_values(self):
        if self.msg_id > 0xFFFFFFFF or self.msg_id < 0:
            raise BadArgumentError('Invalid message ID: ' + str(self.msg_id))
        if self.msg_ctrl > 0xFF or self.msg_ctrl < 0:
            raise BadArgumentError('Invalid message control: ' + str(self.msg_ctrl))
        if self.start_time > 0xFFFFFFFF or self.start_time < 0:
            raise BadArgumentError('Invalid start time: ' + str(self.start_time))
        if self.duration > INFINITE_DURATION or self.duration < 0:
            raise BadArgumentError('Invalid duration: ' + str(self.duration))

    def is_valid(self):
        try:
            self._check_message_values()
            return True
        except BadArgumentError:
            return False

    def get_message(self):
        """Return text message in dictionary format"""
        m = {}
        self.lock.acquire()
        m['valid'] = self.valid
        m['active'] = self.active
        m['id'] = self.msg_id
        m['ctrl'] = self.msg_ctrl
        m['start'] = self.start_time
        m['duration'] = self.duration
        m['message'] = self.message_string
        self.lock.release()
        return m

    def set_message(self, valid=None, active=None, msg_id=None, msg_ctrl=None,
                    start_time=None, duration=None, message_string=None):
        self.lock.acquire()
        if valid is not None:
            self.valid = valid
        if active is not None:
            self.active = active
        if msg_id is not None:
            self.msg_id = msg_id
        if msg_ctrl is not None:
            self.msg_ctrl = msg_ctrl
        if start_time is not None:
            self.start_time = start_time
        if duration is not None:
            self.duration = duration
        if message_string is not None:
            self.message_string = message_string
        self.lock.release()
        self._check_message_values()

    def get_transmission_mode_string(self):
        if self.msg_ctrl & MESSAGE_CONTROL_TX_MODE_MASK == MESSAGE_CONTROL['NORMAL_INTERPAN_TX']:
            return 'both'
        if self.msg_ctrl & MESSAGE_CONTROL_TX_MODE_MASK == MESSAGE_CONTROL['INTERPAN_TX']:
            return 'ipan'
        return 'normal'

    def get_priority_string(self):
        if self.msg_ctrl & MESSAGE_CONTROL_PRIORITY_MASK == MESSAGE_CONTROL['PRIORITY_CRITICAL']:
            return 'critical'
        if self.msg_ctrl & MESSAGE_CONTROL_PRIORITY_MASK == MESSAGE_CONTROL['PRIORITY_HIGH']:
            return 'high'
        if self.msg_ctrl & MESSAGE_CONTROL_PRIORITY_MASK == MESSAGE_CONTROL['PRIORITY_MEDIUM']:
            return 'medium'
        return 'low'

    def get_confirmation_string(self):
        if self.msg_ctrl & MESSAGE_CONTROL['CONFIRMATION']:
            return 'req'
        return 'not'



class ZbMessageMgr(object):

    # plugin messaging-server message "<message>"
    # plugin messaging-server id <msgId:4>
    # plugin messaging-server time <startTime:4> <duration:2>
    # plugin messaging-server transmission <normal | ipan | both>
    # plugin messaging-server importance <low | medium | high | critical>
    # plugin messaging-server confirm <not | req>
    # plugin messaging-server <valid | invalid> <endpoint:1>
    # plugin messaging-server display <nodeId:2> <srcEndpoint:1> <dstEndpoint:1>
    # plugin messaging-server cancel <nodeId:2> <srcEndpoint:1> <dstEndpoint:1>

    # plugin messaging-server print <endpoint:1>
    # = Server Message =
    #  vld: YES                               # valid (msg has been set)
    #  act: YES                               # active (readable by msg clients)
    #   id: 0x00000065                        # msg id
    #   mc: 0x00                              # msg confirmation not required
    #   st: 0x18125AF9                        # msg start time
    #  now: YES                               # msg start now
    # time: 0x18125B1D                        # current time
    #  dur: 0x0001                            # duration in minutes
    #  mes: "Hello world from ESI 2"

    def __init__(self, end_point=1):
        self.logger = logger.Logger('zbmsgmgr')
        self.lock = threading.Lock()
        self.end_point = end_point
        self.last_req = 0
        self.cache_duration = 60
        self.max_num_pending_cmds = 20
        self.ready = False
        self.read_message = True
        self.message = ZbMessage()
        self.message_to_add = None
        self.pending_cmd = []
        self.mrsp = []
        message_start_tag = r'= Server Message ='
        self.mrsp.append(multiline_rsp.MultilineResponseBuilder(message_start_tag, None, 10, self._extract_message_info))

    def _expire_cache(self):
        self.last_req = 0

    def _extract_matched_msg_valid(self, msg, match):
        if match.group(1) == 'YES':
            msg.valid = True
        else:
            msg.valid = False

    def _extract_matched_msg_active(self, msg, match):
        if match.group(1) == 'YES':
            msg.active = True
        else:
            msg.active = False

    def _extract_matched_msg_id(self, msg, match):
        msg.msg_id = int(match.group(1),16)

    def _extract_matched_msg_control(self, msg, match):
        msg.msg_ctrl = int(match.group(1),16)

    def _extract_matched_msg_start(self, msg, match):
        msg.start_time = int(match.group(1),16)

    def _extract_matched_msg_duration(self, msg, match):
        msg.duration = int(match.group(1),16)

    def _extract_matched_msg_string(self, msg, match):
        msg.message_string = match.group(1).strip('"')

    def _extract_message_info(self, start_match, end_match, rsp):
        # = Server Message =
        # vld: NO
        # act: NO
        # id: 0x00000000
        # mc: 0x00
        # st: 0x00000000
        # now: NO
        # time: 0x00000006
        # dur: 0x0000
        # mes: ""
        valid_tag = r'vld: (YES|NO)'
        active_tag = r'act: (YES|NO)'
        id_tag = r'id: (0x[a-fA-F0-9]+)'
        confirm_tag = r'mc: (0x[a-fA-F0-9]+)'
        start_tag = r'st: (0x[a-fA-F0-9]+)'
        #startnow_tag = r'now: (YES|NO)'
        #curtime_tag = r'time: (0x[a-fA-F0-9]+)'
        duration_tag = r'dur: (0x[a-fA-F0-9]+)'
        message_tag = r'mes: (.*)'
        tags = [(valid_tag,    self._extract_matched_msg_valid),
                (active_tag,   self._extract_matched_msg_active),
                (id_tag,       self._extract_matched_msg_id),
                (confirm_tag,  self._extract_matched_msg_control),
                (start_tag,    self._extract_matched_msg_start),
                (duration_tag, self._extract_matched_msg_duration),
                (message_tag,  self._extract_matched_msg_string),]
        self.lock.acquire()

        the_msg = ZbMessage()
        tag_index = 0
        t, f = tags[tag_index]
        for line in rsp:
            match = re.search(t, line)
            if match:
                f(the_msg, match)
                if tag_index + 1 < len(tags):
                    tag_index = tag_index + 1
                    t, f = tags[tag_index]
        #self.logger.log('%s', the_msg)
        if the_msg.is_valid():
            self.message = the_msg
            self.ready = True
        self.lock.release()

    def get_message(self):
        """Return DRLC events in [dictionary] format"""
        return self.message.get_message()

    def set_message(self, **kwargs):
        status = False
        if self.ready:
            self.lock.acquire()
            try:
                the_msg = ZbMessage(**kwargs)
                if the_msg.is_valid():
                    # fill in message ID
                    the_msg.msg_id = get_next_message_id()
                    # queue message
                    self.message_to_add = the_msg
                    status = True
            except BadArgumentError, e:
                pass
            finally:
                self.lock.release()
        return status

    def rm_message(self):
        # plugin messaging-server invalid <endpoint:1>
        if self.ready and len(self.pending_cmd) < self.max_num_pending_cmds:
            self.lock.acquire()
            self.message_to_add = None
            self.pending_cmd.append('plugin messaging-server invalid %d\n' % self.end_point)
            self.lock.release()
            return True
        return False

    def display_message(self, dst_node_id, dst_end_point):
        # plugin messaging-server display <nodeId:2> <srcEndpoint:1> <dstEndpoint:1>
        if self.ready and \
           dst_node_id >= 0 and dst_node_id <= 0xFFFF and \
           dst_end_point > 0 and dst_end_point < 0xFF and \
           len(self.pending_cmd) < self.max_num_pending_cmds:
            self.lock.acquire()
            self.pending_cmd.append('plugin messaging-server display 0x%x %d %d\n' % (dst_node_id, self.end_point, dst_end_point))
            self.lock.release()
            return True
        return False

    def cancel_message(self, dst_node_id, dst_end_point):
        # plugin messaging-server cancel <nodeId:2> <srcEndpoint:1> <dstEndpoint:1>
        if self.ready and \
           dst_node_id >= 0 and dst_node_id <= 0xFFFF and \
           dst_end_point > 0 and dst_end_point < 0xFF and \
           len(self.pending_cmd) < self.max_num_pending_cmds:
            self.lock.acquire()
            self.pending_cmd.append('plugin messaging-server cancel 0x%x %d %d\n' % (dst_node_id, self.end_point, dst_end_point))
            self.lock.release()
            return True
        return False

    def refresh_message_cache(self):
        now = time.time()
        if now - self.last_req > self.cache_duration:
            self.read_message = True

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
        if len(self.pending_cmd) > 0:
            cmds.extend(self.pending_cmd)
            self.pending_cmd = []
            self._expire_cache()
            self.refresh_message_cache()
        if self.message_to_add is not None:
            cmds.append('plugin messaging-server message "%s"\n' % self.message_to_add.message_string.replace('"','\\"'))
            cmds.append('plugin messaging-server id 0x%x\n' % self.message_to_add.msg_id)
            cmds.append('plugin messaging-server time 0x%x 0x%x\n' % (self.message_to_add.start_time, self.message_to_add.duration))
            cmds.append('plugin messaging-server transmission %s\n' % self.message_to_add.get_transmission_mode_string())
            cmds.append('plugin messaging-server importance %s\n' % self.message_to_add.get_priority_string())
            cmds.append('plugin messaging-server confirm %s\n' % self.message_to_add.get_confirmation_string())
            cmds.append('plugin messaging-server valid %d\n' % self.end_point)
            self.message_to_add = None
            self._expire_cache()
            self.refresh_message_cache()
        if self.read_message:
            self.read_message = False
            cmds.append('plugin messaging-server print %d\n' % self.end_point)
            self.last_req = time.time()
        self.lock.release()
        return cmds
