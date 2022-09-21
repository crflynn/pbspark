import datetime
import json
from decimal import Decimal

import pytest
from google.protobuf import descriptor_pb2
from google.protobuf import json_format
from google.protobuf.descriptor_pool import DescriptorPool
from google.protobuf.duration_pb2 import Duration
from google.protobuf.json_format import MessageToDict
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.wrappers_pb2 import BoolValue
from google.protobuf.wrappers_pb2 import BytesValue
from google.protobuf.wrappers_pb2 import DoubleValue
from google.protobuf.wrappers_pb2 import FloatValue
from google.protobuf.wrappers_pb2 import Int32Value
from google.protobuf.wrappers_pb2 import Int64Value
from google.protobuf.wrappers_pb2 import StringValue
from google.protobuf.wrappers_pb2 import UInt32Value
from google.protobuf.wrappers_pb2 import UInt64Value
from pyspark import SparkContext
from pyspark.serializers import CloudPickleSerializer
from pyspark.sql.functions import struct
from pyspark.sql.session import SparkSession
from pyspark.sql.types import ArrayType
from pyspark.sql.types import BinaryType
from pyspark.sql.types import BooleanType
from pyspark.sql.types import DecimalType
from pyspark.sql.types import DoubleType
from pyspark.sql.types import FloatType
from pyspark.sql.types import IntegerType
from pyspark.sql.types import LongType
from pyspark.sql.types import StringType
from pyspark.sql.types import StructField
from pyspark.sql.types import StructType
from pyspark.sql.types import TimestampType

from example.example_pb2 import DecimalMessage
from example.example_pb2 import ExampleMessage
from example.example_pb2 import NestedMessage
from example.example_pb2 import RecursiveMessage
from pbspark._proto import MessageConverter
from pbspark._proto import _patched_convert_scalar_field_value
from pbspark._proto import df_from_protobuf
from pbspark._proto import df_to_protobuf
from pbspark._proto import from_protobuf
from pbspark._proto import to_protobuf
from tests.fixtures import decimal_serializer  # type: ignore[import]
from tests.fixtures import encode_recursive


@pytest.fixture()
def example():
    ts = Timestamp()
    ts.FromDatetime(datetime.datetime.utcnow())
    dur = Duration(seconds=1, nanos=1)
    ex = ExampleMessage(
        string="asdf",
        int32=69,
        int64=789,
        uint64=404,
        float=4.20,
        stringlist=["one", "two", "three"],
        bytes=b"something",
        nested=NestedMessage(
            key="hello",
            value="world",
        ),
        enum=ExampleMessage.SomeEnum.first,
        timestamp=ts,
        duration=dur,
        decimal=DecimalMessage(
            value="3.50",
        ),
        doublevalue=DoubleValue(value=1.23),
        floatvalue=FloatValue(value=2.34),
        int64value=Int64Value(value=9001),
        uint64value=UInt64Value(value=9002),
        int32value=Int32Value(value=666),
        uint32value=UInt32Value(value=789),
        boolvalue=BoolValue(value=True),
        stringvalue=StringValue(value="qwerty"),
        bytesvalue=BytesValue(value=b"buf"),
    )
    return ex


@pytest.fixture(scope="session")
def spark():
    sc = SparkContext(serializer=CloudPickleSerializer())
    spark = SparkSession(sc).builder.getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    return spark


@pytest.fixture(params=[True, False])
def expanded(request):
    return request.param


@pytest.fixture(params=[True, False])
def including_default_value_fields(request):
    return request.param


@pytest.fixture(params=[True, False])
def use_integers_for_enums(request):
    return request.param


@pytest.fixture(params=[True, False])
def preserving_proto_field_name(request):
    return request.param


