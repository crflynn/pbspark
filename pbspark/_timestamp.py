"""Timestamp serde."""
import calendar
import datetime

from google.protobuf.timestamp_pb2 import Timestamp

_EPOCH_DATETIME = datetime.datetime.utcfromtimestamp(0)
_NANOS_PER_MICROSECOND = 1000


def _round_toward_zero(value, divider):
    result = value // divider
    remainder = value % divider
    if result < 0 < remainder:
        return result + 1
    else:
        return result


def _to_datetime(message: Timestamp) -> datetime.datetime:
    """Convert a Timestamp to a python datetime."""
    return _EPOCH_DATETIME + datetime.timedelta(
        seconds=message.seconds,
        microseconds=_round_toward_zero(message.nanos, _NANOS_PER_MICROSECOND),
    )


def _from_datetime(dt):
    """Convert a python datetime to Timestamp."""
    return Timestamp(
        seconds=calendar.timegm(dt.utctimetuple()),
        nanos=dt.microsecond * _NANOS_PER_MICROSECOND,
    )
