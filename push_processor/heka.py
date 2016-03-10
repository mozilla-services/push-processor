"""heka stream decoder"""
import struct

from push_processor.message import Message
from push_processor.message_pb2 import (
    Header,
    Message as ProtobufMessage
)


RECORD_SEPARATOR = 0x1e
UNIT_SEPARATOR = 0x1f


def read_heka_file_stream(file_object):
    """Generator that reads a heka file-like object and emits message
    records
    """
    f = file_object
    while True:
        # Read message separator
        sep = f.read(1)
        if sep == "":
            # EOF, break
            break
        assert struct.unpack("b", sep)[0] == RECORD_SEPARATOR

        # Read the header length, the header, and unpack the
        # protobuf header
        header_len = struct.unpack("b", f.read(1))[0]
        protobuf_header = Header()
        protobuf_header.ParseFromString(f.read(header_len))
        message_len = protobuf_header.message_length

        # Read the unit separtor
        sep = f.read(1)
        u_sep = struct.unpack("b", sep)[0]
        assert u_sep == UNIT_SEPARATOR

        # Read the message, decode, and yield
        protobuf_message = ProtobufMessage()
        protobuf_message.ParseFromString(f.read(message_len))
        yield Message(protobuf=protobuf_message)
