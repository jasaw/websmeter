"""
zigbee drlc manager
"""   
import time
import string
import threading
import re

import error
import logger
import multiline_rsp


DRLC_EVENT_NUM_BYTES = 23

# bit map
DEVICE_CLASS = {
    'COMPRESSOR'          : 0x0001,
    'STRIP_HEATER'        : 0x0002,
    'WATER_HEATER'        : 0x0004,
    'POOL_PUMP'           : 0x0008,
    'SMART_APPLIANCES'    : 0x0010,
    'IRRIGATION_PUMP'     : 0x0020,
    'MANAGED_CI_LOADS'    : 0x0040,
    'SIMPLE_MISC_LOADS'   : 0x0080,
    'EXTERIOR_LIGHTING'   : 0x0100,
    'INTERIOR_LIGHTING'   : 0x0200,
    'ELECTRIC_VEHICLE'    : 0x0400,
    'GENERATION_SYSTEMS'  : 0x0800,
    'ALL'                 : 0x0FFF
}

UTILITY_ENROLMENT_GROUP = {
    'ALL' : 0x00,
}

CRITICALITY_LEVEL = {
    'GREEN'              : 0x01,
    'LEVEL1'             : 0x02,
    'LEVEL2'             : 0x03,
    'LEVEL3'             : 0x04,
    'LEVEL4'             : 0x05,
    'LEVEL5'             : 0x06,
    'EMERGENCY'          : 0x07,
    'PLANNED_OUTAGE'     : 0x08,
    'SERVICE_DISCONNECT' : 0x09,
    'UTILITY1'           : 0x0A,
    'UTILITY2'           : 0x0B,
    'UTILITY3'           : 0x0C,
    'UTILITY4'           : 0x0D,
    'UTILITY5'           : 0x0E,
    'UTILITY6'           : 0x0F,
}

EVENT_NOT_SET = 0xFF
TEMPERATURE_OFFSET_NOT_USED = 0xFF
TEMPERATURE_SET_POINT_NOT_USED = -32768
AVERAGE_LOAD_NOT_USED = -128
DUTY_CYCLE_NOT_USED = 0xFF

# bit map
EVENT_CONTROL = {
    'NONE'       : 0x00,
    'RAND_START' : 0x01,
    'RAND_END'   : 0x02,
    'ALL'        : 0x03
}

current_issuer_event_id = 0
MAX_ISSUER_EVENT_ID = 0xFFFFFFFF


class Error(error.Generic):
    """Base class for drlc manager exceptions"""
    pass

class BadArgumentError(Error):
    """Bad input error"""
    pass


def get_next_issuer_event_id():
    global current_issuer_event_id
    current_issuer_event_id = current_issuer_event_id + 1
    if current_issuer_event_id > MAX_ISSUER_EVENT_ID:
        current_issuer_event_id = 1
    return current_issuer_event_id

def get_byte_mask(num_bytes):
    mask = 0
    for i in range(num_bytes):
        mask = (mask << 8) | 0xFF
    return mask

def signed_hex_to_decimal(number, num_bytes):
    mask = get_byte_mask(num_bytes)
    number = number & mask
    if number & (1 << (num_bytes*8 - 1)):
        return ~(mask - number)
    else:
        return number

def clip_number(number, num_bytes):
    mask = get_byte_mask(num_bytes)
    return number & mask



