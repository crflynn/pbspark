# pbspark

This package provides a way to deserialize protobuf messages into pyspark dataframes using a pyspark udf.

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
from pbspark import MessageSerializer
from example.example_pb2 import SimpleMessage

spark = SparkSession.builder.getOrCreate()

example = SimpleMessage(name="hello", quantity=5, measure=12.3)
data = [{"value": example.SerializeToString()}]
df = spark.createDataFrame(data)

ser = MessageSerializer()
df_decoded = df.select(ser.from_protobuf(df.value, SimpleMessage).alias("value"))
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

By default, protobuf's `MessageToDict` serializes everything into JSON compatible objects. To handle custom serialization of other types, for instance `google.protobuf.Timestamp` or other special types, you can use a custom serializer.

Suppose we have a message in which we want to combine fields when we serialize.

Create and register a custom serializer with the `MessageSerializer`.

```python
from pbspark import MessageSerializer
from example.example_pb2 import ExampleMessage
from example.example_pb2 import NestedMessage
from pyspark.sql.types import StringType

ser = MessageSerializer()
# built-in to serialize Timestamp messages to datetime objects
ser.register_timestamp_serializer()

# register a custom serializer
def combine_key_value(message: NestedMessage) -> str:
    return message.key + ":" + message.value
    
ser.register_serializer(NestedMessage, combine_key_value, StringType)

...

from pyspark.sql.session import SparkSession
from pyspark import SparkContext
from pyspark.serializers import CloudPickleSerializer

sc = SparkContext(serializer=CloudPickleSerializer())
spark = SparkSession.builder.getOrCreate()

message = ExampleMessage(nested=NestedMessage(key="hello", value="world"))
data = [{"value": message.SerializeToString()}]
df = spark.createDataFrame(data)

df_decoded = df.select(ser.from_protobuf(df.value, ExampleMessage).alias("value"))
# rather than a struct the value of `nested` is a string
df_decoded.select("value.nested").show()
# +-----------+
# |     nested|
# +-----------+
# |hello:world|
# +-----------+

```