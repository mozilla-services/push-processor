import json
import unittest

from nose.tools import eq_

TEST_MESSAGE = """\
{"EnvVersion": "2.0", "Severity": 5, "Timestamp": 1.457400685716216e+18, \
"Hostname": "lmnt", "Fields": {"task_uuid": \
"92ec4b44-29e4-46de-9225-dce163197b31", "message": "Stopping protocol\
 <txstatsd.protocol.StatsDClientProtocol instance at 0x7f8e9b3c4200>", \
 "system": "StatsDClientProtocol (UDP)", "error": false}, "Logger": \
 "Autopush-1.13", "Type": "twisted:log"}
"""


class TestMessage(unittest.TestCase):
    def _makeFUT(self, **kwargs):
        from push_processor.message import Message
        return Message(**kwargs)

    def test_json_message(self):
        m = self._makeFUT(json=json.loads(TEST_MESSAGE))
        eq_(len(m.fields), 4)
        eq_(m.logger, "Autopush-1.13")

    def test_bad_args(self):
        self.assertRaises(Exception, self._makeFUT)
