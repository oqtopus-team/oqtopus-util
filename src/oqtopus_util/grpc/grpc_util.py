from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor

import grpc  # type: ignore[import-untyped]

GrpcOption = tuple[str, object] | list[object]
GrpcOptions = Sequence[GrpcOption]


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
