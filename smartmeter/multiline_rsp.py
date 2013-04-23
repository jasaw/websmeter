"""
multiline response handler.
"""   
import re

import logger


class MultilineResponseBuilder(object):

    def __init__(self, start_tag, end_tag, max_num_lines, response_handler):
        self.logger = logger.Logger('mlrsp')
        self.start_tag = start_tag
        self.end_tag = end_tag
        self.max_num_lines = max_num_lines
        self.response_handler = response_handler
        self._reset_state()

    def _reset_state(self):
        self.lines_so_far = []
        self.expect_more_lines = False
        self.start_match = None
        self.end_match = None

    def process_one_response_line(self, rsp_line):
        accepted = False
        match = re.search(self.start_tag, rsp_line)
        if match:
            #self.logger.log('found start')
            self.lines_so_far = [rsp_line]
            self.start_match = match
            self.end_match = None
            self.expect_more_lines = True
            accepted = True
        elif self.expect_more_lines:
            if self.end_tag is not None:
                match = re.search(self.end_tag, rsp_line)
                if match:
                    #self.logger.log('found end')
                    self.lines_so_far.append(rsp_line)
                    self.end_match = match
                    accepted = True
                    self.response_handler(self.start_match, self.end_match, self.lines_so_far)
                    self._reset_state()
            if not accepted:
                #self.logger.log('append')
                self.lines_so_far.append(rsp_line)
                accepted = True
        if len(self.lines_so_far) >= self.max_num_lines:
            #self.logger.log('warning: too many response lines')
            self.response_handler(self.start_match, self.end_match, self.lines_so_far)
            self._reset_state()
        return accepted
