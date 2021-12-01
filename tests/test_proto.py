import datetime
from decimal import Decimal

import pytest
from google.protobuf.duration_pb2 import Duration
from google.protobuf.timestamp_pb2 import Timestamp
from pyspark import SparkContext
from pyspark.serializers import CloudPickleSerializer
from pyspark.sql.session import SparkSession
from pyspark.sql.types import *

from example.example_pb2 import DecimalMessage
from example.example_pb2 import ExampleMessage
from example.example_pb2 import NestedMessage
from pbspark._proto import MessageSerializer


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


decimal_serializer = lambda message: Decimal(message.value)  # noqa


def test_get_spark_schema():
    ser = MessageSerializer()
    ser.register_timestamp_serializer()
    ser.register_serializer(
        DecimalMessage, decimal_serializer, DecimalType, {"precision": 10, "scale": 2}
    )
    schema = ser.get_spark_schema(ExampleMessage)
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
            StructField("bytes", StringType(), True),
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


def test_get_decoder(example):
    ser = MessageSerializer()
    ser.register_timestamp_serializer()
    ser.register_serializer(
        DecimalMessage, decimal_serializer, DecimalType, {"precision": 10, "scale": 2}
    )
    decoder = ser.get_decoder(ExampleMessage)
    s = example.SerializeToString()
    decoded = decoder(s)
    assert decoded == ser.message_to_dict(example)
    expected = {
        "int32": 69,
        "float": 4.2,
        "enum": "first",
        "string": "asdf",
        "nested": {"key": "hello", "value": "world"},
        "stringlist": ["one", "two", "three"],
        "bytes": "c29tZXRoaW5n",  # b64encoded
        "timestamp": example.timestamp.ToDatetime(),
        "duration": example.duration.ToJsonString(),
        "decimal": Decimal(example.decimal.value),
    }
    assert decoded == expected


def test_from_protobuf(example):
    ser = MessageSerializer()
    ser.register_timestamp_serializer()
    ser.register_serializer(
        DecimalMessage, decimal_serializer, DecimalType, {"precision": 10, "scale": 2}
    )
    data = [{"value": example.SerializeToString()}]

    sc = SparkContext(serializer=CloudPickleSerializer())
    spark = SparkSession(sc).builder.getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")

    df = spark.createDataFrame(data)
    dfs = df.select(ser.from_protobuf(df.value, ExampleMessage).alias("value"))
    dfe = dfs.select("value.*")
    dfe.show()
    dfe.printSchema()

    field_names = [field.name for field in ExampleMessage.DESCRIPTOR.fields]
    for field_name in field_names:
        assert field_name in dfe.columns
