# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: example/example.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import duration_pb2 as google_dot_protobuf_dot_duration__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x15\x65xample/example.proto\x12\x07\x65xample\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1egoogle/protobuf/duration.proto\x1a\x1egoogle/protobuf/wrappers.proto"@\n\rSimpleMessage\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x10\n\x08quantity\x18\x02 \x01(\x03\x12\x0f\n\x07measure\x18\x03 \x01(\x02"+\n\rNestedMessage\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t"\x1f\n\x0e\x44\x65\x63imalMessage\x12\r\n\x05value\x18\x01 \x01(\t"\x89\t\n\x0e\x45xampleMessage\x12\r\n\x05int32\x18\x01 \x01(\x05\x12\r\n\x05int64\x18\x02 \x01(\x03\x12\x0e\n\x06uint32\x18\x03 \x01(\r\x12\x0e\n\x06uint64\x18\x04 \x01(\x04\x12\x0e\n\x06\x64ouble\x18\x05 \x01(\x01\x12\r\n\x05\x66loat\x18\x06 \x01(\x02\x12\x0c\n\x04\x62ool\x18\x07 \x01(\x08\x12.\n\x04\x65num\x18\x08 \x01(\x0e\x32 .example.ExampleMessage.SomeEnum\x12\x0e\n\x06string\x18\t \x01(\t\x12&\n\x06nested\x18\n \x01(\x0b\x32\x16.example.NestedMessage\x12\x12\n\nstringlist\x18\x0b \x03(\t\x12\r\n\x05\x62ytes\x18\x0c \x01(\x0c\x12\x10\n\x08sfixed32\x18\r \x01(\x0f\x12\x10\n\x08sfixed64\x18\x0e \x01(\x10\x12\x0e\n\x06sint32\x18\x0f \x01(\x11\x12\x0e\n\x06sint64\x18\x10 \x01(\x12\x12\x0f\n\x07\x66ixed32\x18\x11 \x01(\x07\x12\x0f\n\x07\x66ixed64\x18\x12 \x01(\x06\x12\x15\n\x0boneofstring\x18\x13 \x01(\tH\x00\x12\x14\n\noneofint32\x18\x14 \x01(\x05H\x00\x12-\n\x03map\x18\x15 \x03(\x0b\x32 .example.ExampleMessage.MapEntry\x12-\n\ttimestamp\x18\x16 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12+\n\x08\x64uration\x18\x17 \x01(\x0b\x32\x19.google.protobuf.Duration\x12(\n\x07\x64\x65\x63imal\x18\x18 \x01(\x0b\x32\x17.example.DecimalMessage\x12\x31\n\x0b\x64oublevalue\x18\x19 \x01(\x0b\x32\x1c.google.protobuf.DoubleValue\x12/\n\nfloatvalue\x18\x1a \x01(\x0b\x32\x1b.google.protobuf.FloatValue\x12/\n\nint64value\x18\x1b \x01(\x0b\x32\x1b.google.protobuf.Int64Value\x12\x31\n\x0buint64value\x18\x1c \x01(\x0b\x32\x1c.google.protobuf.UInt64Value\x12/\n\nint32value\x18\x1d \x01(\x0b\x32\x1b.google.protobuf.Int32Value\x12\x31\n\x0buint32value\x18\x1e \x01(\x0b\x32\x1c.google.protobuf.UInt32Value\x12-\n\tboolvalue\x18\x1f \x01(\x0b\x32\x1a.google.protobuf.BoolValue\x12\x31\n\x0bstringvalue\x18  \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12/\n\nbytesvalue\x18! \x01(\x0b\x32\x1b.google.protobuf.BytesValue\x12\x11\n\tcase_name\x18" \x01(\t\x1a*\n\x08MapEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01"2\n\x08SomeEnum\x12\x0f\n\x0bunspecified\x10\x00\x12\t\n\x05\x66irst\x10\x01\x12\n\n\x06second\x10\x02\x42\x07\n\x05oneof"L\n\x10RecursiveMessage\x12\x0c\n\x04note\x18\x01 \x01(\t\x12*\n\x07message\x18\x02 \x01(\x0b\x32\x19.example.RecursiveMessageb\x06proto3'
)

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "example.example_pb2", globals())
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _EXAMPLEMESSAGE_MAPENTRY._options = None
    _EXAMPLEMESSAGE_MAPENTRY._serialized_options = b"8\001"
    _SIMPLEMESSAGE._serialized_start = 131
    _SIMPLEMESSAGE._serialized_end = 195
    _NESTEDMESSAGE._serialized_start = 197
    _NESTEDMESSAGE._serialized_end = 240
    _DECIMALMESSAGE._serialized_start = 242
    _DECIMALMESSAGE._serialized_end = 273
    _EXAMPLEMESSAGE._serialized_start = 276
    _EXAMPLEMESSAGE._serialized_end = 1437
    _EXAMPLEMESSAGE_MAPENTRY._serialized_start = 1334
    _EXAMPLEMESSAGE_MAPENTRY._serialized_end = 1376
    _EXAMPLEMESSAGE_SOMEENUM._serialized_start = 1378
    _EXAMPLEMESSAGE_SOMEENUM._serialized_end = 1428
    _RECURSIVEMESSAGE._serialized_start = 1439
    _RECURSIVEMESSAGE._serialized_end = 1515
# @@protoc_insertion_point(module_scope)
