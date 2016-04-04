import json

import boto3
from boto3.dynamodb.conditions import Key


def get_all_keys(tablename):
    """Return all the public keys in the database"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(tablename)
    response = table.query(
        KeyConditionExpression=Key('options').eq('public_keys')
    )
    return [x["pubkey"] for x in response['Items']]


def dump_latest_messages_to_redis(redis_server, messages):
    """Dumps a messages hash structure to a given redis server"""
    for pubkey, message_deq in messages.iteritems():
        pipe = redis_server.pipeline()
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
