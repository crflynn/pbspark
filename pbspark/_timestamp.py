"""Timestamp serde."""
import calendar
import datetime

from google.protobuf.internal import well_known_types
from google.protobuf.timestamp_pb2 import Timestamp


def _to_datetime(message: Timestamp) -> datetime.datetime:
    """Convert a Timestamp to a python datetime."""
    return well_known_types._EPOCH_DATETIME_NAIVE + datetime.timedelta(  # type: ignore[attr-defined]
        seconds=message.seconds,
        microseconds=well_known_types._RoundTowardZero(  # type: ignore[attr-defined]
            message.nanos,
            well_known_types._NANOS_PER_MICROSECOND,  # type: ignore[attr-defined]
        ),
    )


def _from_datetime(dt: datetime.datetime, timestamp: Timestamp, path: str):
    """Convert a python datetime to Timestamp."""
    timestamp.seconds = calendar.timegm(dt.utctimetuple())
    timestamp.nanos = dt.microsecond * well_known_types._NANOS_PER_MICROSECOND  # type: ignore[attr-defined]
