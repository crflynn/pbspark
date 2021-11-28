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
    FieldDescriptor.CPPTYPE_MESSAGE: StructType,
}


def get_spark_schema(
    descriptor: t.Union[t.Type[Message], Descriptor], options: t.Optional[dict] = None
) -> StructType:
    options = options or {}
    use_camelcase = not options.get("preserving_proto_field_name", False)
    schema = []
    if inspect.isclass(descriptor) and issubclass(descriptor, Message):
        descriptor_ = descriptor.DESCRIPTOR
    else:
        descriptor_ = descriptor
    for field in descriptor_.fields:
        spark_type: t.Union[StructType, ArrayType]
        if field.cpp_type == FieldDescriptor.CPPTYPE_MESSAGE:
            spark_type = get_spark_schema(field.message_type)
        else:
            spark_type = _CPPTYPE_TO_SPARK_TYPE_MAP[field.cpp_type]()
        if field.label == FieldDescriptor.LABEL_REPEATED:
            spark_type = ArrayType(spark_type, True)
        field_name = field.camelcase_name if use_camelcase else field.name
        schema.append((field_name, spark_type, True))
    struct_args = []
    for entry in schema:
        struct_args.append(StructField(*entry))
    return StructType(struct_args)


def get_decoder(
    message_type: t.Type[Message], options: t.Optional[dict] = None
) -> t.Callable:
    kwargs = options or {}

    def decoder(s):
        return MessageToDict(message_type.FromString(s), **kwargs)

    return decoder


def get_decoder_udf(
    message_type: t.Type[Message], options: t.Optional[dict] = None
) -> t.Callable:
    return udf(
        get_decoder(message_type=message_type, options=options),
        get_spark_schema(descriptor=message_type.DESCRIPTOR, options=options),
    )


def from_protobuf(
    data: t.Union[Column, str],
    message_type: t.Type[Message],
    options: t.Optional[dict] = None,
) -> Column:
    column = col(data) if isinstance(data, str) else data
    protobuf_decoder_udf = get_decoder_udf(message_type, options)
    return protobuf_decoder_udf(column)
