import base64
import json
from enum import IntEnum

from confluent_kafka import Message
from pydantic import BaseModel, Field


class MessageTimestampType(IntEnum):
    """Kafka message timestamp types."""

    MSG_TIMESTAMP_NOT_AVAILABLE = 0
    MSG_TIMESTAMP_CREATE_TIME = 1
    MSG_TIMESTAMP_LOG_APPEND_TIME = 2


class MessageTimestamp(BaseModel):
    """Typed representation of a Kafka message timestamp."""

    type: MessageTimestampType = Field(
        description=(
            "Kafka timestamp type: 0=NOT_AVAILABLE, 1=CREATE_TIME, 2=LOG_APPEND_TIME."
        )
    )
    timestamp: int = Field(description="Epoch milliseconds (UTC).")

    model_config = {"extra": "forbid"}


class IcicleResponse(BaseModel):
    """Typed view of a Lustre changelog event payload."""

    # eid: int
    # event_type: str
    # timestamp: str
    # datestamp: str
    # flags: int
    # target_fid: str | None = None
    # extra_flags: str = ""
    # uid_gid: str = ""
    # nid: str = ""
    # parent_fid: str | None = None
    # name: str | None = None
    # source_fid: str | None = None
    # source_parent_fid: str | None = None
    # old_name: str | None = None
    # mode: str | None = None
    typ: str
    tfid: str | None = None
    pfid: str | None = None

    model_config = {"extra": "ignore"}  # ignore unknowns to be future-proof


class ConsumeResponse(BaseModel):
    """
    A structured representation of a Kafka message consumed from a topic.
    """

    topic: str = Field(
        description="The name of the Kafka topic from which the message was consumed."
    )
    partition: int = Field(description="The partition number within the topic.")
    offset: int = Field(description="The message's offset within the partition.")
    message_timestamp: MessageTimestamp = Field(
        description="Structured message timestamp, including type and epoch milliseconds."
    )

    key: str | None = Field(
        default=None,
        description=(
            "Message key, decoded as UTF-8 if possible. If decoding fails, "
            "the value is returned as base64:<data>. None if no key was provided."
        ),
    )
    value: str | None = Field(
        default=None,
        description=(
            "Message payload, decoded as UTF-8 if possible. If decoding fails, "
            "the value is returned as base64:<data>. None if no payload exists."
        ),
    )

    model_config = {"extra": "forbid"}


def _to_safe_text(data: bytes | None) -> str | None:
    """
    Decode bytes to UTF-8, or fallback to base64 if invalid.

    Args:
        data (Optional[bytes]): Raw byte data.

    Returns:
        Optional[str]: Decoded UTF-8 string, base64 string, or None.
    """
    if data is None:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return "base64:" + base64.b64encode(data).decode("ascii")

_KEY_MAP = {
    "event_type": "typ",
    "target_fid": "tfid",
    "parent_fid": "pfid",
}
ALLOWED_EVENT_KEYS = set(_KEY_MAP.keys())

def _parse_event_from_text(text: str | None) -> IcicleResponse | None:
    if not text or not text.strip().startswith("{"):
        return None
    try:
        payload = json.loads(text)
        remapped = { _KEY_MAP[k]: payload.get(k) for k in ALLOWED_EVENT_KEYS }
        return IcicleResponse.model_validate(remapped)
    except Exception as e:
        import sys
        import traceback

        print(f"[event-parse] failed: {e}\ntext={text}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
    return None


def msg_to_response(msg: Message) -> ConsumeResponse:
    ts_type, ts = msg.timestamp() or (0, 0)
    key_text = _to_safe_text(msg.key())
    value_text = _to_safe_text(msg.value())

    return ConsumeResponse(
        topic=msg.topic(),
        partition=msg.partition(),
        offset=msg.offset(),
        message_timestamp=MessageTimestamp(
            type=MessageTimestampType(ts_type), timestamp=ts
        ),
        key=key_text,
        value=value_text,
    )


def msg_to_icicle_response(msg: Message) -> IcicleResponse | None:
    # ts_type, ts = msg.timestamp() or (0, 0)
    value_text = _to_safe_text(msg.value())
    event = _parse_event_from_text(value_text)

    return event
    # return IcicleResponse(
    #     # topic=msg.topic(),
    #     # partition=msg.partition(),
    #     # offset=msg.offset(),
    #     # message_timestamp=MessageTimestamp(
    #     # type=MessageTimestampType(ts_type), timestamp=ts
    #     # ),
    #     event=event,
    # )
