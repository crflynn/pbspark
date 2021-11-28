import pytest
from google.protobuf.json_format import MessageToDict
from pyspark.sql.session import SparkSession
from pyspark.sql.types import *

from example.example_pb2 import ExampleMessage
from example.example_pb2 import NestedMessage
from pbspark import from_protobuf
from pbspark import get_decoder
from pbspark import get_spark_schema


@pytest.fixture()
def example():
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
    )
    return ex


def test_get_spark_schema():
    schema = get_spark_schema(ExampleMessage)
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
        ]
    )
    assert schema == expected_schema


def test_get_decoder(example):
    decoder = get_decoder(ExampleMessage)
    s = example.SerializeToString()
    decoded = decoder(s)
    assert decoded == MessageToDict(example)
    expected = {
        "int32": 69,
        "float": 4.2,
        "enum": "first",
        "string": "asdf",
        "nested": {"key": "hello", "value": "world"},
        "stringlist": ["one", "two", "three"],
        "bytes": "c29tZXRoaW5n",  # b64encoded
    }
    assert decoded == expected


def test_from_protobuf(example):
    data = [{"value": example.SerializeToString()}]

    spark = SparkSession.builder.getOrCreate()
    df = spark.createDataFrame(data)
    dfs = df.select(from_protobuf(df.value, ExampleMessage).alias("value"))
    dfe = dfs.select("value.*")

    field_names = [field.name for field in ExampleMessage.DESCRIPTOR.fields]
    for field_name in field_names:
        assert field_name in dfe.columns
    dfe.show()
