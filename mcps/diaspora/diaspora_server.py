import logging
from typing import Any

from aws_msk_iam_sasl_signer import MSKAuthTokenProvider
from confluent_kafka import (
    Consumer,
    KafkaError,
    KafkaException,
    TopicPartition,
)
from fastmcp import FastMCP
from schemas import (
    ConsumeResponse,
    IcicleResponse,
    msg_to_icicle_response,
    msg_to_response,
)

PARTITION_ZERO = 0


def oauth_cb(oauth_config: dict[str, Any]) -> tuple[str, float]:
    auth_token, expiry_ms = MSKAuthTokenProvider.generate_auth_token("us-east-1")
    return auth_token, expiry_ms / 1000


def get_consumer_conf() -> dict[str, Any]:
    return {
        "bootstrap.servers": "b-2-public.diaspora.jdqn8o.c18.kafka.us-east-1.amazonaws.com:9198,b-1-public.diaspora.jdqn8o.c18.kafka.us-east-1.amazonaws.com:9198",
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "OAUTHBEARER",
        "oauth_cb": oauth_cb,
        "group.id": "bbb-100",
        "enable.auto.commit": "false",
        "auto.offset.reset": "earliest",
        "fetch.min.bytes": 1048576,
        "fetch.max.bytes": 10485760,
        "max.partition.fetch.bytes": 10485760,
        "fetch.wait.max.ms": 50,
        "allow.auto.create.topics": "false",
        "session.timeout.ms": 45000,
    }


def get_consumer(topic: str) -> Consumer:
    """Creates a consumer and assigns it to partition 0 of the specified topic."""
    consumer = Consumer(get_consumer_conf())
    topic_partition = TopicPartition(topic, partition=PARTITION_ZERO)
    consumer.assign([topic_partition])
    return consumer


def _consume_and_process(
    consumer: Consumer, num_msg: int, timeout: float
) -> list[ConsumeResponse]:
    """
    Wraps the core consume loop with centralized error handling.
    """
    try:
        messages = consumer.consume(num_messages=num_msg, timeout=timeout) or []
        responses = []
        for msg in messages:
            if msg is None:
                continue
            if err := msg.error():
                if err.code() == KafkaError._PARTITION_EOF:
                    continue
                logging.error(f"Kafka consumption error: {err}")
                raise err
            responses.append(msg_to_response(msg))
        return responses
    except KafkaException as e:
        logging.error(f"A KafkaException occurred: {e}")
        return []


def _consume_icicle_and_process(
    consumer: Consumer, num_msg: int, timeout: float
) -> list[IcicleResponse]:
    """
    Wraps the core consume loop with centralized error handling.
    """
    try:
        messages = consumer.consume(num_messages=num_msg, timeout=timeout) or []
        responses = []
        for msg in messages:
            if msg is None:
                continue
            if err := msg.error():
                if err.code() == KafkaError._PARTITION_EOF:
                    continue
                logging.error(f"Kafka consumption error: {err}")
                raise err
            if event := msg_to_icicle_response(msg):
                responses.append(event)
        return responses
    except KafkaException as e:
        logging.error(f"A KafkaException occurred: {e}")
        return []


mcp = FastMCP("Octopus")


@mcp.tool
def consume_earliest(
    topic: str = "lustre-mon-out",
    num_msg: int = 1,
    timeout: float = 10,
) -> list[ConsumeResponse]:
    """Consume messages from the beginning of a Kafka topic's partition 0."""
    if num_msg <= 0:
        return []
    consumer: Consumer | None = None
    try:
        consumer = get_consumer(topic)
        consumer.poll(0)

        topic_partition = TopicPartition(topic, PARTITION_ZERO)
        low, high = consumer.get_watermark_offsets(topic_partition, timeout=timeout)
        available_msgs = high - low
        if available_msgs <= 0:
            return []  # No new messages to read

        msgs_to_fetch = min(num_msg, available_msgs)

        # No special setup needed; relies on 'auto.offset.reset' config
        return _consume_and_process(consumer, msgs_to_fetch, timeout)
    finally:
        if consumer is not None:
            consumer.close()


@mcp.tool
def consume_latest(
    topic: str = "lustre-mon-out",
    num_msg: int = 1,
    timeout: float = 10,
) -> list[ConsumeResponse]:
    """Consume the latest N messages from a Kafka topic's partition 0."""
    if num_msg <= 0:
        return []
    consumer: Consumer | None = None
    try:
        consumer = get_consumer(topic)
        consumer.poll(0)

        topic_partition = TopicPartition(topic, PARTITION_ZERO)
        low, high = consumer.get_watermark_offsets(topic_partition, timeout=timeout)
        available_msgs = high - low
        if available_msgs <= 0:
            return []  # No new messages to read

        start_offset = max(low, high - num_msg)
        consumer.assign([TopicPartition(topic, PARTITION_ZERO, start_offset)])

        msgs_to_fetch = min(num_msg, available_msgs)
        return _consume_and_process(consumer, msgs_to_fetch, timeout)
    finally:
        if consumer is not None:
            consumer.close()


