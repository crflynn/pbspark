import inspect
import typing as t
from contextlib import contextmanager
from functools import wraps

from google.protobuf import json_format
from google.protobuf.descriptor import Descriptor
from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.descriptor_pool import DescriptorPool
from google.protobuf.message import Message
from google.protobuf.timestamp_pb2 import Timestamp
from pyspark.sql import Column
from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from pyspark.sql.functions import struct
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType
from pyspark.sql.types import BinaryType
from pyspark.sql.types import BooleanType
from pyspark.sql.types import DataType
from pyspark.sql.types import DoubleType
from pyspark.sql.types import FloatType
from pyspark.sql.types import IntegerType
from pyspark.sql.types import LongType
from pyspark.sql.types import Row
from pyspark.sql.types import StringType
from pyspark.sql.types import StructField
from pyspark.sql.types import StructType
from pyspark.sql.types import TimestampType

from pbspark._timestamp import _from_datetime
from pbspark._timestamp import _to_datetime

# Built in types like these have special methods
# for serialization via MessageToDict. Because the
# MessageToDict function is an intermediate step to
# JSON, some types are serialized to strings.
_MESSAGETYPE_TO_SPARK_TYPE_MAP: t.Dict[str, DataType] = {
    # google/protobuf/timestamp.proto
    "google.protobuf.Timestamp": StringType(),
    # google/protobuf/duration.proto
    "google.protobuf.Duration": StringType(),
    # google/protobuf/wrappers.proto
    "google.protobuf.DoubleValue": DoubleType(),
    "google.protobuf.FloatValue": FloatType(),
    "google.protobuf.Int64Value": LongType(),
    "google.protobuf.UInt64Value": LongType(),
    "google.protobuf.Int32Value": IntegerType(),
    "google.protobuf.UInt32Value": LongType(),
    "google.protobuf.BoolValue": BooleanType(),
    "google.protobuf.StringValue": StringType(),
    "google.protobuf.BytesValue": BinaryType(),
}

# Protobuf types map to these CPP Types. We map
# them to Spark types for generating a spark schema.
# Note that bytes fields are specified by the `type` attribute in addition to
# the `cpp_type` attribute so there is special handling in the `get_spark_schema`
# method.
_CPPTYPE_TO_SPARK_TYPE_MAP: t.Dict[int, DataType] = {
    FieldDescriptor.CPPTYPE_INT32: IntegerType(),
    FieldDescriptor.CPPTYPE_INT64: LongType(),
    FieldDescriptor.CPPTYPE_UINT32: LongType(),
    FieldDescriptor.CPPTYPE_UINT64: LongType(),
    FieldDescriptor.CPPTYPE_DOUBLE: DoubleType(),
    FieldDescriptor.CPPTYPE_FLOAT: FloatType(),
    FieldDescriptor.CPPTYPE_BOOL: BooleanType(),
    FieldDescriptor.CPPTYPE_ENUM: StringType(),
    FieldDescriptor.CPPTYPE_STRING: StringType(),
}


# region serde overrides
class _Printer(json_format._Printer):  # type: ignore
    """Printer override to handle custom messages and byte fields."""

    def __init__(self, custom_serializers=None, **kwargs):
        self._custom_serializers = custom_serializers or {}
        super().__init__(**kwargs)

    def _MessageToJsonObject(self, message):
        full_name = message.DESCRIPTOR.full_name
        if full_name in self._custom_serializers:
            return self._custom_serializers[full_name](message)
        return super()._MessageToJsonObject(message)

    def _FieldToJsonObject(self, field, value):
        # specially handle bytes before protobuf's method does
        if (
            field.cpp_type == FieldDescriptor.CPPTYPE_STRING
            and field.type == FieldDescriptor.TYPE_BYTES
        ):
            return value
        # don't convert int64s to string (protobuf does this for js precision compat)
        elif field.cpp_type in json_format._INT64_TYPES:
            return value
        return super()._FieldToJsonObject(field, value)


class _Parser(json_format._Parser):  # type: ignore
    """Parser override to handle custom messages."""

    def __init__(self, custom_deserializers=None, **kwargs):
        self._custom_deserializers = custom_deserializers or {}
        super().__init__(**kwargs)

    def ConvertMessage(self, value, message, path):
        full_name = message.DESCRIPTOR.full_name
        if full_name in self._custom_deserializers:
            self._custom_deserializers[full_name](value, message, path)
            return
        with _patched_convert_scalar_field_value():
            super().ConvertMessage(value, message, path)


