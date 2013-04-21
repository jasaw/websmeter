"""
zigbee diagnose manager
"""   

import time
import string
import threading
import re
import random

import logger
import multiline_rsp



class ChildTableEntry(object):
    def __init__(self, index, nodetype, nodeid, macaddr):
        self.index = index
        self.nodetype = nodetype # string
        self.nodeid = nodeid
        self.macaddr = macaddr # string

    def __repr__(self):
        return repr((self.index, self.nodetype, self.nodeid, self.macaddr))

    def get_info(self):
        info = {}
        info['nodetype'] = self.nodetype
        info['nodeid'] = self.nodeid
        info['macaddr'] = self.macaddr
        return info



class NeighbourTableEntry(object):
    def __init__(self, index, nodeid, macaddr, lqi, num_in, num_out, age):
        self.index = index
        self.nodeid = nodeid
        self.macaddr = macaddr # string
        self.lqi = lqi
        self.num_in = num_in
        self.num_out = num_out
        self.age = age

    def __repr__(self):
        return repr((self.index, self.nodeid, self.macaddr, self.lqi, self.num_in, self.num_out, self.age))

    def get_info(self):
        info = {}
        info['nodeid'] = self.nodeid
        info['macaddr'] = self.macaddr
        info['lqi'] = self.lqi
        info['in'] = self.num_in
        info['out'] = self.num_out
        info['age'] = self.age
        return info



class RouteTableEntry(object):
    def __init__(self, index, nodeid, nextnode, age, conc, status):
        self.index = index
        self.nodeid = nodeid
        self.nextnode = nextnode
        self.age = age
        self.conc = conc # string
        self.status = status # string

    def __repr__(self):
        return repr((self.index, self.nodeid, self.nextnode, self.age, self.conc, self.status))

    def get_info(self):
        info = {}
        info['nodeid'] = self.nodeid
        info['next'] = self.nextnode
        info['age'] = self.age
        info['conc'] = self.conc
        info['status'] = self.status
        return info




