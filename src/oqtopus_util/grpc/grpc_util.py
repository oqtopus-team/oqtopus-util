import os
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor

import grpc  # type: ignore[import-untyped]

GRPC_MAX_RECEIVE_MESSAGE_LENGTH = "grpc.max_receive_message_length"
GRPC_MAX_SEND_MESSAGE_LENGTH = "grpc.max_send_message_length"
MAX_MESSAGE_LENGTH = "max_message_length"
MAX_MESSAGE_BYTES = "max_message_bytes"
MAX_RECEIVE_MESSAGE_LENGTH = "max_receive_message_length"
MAX_SEND_MESSAGE_LENGTH = "max_send_message_length"
ENV_GRPC_MAX_MESSAGE_LENGTH = "GRPC_MAX_MESSAGE_LENGTH"
ENV_GRPC_MAX_RECEIVE_MESSAGE_LENGTH = "GRPC_MAX_RECEIVE_MESSAGE_LENGTH"
ENV_GRPC_MAX_SEND_MESSAGE_LENGTH = "GRPC_MAX_SEND_MESSAGE_LENGTH"

GrpcOption = tuple[str, int]


def grpc_message_size_options(
    config: Mapping[str, object] | None = None,
) -> list[GrpcOption]:
    """Build gRPC message-size options from configuration.

    Args:
        config: Mapping with ``max_message_length`` or legacy
            ``max_receive_message_length``/``max_send_message_length`` values.
            ``None`` values are ignored.

    Returns:
        gRPC option tuples suitable for ``grpc.server`` and channel factories.

    """
    config = _grpc_config_from_env() if config is None else config
    if not config:
        return []

    shared_message_length = config.get(
        MAX_MESSAGE_LENGTH,
        config.get(MAX_MESSAGE_BYTES),
    )
    if shared_message_length is not None:
        int_value = _parse_message_size(MAX_MESSAGE_LENGTH, shared_message_length)
        return [
            (GRPC_MAX_RECEIVE_MESSAGE_LENGTH, int_value),
            (GRPC_MAX_SEND_MESSAGE_LENGTH, int_value),
        ]

    return [
        option
        for option in (
            _build_message_size_option(
                config,
                MAX_RECEIVE_MESSAGE_LENGTH,
                GRPC_MAX_RECEIVE_MESSAGE_LENGTH,
            ),
            _build_message_size_option(
                config,
                MAX_SEND_MESSAGE_LENGTH,
                GRPC_MAX_SEND_MESSAGE_LENGTH,
            ),
        )
        if option is not None
    ]


def create_insecure_channel(
    target: str,
    grpc_config: Mapping[str, object] | None = None,
    *,
    options: Sequence[GrpcOption] | None = None,
) -> grpc.Channel:
    """Create a synchronous insecure channel with configured gRPC options.

    Returns:
        A synchronous gRPC channel.

    """
    return grpc.insecure_channel(
        target,
        options=_merge_options(grpc_config, options),
    )


def create_aio_insecure_channel(
    target: str,
    grpc_config: Mapping[str, object] | None = None,
    *,
    options: Sequence[GrpcOption] | None = None,
) -> grpc.aio.Channel:
    """Create an asynchronous insecure channel with configured gRPC options.

    Returns:
        An asynchronous gRPC channel.

    """
    return grpc.aio.insecure_channel(
        target,
        options=_merge_options(grpc_config, options),
    )


def create_server(
    thread_pool: ThreadPoolExecutor,
    grpc_config: Mapping[str, object] | None = None,
    *,
    options: Sequence[GrpcOption] | None = None,
) -> grpc.Server:
    """Create a synchronous gRPC server with configured gRPC options.

    Returns:
        A synchronous gRPC server.

    """
    return grpc.server(
        thread_pool,
        options=_merge_options(grpc_config, options),
    )


def create_aio_server(
    grpc_config: Mapping[str, object] | None = None,
    *,
    options: Sequence[GrpcOption] | None = None,
) -> grpc.aio.Server:
    """Create an asynchronous gRPC server with configured gRPC options.

    Returns:
        An asynchronous gRPC server.

    """
    return grpc.aio.server(options=_merge_options(grpc_config, options))


def _build_message_size_option(
    config: Mapping[str, object],
    key: str,
    grpc_key: str,
) -> GrpcOption | None:
    value = config.get(key)
    if value is None:
        return None

    return (grpc_key, _parse_message_size(key, value))


def _parse_message_size(key: str, value: object) -> int:
    """Parse a gRPC message-size value.

    Returns:
        The parsed integer message size.

    Raises:
        TypeError: If the value is a bool.
        ValueError: If the value is not a valid message size.

    """
    if isinstance(value, bool):
        msg = f"{key} must be an integer byte size or -1, but got bool."
        raise TypeError(msg)

    if isinstance(value, int):
        int_value = value
    elif isinstance(value, str):
        try:
            int_value = int(value)
        except ValueError as exc:
            msg = f"{key} must be an integer byte size or -1, but got {value!r}."
            raise ValueError(msg) from exc
    else:
        msg = f"{key} must be an integer byte size or -1, but got {value!r}."
        raise TypeError(msg)

    if int_value < -1 or int_value == 0:
        msg = f"{key} must be a positive integer byte size or -1, but got {int_value}."
        raise ValueError(msg)

    return int_value


def _merge_options(
    grpc_config: Mapping[str, object] | None,
    options: Sequence[GrpcOption] | None,
) -> list[GrpcOption]:
    merged = grpc_message_size_options(grpc_config)
    if options is not None:
        merged.extend(options)
    return merged


def _grpc_config_from_env() -> dict[str, str]:
    max_message_length = os.environ.get(ENV_GRPC_MAX_MESSAGE_LENGTH)
    if max_message_length is not None:
        return {MAX_MESSAGE_LENGTH: max_message_length}

    config = {}
    max_receive_message_length = os.environ.get(ENV_GRPC_MAX_RECEIVE_MESSAGE_LENGTH)
    max_send_message_length = os.environ.get(ENV_GRPC_MAX_SEND_MESSAGE_LENGTH)
    if max_receive_message_length is not None:
        config[MAX_RECEIVE_MESSAGE_LENGTH] = max_receive_message_length
    if max_send_message_length is not None:
        config[MAX_SEND_MESSAGE_LENGTH] = max_send_message_length
    return config