class ZbDrlcEvent(object):

    def __init__(self, index=-1,
                 eid=0, dev=DEVICE_CLASS['ALL'], ueg=UTILITY_ENROLMENT_GROUP['ALL'],
                 start_time=0, duration=0, criticality=CRITICALITY_LEVEL['GREEN'],
                 cto=TEMPERATURE_OFFSET_NOT_USED, hto=TEMPERATURE_OFFSET_NOT_USED,
                 ctsp=TEMPERATURE_SET_POINT_NOT_USED, htsp=TEMPERATURE_SET_POINT_NOT_USED,
                 avgload=AVERAGE_LOAD_NOT_USED, dutycycle=DUTY_CYCLE_NOT_USED,
                 ectrl=EVENT_CONTROL['NONE']):
        """Create a DRLC event
        - index is the DRLC table entry index
        - eid is event id (unsigned 32bits)
        - dev is device class (example: DEVICE_CLASS['ELECTRIC_VEHICLE'] | DEVICE_CLASS['POOL_PUMP'])
        - ueg is utility enrolment group
        - start_time in zigbee utc (unsigned 32bits)
        - duration in minutes, max 1440 or one day (unsigned 16bits)
        - avgload is average load adjustment percentage (range -100 to +100; -100 is 100% load shed, +100 is client decide)
        - dutycycle range is 0 to 100
        - ectrl is event control
        """
        self.lock = threading.Lock()
        self.data_length = DRLC_EVENT_NUM_BYTES
        self.set_event(index=index, eid=eid, dev=dev, ueg=ueg,
                       start_time=start_time, duration=duration, criticality=criticality,
                       cto=cto, hto=hto, ctsp=ctsp, htsp=htsp,
                       avgload=avgload, dutycycle=dutycycle, ectrl=ectrl)

    def __repr__(self):
        return repr((self.index, self.event_id, self.device_class, self.utility_group,
                     self.start_time, self.duration, self.criticality_value,
                     self.cool_temp_offset, self.heat_temp_offset,
                     self.cool_temp_set, self.heat_temp_set,
                     self.average_load, self.duty_cycle))

    def _check_event_values(self):
        if self.device_class > DEVICE_CLASS['ALL'] or self.device_class < 0:
            raise BadArgumentError('Invalid device class value: ' + str(self.device_class))
        if self.utility_group > 0xFF or self.utility_group < 0:
            raise BadArgumentError('Invalid utility enrolment group value: ' + str(self.utility_group))
        if self.criticality_value > CRITICALITY_LEVEL['UTILITY6'] or self.criticality_value < CRITICALITY_LEVEL['GREEN']:
            raise BadArgumentError('Invalid criticality value: ' + str(self.criticality_value))
        if self.event_control > EVENT_CONTROL['ALL'] or self.event_control < 0:
            raise BadArgumentError('Invalid event control value: ' + str(self.event_control))
        if self.start_time > 0xFFFFFFFF or self.start_time < 0:
            raise BadArgumentError('Invalid start time: ' + str(self.start_time))
        if self.event_control > EVENT_CONTROL['ALL'] or self.event_control < EVENT_CONTROL['NONE']:
            raise BadArgumentError('Invalid event control value: ' + str(self.event_control))
        if self.duration > 1440 or self.duration < 0:
            raise BadArgumentError('Invalid duration: ' + str(self.duration))
        if self.cool_temp_offset > 0xFF or self.cool_temp_offset < 0:
            raise BadArgumentError('Invalid cooling temperature offset: ' + str(self.cool_temp_offset))
        if self.heat_temp_offset > 0xFF or self.heat_temp_offset < 0:
            raise BadArgumentError('Invalid heating temperature offset: ' + str(self.heat_temp_offset))
        if self.cool_temp_set != TEMPERATURE_SET_POINT_NOT_USED:
            if self.cool_temp_set > 32767 or self.cool_temp_set < -27315:
                raise BadArgumentError('Invalid cooling temperature set point: ' + str(self.cool_temp_set))
        if self.heat_temp_set != TEMPERATURE_SET_POINT_NOT_USED:
            if self.heat_temp_set > 32767 or self.heat_temp_set < -27315:
                raise BadArgumentError('Invalid heating temperature set point: ' + str(self.heat_temp_set))
        if self.average_load != AVERAGE_LOAD_NOT_USED:
            if self.average_load > 100 or self.average_load < -100:
                raise BadArgumentError('Invalid average load adjustment percentage: ' + str(self.average_load))
        if self.duty_cycle != DUTY_CYCLE_NOT_USED:
            if self.duty_cycle > 100 or self.duty_cycle < 0:
                raise BadArgumentError('Invalid duty cycle: ' + str(self.duty_cycle))

    def _set_event_control(self, ectrl=[]):
        self.event_control = 0
        for e in ectrl:
            if EVENT_CONTROL.has_key(e):
                self.event_control = self.event_control | EVENT_CONTROL[e]
            else:
                raise BadArgumentError('Invalid event control: ' + str(e))

    def get_event(self):
        """Return DRLC event in dictionary format"""
        e = {}
        self.lock.acquire()
        e['eid'] = self.event_id
        e['dev'] = self.device_class
        e['ueg'] = self.utility_group
        e['start'] = self.start_time
        e['duration'] = self.duration
        e['criticality'] = self.criticality_value
        e['ectrl'] = self.event_control
        if self.cool_temp_offset != TEMPERATURE_OFFSET_NOT_USED:
            e['cto'] = self.cool_temp_offset
        if self.heat_temp_offset != TEMPERATURE_OFFSET_NOT_USED:
            e['hto'] = self.heat_temp_offset
        if self.cool_temp_set != TEMPERATURE_SET_POINT_NOT_USED:
            e['ctsp'] = self.cool_temp_set
        if self.heat_temp_set != TEMPERATURE_SET_POINT_NOT_USED:
            e['htsp'] = self.heat_temp_set
        if self.average_load != AVERAGE_LOAD_NOT_USED:
            e['avgload'] = self.average_load
        if self.duty_cycle != DUTY_CYCLE_NOT_USED:
            e['dutycycle'] = self.duty_cycle
        self.lock.release()
        return e

    def set_event(self, index=None, eid=None, dev=None, ueg=None,
                  start_time=None, duration=None, criticality=None,
                  cto=None, hto=None, ctsp=None, htsp=None,
                  avgload=None, dutycycle=None, ectrl=None):
        self.lock.acquire()
        self.source = 0
        if index is not None:
            self.index = index
        if eid is not None:
            self.event_id = eid
        if dev is not None:
            self.device_class = dev
        if ueg is not None:
            self.utility_group = ueg
        if start_time is not None:
            self.start_time = start_time
        if duration is not None:
            self.duration = duration
        if criticality is not None:
            self.criticality_value = criticality
        if cto is not None:
            self.cool_temp_offset = cto
        if hto is not None:
            self.heat_temp_offset = hto
        if ctsp is not None:
            self.cool_temp_set = ctsp
        if htsp is not None:
            self.heat_temp_set = htsp
        if avgload is not None:
            self.average_load = avgload
        if dutycycle is not None:
            self.duty_cycle = dutycycle
        if ectrl is not None:
            self.event_control = ectrl
        self.lock.release()
        self._check_event_values()

    def is_set(self):
        if self.source == EVENT_NOT_SET:
            return False
        else:
            return True

    def is_valid(self):
        try:
            self._check_event_values()
            return True
        except BadArgumentError:
            return False

    def _byte_swap(self, hex_string):
        """hex_string input length must be even"""
        return "".join([hex_string[x:x+2] for x in range(0,len(hex_string),2)][::-1])

    def _format_bytes(self, hex_string):
        return re.sub(r'(..)', r'\1 ', hex_string)

    def set_event_raw_bytes(self):
        #  80 00 00 00 ff 0f 00 10 27 00 00 30 00 01 ff ff 00 80 00 80 2a 32 02
        # | Event ID  |class|gp| StartTime | Dur |CL|Co|Ho|CSet |HSet |AL|DC|EC|
        mask1 =  get_byte_mask(1)
        mask2 =  get_byte_mask(2)
        mask4 =  get_byte_mask(4)
        eid_str = self._format_bytes(self._byte_swap('%08X' % (self.event_id & mask4)))
        dev_str = self._format_bytes(self._byte_swap('%04X' % (self.device_class & mask2)))
        gp_str = self._format_bytes(self._byte_swap('%02X' % (self.utility_group & mask1)))
        st_str = self._format_bytes(self._byte_swap('%08X' % (self.start_time & mask4)))
        dur_str = self._format_bytes(self._byte_swap('%04X' % (self.duration & mask2)))
        cl_str = self._format_bytes(self._byte_swap('%02X' % (self.criticality_value & mask1)))
        co_str = self._format_bytes(self._byte_swap('%02X' % (self.cool_temp_offset & mask1)))
        ho_str = self._format_bytes(self._byte_swap('%02X' % (self.heat_temp_offset & mask1)))
        cset_str = self._format_bytes(self._byte_swap('%04X' % (self.cool_temp_set & mask2)))
        hset_str = self._format_bytes(self._byte_swap('%04X' % (self.heat_temp_set & mask2)))
        al_str = self._format_bytes(self._byte_swap('%02X' % (self.average_load & mask1)))
        dc_str = self._format_bytes(self._byte_swap('%02X' % (self.duty_cycle & mask1)))
        ec_str = self._format_bytes(self._byte_swap('%02X' % (self.event_control & mask1)))
        return eid_str + dev_str + gp_str + st_str + dur_str + cl_str + co_str + ho_str + cset_str + hset_str + al_str + dc_str + ec_str