def test_get_spark_schema():
    mc = MessageConverter()
    mc.register_serializer(
        DecimalMessage, decimal_serializer, DecimalType(precision=10, scale=2)
    )
    schema = mc.get_spark_schema(ExampleMessage)
    expected_schema = StructType(
        [
            StructField("int32", IntegerType(), True),
            StructField("int64", LongType(), True),
            StructField("uint32", LongType(), True),
            StructField("uint64", LongType(), True),
            StructField("double", DoubleType(), True),
            StructField("float", FloatType(), True),
            StructField("bool", BooleanType(), True),
            StructField("enum", StringType(), True),
            StructField("string", StringType(), True),
            StructField(
                "nested",
                StructType(
                    [
                        StructField("key", StringType(), True),
                        StructField("value", StringType(), True),
                    ]
                ),
                True,
            ),
            StructField("stringlist", ArrayType(StringType(), True), True),
            StructField("bytes", BinaryType(), True),
            StructField("sfixed32", IntegerType(), True),
            StructField("sfixed64", LongType(), True),
            StructField("sint32", IntegerType(), True),
            StructField("sint64", LongType(), True),
            StructField("fixed32", LongType(), True),
            StructField("fixed64", LongType(), True),
            StructField("oneofstring", StringType(), True),
            StructField("oneofint32", IntegerType(), True),
            StructField(
                "map",
                ArrayType(
                    StructType(
                        [
                            StructField("key", StringType(), True),
                            StructField("value", StringType(), True),
                        ]
                    ),
                    True,
                ),
                True,
            ),
            StructField("timestamp", TimestampType(), True),
            StructField("duration", StringType(), True),
            StructField("decimal", DecimalType(10, 2), True),
            StructField("doublevalue", DoubleType(), True),
            StructField("floatvalue", FloatType(), True),
            StructField("int64value", LongType(), True),
            StructField("uint64value", LongType(), True),
            StructField("int32value", IntegerType(), True),
            StructField("uint32value", LongType(), True),
            StructField("boolvalue", BooleanType(), True),
            StructField("stringvalue", StringType(), True),
            StructField("bytesvalue", BinaryType(), True),
            StructField("caseName", StringType(), True),
        ]
    )
    assert schema == expected_schema


def test_patched_convert_scalar_field_value():
    assert not hasattr(json_format._ConvertScalarFieldValue, "__wrapped__")
    with _patched_convert_scalar_field_value():
        assert hasattr(json_format._ConvertScalarFieldValue, "__wrapped__")
    assert not hasattr(json_format._ConvertScalarFieldValue, "__wrapped__")


def test_get_decoder(example):
    mc = MessageConverter()
    mc.register_serializer(
        DecimalMessage, decimal_serializer, DecimalType(precision=10, scale=2)
    )
    decoder = mc.get_decoder(ExampleMessage)
    s = example.SerializeToString()
    decoded = decoder(s)
    assert decoded == mc.message_to_dict(example)
    expected = {
        "int32": 69,
        "int64": 789,
        "uint64": 404,
        "float": 4.2,
        "enum": "first",
        "string": "asdf",
        "nested": {"key": "hello", "value": "world"},
        "stringlist": ["one", "two", "three"],
        "bytes": b"something",
        "timestamp": example.timestamp.ToDatetime(),
        "duration": example.duration.ToJsonString(),
        "decimal": Decimal(example.decimal.value),
        "doublevalue": 1.23,
        "floatvalue": 2.34,
        "int64value": 9001,
        "uint64value": 9002,
        "int32value": 666,
        "uint32value": 789,
        "boolvalue": True,
        "stringvalue": "qwerty",
        "bytesvalue": b"buf",
    }
    assert decoded == expected


