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

`pbspark` uses protobuf's `MessageToDict`, which deserializes everything into JSON compatible objects by default. The exception is the bytes type, which `MessageToDict` would decode to a base64-encoded string; `pbspark` will decode any bytes fields directly to a spark `ByteType`.

Conversion between `google.protobuf.Timestamp` and spark `TimestampType` can be enabled using:

```python
from pbspark import MessageConverter

mc = MessageConverter()
mc.register_timestamp_serializer()
mc.register_timestamp_deserializer()
```

Custom serde is also supported. Suppose we have a message in which we want to combine fields when we serialize.

Create and register a custom serializer with the `MessageConverter`.

```python
from pbspark import MessageConverter
from example.example_pb2 import ExampleMessage
from example.example_pb2 import NestedMessage
from pyspark.sql.types import StringType

mc = MessageConverter()
# built-in to serialize Timestamp messages to datetime objects
mc.register_timestamp_serializer()

# register a custom serializer
# this will serialize the NestedMessages into a string rather than a
# struct with `key` and `value` fields
combine_key_value = lambda message: message.key + ":" + message.value

mc.register_serializer(NestedMessage, combine_key_value, StringType)

...

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