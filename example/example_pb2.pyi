"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.duration_pb2
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.timestamp_pb2
import google.protobuf.wrappers_pb2
import typing
import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class SimpleMessage(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    QUANTITY_FIELD_NUMBER: builtins.int
    MEASURE_FIELD_NUMBER: builtins.int
    name: typing.Text
    quantity: builtins.int
    measure: builtins.float
    def __init__(
        self,
        *,
        name: typing.Text = ...,
        quantity: builtins.int = ...,
        measure: builtins.float = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "measure", b"measure", "name", b"name", "quantity", b"quantity"
        ],
    ) -> None: ...

global___SimpleMessage = SimpleMessage

class NestedMessage(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    KEY_FIELD_NUMBER: builtins.int
    VALUE_FIELD_NUMBER: builtins.int
    key: typing.Text
    value: typing.Text
    def __init__(
        self,
        *,
        key: typing.Text = ...,
        value: typing.Text = ...,
    ) -> None: ...
    def ClearField(
        self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]
    ) -> None: ...

global___NestedMessage = NestedMessage

class DecimalMessage(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: typing.Text
    def __init__(
        self,
        *,
        value: typing.Text = ...,
    ) -> None: ...
    def ClearField(
        self, field_name: typing_extensions.Literal["value", b"value"]
    ) -> None: ...

global___DecimalMessage = DecimalMessage

class ExampleMessage(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _SomeEnum:
        ValueType = typing.NewType("ValueType", builtins.int)
        V: typing_extensions.TypeAlias = ValueType
    class _SomeEnumEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            ExampleMessage._SomeEnum.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        unspecified: ExampleMessage._SomeEnum.ValueType  # 0
        first: ExampleMessage._SomeEnum.ValueType  # 1
        second: ExampleMessage._SomeEnum.ValueType  # 2
    class SomeEnum(_SomeEnum, metaclass=_SomeEnumEnumTypeWrapper):
        pass
    unspecified: ExampleMessage.SomeEnum.ValueType  # 0
    first: ExampleMessage.SomeEnum.ValueType  # 1
    second: ExampleMessage.SomeEnum.ValueType  # 2
    class MapEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: typing.Text
        value: typing.Text
        def __init__(
            self,
            *,
            key: typing.Text = ...,
            value: typing.Text = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing_extensions.Literal["key", b"key", "value", b"value"],
        ) -> None: ...
    INT32_FIELD_NUMBER: builtins.int
    INT64_FIELD_NUMBER: builtins.int
    UINT32_FIELD_NUMBER: builtins.int
    UINT64_FIELD_NUMBER: builtins.int
    DOUBLE_FIELD_NUMBER: builtins.int
    FLOAT_FIELD_NUMBER: builtins.int
    BOOL_FIELD_NUMBER: builtins.int
    ENUM_FIELD_NUMBER: builtins.int
    STRING_FIELD_NUMBER: builtins.int
    NESTED_FIELD_NUMBER: builtins.int
    STRINGLIST_FIELD_NUMBER: builtins.int
    BYTES_FIELD_NUMBER: builtins.int
    SFIXED32_FIELD_NUMBER: builtins.int
    SFIXED64_FIELD_NUMBER: builtins.int
    SINT32_FIELD_NUMBER: builtins.int
    SINT64_FIELD_NUMBER: builtins.int
    FIXED32_FIELD_NUMBER: builtins.int
    FIXED64_FIELD_NUMBER: builtins.int
    ONEOFSTRING_FIELD_NUMBER: builtins.int
    ONEOFINT32_FIELD_NUMBER: builtins.int
    MAP_FIELD_NUMBER: builtins.int
    TIMESTAMP_FIELD_NUMBER: builtins.int
    DURATION_FIELD_NUMBER: builtins.int
    DECIMAL_FIELD_NUMBER: builtins.int
    DOUBLEVALUE_FIELD_NUMBER: builtins.int
    FLOATVALUE_FIELD_NUMBER: builtins.int
    INT64VALUE_FIELD_NUMBER: builtins.int
    UINT64VALUE_FIELD_NUMBER: builtins.int
    INT32VALUE_FIELD_NUMBER: builtins.int
    UINT32VALUE_FIELD_NUMBER: builtins.int
    BOOLVALUE_FIELD_NUMBER: builtins.int
    STRINGVALUE_FIELD_NUMBER: builtins.int
    BYTESVALUE_FIELD_NUMBER: builtins.int
    int32: builtins.int
    int64: builtins.int
    uint32: builtins.int
    uint64: builtins.int
    double: builtins.float
    float: builtins.float
    bool: builtins.bool
    enum: global___ExampleMessage.SomeEnum.ValueType
    string: typing.Text
    @property
    def nested(self) -> global___NestedMessage: ...
    @property
    def stringlist(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        typing.Text
    ]: ...
    bytes: builtins.bytes
    sfixed32: builtins.int
    sfixed64: builtins.int
    sint32: builtins.int
    sint64: builtins.int
    fixed32: builtins.int
    fixed64: builtins.int
    oneofstring: typing.Text
    oneofint32: builtins.int
    @property
    def map(
        self,
    ) -> google.protobuf.internal.containers.ScalarMap[typing.Text, typing.Text]: ...
    @property
    def timestamp(self) -> google.protobuf.timestamp_pb2.Timestamp: ...
    @property
    def duration(self) -> google.protobuf.duration_pb2.Duration: ...
    @property
    def decimal(self) -> global___DecimalMessage: ...
    @property
    def doublevalue(self) -> google.protobuf.wrappers_pb2.DoubleValue: ...
    @property
    def floatvalue(self) -> google.protobuf.wrappers_pb2.FloatValue: ...
    @property
    def int64value(self) -> google.protobuf.wrappers_pb2.Int64Value: ...
    @property
    def uint64value(self) -> google.protobuf.wrappers_pb2.UInt64Value: ...
    @property
    def int32value(self) -> google.protobuf.wrappers_pb2.Int32Value: ...
    @property
    def uint32value(self) -> google.protobuf.wrappers_pb2.UInt32Value: ...
    @property
    def boolvalue(self) -> google.protobuf.wrappers_pb2.BoolValue: ...
    @property
    def stringvalue(self) -> google.protobuf.wrappers_pb2.StringValue: ...
    @property
    def bytesvalue(self) -> google.protobuf.wrappers_pb2.BytesValue: ...
    def __init__(
        self,
        *,
        int32: builtins.int = ...,
        int64: builtins.int = ...,
        uint32: builtins.int = ...,
        uint64: builtins.int = ...,
        double: builtins.float = ...,
        float: builtins.float = ...,
        bool: builtins.bool = ...,
        enum: global___ExampleMessage.SomeEnum.ValueType = ...,
        string: typing.Text = ...,
        nested: typing.Optional[global___NestedMessage] = ...,
        stringlist: typing.Optional[typing.Iterable[typing.Text]] = ...,
        bytes: builtins.bytes = ...,
        sfixed32: builtins.int = ...,
        sfixed64: builtins.int = ...,
        sint32: builtins.int = ...,
        sint64: builtins.int = ...,
        fixed32: builtins.int = ...,
        fixed64: builtins.int = ...,
        oneofstring: typing.Text = ...,
        oneofint32: builtins.int = ...,
        map: typing.Optional[typing.Mapping[typing.Text, typing.Text]] = ...,
        timestamp: typing.Optional[google.protobuf.timestamp_pb2.Timestamp] = ...,
        duration: typing.Optional[google.protobuf.duration_pb2.Duration] = ...,
        decimal: typing.Optional[global___DecimalMessage] = ...,
        doublevalue: typing.Optional[google.protobuf.wrappers_pb2.DoubleValue] = ...,
        floatvalue: typing.Optional[google.protobuf.wrappers_pb2.FloatValue] = ...,
        int64value: typing.Optional[google.protobuf.wrappers_pb2.Int64Value] = ...,
        uint64value: typing.Optional[google.protobuf.wrappers_pb2.UInt64Value] = ...,
        int32value: typing.Optional[google.protobuf.wrappers_pb2.Int32Value] = ...,
        uint32value: typing.Optional[google.protobuf.wrappers_pb2.UInt32Value] = ...,
        boolvalue: typing.Optional[google.protobuf.wrappers_pb2.BoolValue] = ...,
        stringvalue: typing.Optional[google.protobuf.wrappers_pb2.StringValue] = ...,
        bytesvalue: typing.Optional[google.protobuf.wrappers_pb2.BytesValue] = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing_extensions.Literal[
            "boolvalue",
            b"boolvalue",
            "bytesvalue",
            b"bytesvalue",
            "decimal",
            b"decimal",
            "doublevalue",
            b"doublevalue",
            "duration",
            b"duration",
            "floatvalue",
            b"floatvalue",
            "int32value",
            b"int32value",
            "int64value",
            b"int64value",
            "nested",
            b"nested",
            "oneof",
            b"oneof",
            "oneofint32",
            b"oneofint32",
            "oneofstring",
            b"oneofstring",
            "stringvalue",
            b"stringvalue",
            "timestamp",
            b"timestamp",
            "uint32value",
            b"uint32value",
            "uint64value",
            b"uint64value",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "bool",
            b"bool",
            "boolvalue",
            b"boolvalue",
            "bytes",
            b"bytes",
            "bytesvalue",
            b"bytesvalue",
            "decimal",
            b"decimal",
            "double",
            b"double",
            "doublevalue",
            b"doublevalue",
            "duration",
            b"duration",
            "enum",
            b"enum",
            "fixed32",
            b"fixed32",
            "fixed64",
            b"fixed64",
            "float",
            b"float",
            "floatvalue",
            b"floatvalue",
            "int32",
            b"int32",
            "int32value",
            b"int32value",
            "int64",
            b"int64",
            "int64value",
            b"int64value",
            "map",
            b"map",
            "nested",
            b"nested",
            "oneof",
            b"oneof",
            "oneofint32",
            b"oneofint32",
            "oneofstring",
            b"oneofstring",
            "sfixed32",
            b"sfixed32",
            "sfixed64",
            b"sfixed64",
            "sint32",
            b"sint32",
            "sint64",
            b"sint64",
            "string",
            b"string",
            "stringlist",
            b"stringlist",
            "stringvalue",
            b"stringvalue",
            "timestamp",
            b"timestamp",
            "uint32",
            b"uint32",
            "uint32value",
            b"uint32value",
            "uint64",
            b"uint64",
            "uint64value",
            b"uint64value",
        ],
    ) -> None: ...
    def WhichOneof(
        self, oneof_group: typing_extensions.Literal["oneof", b"oneof"]
    ) -> typing.Optional[typing_extensions.Literal["oneofstring", "oneofint32"]]: ...

global___ExampleMessage = ExampleMessage

class RecursiveMessage(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NOTE_FIELD_NUMBER: builtins.int
    MESSAGE_FIELD_NUMBER: builtins.int
    note: typing.Text
    @property
    def message(self) -> global___RecursiveMessage: ...
    def __init__(
        self,
        *,
        note: typing.Text = ...,
        message: typing.Optional[global___RecursiveMessage] = ...,
    ) -> None: ...
    def HasField(
        self, field_name: typing_extensions.Literal["message", b"message"]
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal["message", b"message", "note", b"note"],
    ) -> None: ...

global___RecursiveMessage = RecursiveMessage
