"""Handler functions for running under Lambda or otherwise"""
from __future__ import print_function

import json

import boto3
import redis
from twisted.logger import eventsFromJSONLogFile

import push_processor
import push_processor.aws_helpers as aws_helpers
from push_processor.heka import read_heka_file_stream
from push_processor.message import Message
from push_processor.processor.pubkey import PubKeyProcessor


class ConfigException(Exception):
    pass


class Lambda(object):
    s3_open = staticmethod(aws_helpers.s3_open)
    __instance = None

    @classmethod
    def _reset(cls):
        """Resets the singleton, mainly for testing"""
        cls.__instance = None

    def __new__(cls, event, context):
        """Singleton instance to avoid repeat setup"""
        # We don't cache test calls
        if "Bucket" in event:
            return object.__new__(cls)

        if Lambda.__instance is None:
            Lambda.__instance = object.__new__(cls)
        return Lambda.__instance

    def __init__(self, event, context):
        # Test event
        if "Bucket" in event:
            return

        # Attempt to locate a settings file
        try:
            s3_rec = event["Records"][0]["s3"]
            bucket = s3_rec["bucket"]["name"]
            print("Attempting to load config data from bucket: "
                  "{}".format(bucket))
            f = self.s3_open(bucket, "processor_settings.json")
            s3_config = json.loads(f.read())
            settings = s3_config
        except Exception as exc:
            raise ConfigException("No settings found: {}".format(exc))

        if "redis_name" in settings:
            # Locate elasticache instance, bail if not ready
            print("Loading Redis endpoint config")
            result = self.es_client.describe_cache_clusters(
                CacheClusterId=settings["redis_name"],
                ShowCacheNodeInfo=True,
            )
            if not result["CacheClusters"]:
                raise ConfigException("No cache cluster found of id: %s" %
                                      settings["redis_name"])
            cluster = result["CacheClusters"][0]
            print("Cluster info: {}".format(cluster))
            redis_host = cluster["CacheNodes"][0]["Endpoint"]["Address"]
        else:
            redis_host = settings["redis_host"]

        self.redis_server = redis.StrictRedis(
            host=redis_host,
            port=settings.get("redis_port", 6379)
        )
        self.settings = settings
        print("Loaded all settings.")

    @property
    def es_client(self):
        try:
            return self._es_client
        except AttributeError:
            self._es_client = boto3.client('elasticache')
            return self._es_client

    @classmethod
    def handler(cls, event, context):
        return cls(event, context).handle_event(event, context)

    def handle_event(self, event, context):
        if "Bucket" in event:
            # S3 test event, return
            return "Test event"

        print("Running push_processor, version: {}".format(
            push_processor.__version__))
        pub_keys = self.get_all_keys()
        print("Found {} public keys to search for.".format(len(pub_keys)))
        processor = PubKeyProcessor(pub_keys)
        use_gzip = self.settings.get("use_gzip", False)

        print("Processing records")
        for record in event["Records"]:
            s3_obj = record["s3"]
            bucket, key = s3_obj["bucket"]["name"], s3_obj["object"]["key"]
            if key == "processor_settings.json":
                # Don't process changes to our config file
                continue

            print("Attempting to load bucket: {}, key: {}".format(bucket, key))
            f = self.s3_open(bucket, key, use_gzip=use_gzip)
            if self.settings["file_type"] == "heka":
                self.process_heka_stream(processor, f)
            else:
                self.process_json_stream(processor, f)
            self.dump_latest_messages_to_redis(processor.latest_messages)
        total_messages = processor.total
        total_flagged = processor.flagged
        print("Processed {} records, found {} messages to log for {} "
              "public keys.".format(total_messages, total_flagged,
                                    len(processor.latest_messages))
              )

    def process_heka_stream(self, processor, stream):
        reader = read_heka_file_stream(stream)
        for msg in reader:
            processor.process_message(msg)

    def process_json_stream(self, processor, stream):
        for msg in eventsFromJSONLogFile(stream):
            processor.process_message(Message(json=msg))

    def get_all_keys(self):
        return self.redis_server.hkeys("registered_keys")

    def dump_latest_messages_to_redis(self, messages):
        """Dumps a messages hash structure to a given redis server"""
        for pubkey, message_deq in messages.iteritems():
            pipe = self.redis_server.pipeline()
            if len(message_deq) == 100:
                # Drop the prior key
                pipe = pipe.delete(pubkey)
            # Queue all the messages to be added
            msgs = [
                json.dumps(
                    {
                        "id": m.fields["message_id"],
                        "timestamp": m.timestamp,
                        "size": m.fields["message_size"],
                        "ttl": m.fields.get("message_ttl", 0)
                    }) for m in message_deq
            ]
            pipe.lpush(pubkey, *msgs)
            pipe.ltrim(pubkey, 0, 100)
            pipe.execute()
