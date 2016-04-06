import json
import unittest

from nose.tools import eq_

from push_processor.message import Message

TEST_MESSAGE = """\
{"EnvVersion": "2.0", "Severity": 5, "Timestamp": 1.457400685716216e+18, \
"Hostname": "lmnt", "Fields": {"task_uuid": \
"92ec4b44-29e4-46de-9225-dce163197b31", "message": "Stopping protocol\
 <txstatsd.protocol.StatsDClientProtocol instance at 0x7f8e9b3c4200>", \
 "system": "StatsDClientProtocol (UDP)", "error": false}, "Logger": \
 "Autopush-1.13", "Type": "twisted:log"}
"""


class TestPubKeyProcessor(unittest.TestCase):
    def _makeFUT(self, pubkey_list):
        from push_processor.processor.pubkey import PubKeyProcessor
        return PubKeyProcessor(pubkey_list)

    def test_messages(self):
        proc = self._makeFUT(["asdfasdf"])
        msg = Message(json=json.loads(TEST_MESSAGE))
        proc.process_message(msg)
        eq_(len(proc.latest_messages), 0)

        msg.fields["message"] = "Something"
        msg.fields["jwt_crypto_key"] = "fred"
        proc.process_message(msg)
        eq_(len(proc.latest_messages), 0)

        msg.fields["message"] = "Successful delivery"
        msg.fields["jwt_crypto_key"] = "fred"
        proc.process_message(msg)
        eq_(len(proc.latest_messages), 0)

        msg.fields["jwt_crypto_key"] = "asdfasdf"
        proc.process_message(msg)
        eq_(len(proc.latest_messages), 1)
