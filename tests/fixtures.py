"""These items are in a separate module so that spark workers can deserialize them.

When referenced from the same file as the test a ModuleNotFoundError is raised.
"""
import json
from decimal import Decimal

from google.protobuf.json_format import MessageToDict

from example.example_pb2 import DecimalMessage
from example.example_pb2 import RecursiveMessage


def encode_recursive(message: RecursiveMessage, depth=0):
    if depth == 2:
        return json.dumps(MessageToDict(message))
    return {
        "note": message.note,
        "message": encode_recursive(message.message, depth=depth + 1),
    }


def decimal_serializer(message: DecimalMessage):
    return Decimal(message.value)