# protobuf converts to/from b64 strings, but we prefer to stay as bytes.
# we handle bytes parser by decorating to handle byte fields first
def _handle_bytes(func):
    @wraps(func)
    def wrapper(value, field, path, require_str=False):
        if (
            field.cpp_type == FieldDescriptor.CPPTYPE_STRING
            and field.type == FieldDescriptor.TYPE_BYTES
        ):
            return bytes(value)  # convert from bytearray to bytes
        return func(value=value, field=field, path=path, require_str=require_str)

    return wrapper


@contextmanager
def _patched_convert_scalar_field_value():
    """Temporarily patch the scalar field conversion function."""
    convert_scalar_field_value_func = json_format._ConvertScalarFieldValue  # type: ignore[attr-defined]
    json_format._ConvertScalarFieldValue = _handle_bytes(  # type: ignore[attr-defined]
        json_format._ConvertScalarFieldValue  # type: ignore[attr-defined]
    )
    try:
        yield
    finally:
        json_format._ConvertScalarFieldValue = convert_scalar_field_value_func


# endregion


class MessageConverter:
    def __init__(self):
        self._custom_serializers: t.Dict[str, t.Callable] = {}
        self._custom_deserializers: t.Dict[str, t.Callable] = {}
        self._message_type_to_spark_type_map = _MESSAGETYPE_TO_SPARK_TYPE_MAP.copy()
        self.register_timestamp_serializer()
        self.register_timestamp_deserializer()

    def register_serializer(
        self,
        message: t.Type[Message],
        serializer: t.Callable,
        return_type: DataType,
    ):
        """Map a message type to a custom serializer and spark output type.

        The serializer should be a function which returns an object which
        can be coerced into the spark return type.
        """
        full_name = message.DESCRIPTOR.full_name
        self._custom_serializers[full_name] = serializer
        self._message_type_to_spark_type_map[full_name] = return_type

    def unregister_serializer(self, message: t.Type[Message]):
        full_name = message.DESCRIPTOR.full_name
        self._custom_serializers.pop(full_name, None)
        self._message_type_to_spark_type_map.pop(full_name, None)
        if full_name in _MESSAGETYPE_TO_SPARK_TYPE_MAP:
            self._message_type_to_spark_type_map[
                full_name
            ] = _MESSAGETYPE_TO_SPARK_TYPE_MAP[full_name]

    def register_deserializer(self, message: t.Type[Message], deserializer: t.Callable):
        full_name = message.DESCRIPTOR.full_name
        self._custom_deserializers[full_name] = deserializer

    def unregister_deserializer(self, message: t.Type[Message]):
        full_name = message.DESCRIPTOR.full_name
        self._custom_deserializers.pop(full_name, None)

    # region timestamp
    def register_timestamp_serializer(self):
        self.register_serializer(Timestamp, _to_datetime, TimestampType())

    def unregister_timestamp_serializer(self):
        self.unregister_serializer(Timestamp)

    def register_timestamp_deserializer(self):
        self.register_deserializer(Timestamp, _from_datetime)

    def unregister_timestamp_deserializer(self):
        self.unregister_deserializer(Timestamp)

    # endregion

    def message_to_dict(
        self,
        message: Message,
        including_default_value_fields: bool = False,
        preserving_proto_field_name: bool = False,
        use_integers_for_enums: bool = False,
        descriptor_pool: t.Optional[DescriptorPool] = None,
        float_precision: t.Optional[int] = None,
    ):
        """Custom MessageToDict using overridden printer.

        Args:
            message: The protocol buffers message instance to serialize.
            including_default_value_fields: If True, singular primitive fields,
                repeated fields, and map fields will always be serialized.  If
                False, only serialize non-empty fields.  Singular message fields
                and oneof fields are not affected by this option.
            preserving_proto_field_name: If True, use the original proto field
                names as defined in the .proto file. If False, convert the field
                names to lowerCamelCase.
            use_integers_for_enums: If true, print integers instead of enum names.
            descriptor_pool: A Descriptor Pool for resolving types. If None use the
                default.
            float_precision: If set, use this to specify float field valid digits.
        """
        printer = _Printer(
            custom_serializers=self._custom_serializers,
            including_default_value_fields=including_default_value_fields,
            preserving_proto_field_name=preserving_proto_field_name,
            use_integers_for_enums=use_integers_for_enums,
            descriptor_pool=descriptor_pool,
            float_precision=float_precision,
        )
        return printer._MessageToJsonObject(message=message)

    def parse_dict(
        self,
        value: dict,
        message: Message,
        ignore_unknown_fields: bool = False,
        descriptor_pool: t.Optional[DescriptorPool] = None,
        max_recursion_depth: int = 100,
    ):
        """Custom ParseDict using overridden parser."""
        parser = _Parser(
            custom_deserializers=self._custom_deserializers,
            ignore_unknown_fields=ignore_unknown_fields,
            descriptor_pool=descriptor_pool,
            max_recursion_depth=max_recursion_depth,
        )
        return parser.ConvertMessage(value=value, message=message, path=None)

    def get_spark_schema(
        self,
        descriptor: t.Union[t.Type[Message], Descriptor],
        preserving_proto_field_name: bool = False,
        use_integers_for_enums: bool = False,
    ) -> DataType:
        """Generate a spark schema from a message type or descriptor

        Given a message type generated from protoc (or its descriptor),
        create a spark schema derived from the protobuf schema when
        serializing with ``MessageToDict``.

        Args:
            descriptor: A message type or its descriptor
            preserving_proto_field_name: If True, use the original proto field
                names as defined in the .proto file. If False, convert the field
                names to lowerCamelCase.
            use_integers_for_enums: If true, print integers instead of enum names.
        """
        schema = []
        if inspect.isclass(descriptor) and issubclass(descriptor, Message):
            descriptor_ = descriptor.DESCRIPTOR
        else:
            descriptor_ = descriptor  # type: ignore[assignment]
        full_name = descriptor_.full_name
        if full_name in self._message_type_to_spark_type_map:
            return self._message_type_to_spark_type_map[full_name]
        for field in descriptor_.fields:
            spark_type: DataType
            if field.cpp_type == FieldDescriptor.CPPTYPE_MESSAGE:
                full_name = field.message_type.full_name
                if full_name in self._message_type_to_spark_type_map:
                    spark_type = self._message_type_to_spark_type_map[full_name]
                else:
                    spark_type = self.get_spark_schema(
                        descriptor=field.message_type,
                        preserving_proto_field_name=preserving_proto_field_name,
                    )
            # protobuf converts to/from b64 strings, but we prefer to stay as bytes
            elif (
                field.cpp_type == FieldDescriptor.CPPTYPE_STRING
                and field.type == FieldDescriptor.TYPE_BYTES
            ):
                spark_type = BinaryType()
            elif (
                field.cpp_type == FieldDescriptor.CPPTYPE_ENUM
                and use_integers_for_enums
            ):
                spark_type = IntegerType()
            else:
                spark_type = _CPPTYPE_TO_SPARK_TYPE_MAP[field.cpp_type]
            if field.label == FieldDescriptor.LABEL_REPEATED:
                spark_type = ArrayType(spark_type, True)
            field_name = (
                field.camelcase_name if not preserving_proto_field_name else field.name
            )
            schema.append((field_name, spark_type, True))
        struct_args = [StructField(*entry) for entry in schema]
        return StructType(struct_args)

    def get_decoder(
        self,
        message_type: t.Type[Message],
        including_default_value_fields: bool = False,
        preserving_proto_field_name: bool = False,
        use_integers_for_enums: bool = False,
        float_precision: t.Optional[int] = None,
    ) -> t.Callable:
        """Create a deserialization function for a message type.

        Create a function that accepts a serialized message bytestring
        and returns a dictionary representing the message.

        Args:
            message_type: The message type for decoding.
            including_default_value_fields: If True, singular primitive fields,
                repeated fields, and map fields will always be serialized.  If
                False, only serialize non-empty fields.  Singular message fields
                and oneof fields are not affected by this option.
            preserving_proto_field_name: If True, use the original proto field
                names as defined in the .proto file. If False, convert the field
                names to lowerCamelCase.
            use_integers_for_enums: If true, print integers instead of enum names.
            float_precision: If set, use this to specify float field valid digits.
        """

        def decoder(s: bytes) -> dict:
            if isinstance(s, bytearray):
                s = bytes(s)
            return self.message_to_dict(
                message_type.FromString(s),
                including_default_value_fields=including_default_value_fields,
                preserving_proto_field_name=preserving_proto_field_name,
                use_integers_for_enums=use_integers_for_enums,
                float_precision=float_precision,
            )

        return decoder

    def get_decoder_udf(
        self,
        message_type: t.Type[Message],
        including_default_value_fields: bool = False,
        preserving_proto_field_name: bool = False,
        use_integers_for_enums: bool = False,
        float_precision: t.Optional[int] = None,
    ) -> t.Callable:
        """Create a deserialization udf for a message type.

        Creates a function for deserializing messages to dict
        with spark schema for expected output.

        Args:
            message_type: The message type for decoding.
            including_default_value_fields: If True, singular primitive fields,
                repeated fields, and map fields will always be serialized.  If
                False, only serialize non-empty fields.  Singular message fields
                and oneof fields are not affected by this option.
            preserving_proto_field_name: If True, use the original proto field
                names as defined in the .proto file. If False, convert the field
                names to lowerCamelCase.
            use_integers_for_enums: If true, print integers instead of enum names.
            float_precision: If set, use this to specify float field valid digits.
        """
        return udf(
            self.get_decoder(
                message_type=message_type,
                including_default_value_fields=including_default_value_fields,
                preserving_proto_field_name=preserving_proto_field_name,
                use_integers_for_enums=use_integers_for_enums,
                float_precision=float_precision,
            ),
            self.get_spark_schema(
                descriptor=message_type.DESCRIPTOR,
                preserving_proto_field_name=preserving_proto_field_name,
                use_integers_for_enums=use_integers_for_enums,
            ),
        )

    def from_protobuf(
        self,
        data: t.Union[Column, str],
        message_type: t.Type[Message],
        including_default_value_fields: bool = False,
        preserving_proto_field_name: bool = False,
        use_integers_for_enums: bool = False,
        float_precision: t.Optional[int] = None,
    ) -> Column:
        """Deserialize protobuf messages to spark structs.

        Given a column and protobuf message type, deserialize
        protobuf messages also using our custom serializers.

        Args:
            message_type: The message type for decoding.
            including_default_value_fields: If True, singular primitive fields,
                repeated fields, and map fields will always be serialized.  If
                False, only serialize non-empty fields.  Singular message fields
                and oneof fields are not affected by this option.
            preserving_proto_field_name: If True, use the original proto field
                names as defined in the .proto file. If False, convert the field
                names to lowerCamelCase.
            use_integers_for_enums: If true, print integers instead of enum names.
            float_precision: If set, use this to specify float field valid digits.
        """
        column = col(data) if isinstance(data, str) else data
        protobuf_decoder_udf = self.get_decoder_udf(
            message_type=message_type,
            including_default_value_fields=including_default_value_fields,
            preserving_proto_field_name=preserving_proto_field_name,
            use_integers_for_enums=use_integers_for_enums,
            float_precision=float_precision,
        )
        return protobuf_decoder_udf(column)

    def get_encoder(
        self,
        message_type: t.Type[Message],
        ignore_unknown_fields: bool = False,
        max_recursion_depth: int = 100,
    ) -> t.Callable:
        """Create an encoding function for a message type.

        Create a function that accepts a dictionary representing the message
        and returns a serialized message bytestring.

        Args:
            message_type: The message type for encoding.
            ignore_unknown_fields: If True, do not raise errors for unknown fields.
            max_recursion_depth: max recursion depth of JSON message to be
                deserialized. JSON messages over this depth will fail to be
                deserialized. Default value is 100.
        """

        def encoder(s: dict) -> bytes:
            message = message_type()
            # udf may pass a Row object, but we want to pass a dict to the parser
            if isinstance(s, Row):
                s = s.asDict(recursive=True)
            self.parse_dict(
                s,
                message,
                ignore_unknown_fields=ignore_unknown_fields,
                max_recursion_depth=max_recursion_depth,
            )
            return message.SerializeToString()

        return encoder

    def get_encoder_udf(
        self,
        message_type: t.Type[Message],
        ignore_unknown_fields: bool = False,
        max_recursion_depth: int = 100,
    ) -> t.Callable:
        """Get a pyspark udf for encoding to protobuf.

        Args:
            message_type: The message type for encoding.
            ignore_unknown_fields: If True, do not raise errors for unknown fields.
            max_recursion_depth: max recursion depth of JSON message to be
                deserialized. JSON messages over this depth will fail to be
                deserialized. Default value is 100.
        """
        return udf(
            self.get_encoder(
                message_type=message_type,
                ignore_unknown_fields=ignore_unknown_fields,
                max_recursion_depth=max_recursion_depth,
            ),
            BinaryType(),
        )

    def to_protobuf(
        self,
        data: t.Union[Column, str],
        message_type: t.Type[Message],
        ignore_unknown_fields: bool = False,
        max_recursion_depth: int = 100,
    ) -> Column:
        """Serialize spark structs to protobuf messages.

        Given a column and protobuf message type, serialize
        protobuf messages also using our custom serializers.

        Args:
            data: A pyspark column.
            message_type: The message type for encoding.
            ignore_unknown_fields: If True, do not raise errors for unknown fields.
            max_recursion_depth: max recursion depth of JSON message to be
                deserialized. JSON messages over this depth will fail to be
                deserialized. Default value is 100.
        """
        column = col(data) if isinstance(data, str) else data
        protobuf_encoder_udf = self.get_encoder_udf(
            message_type,
            ignore_unknown_fields=ignore_unknown_fields,
            max_recursion_depth=max_recursion_depth,
        )
        return protobuf_encoder_udf(column)

    def df_from_protobuf(
        self,
        df: DataFrame,
        message_type: t.Type[Message],
        including_default_value_fields: bool = False,
        preserving_proto_field_name: bool = False,
        use_integers_for_enums: bool = False,
        float_precision: t.Optional[int] = None,
        expanded: bool = False,
    ) -> DataFrame:
        """Decode a dataframe of encoded protobuf.

        Args:
            df: A pyspark dataframe with encoded protobuf in the column at index 0.
            message_type: The message type for decoding.
            including_default_value_fields: If True, singular primitive fields,
                repeated fields, and map fields will always be serialized.  If
                False, only serialize non-empty fields.  Singular message fields
                and oneof fields are not affected by this option.
            preserving_proto_field_name: If True, use the original proto field
                names as defined in the .proto file. If False, convert the field
                names to lowerCamelCase.
            use_integers_for_enums: If true, print integers instead of enum names.
            float_precision: If set, use this to specify float field valid digits.
            expanded: If True, return a dataframe in which each field is its own
                column. Otherwise, return a dataframe with a single struct column
                named `value`.
        """
        df_decoded = df.select(
            self.from_protobuf(
                data=df.columns[0],
                message_type=message_type,
                including_default_value_fields=including_default_value_fields,
                preserving_proto_field_name=preserving_proto_field_name,
                use_integers_for_enums=use_integers_for_enums,
                float_precision=float_precision,
            ).alias("value")
        )
        if expanded:
            df_decoded = df_decoded.select("value.*")
        return df_decoded

    def df_to_protobuf(
        self,
        df: DataFrame,
        message_type: t.Type[Message],
        ignore_unknown_fields: bool = False,
        max_recursion_depth: int = 100,
        expanded: bool = False,
    ) -> DataFrame:
        """Encode data in a dataframe to protobuf as column `value`.

        Args:
            df: A pyspark dataframe.
            message_type: The message type for encoding.
            ignore_unknown_fields: If True, do not raise errors for unknown fields.
            max_recursion_depth: max recursion depth of JSON message to be
                deserialized. JSON messages over this depth will fail to be
                deserialized. Default value is 100.
            expanded: If True, the passed dataframe columns will be packed into a
                struct before converting. Otherwise, it is assumed that the
                dataframe passed is a single column of data already packed into a
                struct.

        Returns a dataframe with a single column named `value` containing encoded data.
        """
        if expanded:
            df_struct = df.select(
                struct([df[c] for c in df.columns]).alias("value")  # type: ignore[arg-type]
            )
        else:
            df_struct = df.select(col(df.columns[0]).alias("value"))
        df_encoded = df_struct.select(
            self.to_protobuf(
                data=df_struct.value,
                message_type=message_type,
                ignore_unknown_fields=ignore_unknown_fields,
                max_recursion_depth=max_recursion_depth,
            ).alias("value")
        )
        return df_encoded


