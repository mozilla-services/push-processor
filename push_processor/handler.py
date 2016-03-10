"""Handler functions for running under Lambda or otherwise"""
import json
import os

import redis

from push_processor.aws_helpers import s3_open
from push_processor.db import (
    get_all_keys,
    dump_latest_messages_to_redis
)
from push_processor.heka import read_heka_file_stream
from push_processor.message import Message
from push_processor.processor.pubkey import PubKeyProcessor


here_dir = os.path.abspath(os.path.dirname(__file__))


redis_server = None
settings = None


def aws_lambda(event, context):
    if "Bucket" in event:
        # S3 test event, return
        return "Test event"

    # Check that we have a record
    if "Records" not in event:
        return "No record found in event"

    # Setup local objects if needed
    if not redis_server:
        setup_objects()

    pub_keys = get_all_keys(settings["db_tablename"])
    processor = PubKeyProcessor(pub_keys)
    use_gzip = settings.get("use_gzip", False)

    for record in event["Records"]:
        s3_obj = record["s3"]
        bucket, key = s3_obj["bucket"]["name"], s3_obj["object"]["key"]
        f = s3_open(bucket, key, use_gzip=use_gzip)
        if settings["file_type"] == "heka":
            process_heka_stream(redis_server, processor, f)
        else:
            process_json_stream(redis_server, processor, f)


def setup_objects():
    """Sets up module globals for handler run based on S3 config

    Reads a local file to the package, which is hard-coded on bundling
    for S3 to reference runtime options

    """
    global redis_server, settings
    with open(os.path.join(here_dir, "settings.js")) as f:
        settings = json.load(f)

    # Load S3 config settings if supplied
    if "s3_bucket" in settings:
        f = s3_open(settings["s3_bucket"], settings["s3_key"])
        s3_config = json.loads(f.read())
        settings.update(s3_config)

    redis_server = redis.StrictRedis(
        host=settings["redis_host"],
        port=settings["redis_port"]
    )


def process_heka_stream(redis_server, processor, stream):
    reader = read_heka_file_stream(stream)
    for msg in reader:
        processor.process_message(msg)
    dump_latest_messages_to_redis(redis_server, processor.latest_messages)


def process_json_stream(redis_server, processor, stream):
    json_line = stream.readline()
    while json_line:
        msg = Message(json=json.loads(json_line))
        processor.process_message(msg)
        json_line = stream.readline()
    dump_latest_messages_to_redis(redis_server, processor.latest_messages)
