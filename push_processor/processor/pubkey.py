from collections import defaultdict, deque


class PubKeyProcessor(object):
    def __init__(self, pubkey_list):
        # Store public keys as hash for fast lookup
        self.total = 0
        self.flagged = 0
        self.pubkeys = {k: True for k in pubkey_list}
        self.latest_messages = defaultdict(lambda: deque(maxlen=100))

    def process_message(self, message):
        """Process a message and store metadata for top matches"""
        self.total += 1

        # Need a message field and jwt
        if ("message" not in message.fields or
                "jwt_crypto_key" not in message.fields):
            return

        # Message needs to be a message delivery or storage on endpoint
        m = message.fields["message"]
        if m not in ["Router miss, message stored.", "Successful delivery"]:
            return

        # Check the jwt public key for match
        message_key = message.fields["jwt_crypto_key"]

        # Valid key?
        if message_key not in self.pubkeys:
            return

        self.flagged += 1
        self.latest_messages[message_key].append(message)
