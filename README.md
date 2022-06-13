# pbspark

This package provides a way to convert protobuf messages into pyspark dataframes and vice versa using pyspark `udf`s.

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

### Basic conversion functions

There are two functions for operating on columns, `to_protobuf` and `from_protobuf`. These operations convert to/from an encoded protobuf column to a column of a struct representing the inferred message structure. `MessageConverter` instances (discussed below) can optionally be passed to these functions.

```python
from pyspark.sql.session import SparkSession
from example.example_pb2 import SimpleMessage
from pbspark import from_protobuf
from pbspark import to_protobuf

spark = SparkSession.builder.getOrCreate()

example = SimpleMessage(name="hello", quantity=5, measure=12.3)
data = [{"value": example.SerializeToString()}]
df_encoded = spark.createDataFrame(data)

df_decoded = df_encoded.select(from_protobuf(df_encoded.value, SimpleMessage).alias("value"))
df_expanded = df_decoded.select("value.*")
df_expanded.show()

# +-----+--------+-------+
# | name|quantity|measure|
# +-----+--------+-------+
# |hello|       5|   12.3|
# +-----+--------+-------+

df_reencoded = df_decoded.select(to_protobuf(df_decoded.value, SimpleMessage).alias("value"))
```

There are two helper functions, `df_to_protobuf` and `df_from_protobuf` for use on dataframes. They have a kwarg `expanded`, which will also take care of expanding/contracting the data between the single `value` column used in these examples and a dataframe which contains a column for each message field. `MessageConverter` instances (discussed below) can optionally be passed to these functions.

```python
from pyspark.sql.session import SparkSession
from example.example_pb2 import SimpleMessage
from pbspark import df_from_protobuf
from pbspark import df_to_protobuf

spark = SparkSession.builder.getOrCreate()

example = SimpleMessage(name="hello", quantity=5, measure=12.3)
data = [{"value": example.SerializeToString()}]
df_encoded = spark.createDataFrame(data)

# expanded=True will perform a `.select("value.*")` after converting,
# resulting in each protobuf field having its own column
df_expanded = df_from_protobuf(df_encoded, SimpleMessage, expanded=True)
df_expanded.show()

# +-----+--------+-------+
# | name|quantity|measure|
# +-----+--------+-------+
# |hello|       5|   12.3|
# +-----+--------+-------+

# expanded=True will first pack data using `struct([df[c] for c in df.columns])`,
# use this if the passed dataframe is already expanded
df_reencoded = df_to_protobuf(df_expanded, SimpleMessage, expanded=True)
```

### Column conversion using the `MessageConverter`

The four helper functions above are also available as methods on the `MessageConverter` class. Using an instance of `MessageConverter` we can decode the column of encoded messages into a column of spark `StructType` and then expand the fields.

```python
from pyspark.sql.session import SparkSession
from pbspark import MessageConverter
from example.example_pb2 import SimpleMessage

spark = SparkSession.builder.getOrCreate()

example = SimpleMessage(name="hello", quantity=5, measure=12.3)
data = [{"value": example.SerializeToString()}]
df_encoded = spark.createDataFrame(data)

mc = MessageConverter()
df_decoded = df_encoded.select(mc.from_protobuf(df_encoded.value, SimpleMessage).alias("value"))
df_expanded = df_decoded.select("value.*")
df_expanded.show()

# +-----+--------+-------+
# | name|quantity|measure|
# +-----+--------+-------+
# |hello|       5|   12.3|
# +-----+--------+-------+

df_expanded.schema
# StructType(List(StructField(name,StringType,true),StructField(quantity,IntegerType,true),StructField(measure,FloatType,true))
```

We can also re-encode them into protobuf.

```python
df_reencoded = df_decoded.select(mc.to_protobuf(df_decoded.value, SimpleMessage).alias("value"))
```

For expanded data, we can also encode after packing into a struct column:

```python
from pyspark.sql.functions import struct

df_unexpanded = df_expanded.select(
    struct([df_expanded[c] for c in df_expanded.columns]).alias("value")
)
df_reencoded = df_unexpanded.select(
    mc.to_protobuf(df_unexpanded.value, SimpleMessage).alias("value")
)
```

### Conversion details

Internally, `pbspark` uses protobuf's `MessageToDict`, which deserializes everything into JSON compatible objects by default. The exceptions are
* protobuf's bytes type, which `MessageToDict` would decode to a base64-encoded string; `pbspark` will decode any bytes fields directly to a spark `BinaryType`.
* protobuf's well known type, Timestamp type, which `MessageToDict` would decode to a string; `pbspark` will decode any Timestamp messages directly to a spark `TimestampType` (via python datetime objects).

### Custom conversion of message types

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

mc.register_serializer(NestedMessage, encode_nested, StringType())

# ...

from pyspark.sql.session import SparkSession
from pyspark import SparkContext
from pyspark.serializers import CloudPickleSerializer

sc = SparkContext(serializer=CloudPickleSerializer())
spark = SparkSession(sc).builder.getOrCreate()

message = ExampleMessage(nested=NestedMessage(key="hello", value="world"))
data = [{"value": message.SerializeToString()}]
df_encoded = spark.createDataFrame(data)

df_decoded = df_encoded.select(mc.from_protobuf(df_encoded.value, ExampleMessage).alias("value"))
# rather than a struct the value of `nested` is a string
df_decoded.select("value.nested").show()

# +-----------+
# |     nested|
# +-----------+
# |hello:world|
# +-----------+
```

### How to write conversion functions

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

### Known issues

`RecursionError` when using self-referencing protobuf messages. Spark schemas do not allow for arbitrary depth, so protobuf messages which are circular- or self-referencing will result in infinite recursion errors when inferring the schema. If you have message structures like this you should resort to creating custom conversion functions, which forcibly limit the structural depth when converting these messages.