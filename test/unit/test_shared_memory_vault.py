from unittest import mock
from exasol.shared_memory_vault import (compute_crc, encode, decode, write_to_sm, read_from_sm, clear_sm)
from datetime import datetime


def test_compute_crc():
    assert compute_crc('11010011101100000', '011') == '100'


def test_encode_decode():

    dt = datetime(year=2023, month=12, day=11, hour=16, minute=35, second=21)
    content = 'Supercalifragilisticexpialidocious'
    key = '10011010'
    success, enc_content = encode(content, key, dt)
    assert success
    success, dt_out, content_out = decode(enc_content, key)
    assert success
    assert dt_out == dt
    assert content_out == content


def test_encode_corrupt_decode():

    content = 'Go ahead, make my day.'
    key = '10011010'
    _, enc_content = encode(content, key, datetime.now())
    enc_content[0] ^= 127
    success, _, _ = decode(enc_content, key)
    assert not success


@mock.patch("exasol.shared_memory_vault._open_shared_memory")
def test_write_read(mock_sm_factory):

    max_size = 200
    mock_sm = mock.MagicMock()
    mock_sm.buf = bytearray(max_size)
    mock_sm_factory.return_value = mock_sm
    key = '100110100011'
    content = 'The truth will set you free.'
    dt = datetime(year=2023, month=12, day=12, hour=8, minute=39, second=45)
    success = write_to_sm(content, creation_time=dt, key=key, max_size=max_size)
    assert success
    success, dt_out, content_out = read_from_sm(key=key, max_size=max_size)
    assert success
    assert dt_out == dt
    assert content_out == content


@mock.patch("exasol.shared_memory_vault._open_shared_memory")
def test_write_corrupt_read(mock_sm_factory):

    max_size = 200
    mock_sm = mock.MagicMock()
    mock_sm.buf = bytearray(max_size)
    mock_sm_factory.return_value = mock_sm
    key = '100110100011'
    content = 'The truth will set you free.'
    dt = datetime(year=2023, month=12, day=12, hour=8, minute=39, second=45)
    write_to_sm(content, creation_time=dt, key=key, max_size=max_size)
    mock_sm.buf = bytearray(max_size)
    mock_sm.buf[10] = mock_sm.buf[10]
    success, _, _ = read_from_sm(key=key, max_size=max_size)
    assert not success


@mock.patch("exasol.shared_memory_vault._open_shared_memory")
def test_read_fail_no_sm(mock_sm_factory):

    # Simulate the case when the shared memory block doesn't exist.
    mock_sm_factory.return_value = None
    max_size = 200
    key = '100110100011'
    success, _, _ = read_from_sm(key=key, max_size=max_size)
    assert not success


@mock.patch("exasol.shared_memory_vault._open_shared_memory")
def test_write_fail_insufficient_memory(mock_sm_factory):

    max_size = 50
    mock_sm = mock.MagicMock()
    mock_sm.buf = bytearray(max_size)
    mock_sm_factory.return_value = mock_sm
    key = '100110100011'
    content = 'If you want something said, ask a man; if you want something done, ask a woman.'
    dt = datetime(year=2023, month=12, day=12, hour=9, minute=19, second=10)
    success = write_to_sm(content, creation_time=dt, key=key, max_size=max_size)
    assert not success


@mock.patch("exasol.shared_memory_vault._open_shared_memory")
def test_write_clear_read(mock_sm_factory):

    max_size = 200
    mock_sm = mock.MagicMock()
    mock_sm.buf = bytearray(max_size)
    mock_sm_factory.return_value = mock_sm
    key = '100110100011'
    content = 'The truth will set you free.'
    dt = datetime(year=2023, month=12, day=12, hour=8, minute=39, second=45)
    write_to_sm(content, creation_time=dt, key=key, max_size=max_size)
    clear_sm(max_size=max_size)
    success, _, _ = read_from_sm(key=key, max_size=max_size)
    assert not success