def from_protobuf(
    data: t.Union[Column, str],
    message_type: t.Type[Message],
    including_default_value_fields: bool = False,
    preserving_proto_field_name: bool = False,
    use_integers_for_enums: bool = False,
    float_precision: t.Optional[int] = None,
    message_converter: MessageConverter = None,
) -> Column:
    """Deserialize protobuf messages to spark structs

    Args:
        data: A pyspark column.
        message_type: The message type for decoding.
        including_default_value_fields: If True, singular primitive fields,
            repeated fields, and map fields will always be serialized.  If
            False, only serialize non-empty fields.  Singular message fields
            and oneof fields are not affected by this option.
        preserving_proto_field_name: If True, use the original proto field
            names as defined in the .proto file. If False, convert the field
            names to lowerCamelCase.
        use_integers_for_enums: If true, print integers instead of enum names.
        float_precision: If set, use this to specify float field valid digits.
        message_converter: An instance of a message converter. If None, use the default.
    """
    message_converter = message_converter or MessageConverter()
    return message_converter.from_protobuf(
        data=data,
        message_type=message_type,
        including_default_value_fields=including_default_value_fields,
        preserving_proto_field_name=preserving_proto_field_name,
        use_integers_for_enums=use_integers_for_enums,
        float_precision=float_precision,
    )


