import copy
import json
import StringIO
import unittest
import uuid

import redis
from mock import Mock, patch
from nose.tools import eq_, raises

from push_processor.handler import ConfigException


TEST_MESSAGE = """\
{"EnvVersion": "2.0", "Severity": 5, "Timestamp": 1.457400685716216e+18, \
"Hostname": "lmnt", "Fields": {"task_uuid": \
"92ec4b44-29e4-46de-9225-dce163197b31", "message": "Successful delivery", \
 "system": "StatsDClientProtocol (UDP)", "error": false}, "Logger": \
 "Autopush-1.13", "Type": "twisted:log"}
"""


def setUp():
    import push_processor.aws_helpers as aws
    from botocore.handlers import disable_signing
    aws.s3.meta.client.meta.events.register(
        'choose-signer.s3.*', disable_signing)


class Effect(object):
    def __init__(self, responses):
        self._index = 0
        self._responses = responses

    def __call__(self, *args, **kwargs):
        i = self._index
        self._index += 1
        if callable(self._responses[i]):
            return self._responses[i](*args, **kwargs)
        else:
            return self._responses[i]


class TestHandler(unittest.TestCase):
    def setUp(self):
        import push_processor.handler as handler
        self._orig_s3_open = handler.aws_helpers.s3_open
        handler.Lambda._reset()

    def tearDown(self):
        import push_processor.handler as handler
        handler.Lambda.s3_open = staticmethod(handler.aws_helpers.s3_open)

    @raises(ConfigException)
    def test_lamda_no_settings(self):
        import push_processor.handler as handler
        handler.Lambda.handler({}, None)

    @patch("push_processor.handler.boto3")
    def test_lambda_elasticache(self, mock_boto):
        import push_processor.handler as handler

        # Swap out the settings
        handler.Lambda.s3_open = s3_mock = Mock()

        s3_mock.side_effect = Effect([
            StringIO.StringIO(
                json.dumps(dict(redis_name="some_cluster_name",
                                db_tablename="push_messages_db",
                                file_type="heka"))
            ),
            self._orig_s3_open
        ])

        # Add in Redis lookups
        mock_boto.client.return_value = es_mock = Mock()
        es_mock.describe_cache_clusters.return_value = dict(
            CacheClusters=[
                dict(
                    CacheNodes=[
                        dict(Endpoint=dict(Address="localhost"))
                    ]
                )
            ]
        )

        # Do basic run
        result = handler.Lambda.handler(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="test_protobuf_stream.gz")
                          ))]
        ), None)
        eq_(result, None)
        eq_(len(es_mock.describe_cache_clusters.mock_calls), 1)

    @raises(ConfigException)
    def test_lambda_elasticache_no_cluster(self):
        import push_processor.handler as handler
        # Swap out the settings
        handler.Lambda.s3_open = s3_mock = Mock()

        s3_mock.side_effect = Effect([
            StringIO.StringIO(
                json.dumps(dict(redis_name="some_cluster_name",
                                db_tablename="push_messages_db",
                                file_type="heka"))
            ),
            self._orig_s3_open
        ])

        # Add in Redis lookups
        handler.Lambda._es_client = es_mock = Mock()
        es_mock.describe_cache_clusters.return_value = dict(
            CacheClusters=[]
        )

        # Do basic run
        handler.Lambda.handler(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="test_protobuf_stream.gz")
                          ))]
        ), None)

    def test_lambda(self):
        import push_processor.handler as handler
        result = handler.Lambda.handler(dict(
            Bucket=""
        ), None)
        eq_(result, "Test event")

        # Test event
        result = handler.Lambda.handler(dict(Bucket=""), None)
        eq_(result, "Test event")

        # Swap out the settings
        handler.Lambda.s3_open = s3_mock = Mock()

        s3_mock.side_effect = Effect([
            StringIO.StringIO(
                json.dumps(dict(redis_host="localhost",
                                db_tablename="push_messages_db",
                                file_type="heka"))
            ),
            self._orig_s3_open
        ])

        result = handler.Lambda.handler(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="test_protobuf_stream.gz")
                          ))]
        ), None)
        eq_(result, None)

        s3_mock.side_effect = Effect([
            StringIO.StringIO(
                json.dumps(dict(redis_host="localhost",
                                db_tablename="push_messages_db",
                                file_type="heka"))
            ),
            self._orig_s3_open
        ])
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

        handler.Lambda.s3_open = s3_mock = Mock()
        s3_mock.side_effect = Effect([
            StringIO.StringIO(
                json.dumps(dict(redis_host="localhost",
                                db_tablename="push_messages_db",
                                file_type="json"))
            ),
            self._orig_s3_open
        ])

        l = handler.Lambda(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="push_dash_logs.json")
                          ))]
        ), None)

        result = l.handle_event(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="push_dash_logs.json")
                          ))]
        ), None)
        eq_(result, None)
        eq_(len(mock_processor.process_message.mock_calls), 407)

    def test_skip_processor_file(self):
        import push_processor.handler as handler

        handler.Lambda.s3_open = s3_mock = Mock()
        s3_mock.side_effect = Effect([
            StringIO.StringIO(
                json.dumps(dict(redis_host="localhost",
                                db_tablename="push_messages_db",
                                file_type="json"))
            ),
        ])

        handler.Lambda.handler(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="processor_settings.json")
                          ))]
        ), None)
        s3_mock.assert_called_with("push-test", "processor_settings.json")

    def test_json_process(self):
        import push_processor.handler as handler
        pkey = uuid.uuid4().hex
        from push_processor.processor.pubkey import PubKeyProcessor
        handler.Lambda.s3_open = s3_mock = Mock()
        s3_mock.return_value = StringIO.StringIO(
            json.dumps(dict(redis_host="localhost",
                            file_type="json"))
        )
        l = handler.Lambda(dict(
            Records=[dict(s3=dict(
                          bucket=dict(name="push-test"),
                          object=dict(key="push_dash_logs.json")
                          ))]
        ), None)

        proc = PubKeyProcessor([pkey])
        msg = json.loads(TEST_MESSAGE)
        msg["Fields"]["jwt_crypto_key"] = pkey
        msg["Fields"]["message_id"] = "jailj24il2j424ijiljlija"
        msg["Fields"]["message_size"] = 312
        msg["Fields"]["message_ttl"] = 600
        f = StringIO.StringIO(json.dumps(msg))
        l.redis_server = redis.StrictRedis()
        l.redis_server.hset("registered_keys", pkey, "")
        l.process_json_stream(proc, f)
        l.dump_latest_messages_to_redis(proc.latest_messages)
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
        l.dump_latest_messages_to_redis(proc.latest_messages)
        eq_(l.redis_server.exists(pkey), True)
        eq_(l.redis_server.llen(pkey), 100)