@mcp.tool
def consume_from_timestamp(
    topic: str = "lustre-mon-out",
    timestamp_ms: int = 0,
    num_msg: int = 1,
    timeout: float = 10,
) -> list[ConsumeResponse]:
    """Consume messages from a Kafka topic starting at a specific timestamp."""
    if timestamp_ms < 0 or num_msg <= 0:
        return []
    consumer: Consumer | None = None
    try:
        consumer = get_consumer(topic)
        consumer.poll(0)

        query_tp = TopicPartition(topic, PARTITION_ZERO, timestamp_ms)
        offset_tp_list = consumer.offsets_for_times([query_tp], timeout=timeout)

        if not offset_tp_list or offset_tp_list[0].offset < 0:
            return []

        start_offset = offset_tp_list[0].offset

        topic_partition = TopicPartition(topic, PARTITION_ZERO)
        _, high = consumer.get_watermark_offsets(topic_partition, timeout=timeout)
        available_msgs = high - start_offset
        if available_msgs <= 0:
            return []  # No new messages to read

        consumer.assign([TopicPartition(topic, PARTITION_ZERO, start_offset)])

        msgs_to_fetch = min(num_msg, available_msgs)
        return _consume_and_process(consumer, msgs_to_fetch, timeout)
    finally:
        if consumer is not None:
            consumer.close()


@mcp.tool
def consume_from_offset(
    topic: str = "lustre-mon-out",
    offset: int = 0,
    num_msg: int = 1,
    timeout: float = 10,
) -> list[ConsumeResponse]:
    """
    Consume messages from a specific offset in a Kafka topic's partition 0.
    If the requested offset is older than the earliest available offset (log retention),
    it will automatically start from the earliest available one.
    """
    if offset < 0 or num_msg <= 0:
        return []

    consumer: Consumer | None = None
    try:
        # Note: get_consumer() still performs an initial assignment.
        consumer = get_consumer(topic)
        consumer.poll(0)

        # 1. Get the partition's available offset range.
        topic_partition_info = TopicPartition(topic, PARTITION_ZERO)
        low, high = consumer.get_watermark_offsets(
            topic_partition_info, timeout=timeout
        )

        # 2. Determine the effective starting offset.
        # This handles the case where the requested offset is too old by snapping to the earliest available offset.
        start_offset = max(offset, low)

        # 3. Position the consumer by re-assigning the partition with the specific start_offset.
        assign_partition = TopicPartition(topic, PARTITION_ZERO, start_offset)
        consumer.assign([assign_partition])

        # 4. Calculate how many messages are available from the starting position.
        available_msgs = high - start_offset
        if available_msgs <= 0:
            return []

        # The number of messages to fetch is the smaller of the user's request or what's available.
        msgs_to_fetch = min(num_msg, available_msgs)

        return _consume_and_process(consumer, msgs_to_fetch, timeout)
    finally:
        if consumer is not None:
            consumer.close()


@mcp.tool
def consume_icicle_changelogs_from_timestamp(
    topic: str = "lustre-mon-out",
    timestamp_ms: int = 0,
    num_msg: int = 10_000,
    timeout: float = 10,
) -> list[IcicleResponse]:
    """Consume Icicle changelogs from a Kafka topic starting at a specific timestamp."""
    if timestamp_ms < 0 or num_msg <= 0:
        return []
    consumer: Consumer | None = None
    try:
        consumer = get_consumer(topic)
        consumer.poll(0)

        query_tp = TopicPartition(topic, PARTITION_ZERO, timestamp_ms)
        offset_tp_list = consumer.offsets_for_times([query_tp], timeout=timeout)

        if not offset_tp_list or offset_tp_list[0].offset < 0:
            return []

        start_offset = offset_tp_list[0].offset

        topic_partition = TopicPartition(topic, PARTITION_ZERO)
        _, high = consumer.get_watermark_offsets(topic_partition, timeout=timeout)
        available_msgs = high - start_offset
        if available_msgs <= 0:
            return []  # No new messages to read

        consumer.assign([TopicPartition(topic, PARTITION_ZERO, start_offset)])

        msgs_to_fetch = min(num_msg, available_msgs)
        return _consume_icicle_and_process(consumer, msgs_to_fetch, timeout)
    finally:
        if consumer is not None:
            consumer.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