def test_from_protobuf(
    example, spark, preserving_proto_field_name, use_integers_for_enums
):
    mc = MessageConverter()
    mc.register_serializer(
        DecimalMessage, decimal_serializer, DecimalType(precision=10, scale=2)
    )

    data = [{"value": example.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]
    dfs = df.select(
        mc.from_protobuf(
            data=df.value,
            message_type=ExampleMessage,
            preserving_proto_field_name=preserving_proto_field_name,
            use_integers_for_enums=use_integers_for_enums,
        ).alias("value")
    )
    dfe = dfs.select("value.*")
    dfe.show()
    dfe.printSchema()

    if preserving_proto_field_name:
        field_names = [field.name for field in ExampleMessage.DESCRIPTOR.fields]
    else:
        field_names = [
            field.camelcase_name for field in ExampleMessage.DESCRIPTOR.fields
        ]
    for field_name in field_names:
        assert field_name in dfe.columns

    if use_integers_for_enums:
        assert StructField("enum", IntegerType(), True) in dfe.schema.fields
    else:
        assert StructField("enum", StringType(), True) in dfe.schema.fields


def test_round_trip(example, spark):
    mc = MessageConverter()

    data = [{"value": example.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]
    df.show()

    df.printSchema()
    dfs = df.select(mc.from_protobuf(df.value, ExampleMessage).alias("value"))
    df_again = dfs.select(mc.to_protobuf(dfs.value, ExampleMessage).alias("value"))
    df_again.show()
    assert df.schema == df_again.schema
    assert df.collect() == df_again.collect()

    # make a flattened df and then encode from unflattened df
    df_flattened = dfs.select("value.*")

    df_unflattened = df_flattened.select(
        struct([df_flattened[c] for c in df_flattened.columns]).alias("value")
    )
    df_unflattened.show()
    schema = df_unflattened.schema
    # this will be false because there are no null records
    schema.fields[0].nullable = True
    assert dfs.schema == schema
    assert dfs.collect() == df_unflattened.collect()
    df_again = df_unflattened.select(
        mc.to_protobuf(df_unflattened.value, ExampleMessage).alias("value")
    )
    df_again.show()
    assert df.schema == df_again.schema
    assert df.collect() == df_again.collect()


def test_recursive_message(spark):
    message = RecursiveMessage(
        note="one",
        message=RecursiveMessage(note="two", message=RecursiveMessage(note="three")),
    )

    return_type = StructType(
        [
            StructField("note", StringType(), True),
            StructField(
                "message",
                StructType(
                    [
                        StructField("note", StringType(), True),
                        StructField("message", StringType(), True),
                    ]
                ),
                True,
            ),
        ]
    )
    expected = {
        "note": "one",
        "message": {
            "note": "two",
            "message": json.dumps(MessageToDict(message.message.message)),
        },
    }
    assert encode_recursive(message) == expected
    mc = MessageConverter()
    mc.register_serializer(RecursiveMessage, encode_recursive, return_type)

    data = [{"value": message.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]
    df.show()

    dfs = df.select(mc.from_protobuf(df.value, RecursiveMessage).alias("value"))
    dfs.show(truncate=False)
    data = dfs.collect()
    assert data[0].asDict(True)["value"] == expected


def test_to_from_protobuf(example, spark, expanded):
    data = [{"value": example.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]

    df_decoded = df.select(from_protobuf(df.value, ExampleMessage).alias("value"))

    mc = MessageConverter()
    assert df_decoded.schema.fields[0].dataType == mc.get_spark_schema(ExampleMessage)

    df_encoded = df_decoded.select(
        to_protobuf(df_decoded.value, ExampleMessage).alias("value")
    )

    assert df_encoded.columns == ["value"]
    assert df_encoded.schema == df.schema
    assert df.collect() == df_encoded.collect()


def test_df_to_from_protobuf(example, spark, expanded):
    data = [{"value": example.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]

    df_decoded = df_from_protobuf(df, ExampleMessage, expanded=expanded)

    mc = MessageConverter()
    schema = mc.get_spark_schema(ExampleMessage)
    if expanded:
        assert df_decoded.schema == schema
    else:
        assert df_decoded.schema.fields[0].dataType == schema

    df_encoded = df_to_protobuf(df_decoded, ExampleMessage, expanded=expanded)

    assert df_encoded.columns == ["value"]
    assert df_encoded.schema == df.schema
    assert df.collect() == df_encoded.collect()


def test_including_default_value_fields(spark, including_default_value_fields):
    example = ExampleMessage(string="asdf")
    data = [{"value": example.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]

    df_decoded = df_from_protobuf(
        df=df,
        message_type=ExampleMessage,
        expanded=True,
        including_default_value_fields=including_default_value_fields,
    )
    data = df_decoded.collect()
    if including_default_value_fields:
        assert data[0].asDict(True)["int32"] == 0
    else:
        assert data[0].asDict(True)["int32"] is None


def test_use_integers_for_enums(spark, use_integers_for_enums):
    example = ExampleMessage(enum=ExampleMessage.SomeEnum.first)
    data = [{"value": example.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]

    df_decoded = df_from_protobuf(
        df=df,
        message_type=ExampleMessage,
        expanded=True,
        use_integers_for_enums=use_integers_for_enums,
    )
    data = df_decoded.collect()
    if use_integers_for_enums:
        assert data[0].asDict(True)["enum"] == 1
    else:
        assert data[0].asDict(True)["enum"] == "first"


def test_preserving_proto_field_name(spark, preserving_proto_field_name):
    example = ExampleMessage(case_name="asdf")
    data = [{"value": example.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]

    df_decoded = df_from_protobuf(
        df=df,
        message_type=ExampleMessage,
        expanded=True,
        preserving_proto_field_name=preserving_proto_field_name,
    )
    data = df_decoded.collect()
    if preserving_proto_field_name:
        assert data[0].asDict(True)["case_name"] == "asdf"
    else:
        assert data[0].asDict(True)["caseName"] == "asdf"


def test_float_precision(spark):
    example = ExampleMessage(float=1.234567)
    data = [{"value": example.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]

    df_decoded = df_from_protobuf(
        df=df,
        message_type=ExampleMessage,
        expanded=True,
        float_precision=2,
    )
    data = df_decoded.collect()
    assert data[0].asDict(True)["float"] == pytest.approx(1.2)
