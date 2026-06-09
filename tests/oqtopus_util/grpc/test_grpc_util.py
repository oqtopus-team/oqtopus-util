from concurrent.futures import ThreadPoolExecutor

from pytest_mock import MockerFixture

from oqtopus_util.grpc import (
    create_aio_insecure_channel,
    create_aio_server,
    create_insecure_channel,
    create_server,
)


def test_create_insecure_channel_passes_options(mocker: MockerFixture):
    mock_insecure_channel = mocker.patch(
        "oqtopus_util.grpc.grpc_util.grpc.insecure_channel"
    )

    create_insecure_channel(
        "localhost:50051",
        [("grpc.max_receive_message_length", 1024)],
    )

    mock_insecure_channel.assert_called_once_with(
        "localhost:50051",
        options=[("grpc.max_receive_message_length", 1024)],
    )


def test_create_aio_insecure_channel_passes_options(mocker: MockerFixture):
    mock_insecure_channel = mocker.patch(
        "oqtopus_util.grpc.grpc_util.grpc.aio.insecure_channel"
    )

    create_aio_insecure_channel(
        "localhost:50051",
        [("grpc.max_send_message_length", 2048)],
    )

    mock_insecure_channel.assert_called_once_with(
        "localhost:50051",
        options=[("grpc.max_send_message_length", 2048)],
    )


def test_create_server_passes_options(mocker: MockerFixture):
    mock_server = mocker.patch("oqtopus_util.grpc.grpc_util.grpc.server")
    executor = ThreadPoolExecutor(max_workers=1)

    create_server(executor, [("grpc.max_receive_message_length", -1)])

    mock_server.assert_called_once_with(
        executor,
        options=[("grpc.max_receive_message_length", -1)],
    )


def test_create_aio_server_passes_options(mocker: MockerFixture):
    mock_server = mocker.patch("oqtopus_util.grpc.grpc_util.grpc.aio.server")

    create_aio_server([("grpc.max_send_message_length", -1)])

    mock_server.assert_called_once_with(
        options=[("grpc.max_send_message_length", -1)],
    )


def test_create_server_merges_explicit_options(mocker: MockerFixture):
    mock_server = mocker.patch("oqtopus_util.grpc.grpc_util.grpc.server")
    executor = ThreadPoolExecutor(max_workers=1)

    create_server(
        executor,
        [("grpc.max_receive_message_length", 1024)],
        options=[("grpc.max_send_message_length", 2048)],
    )

    mock_server.assert_called_once_with(
        executor,
        options=[
            ("grpc.max_receive_message_length", 1024),
            ("grpc.max_send_message_length", 2048),
        ],
    )
