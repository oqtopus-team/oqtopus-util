from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor

import grpc  # type: ignore[import-untyped]

GrpcOption = tuple[str, object]
GrpcOptions = Sequence[GrpcOption]


def create_insecure_channel(
    target: str,
    options: GrpcOptions | None = None,
) -> grpc.Channel:
    """Create a synchronous insecure channel with gRPC options.

    Returns:
        A synchronous gRPC channel.

    """
    return grpc.insecure_channel(
        target,
        options=list(options or []),
    )


def create_aio_insecure_channel(
    target: str,
    options: GrpcOptions | None = None,
) -> grpc.aio.Channel:
    """Create an asynchronous insecure channel with gRPC options.

    Returns:
        An asynchronous gRPC channel.

    """
    return grpc.aio.insecure_channel(
        target,
        options=list(options or []),
    )


def create_server(
    thread_pool: ThreadPoolExecutor,
    options: GrpcOptions | None = None,
) -> grpc.Server:
    """Create a synchronous gRPC server with gRPC options.

    Returns:
        A synchronous gRPC server.

    """
    return grpc.server(
        thread_pool,
        options=list(options or []),
    )


def create_aio_server(
    options: GrpcOptions | None = None,
) -> grpc.aio.Server:
    """Create an asynchronous gRPC server with gRPC options.

    Returns:
        An asynchronous gRPC server.

    """
    return grpc.aio.server(options=list(options or []))
