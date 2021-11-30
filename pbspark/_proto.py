import inspect
import typing as t

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message
from google.protobuf.pyext._message import Descriptor  # type: ignore
from pyspark.sql import Column
from pyspark.sql.functions import col
from pyspark.sql.functions import udf
from pyspark.sql.types import *

# Built in types like these have special methods
# for serialization via MessageToDict. Because the
# MessageToDict function is an intermediate step to
# JSON, these types are serialized to strings.
_MESSAGETYPE_TO_SPARK_TYPE_MAP = {
    "google.protobuf.Timestamp": StringType,
    "google.protobuf.Duration": StringType,
}

# Protobuf types map to these CPP Types. We map
# them to Spark types for generating a spark schema
_CPPTYPE_TO_SPARK_TYPE_MAP = {
    FieldDescriptor.CPPTYPE_INT32: IntegerType,
    FieldDescriptor.CPPTYPE_INT64: LongType,
    FieldDescriptor.CPPTYPE_UINT32: LongType,
    FieldDescriptor.CPPTYPE_UINT64: LongType,
    FieldDescriptor.CPPTYPE_DOUBLE: DoubleType,
    FieldDescriptor.CPPTYPE_FLOAT: FloatType,
    FieldDescriptor.CPPTYPE_BOOL: BooleanType,
    FieldDescriptor.CPPTYPE_ENUM: StringType,
    FieldDescriptor.CPPTYPE_STRING: StringType,
}


def get_spark_schema(
    descriptor: t.Union[t.Type[Message], Descriptor], options: t.Optional[dict] = None
) -> StructType:
    """Generate a spark schema from a message type or descriptor

    Given a message type generated from protoc (or its descriptor),
    create a spark schema derived from the protobuf schema when
    serializing with ``MessageToDict``.
    """
    options = options or {}
    use_camelcase = not options.get("preserving_proto_field_name", False)
    schema = []
    if inspect.isclass(descriptor) and issubclass(descriptor, Message):
        descriptor_ = descriptor.DESCRIPTOR
    else:
        descriptor_ = descriptor
    for field in descriptor_.fields:
        spark_type: DataType
        if field.cpp_type == FieldDescriptor.CPPTYPE_MESSAGE:
            if field.message_type.full_name in _MESSAGETYPE_TO_SPARK_TYPE_MAP:
                spark_type = _MESSAGETYPE_TO_SPARK_TYPE_MAP[
                    field.message_type.full_name
                ]()
            else:
                spark_type = get_spark_schema(field.message_type)
        else:
            spark_type = _CPPTYPE_TO_SPARK_TYPE_MAP[field.cpp_type]()
        if field.label == FieldDescriptor.LABEL_REPEATED:
            spark_type = ArrayType(spark_type, True)
        field_name = field.camelcase_name if use_camelcase else field.name
        schema.append((field_name, spark_type, True))
    struct_args = [StructField(*entry) for entry in schema]
    return StructType(struct_args)


def get_decoder(
    message_type: t.Type[Message], options: t.Optional[dict] = None
) -> t.Callable:
    """Create a deserialization function for a message type.

    Create a function that accepts a serialized message bytestring
    and returns a dictionary representing the message using
    ``MessageToDict``.

    The ``options`` arg should be a dictionary for the kwargs passsed
    to ``MessageToDict``.
    """
    kwargs = options or {}

    def decoder(s: bytes) -> dict:
        return MessageToDict(message_type.FromString(s), **kwargs)

    return decoder


def get_decoder_udf(
    message_type: t.Type[Message], options: t.Optional[dict] = None
) -> t.Callable:
    """Create a deserialization udf for a message type.

    Creates a function for deserializing messages to dict using
    ``MessageToDict`` with spark schema for expected output.

    The ``options`` arg should be a dictionary for the kwargs passsed
    to ``MessageToDict``.
    """
    return udf(
        get_decoder(message_type=message_type, options=options),
        get_spark_schema(descriptor=message_type.DESCRIPTOR, options=options),
    )


def from_protobuf(
    data: t.Union[Column, str],
    message_type: t.Type[Message],
    options: t.Optional[dict] = None,
) -> Column:
    """Deserialize protobuf messages to spark structs.

    Given a column and protobuf message type, deserialize
    protobuf messages using ``MessageToDict``.

    The ``options`` arg should be a dictionary for the kwargs passed
    to ``MessageToDict``.
    """
    column = col(data) if isinstance(data, str) else data
    protobuf_decoder_udf = get_decoder_udf(message_type, options)
    return protobuf_decoder_udf(column)
