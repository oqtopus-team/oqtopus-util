from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor

import grpc  # type: ignore[import-untyped]

GrpcOption = tuple[str, object]
GrpcOptions = Sequence[GrpcOption]
_GRPC_OPTION_PAIR_LEN = 2


def load_grpc_options(proto_config: Mapping[str, object]) -> list[tuple[str, int]]:
    """Build gRPC options from proto config.

    This supports both:
    - `proto.grpc_options: [["max_receive_message_length", 4194304], ...]`
    - legacy flat keys like `proto.grpc.max_receive_message_length: 4194304`

    Returns:
        A list of (`grpc.<key>`, int_value) tuples.

    Raises:
        TypeError: If `grpc_options` is not a list of [key, value] pairs, or if
            an option value is not int-like.

    """
    configured = proto_config.get("grpc_options")
    if configured is not None:
        if not isinstance(configured, list):
            msg = "proto.grpc_options must be a list of [key, value] pairs"
            raise TypeError(msg)

        normalized: list[tuple[str, int]] = []
        for item in configured:
            if not isinstance(item, (list, tuple)):
                msg = "Each proto.grpc_options entry must be a [key, value] pair"
                raise TypeError(msg)
            if len(item) != _GRPC_OPTION_PAIR_LEN:
                msg = "Each proto.grpc_options entry must be a [key, value] pair"
                raise TypeError(msg)
            key = str(item[0])
            if not key.startswith("grpc."):
                key = f"grpc.{key}"
            value = item[1]
            if not isinstance(value, (int, str, bytes, bytearray)):
                msg = f"gRPC option value for {key} must be int-like"
                raise TypeError(msg)
            normalized.append((key, int(value)))
        return normalized

    return [
        (key, int(value))
        for key, value in proto_config.items()
        if key.startswith("grpc.") and isinstance(value, (int, str, bytes, bytearray))
    ]


def create_insecure_channel(
    target: str,
    grpc_options: GrpcOptions | None = None,
    *,
    options: GrpcOptions | None = None,
) -> grpc.Channel:
    """Create a synchronous insecure channel with gRPC options.

    Returns:
        A synchronous gRPC channel.

    """
    return grpc.insecure_channel(
        target,
        options=_merge_options(grpc_options, options),
    )


def create_aio_insecure_channel(
    target: str,
    grpc_options: GrpcOptions | None = None,
    *,
    options: GrpcOptions | None = None,
) -> grpc.aio.Channel:
    """Create an asynchronous insecure channel with gRPC options.

    Returns:
        An asynchronous gRPC channel.

    """
    return grpc.aio.insecure_channel(
        target,
        options=_merge_options(grpc_options, options),
    )


def create_server(
    thread_pool: ThreadPoolExecutor,
    grpc_options: GrpcOptions | None = None,
    *,
    options: GrpcOptions | None = None,
) -> grpc.Server:
    """Create a synchronous gRPC server with gRPC options.

    Returns:
        A synchronous gRPC server.

    """
    return grpc.server(
        thread_pool,
        options=_merge_options(grpc_options, options),
    )


def create_aio_server(
    grpc_options: GrpcOptions | None = None,
    *,
    options: GrpcOptions | None = None,
) -> grpc.aio.Server:
    """Create an asynchronous gRPC server with gRPC options.

    Returns:
        An asynchronous gRPC server.

    """
    return grpc.aio.server(options=_merge_options(grpc_options, options))


def _merge_options(
    grpc_options: GrpcOptions | None,
    options: GrpcOptions | None,
) -> list[GrpcOption]:
    merged = list(grpc_options or [])
    if options is not None:
        merged.extend(options)
    return merged
