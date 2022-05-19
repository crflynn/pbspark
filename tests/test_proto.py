import datetime
from decimal import Decimal

import pytest
from google.protobuf import json_format
from google.protobuf.duration_pb2 import Duration
from google.protobuf.timestamp_pb2 import Timestamp
from pyspark import SparkContext
from pyspark.serializers import CloudPickleSerializer
from pyspark.sql import Row
from pyspark.sql.session import SparkSession
from pyspark.sql.types import *

from example.example_pb2 import DecimalMessage
from example.example_pb2 import ExampleMessage
from example.example_pb2 import NestedMessage
from pbspark._proto import MessageConverter
from pbspark._proto import _patched_convert_scalar_field_value


@pytest.fixture()
def example():
    ts = Timestamp()
    ts.FromDatetime(datetime.datetime.utcnow())
    dur = Duration(seconds=1, nanos=1)
    ex = ExampleMessage(
        string="asdf",
        int32=69,
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
    )
    return ex


@pytest.fixture(scope="session")
def spark():
    sc = SparkContext(serializer=CloudPickleSerializer())
    spark = SparkSession(sc).builder.getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    return spark


decimal_serializer = lambda message: Decimal(message.value)  # noqa


def test_get_spark_schema():
    mc = MessageConverter()
    mc.register_timestamp_serializer()
    mc.register_serializer(
        DecimalMessage, decimal_serializer, DecimalType, {"precision": 10, "scale": 2}
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
    mc.register_timestamp_serializer()
    mc.register_serializer(
        DecimalMessage, decimal_serializer, DecimalType, {"precision": 10, "scale": 2}
    )
    decoder = mc.get_decoder(ExampleMessage)
    s = example.SerializeToString()
    decoded = decoder(s)
    assert decoded == mc.message_to_dict(example)
    expected = {
        "int32": 69,
        "float": 4.2,
        "enum": "first",
        "string": "asdf",
        "nested": {"key": "hello", "value": "world"},
        "stringlist": ["one", "two", "three"],
        "bytes": b"something",
        "timestamp": example.timestamp.ToDatetime(),
        "duration": example.duration.ToJsonString(),
        "decimal": Decimal(example.decimal.value),
    }
    assert decoded == expected


def test_from_protobuf(example, spark):
    mc = MessageConverter()
    mc.register_timestamp_serializer()
    mc.register_serializer(
        DecimalMessage, decimal_serializer, DecimalType, {"precision": 10, "scale": 2}
    )

    data = [{"value": example.SerializeToString()}]

    df = spark.createDataFrame(data)  # type: ignore[type-var]
    dfs = df.select(mc.from_protobuf(df.value, ExampleMessage).alias("value"))
    dfe = dfs.select("value.*")
    dfe.show()
    dfe.printSchema()

    field_names = [field.name for field in ExampleMessage.DESCRIPTOR.fields]
    for field_name in field_names:
        assert field_name in dfe.columns


def test_round_trip(example, spark):
    mc = MessageConverter()
    mc.register_timestamp_serializer()
    mc.register_timestamp_deserializer()

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

    data = [Row(value=row).asDict(recursive=True) for row in df_flattened.collect()]
    df_unflattened = spark.createDataFrame(  # type: ignore[type-var]
        data=data,
        schema=StructType(
            [
                StructField(
                    name="value",
                    dataType=mc.get_spark_schema(ExampleMessage),
                    nullable=True,
                )
            ]
        ),
    )
    df_unflattened.show()
    assert dfs.schema == df_unflattened.schema
    assert dfs.collect() == df_unflattened.collect()
    df_again = df_unflattened.select(
        mc.to_protobuf(df_unflattened.value, ExampleMessage).alias("value")
    )
    df_again.show()
    assert df.schema == df_again.schema
    assert df.collect() == df_again.collect()
