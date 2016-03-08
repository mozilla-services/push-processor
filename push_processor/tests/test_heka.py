import os
import unittest

from nose.tools import eq_


here_dir = os.path.abspath(os.path.dirname(__file__))


class TestHeka(unittest.TestCase):
    def _makeFUT(self, obj):
        from push_processor.heka import read_heka_file_stream
        return read_heka_file_stream(obj)

    def test_read(self):
        filename = os.path.join(here_dir, "test_protobuf_stream")
        f = open(filename)
        out = self._makeFUT(f)
        m = out.next()
        eq_(m.logger, "flood")
        eq_(len(m.fields), 13)

        m = out.next()
        eq_(m.logger, "flood")

        # Drain the rest
        count = 0
        for m in out:
            count += 1
        eq_(count, 48)


class TestAWSHeka(unittest.TestCase):
    def _makeIUT(self, bucket, key):
        import push_processor.aws_helpers as aws
        from botocore.handlers import disable_signing
        aws.s3.meta.client.meta.events.register(
            'choose-signer.s3.*', disable_signing)
        from push_processor.heka import read_heka_file_stream
        from push_processor.aws_helpers import s3_open
        return read_heka_file_stream(s3_open(bucket, key))

    def test_gzip_stream(self):
        out = self._makeIUT("push-test", "test_protobuf_stream.gz")
        m = out.next()
        eq_(m.logger, "flood")
        eq_(len(m.fields), 13)
        # Drain the rest
        count = 0
        for m in out:
            count += 1
        eq_(count, 49)

    def test_uncompressed_stream(self):
        out = self._makeIUT("push-test", "test_protobuf_stream")
        m = out.next()
        eq_(m.logger, "flood")
        eq_(len(m.fields), 13)
        # Drain the rest
        count = 0
        for m in out:
            count += 1
        eq_(count, 49)
