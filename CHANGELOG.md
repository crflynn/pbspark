# Changelog

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