class ZbDiagMgr(object):

    #smartmeter>plugin stack-diagnostics child-table
    ##  type    id     eui64
    #0: Sleepy  0x0718 (>)D103C0B7DDA60003
    #
    #1 of 20 entries used.

    #smartmeter>plugin stack-diagnostics neighbor-table
    ##  id     lqi  in  out  age  eui
    #0: 0x0D80 255  1   1    3    (>)8CEEC60101000054
    #
    #1 of 16 entries used.

    #smartmeter>plugin stack-diagnostics route-table
    ##  id      next    age  conc    status
    #0: 0x0000  0x0000  0   low    discovering
    #
    #1 of 16 entries used.

    def __init__(self):
        self.logger = logger.Logger('zbdiagmgr')
        self.read_diag = True
        self.last_req = 0
        self.cache_duration = 10
        self.lock = threading.Lock()
        self.mrsp = []
        # child table
        self.child_table = []
        self.child_table_min_lines = 3
        self.child_table_max_num_entries = 20
        child_table_start_tag = r'#  type    id     eui64'
        child_table_end_tag = r'[0-9]+ of ([0-9]+) entries used.'
        self.child_table_mrsp = multiline_rsp.MultilineResponseBuilder(child_table_start_tag, child_table_end_tag, self.child_table_min_lines + self.child_table_max_num_entries, self._extract_child_table)
        self.mrsp.append(self.child_table_mrsp)
        # neighbour table
        self.neighbour_table = []
        self.neighbour_table_min_lines = 3
        self.neighbour_table_max_num_entries = 16
        neighbour_table_start_tag = r'#  id     lqi  in  out  age  eui'
        neighbour_table_end_tag = r'[0-9]+ of ([0-9]+) entries used.'
        self.neighbour_table_mrsp = multiline_rsp.MultilineResponseBuilder(neighbour_table_start_tag, neighbour_table_end_tag, self.neighbour_table_min_lines + self.neighbour_table_max_num_entries, self._extract_neighbour_table)
        self.mrsp.append(self.neighbour_table_mrsp)
        # route table
        self.route_table = []
        self.route_table_min_lines = 3
        self.route_table_max_num_entries = 16
        route_table_start_tag = r'#  id      next    age  conc    status'
        route_table_end_tag = r'[0-9]+ of ([0-9]+) entries used.'
        self.route_table_mrsp = multiline_rsp.MultilineResponseBuilder(route_table_start_tag, route_table_end_tag, self.route_table_min_lines + self.route_table_max_num_entries, self._extract_route_table)
        self.mrsp.append(self.route_table_mrsp)

    def _expire_cache(self):
        self.last_req = 0

    def get_child_table(self):
        all_entries = []
        for e in self.child_table:
            all_entries.append(e.get_info())
        return all_entries

    def get_neighbour_table(self):
        all_entries = []
        for e in self.neighbour_table:
            all_entries.append(e.get_info())
        return all_entries

    def get_route_table(self):
        all_entries = []
        for e in self.route_table:
            all_entries.append(e.get_info())
        return all_entries

    def _extract_child_entry(self, match):
        index = int(match.group(1))
        nodetype = match.group(2).strip()
        nodeid = int(match.group(3),16)
        macaddr = match.group(4).upper()
        self.child_table.append(ChildTableEntry(index, nodetype, nodeid, macaddr))

    def _extract_child_table(self, start_match, end_match, rsp):
        #0: Sleepy  0x0718 (>)D103C0B7DDA60003
        if end_match is not None:
            self.child_table_max_num_entries = int(end_match.group(1))
            self.child_table_mrsp.max_num_line = self.child_table_min_lines + self.child_table_max_num_entries
        node_tag = r'([0-9]+): (.+) (0x[a-fA-F0-9]+) \(>\)([a-fA-F0-9]{16})'
        self.child_table = []
        for line in rsp:
            match = re.search(node_tag, line)
            if match:
                self._extract_child_entry(match)
        self.child_table.sort(key=lambda k: k.index)

    def _extract_neighbour_entry(self, match):
        index = int(match.group(1))
        nodeid = int(match.group(2),16)
        lqi = int(match.group(3))
        num_in = int(match.group(4))
        num_out = int(match.group(5))
        age = int(match.group(6))
        macaddr = match.group(7).upper()
        self.neighbour_table.append(NeighbourTableEntry(index, nodeid, macaddr, lqi, num_in, num_out, age))

    def _extract_neighbour_table(self, start_match, end_match, rsp):
        #0: 0x0D80 255  1   1    3    (>)8CEEC60101000054
        if end_match is not None:
            self.neighbour_table_max_num_entries = int(end_match.group(1))
            self.neighbour_table_mrsp.max_num_line = self.neighbour_table_min_lines + self.neighbour_table_max_num_entries
        node_tag = r'([0-9]+): (0x[a-fA-F0-9]+) ([0-9]+)[ ]+([0-9]+)[ ]+([0-9]+)[ ]+([0-9]+)[ ]+\(>\)([a-fA-F0-9]{16})'
        self.neighbour_table = []
        for line in rsp:
            match = re.search(node_tag, line)
            if match:
                self._extract_neighbour_entry(match)
        self.neighbour_table.sort(key=lambda k: k.index)

    def _extract_route_entry(self, match):
        index = int(match.group(1))
        nodeid = int(match.group(2),16)
        nextnode = int(match.group(3),16)
        age = int(match.group(4))
        conc = match.group(5).strip()
        status = match.group(6).strip()
        self.route_table.append(RouteTableEntry(index, nodeid, nextnode, age, conc, status))

    def _extract_route_table(self, start_match, end_match, rsp):
        #0: 0x0000  0x0000  0   low    discovering
        if end_match is not None:
            self.route_table_max_num_entries = int(end_match.group(1))
            self.route_table_mrsp.max_num_line = self.route_table_min_lines + self.route_table_max_num_entries
        node_tag = r'([0-9]+): (0x[a-fA-F0-9]+)[ ]+(0x[a-fA-F0-9]+)[ ]+([0-9]+)[ ]+([a-zA-Z]+)[ ]+(.+)'
        self.route_table = []
        for line in rsp:
            match = re.search(node_tag, line)
            if match:
                self._extract_route_entry(match)
        self.route_table.sort(key=lambda k: k.index)

    def handle_rsp(self, rsp_line):
        accepted = False
        for m in self.mrsp:
            accepted = m.process_one_response_line(rsp_line)
            if accepted:
                break
        return accepted

    def refresh_diag_info(self):
        now = time.time()
        if now - self.last_req > self.cache_duration:
            self.read_diag = True

    def process(self):
        cmds = []
        if self.read_diag:
            self.lock.acquire()
            self.read_diag = False
            cmds.append('plugin stack-diagnostics child-table\n')
            cmds.append('plugin stack-diagnostics neighbor-table\n')
            cmds.append('plugin stack-diagnostics route-table\n')
            self.last_req = time.time()
            self.lock.release()
        return cmds
