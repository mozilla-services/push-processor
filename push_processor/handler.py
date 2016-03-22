"""Handler functions for running under Lambda or otherwise"""
import json
import os

import redis
from twisted.logger import eventsFromJSONLogFile

from push_processor.aws_helpers import s3_open
from push_processor.db import (
    get_all_keys,
    dump_latest_messages_to_redis
)
from push_processor.heka import read_heka_file_stream
from push_processor.message import Message
from push_processor.processor.pubkey import PubKeyProcessor


class Lambda(object):
    __instance = None

    def __new__(cls):
        """Singleton instance to avoid repeat setup"""
        if Lambda.__instance is None:
            Lambda.__instance = object.__new__(cls)
        return Lambda.__instance

    def __init__(self):
        here_dir = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(here_dir, "settings.js")) as f:
            settings = json.load(f)

        # Load S3 config settings if supplied
        if "s3_bucket" in settings:
            f = s3_open(settings["s3_bucket"], settings["s3_key"])
            s3_config = json.loads(f.read())
            settings.update(s3_config)

        self.redis_server = redis.StrictRedis(
            host=settings["redis_host"],
            port=settings["redis_port"]
        )
        self.settings = settings

    @classmethod
    def handler(cls, event, context):
        return cls().handle_event(event, context)

    def handle_event(self, event, context):
        if "Bucket" in event:
            # S3 test event, return
            return "Test event"

        # Check that we have a record
        if "Records" not in event:
            return "No record found in event"

        pub_keys = get_all_keys(self.settings["db_tablename"])
        processor = PubKeyProcessor(pub_keys)
        use_gzip = self.settings.get("use_gzip", False)

        for record in event["Records"]:
            s3_obj = record["s3"]
            bucket, key = s3_obj["bucket"]["name"], s3_obj["object"]["key"]
            f = s3_open(bucket, key, use_gzip=use_gzip)
            if self.settings["file_type"] == "heka":
                self.process_heka_stream(processor, f)
            else:
                self.process_json_stream(processor, f)

    def process_heka_stream(self, processor, stream):
        reader = read_heka_file_stream(stream)
        for msg in reader:
            processor.process_message(msg)
        dump_latest_messages_to_redis(self.redis_server,
                                      processor.latest_messages)

    def process_json_stream(self, processor, stream):
        for msg in eventsFromJSONLogFile(stream):
            processor.process_message(Message(json=msg))
        dump_latest_messages_to_redis(self.redis_server,
                                      processor.latest_messages)
