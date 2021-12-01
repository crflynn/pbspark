import datetime
import inspect
import typing as t

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.json_format import _Printer  # type: ignore  # noqa
from google.protobuf.message import Message
from google.protobuf.pyext._message import Descriptor  # type: ignore
from google.protobuf.timestamp_pb2 import Timestamp
from pyspark.sql import Column
from pyspark.sql.functions import col
from pyspark.sql.functions import udf
from pyspark.sql.types import *

# Built in types like these have special methods
# for serialization via MessageToDict. Because the
# MessageToDict function is an intermediate step to
# JSON, these types are serialized to strings.
_MESSAGETYPE_TO_SPARK_TYPE_MAP: t.Dict[str, t.Type[DataType]] = {
    "google.protobuf.Timestamp": StringType,
    "google.protobuf.Duration": StringType,
}
_MESSAGETYPE_TO_SPARK_TYPE_KWARGS_MAP: t.Dict[str, t.Dict[str, t.Any]] = {}

# Protobuf types map to these CPP Types. We map
# them to Spark types for generating a spark schema
_CPPTYPE_TO_SPARK_TYPE_MAP: t.Dict[int, t.Type[DataType]] = {
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

# region Timestamp code from WKT
_EPOCH_DATETIME = datetime.datetime.utcfromtimestamp(0)
_NANOS_PER_MICROSECOND = 1000


def _round_toward_zero(value, divider):
    result = value // divider
    remainder = value % divider
    if result < 0 < remainder:
        return result + 1
    else:
        return result


def _to_datetime(message: Timestamp) -> datetime.datetime:
    """Serialize a Timestamp to a python datetime."""
    return _EPOCH_DATETIME + datetime.timedelta(
        seconds=message.seconds,
        microseconds=_round_toward_zero(message.nanos, _NANOS_PER_MICROSECOND),
    )


# endregion


class Printer(_Printer):
    """Subclass the protobuf printer to override serialization"""

    def __init__(self, custom_serializers=None, **kwargs):
        self._custom_serializers = custom_serializers or {}
        super().__init__(**kwargs)

    def _MessageToJsonObject(self, message):
        """Override serialization to prioritize custom serializers."""
        full_name = message.DESCRIPTOR.full_name
        if full_name in self._custom_serializers:
            return self._custom_serializers[full_name](message)
        return super()._MessageToJsonObject(message)


class MessageConverter:
    """Class for converting serialized protobuf messages into spark structs."""

    def __init__(self):
        self._custom_serializers = {}
        self._message_type_to_spark_type_map = _MESSAGETYPE_TO_SPARK_TYPE_MAP.copy()
        self._message_type_to_spark_type_kwargs_map = (
            _MESSAGETYPE_TO_SPARK_TYPE_KWARGS_MAP.copy()
        )

    def register_serializer(
        self,
        message: t.Type[Message],
        serializer: t.Callable,
        return_type: t.Type[DataType],
        return_type_kwargs: t.Dict[str, t.Any] = None,
    ):
        """Map a message type to a custom serializer and spark output type.

        The serializer should be a function which returns an object which
        can be coerced into the spark return type.
        """
        full_name = message.DESCRIPTOR.full_name
        self._custom_serializers[full_name] = serializer
        self._message_type_to_spark_type_map[full_name] = return_type
        if return_type_kwargs is not None:
            self._message_type_to_spark_type_kwargs_map[full_name] = return_type_kwargs

    def unregister_serializer(self, message: t.Type[Message]):
        full_name = message.DESCRIPTOR.full_name
        self._custom_serializers.pop(full_name, None)
        self._message_type_to_spark_type_map.pop(full_name, None)
        self._message_type_to_spark_type_kwargs_map.pop(full_name, None)
        if full_name in _MESSAGETYPE_TO_SPARK_TYPE_MAP:
            self._message_type_to_spark_type_map[
                full_name
            ] = _MESSAGETYPE_TO_SPARK_TYPE_MAP[full_name]
        if full_name in _MESSAGETYPE_TO_SPARK_TYPE_KWARGS_MAP:
            self._message_type_to_spark_type_kwargs_map[
                full_name
            ] = _MESSAGETYPE_TO_SPARK_TYPE_KWARGS_MAP[full_name]

    def register_timestamp_serializer(self):
        """Serialize Timestamps to datetimes instead of strings."""
        self.register_serializer(Timestamp, _to_datetime, TimestampType)

    def unregister_timestamp_serializer(self):
        self.unregister_serializer(Timestamp)

    def message_to_dict(
        self,
        message,
        including_default_value_fields=False,
        preserving_proto_field_name=False,
        use_integers_for_enums=False,
        descriptor_pool=None,
        float_precision=None,
    ):
        """Custom MessageToDict using overridden printer."""
        printer = Printer(
            custom_serializers=self._custom_serializers,
            including_default_value_fields=including_default_value_fields,
            preserving_proto_field_name=preserving_proto_field_name,
            use_integers_for_enums=use_integers_for_enums,
            descriptor_pool=descriptor_pool,
            float_precision=float_precision,
        )
        return printer._MessageToJsonObject(message)

    def get_spark_schema(
        self,
        descriptor: t.Union[t.Type[Message], Descriptor],
        options: t.Optional[dict] = None,
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
                full_name = field.message_type.full_name
                if full_name in self._message_type_to_spark_type_map:
                    kwargs = self._message_type_to_spark_type_kwargs_map.get(
                        full_name, {}
                    )
                    # noinspection PyArgumentList
                    spark_type = self._message_type_to_spark_type_map[full_name](
                        **kwargs
                    )
                else:
                    spark_type = self.get_spark_schema(field.message_type)
            else:
                spark_type = _CPPTYPE_TO_SPARK_TYPE_MAP[field.cpp_type]()
            if field.label == FieldDescriptor.LABEL_REPEATED:
                spark_type = ArrayType(spark_type, True)
            field_name = field.camelcase_name if use_camelcase else field.name
            schema.append((field_name, spark_type, True))
        struct_args = [StructField(*entry) for entry in schema]
        return StructType(struct_args)

    def get_decoder(
        self, message_type: t.Type[Message], options: t.Optional[dict] = None
    ) -> t.Callable:
        """Create a deserialization function for a message type.

        Create a function that accepts a serialized message bytestring
        and returns a dictionary representing the message.

        The ``options`` arg should be a dictionary for the kwargs passsed
        to ``MessageToDict``.
        """
        kwargs = options or {}

        def decoder(s: bytes) -> dict:
            return self.message_to_dict(message_type.FromString(s), **kwargs)

        return decoder

    def get_decoder_udf(
        self, message_type: t.Type[Message], options: t.Optional[dict] = None
    ) -> t.Callable:
        """Create a deserialization udf for a message type.

        Creates a function for deserializing messages to dict
        with spark schema for expected output.

        The ``options`` arg should be a dictionary for the kwargs passsed
        to ``MessageToDict``.
        """
        return udf(
            self.get_decoder(message_type=message_type, options=options),
            self.get_spark_schema(descriptor=message_type.DESCRIPTOR, options=options),
        )

    def from_protobuf(
        self,
        data: t.Union[Column, str],
        message_type: t.Type[Message],
        options: t.Optional[dict] = None,
    ) -> Column:
        """Deserialize protobuf messages to spark structs.

        Given a column and protobuf message type, deserialize
        protobuf messages also using our custom serializers.

        The ``options`` arg should be a dictionary for the kwargs passed
        our message_to_dict (same args as protobuf's MessageToDict).
        """
        column = col(data) if isinstance(data, str) else data
        protobuf_decoder_udf = self.get_decoder_udf(message_type, options)
        return protobuf_decoder_udf(column)
