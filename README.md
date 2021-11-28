# pbspark

This package provides a way to deserialize protobuf messages into pyspark dataframes using a pyspark udf.

## Installation

To install:

```bash
pip install pbspark
```

## Usage

Suppose we have a pyspark DataFrame which contains a column `value` which has protobuf encoded messages of our `ExampleMessage`:

```protobuf
syntax = "proto3";

package example;

message ExampleMessage {
  string name = 1;
  int64 quantity = 2;
  float measure = 3;
}
```

Using `pbspark` we can decode the messages into spark `StructType` and then flatten them.

```python
from pyspark.sql.session import SparkSession
from pbspark import from_protobuf
from example.example_pb2 import ExampleMessage

spark = SparkSession.builder.getOrCreate()
df = spark.sql("SELECT value FROM examplemessagetable")
df_decoded = df.select(from_protobuf(df.value, ExampleMessage).alias("value"))
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

## Details

The function `from_protobuf` creates a decoder udf which deserializes the encoded messages to a dictionary, and generates a spark schema from the message descriptor. The function requires a protoc-generated `Message` type derived from the proto message definition. The function also accepts an `options` dict arg which are kwargs passed to `google.protobuf.json_format.MessageToDict` for serializing to a dictionary.