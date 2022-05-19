# pbspark

This package provides a way to convert protobuf messages into pyspark dataframes and vice versa using a pyspark udf.

## Installation

To install:

```bash
pip install pbspark
```

## Usage

Suppose we have a pyspark DataFrame which contains a column `value` which has protobuf encoded messages of our `SimpleMessage`:

```protobuf
syntax = "proto3";

package example;

message SimpleMessage {
  string name = 1;
  int64 quantity = 2;
  float measure = 3;
}
```

Using `pbspark` we can decode the messages into spark `StructType` and then flatten them.

```python
from pyspark.sql.session import SparkSession
from pbspark import MessageConverter
from example.example_pb2 import SimpleMessage

spark = SparkSession.builder.getOrCreate()

example = SimpleMessage(name="hello", quantity=5, measure=12.3)
data = [{"value": example.SerializeToString()}]
df = spark.createDataFrame(data)

mc = MessageConverter()
df_decoded = df.select(mc.from_protobuf(df.value, SimpleMessage).alias("value"))
df_flattened = df_decoded.select("value.*")
df_flattened.show()

# +-----+--------+-------+
# | name|quantity|measure|
# +-----+--------+-------+
# |hello|       5|   12.3|
# +-----+--------+-------+

df_flattened.schema
# StructType(List(StructField(name,StringType,true),StructField(quantity,IntegerType,true),StructField(measure,FloatType,true))
```

We can also re-encode them into protobuf strings.

```python
df_reencoded = df_decoded.select(mc.to_protobuf(df_decoded.value, SimpleMessage).alias("value"))
```

For flattened data, we can also (re-)encode after collecting and packing into a struct:

```python
from pyspark.sql import Row

data = [Row(value=row).asDict(recursive=True) for row in df_flattened.collect()]
df_unflattened = spark.createDataFrame(
    data=data,
    schema=StructType(
        [
            StructField(
                name="value",
                dataType=mc.get_spark_schema(SimpleMessage),
                nullable=True,
            )
        ]
    ),
)
df_unflattened.show()
df_reencoded = df_unflattened.select(
    mc.to_protobuf(df_unflattened.value, SimpleMessage).alias("value")
)
```

Internally, `pbspark` uses protobuf's `MessageToDict`, which deserializes everything into JSON compatible objects by default. The exceptions are
* protobuf's bytes type, which `MessageToDict` would decode to a base64-encoded string; `pbspark` will decode any bytes fields directly to a spark `BinaryType`.
* protobuf's well known type, Timestamp type, which `MessageToDict` would decode to a string; `pbspark` will decode any Timestamp messages directly to a spark `TimestampType` (via python datetime objects).

Custom serde is also supported. Suppose we use our `NestedMessage` from the repository's example and we want to serialize the key and value together into a single string.

```protobuf
message NestedMessage {
  string key = 1;
  string value = 2;
}
```

We can create and register a custom serializer with the `MessageConverter`.

```python
from pbspark import MessageConverter
from example.example_pb2 import ExampleMessage
from example.example_pb2 import NestedMessage
from pyspark.sql.types import StringType

mc = MessageConverter()

# register a custom serializer
# this will serialize the NestedMessages into a string rather than a
# struct with `key` and `value` fields
encode_nested = lambda message:  message.key + ":" + message.value

mc.register_serializer(NestedMessage, encode_nested, StringType)

# ...

from pyspark.sql.session import SparkSession
from pyspark import SparkContext
from pyspark.serializers import CloudPickleSerializer

sc = SparkContext(serializer=CloudPickleSerializer())
spark = SparkSession(sc).builder.getOrCreate()

message = ExampleMessage(nested=NestedMessage(key="hello", value="world"))
data = [{"value": message.SerializeToString()}]
df = spark.createDataFrame(data)

df_decoded = df.select(mc.from_protobuf(df.value, ExampleMessage).alias("value"))
# rather than a struct the value of `nested` is a string
df_decoded.select("value.nested").show()

# +-----------+
# |     nested|
# +-----------+
# |hello:world|
# +-----------+
```

More generally, custom serde functions should be written in the following format.

```python
# Encoding takes a message instance and returns the result
# of the custom transformation.
def encode_nested(message: NestedMessage) -> str:
    return message.key + ":" + message.value

# Decoding takes the encoded value, a message instance, and path string
# and populates the fields of the message instance. It returns `None`.
# The path str is used in the protobuf parser to log parse error info.
# Note that the first argument type should match the return type of the
# encoder if using both.
def decode_nested(s: str, message: NestedMessage, path: str):
    key, value = s.split(":")
    message.key = key
    message.value = value
```
