# Changelog

## 2023-06-07 - 0.9.0

* Relax pyspark constraint

## 2023-01-11 - 0.8.0

* Breaking: Provide the same kwargs used in the protobuf lib on encoding/decoding rather than the ``options`` dict, except ``DescriptorPool`` which is unserializable.
* Breaking: Change param ``mc`` -> ``message_converter`` on top level functions.

## 2022-07-07 - 0.7.0

* Bugfix: Fixed a bug where int64 protobuf types were not being properly converted into spark types.
* Added support for protobuf wrapper types.

## 2022-06-22 - 0.6.1

* Bugfix: Fixed a bug where ``options`` was not being passed recursively in ``get_spark_schema``. 

## 2022-06-13 - 0.6.0

* Add ``to_protobuf`` and ``from_protobuf`` functions to operate on columns without needing a ``MessageConverter``.
* Add ``df_to_protobuf`` and ``df_from_protobuf`` functions to operate on DataFrames without needing a ``MessageConverter``. These functions also optionally handle struct expansion.

## 2022-06-12 - 0.5.1

* Bugfix: Fix ``bytearray`` TypeError when using newer versions of protobuf

## 2022-05-20 - 0.5.0

* Breaking: return type instances to be passed to custom serializers rather than type class + init kwargs
* Bugfix: `get_spark_schema` now returns properly when the descriptor passed has a registered custom serializer

## 2022-05-19 - 0.4.0

* Breaking: pbspark now encodes the well known type `Timestamp` to spark `TimestampType` by default.
* Bugfix: protobuf bytes now properly convert to spark BinaryType
* Bugfix: message decoding now properly works by populating the passed message instance rather than returning a new one
* protobuf objects are now patched only temporarily when being used by pbspark
* Timestamp conversion now references protobuf well known type objects rather than objects copied from protobuf to pbspark
* Modify the encoding function to convert udf-passed Row objects to dictionaries before passing to the parser.
* Documentation fixes and more details on custom encoders.

## 2022-04-19 - 0.3.0

* Breaking: protobuf bytes fields will now convert directly to spark ByteType and vice versa.
* Relax constraint on pyspark
* Bump minimum protobuf version to 3.20.0

## 2021-12-05 - 0.2.0

* Add `to_protobuf` method to encode pyspark structs to protobuf

## 2021-12-01 - 0.1.0

* initial release
