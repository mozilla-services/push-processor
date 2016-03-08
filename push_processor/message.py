"""Message abstraction"""
from push_processor.message_pb2 import (
    Field,
)

_FIELD_TYPE_TO_ATTRIBUTE = {
    Field.INTEGER: 'value_integer',
    Field.DOUBLE: 'value_double',
    Field.BOOL: 'value_bool',
    Field.STRING: 'value_string',
    Field.BYTES: 'value_bytes',
}


def _get_value_from_field(field):
    attr_name = _FIELD_TYPE_TO_ATTRIBUTE[field.value_type]
    return getattr(field, attr_name)


class Message(object):
    """Message abstraction for JSON or Protobuf originating Message"""
    def __init__(self, json=None, protobuf=None):
        """Create Message object

        Either json or protobuf must be provided, as the data to use for
        the message.

        """
        if json:
            # JSON has the root dict capitalized, protobuf does not, so we
            # normalize to lowercase
            json = {k.lower(): v for k, v in json.items()}

        self._message = json or protobuf
        self._use_json = json is not None
        if not json and not protobuf:
            raise Exception("Must supply json or protobuf structure")
        self._fields = None

    def __getattr__(self, name):
        if self._use_json:
            return self._message[name]
        else:
            return getattr(self._message, name)

    def fields(self):
        if self._use_json:
            return self._message["fields"]

        if self._fields is None:
            self._fields = {
                field.name: _get_value_from_field(field)[0]
                for field in self._message.fields
            }
        return self._fields
    fields = property(fields)