class ZbDrlcMgr(object):

    # plugin drlc-server slce <endpoint:1> <index:1> <length:1> <load control event bytes>
    # load control event bytes are expected as 23 raw bytes in the form
    # {<eventId:4> <deviceClass:2> <ueg:1> <startTime:4> <duration:2> <criticalityLevel:1>
    #  <coolingTempOffset:1> <heatingTempOffset:1> <coolingTempSetPoint:2> <heatingTempSetPoint:2>
    #  <afgLoadPercentage:1> <dutyCycle:1> <eventControl:1> } all multibyte values should be
    # little endian as though they were coming over the air.
    # Example:
    #plugin drlc-server slce 1 0 23 { 80 00 00 00 ff 0f 00 10 27 00 00 30 00 01 ff ff 00 80 00 80 2a 32 02 }
    #                               {| Event ID  |class|gp| StartTime | Dur |CL|Co|Ho|CSet |HSet |AL|DC|EC|}

    def __init__(self, max_num_events=10, end_point=1):
        self.logger = logger.Logger('zbdrlcmgr')
        self.lock = threading.Lock()
        self.max_num_events = max_num_events
        self.end_point = end_point
        self.last_req = 0
        self.cache_duration = 60
        self.ready = False
        self.read_drlc_table = True
        self.drlc_events = []
        self.drlc_events_to_add = []
        self.pending_cmd = []
        self.mrsp = []
        event_start_tag = r'= LCE ([0-9]*) ='
        event_table_size_tag = r'Table size: ([0-9]+)'
        self.mrsp.append(multiline_rsp.MultilineResponseBuilder(event_start_tag, None, 20, self._extract_event_info))
        self.mrsp.append(multiline_rsp.MultilineResponseBuilder(event_table_size_tag, None, 1, self._extract_max_num_events))

    def _expire_cache(self):
        self.last_req = 0

    def _find_event_by_index(self, event_list, index):
        for e in event_list:
            if e.index == index:
                return e
        return None

    def _find_event_by_id(self, event_list, event_id):
        for e in event_list:
            if e.event_id == event_id:
                return e
        return None

    def _get_next_free_drlc_index(self):
        for i, e in enumerate(self.drlc_events):
            if e.source == EVENT_NOT_SET:
                return i
        for i, e in enumerate(self.drlc_events_to_add):
            if e.source == EVENT_NOT_SET:
                return i
        if len(self.drlc_events) + len(self.drlc_events_to_add) < self.max_num_events:
            return len(self.drlc_events) + len(self.drlc_events_to_add)
        else:
            return None

    def _extract_matched_event_id(self, event, match):
        event.event_id = int(match.group(1),16)

    def _extract_matched_event_source(self, event, match):
        event.source = int(match.group(1),16)

    def _extract_matched_device_class(self, event, match):
        event.device_class = int(match.group(1),16)

    def _extract_matched_utility_group(self, event, match):
        event.utility_group = int(match.group(1),16)

    def _extract_matched_start_time(self, event, match):
        event.start_time = int(match.group(1),16)

    def _extract_matched_duration(self, event, match):
        event.duration = int(match.group(1),16)

    def _extract_matched_criticality(self, event, match):
        event.criticality_value = int(match.group(1),16)

    def _extract_matched_cooling_offset(self, event, match):
        event.cool_temp_offset = clip_number(int(match.group(1)[-2:],16),1)

    def _extract_matched_heating_offset(self, event, match):
        event.heat_temp_offset = clip_number(int(match.group(1)[-2:],16),1)

    def _extract_matched_cooling_set(self, event, match):
        event.cool_temp_set = signed_hex_to_decimal(int(match.group(1)[-4:],16),2)

    def _extract_matched_heating_set(self, event, match):
        event.heat_temp_set = signed_hex_to_decimal(int(match.group(1)[-4:],16),2)

    def _extract_matched_average_load(self, event, match):
        event.average_load = signed_hex_to_decimal(int(match.group(1)[-2:],16),1)

    def _extract_matched_duty_cycle(self, event, match):
        event.duty_cycle = clip_number(int(match.group(1)[-2:],16),1)

    def _extract_matched_event_control(self, event, match):
        event.event_control = int(match.group(1),16)

    def _extract_max_num_events(self, start_match, end_match, rsp):
        self.max_num_events = int(start_match.group(1))
        self.ready = True

    def _extract_event_info(self, start_match, end_match, rsp):
        #= LCE 0 =
        #eid: 0x00000080
        #src: 0x00
        #sep: 0x00
        #dep: 0x00
        #dev: 0x0FFF
        #ueg: 0x00
        # st: 0x00002710
        #dur: 0x0030
        # cl: 0x01
        #cto: 0xFF
        #hto: 0xFF
        #cts: 0xFFFF8000
        #hts: 0xFFFF8000
        #alp: 0x2A
        # dc: 0x32
        # ev: 0x02
        # sr: 0x0000
        # er: 0x0000
        # oc: 0x00
        eid_tag = r'eid: (0x[a-fA-F0-9]+)'
        src_tag = r'src: (0x[a-fA-F0-9]+)'
        dev_tag = r'dev: (0x[a-fA-F0-9]+)'
        ueg_tag = r'ueg: (0x[a-fA-F0-9]+)'
        start_tag = r' st: (0x[a-fA-F0-9]+)'
        duration_tag = r'dur: (0x[a-fA-F0-9]+)'
        criticality_tag = r' cl: (0x[a-fA-F0-9]+)'
        cto_tag = r'cto: (0x[a-fA-F0-9]+)'
        hto_tag = r'hto: (0x[a-fA-F0-9]+)'
        cts_tag = r'cts: (0x[a-fA-F0-9]+)'
        hts_tag = r'hts: (0x[a-fA-F0-9]+)'
        avgload_tag = r'alp: (0x[a-fA-F0-9]+)'
        dutycycle_tag = r' dc: (0x[a-fA-F0-9]+)'
        ectrl_tag = r' ev: (0x[a-fA-F0-9]+)'
        tags = [(eid_tag,           self._extract_matched_event_id),
                (src_tag,           self._extract_matched_event_source),
                (dev_tag,           self._extract_matched_device_class),
                (ueg_tag,           self._extract_matched_utility_group),
                (start_tag,         self._extract_matched_start_time),
                (duration_tag,      self._extract_matched_duration),
                (criticality_tag,   self._extract_matched_criticality),
                (cto_tag,           self._extract_matched_cooling_offset),
                (hto_tag,           self._extract_matched_heating_offset),
                (cts_tag,           self._extract_matched_cooling_set),
                (hts_tag,           self._extract_matched_heating_set),
                (avgload_tag,       self._extract_matched_average_load),
                (dutycycle_tag,     self._extract_matched_duty_cycle),
                (ectrl_tag,         self._extract_matched_event_control),]
        event_index = int(start_match.group(1))
        self.lock.acquire()

        the_event = self._find_event_by_index(self.drlc_events, event_index)
        if the_event is None:
            the_event = ZbDrlcEvent(index=event_index)
            the_event.source = EVENT_NOT_SET
            self.drlc_events.append(the_event)

        tag_index = 0
        t, f = tags[tag_index]
        for line in rsp:
            match = re.search(t, line)
            if match:
                f(the_event, match)
                if tag_index + 1 < len(tags):
                    tag_index = tag_index + 1
                    t, f = tags[tag_index]
        #self.logger.log('%s', the_event)
        if the_event.is_set() and the_event.is_valid():
            global current_issuer_event_id
            for e in self.drlc_events:
                if e.event_id > current_issuer_event_id:
                    current_issuer_event_id = e.event_id
            self.drlc_events.sort(key=lambda e: e.index)
        else:
            self.drlc_events.remove(the_event)
        self.lock.release()

    def get_all_events(self):
        """Return DRLC events in [dictionary] format"""
        all_events = []
        for e in self.drlc_events:
            if e.source != EVENT_NOT_SET:
                all_events.append(e.get_event())
        return all_events

    def add_event(self, **kwargs):
        status = False
        if self.ready:
            self.lock.acquire()
            try:
                the_event = ZbDrlcEvent(**kwargs)
                # find an empty index
                the_event.index = self._get_next_free_drlc_index()
                #self.logger.log('%s', the_event.index)
                if the_event.index is not None:
                    # fill in event ID
                    the_event.event_id = get_next_issuer_event_id()
                    # insert to list and sort
                    self.drlc_events_to_add.append(the_event)
                    self.drlc_events_to_add.sort(key=lambda e: e.index)
                    status = True
            except BadArgumentError, e:
                pass
            finally:
                self.lock.release()
        return status

    def rm_event(self, event_id):
        if self.ready and len(self.pending_cmd) < self.max_num_events*5:
            self.lock.acquire()
            e = self._find_event_by_id(self.drlc_events, event_id)
            if e is not None:
                # TODO: add remove single event to smart meter
                # command below does not exist yet
                self.pending_cmd.append('plugin drlc-server clce %d %d\n' % (self.end_point, e.index))
                self._expire_cache()
                self.refresh_drlc_table()
                self.drlc_events.remove(e)
                self.lock.release()
                return True
            e = self._find_event_by_id(self.drlc_events_to_add, event_id)
            if e is not None:
                self.drlc_events_to_add.remove(e)
                self.lock.release()
                return True
            self.lock.release()
        return False

    def rm_all_events(self):
        if self.ready and len(self.pending_cmd) == 0:
            self.lock.acquire()
            self.drlc_events = []
            self.drlc_events_to_add = []
            self.pending_cmd.append('plugin drlc-server cslce %d\n' % self.end_point)
            self._expire_cache()
            self.refresh_drlc_table()
            self.lock.release()
            return True
        return False

    def send_event(self, event_id, dst_node_id, dst_end_point):
        #plugin drlc-server sslce <nodeId:2> <srcEndpoint:1> <dstEndpoint:1> <index:1>
        #plugin drlc-server sslce 0x25d7 1 9 0
        status = False
        if self.ready and \
           dst_node_id >= 0 and dst_node_id <= 0xFFFF and \
           dst_end_point > 0 and dst_end_point < 0xFF and \
           len(self.pending_cmd) < self.max_num_events*5:
            self.lock.acquire()
            e = self._find_event_by_id(self.drlc_events, event_id)
            if e is not None:
                self.pending_cmd.append('plugin drlc-server sslce 0x%x %d %d %d\n' % (dst_node_id, self.end_point, dst_end_point, e.index))
                status = True
            self.lock.release()
        return status

    def refresh_drlc_table(self):
        now = time.time()
        if now - self.last_req > self.cache_duration:
            self.read_drlc_table = True

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
        if len(self.drlc_events_to_add) > 0:
            for e in self.drlc_events_to_add:
                #self.logger.log('cmd: %s', e)
                cmds.append('plugin drlc-server slce %d %d %d {%s}\n' % (self.end_point, e.index, e.data_length, e.set_event_raw_bytes()))
                entry = self._find_event_by_index(self.drlc_events, e.index)
                if entry is not None:
                    self.drlc_events.remove(entry)
                    self.drlc_events.append(e)
            self.drlc_events.sort(key=lambda e: e.index)
            self._expire_cache()
            self.refresh_drlc_table()
            self.drlc_events_to_add = []
        if self.read_drlc_table:
            self.read_drlc_table = False
            cmds.append('plugin drlc-server print %d\n' % self.end_point)
            self.last_req = time.time()
        self.lock.release()
        return cmds
