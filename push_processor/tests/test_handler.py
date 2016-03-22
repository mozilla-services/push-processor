import copy
import json
import os
import StringIO
import unittest
import uuid

import redis
from mock import Mock, patch
from nose.tools import eq_

import push_messages.tests as pmtests

TEST_MESSAGE = """\
{"EnvVersion": "2.0", "Severity": 5, "Timestamp": 1.457400685716216e+18, \
"Hostname": "lmnt", "Fields": {"task_uuid": \
"92ec4b44-29e4-46de-9225-dce163197b31", "message": "Successful delivery", \
 "system": "StatsDClientProtocol (UDP)", "error": false}, "Logger": \
 "Autopush-1.13", "Type": "twisted:log"}
"""

here_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.dirname(os.path.dirname(here_dir))
ddb_dir = os.path.join(root_dir, "ddb")
ddb_lib_dir = os.path.join(ddb_dir, "DynamoDBLocal_lib")
ddb_jar = os.path.join(ddb_dir, "DynamoDBLocal.jar")


def setUp():
    pmtests.ddb_jar = ddb_jar
    pmtests.setUp()
    import push_processor.aws_helpers as aws
    from botocore.handlers import disable_signing
    aws.s3.meta.client.meta.events.register(
        'choose-signer.s3.*', disable_signing)


def tearDown():
    pmtests.tearDown()


class TestHandler(unittest.TestCase):
    def test_lambda(self):
        import push_processor.handler as handler
        result = handler.Lambda.handler(dict(
            Bucket=""
        ), None)
        eq_(result, "Test event")

        result = handler.Lambda.handler(dict(), None)
        eq_(result, "No record found in event")

        result = handler.Lambda.handler(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="test_protobuf_stream.gz")
                          ))]
        ), None)
        eq_(result, None)

    @patch("push_processor.handler.PubKeyProcessor")
    def test_lambda_with_json(self, mock_pubkey):
        import push_processor.handler as handler
        mock_pubkey.return_value = mock_processor = Mock()
        mock_processor.latest_messages = {}
        l = handler.Lambda()

        l.settings = {
            "s3_bucket": "push-test",
            "s3_key": "opts.js",
            "redis_port": 6379,
            "db_tablename": "push_messages_db",
            "file_type": "json"
        }

        result = l.handle_event(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="push_dash_logs.json")
                          ))]
        ), None)
        eq_(result, None)
        eq_(len(mock_processor.process_message.mock_calls), 407)

    def test_json_process(self):
        pkey = uuid.uuid4().hex
        from push_processor.processor.pubkey import PubKeyProcessor
        from push_processor.handler import Lambda
        l = Lambda()
        proc = PubKeyProcessor([pkey])
        msg = json.loads(TEST_MESSAGE)
        msg["Fields"]["jwt"] = {"crypto_key": pkey}
        msg["Fields"]["message_id"] = "jailj24il2j424ijiljlija"
        msg["Fields"]["message_size"] = 312
        msg["Fields"]["message_ttl"] = 600
        f = StringIO.StringIO(json.dumps(msg))
        l.redis_server = redis.StrictRedis()
        l.process_json_stream(proc, f)
        eq_(l.redis_server.exists(pkey), True)
        eq_(l.redis_server.llen(pkey), 1)

        # Now run with at least 100 messages
        messages = []
        for _ in range(0, 100):
            nmsg = copy.deepcopy(msg)
            nmsg["Fields"]["message_id"] = str(uuid.uuid4())
            messages.append(nmsg)
        f = StringIO.StringIO("\n".join([json.dumps(m) for m in messages]))
        l.process_json_stream(proc, f)
        eq_(l.redis_server.exists(pkey), True)
        eq_(l.redis_server.llen(pkey), 100)