def to_protobuf(
    data: t.Union[Column, str],
    message_type: t.Type[Message],
    ignore_unknown_fields: bool = False,
    max_recursion_depth: int = 100,
    message_converter: MessageConverter = None,
) -> Column:
    """Serialize spark structs to protobuf messages.

    Given a column and protobuf message type, serialize
    protobuf messages also using our custom serializers.

    Args:
        data: A pyspark column.
        message_type: The message type for encoding.
        ignore_unknown_fields: If True, do not raise errors for unknown fields.
        max_recursion_depth: max recursion depth of JSON message to be
            deserialized. JSON messages over this depth will fail to be
            deserialized. Default value is 100.
        message_converter: An instance of a message converter. If None, use the default.
    """
    message_converter = message_converter or MessageConverter()
    return message_converter.to_protobuf(
        data=data,
        message_type=message_type,
        ignore_unknown_fields=ignore_unknown_fields,
        max_recursion_depth=max_recursion_depth,
    )


def df_from_protobuf(
    df: DataFrame,
    message_type: t.Type[Message],
    including_default_value_fields: bool = False,
    preserving_proto_field_name: bool = False,
    use_integers_for_enums: bool = False,
    float_precision: t.Optional[int] = None,
    expanded: bool = False,
    message_converter: MessageConverter = None,
) -> DataFrame:
    """Decode a dataframe of encoded protobuf.

    Args:
        df: A pyspark dataframe with encoded protobuf in the column at index 0.
        message_type: The message type for decoding.
        including_default_value_fields: If True, singular primitive fields,
            repeated fields, and map fields will always be serialized.  If
            False, only serialize non-empty fields.  Singular message fields
            and oneof fields are not affected by this option.
        preserving_proto_field_name: If True, use the original proto field
            names as defined in the .proto file. If False, convert the field
            names to lowerCamelCase.
        use_integers_for_enums: If true, print integers instead of enum names.
        float_precision: If set, use this to specify float field valid digits.
        expanded: If True, return a dataframe in which each field is its own
            column. Otherwise, return a dataframe with a single struct column
            named `value`.
        message_converter: An instance of a message converter. If None, use the default.
    """
    message_converter = message_converter or MessageConverter()
    return message_converter.df_from_protobuf(
        df=df,
        message_type=message_type,
        including_default_value_fields=including_default_value_fields,
        preserving_proto_field_name=preserving_proto_field_name,
        use_integers_for_enums=use_integers_for_enums,
        float_precision=float_precision,
        expanded=expanded,
    )


def df_to_protobuf(
    df: DataFrame,
    message_type: t.Type[Message],
    ignore_unknown_fields: bool = False,
    max_recursion_depth: int = 100,
    expanded: bool = False,
    message_converter: MessageConverter = None,
) -> DataFrame:
    """Encode data in a dataframe to protobuf as column `value`.

    Args:
        df: A pyspark dataframe.
        message_type: The message type for encoding.
        ignore_unknown_fields: If True, do not raise errors for unknown fields.
        max_recursion_depth: max recursion depth of JSON message to be
            deserialized. JSON messages over this depth will fail to be
            deserialized. Default value is 100.
        expanded: If True, the passed dataframe columns will be packed into a
            struct before converting. Otherwise, it is assumed that the
            dataframe passed is a single column of data already packed into a
            struct.
        message_converter: An instance of a message converter. If None, use the default.

    Returns a dataframe with a single column named `value` containing encoded data.
    """
    message_converter = message_converter or MessageConverter()
    return message_converter.df_to_protobuf(
        df=df,
        message_type=message_type,
        ignore_unknown_fields=ignore_unknown_fields,
        max_recursion_depth=max_recursion_depth,
        expanded=expanded,
    )
