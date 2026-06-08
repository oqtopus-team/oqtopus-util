from concurrent.futures import ThreadPoolExecutor

import pytest
from pytest_mock import MockerFixture

from oqtopus_util.grpc import (
    create_aio_insecure_channel,
    create_aio_server,
    create_insecure_channel,
    create_server,
    grpc_message_size_options,
)


def test_grpc_message_size_options_returns_configured_options():
    assert grpc_message_size_options({"max_message_length": "64"}) == [
        ("grpc.max_receive_message_length", 64),
        ("grpc.max_send_message_length", 64),
    ]


def test_grpc_message_size_options_supports_legacy_separate_options():
    assert grpc_message_size_options({
        "max_receive_message_length": 16,
        "max_send_message_length": "32",
    }) == [
        ("grpc.max_receive_message_length", 16),
        ("grpc.max_send_message_length", 32),
    ]


def test_grpc_message_size_options_ignores_missing_values():
    assert grpc_message_size_options({}) == []
    assert (
        grpc_message_size_options({
            "max_receive_message_length": None,
            "max_send_message_length": None,
        })
        == []
    )


def test_grpc_message_size_options_reads_shared_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GRPC_MAX_MESSAGE_LENGTH", "4096")

    assert grpc_message_size_options() == [
        ("grpc.max_receive_message_length", 4096),
        ("grpc.max_send_message_length", 4096),
    ]


@pytest.mark.parametrize(
    ("value", "expected_exception", "match"),
    [
        (False, TypeError, "got bool"),
        (0, ValueError, "positive integer"),
        (-2, ValueError, "positive integer"),
        ("invalid", ValueError, "must be an integer"),
    ],
)
def test_grpc_message_size_options_rejects_invalid_values(
    value: object,
    expected_exception: type[Exception],
    match: str,
):
    with pytest.raises(expected_exception, match=match):
        grpc_message_size_options({"max_receive_message_length": value})


def test_create_insecure_channel_passes_options(mocker: MockerFixture):
    mock_insecure_channel = mocker.patch(
        "oqtopus_util.grpc.grpc_util.grpc.insecure_channel"
    )

    create_insecure_channel(
        "localhost:50051",
        {"max_receive_message_length": 1024},
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
        {"max_send_message_length": 2048},
    )

    mock_insecure_channel.assert_called_once_with(
        "localhost:50051",
        options=[("grpc.max_send_message_length", 2048)],
    )


def test_create_server_passes_options(mocker: MockerFixture):
    mock_server = mocker.patch("oqtopus_util.grpc.grpc_util.grpc.server")
    executor = ThreadPoolExecutor(max_workers=1)

    create_server(executor, {"max_receive_message_length": -1})

    mock_server.assert_called_once_with(
        executor,
        options=[("grpc.max_receive_message_length", -1)],
    )


def test_create_aio_server_passes_options(mocker: MockerFixture):
    mock_server = mocker.patch("oqtopus_util.grpc.grpc_util.grpc.aio.server")

    create_aio_server({"max_send_message_length": -1})

    mock_server.assert_called_once_with(
        options=[("grpc.max_send_message_length", -1)],
    )
