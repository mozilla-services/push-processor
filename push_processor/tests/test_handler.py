import copy
import json
import os
import StringIO
import unittest
import uuid

import redis
from nose.tools import eq_, ok_

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
    def test_setup(self):
        import push_processor.handler as handler
        handler.setup_objects()
        eq_(len(handler.settings), 6)
        ok_("redis_host" in handler.settings)

    def test_lambda(self):
        import push_processor.handler as handler
        handler.redis_server = None
        result = handler.aws_lambda(dict(
            Bucket=""
        ), None)
        eq_(result, "Test event")

        handler.redis_server = None
        result = handler.aws_lambda(dict(), None)
        eq_(result, "No record found in event")

        result = handler.aws_lambda(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="test_protobuf_stream.gz")
                          ))]
        ), None)
        eq_(result, None)

    def test_json_process(self):
        pkey = uuid.uuid4().hex
        from push_processor.processor.pubkey import PubKeyProcessor
        from push_processor.handler import process_json_stream
        proc = PubKeyProcessor([pkey])
        msg = json.loads(TEST_MESSAGE)
        msg["Fields"]["jwt"] = {"crypto_key": pkey}
        msg["Fields"]["message_id"] = "jailj24il2j424ijiljlija"
        msg["Fields"]["message_size"] = 312
        msg["Fields"]["message_ttl"] = 600
        f = StringIO.StringIO(json.dumps(msg))
        redis_server = redis.StrictRedis()
        process_json_stream(redis_server, proc, f)
        eq_(redis_server.exists(pkey), True)
        eq_(redis_server.llen(pkey), 1)

        # Now run with at least 100 messages
        messages = []
        for _ in range(0, 100):
            nmsg = copy.deepcopy(msg)
            nmsg["Fields"]["message_id"] = str(uuid.uuid4())
            messages.append(nmsg)
        f = StringIO.StringIO("\n".join([json.dumps(m) for m in messages]))
        process_json_stream(redis_server, proc, f)
        eq_(redis_server.exists(pkey), True)
        eq_(redis_server.llen(pkey), 100)
