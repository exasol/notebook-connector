from typing import Optional
from multiprocessing.shared_memory import SharedMemory
from math import ceil
from datetime import datetime
import struct


default_key = '1001011001100101'
default_max_size = 100
default_storage_name = 'notebook_connector_vault'


def _xor(sequence: str, key: str) -> str:
    return ''.join('0' if a == b else '1' for a, b in zip(sequence, key))


def compute_crc(sequence: str, key: str) -> str:
    """
    Computes a Cyclic Redundancy Check (CRC) code for a provided binary sequence using a provided key.
    Check this wiki for details: https://en.wikipedia.org/wiki/Cyclic_redundancy_check
    For example if the sequence is '11010011101100000' and the key is '011' the output crc code will
    be '100'. Note that the n+1 bit long key, commonly used in literature, 1011 in the above example,
    is assumed to have the most significant bit (MSB) equal 1. Here the MSB is omitted.
    """
    n = len(key)
    reminder = sequence[:n]
    for i in range(n, len(sequence)):
        starts_one = reminder[0] == '1'
        reminder = reminder[1:] + sequence[i]
        if starts_one:
            reminder = _xor(reminder, key)
    return reminder


def _get_byte_size(n: int) -> int:
    """Returns the number of bytes required to store an integer value"""
    return int(ceil(n.bit_length() / 8))


def _get_key_size(key: str) -> int:
    """Calculates the byte size of a CRC key"""
    return int(ceil(len(key) / 8))


def _bytes_to_bin(msg_bytes: bytes) -> str:
    """Converts byte array to a binary string, e.g.[6, 7] => 01100111"""
    return ''.join(format(c, '08b') for c in msg_bytes)


def encode(content: str, key: str, creation_time: datetime) -> (int, bytearray):
    """
    Creates a bytearray with encoded content and its creation datetime.
    Currently, the content is not being encrypted. It gets appended by the Cyclic Redundancy Check (CRC)
    code. The CRC is computed over both the timestamp and the content.

    The need for a CRC is debatable. Its use is motivated by the problem of non-synchronised concurrent
    access to the shared memory. In theory, the content can get corrupted by simultaneous reading/writing.
    Hence, is the need to validate the data retrieved from the shared memory. On the other hand, given the
    use case, the possibility of concurrent access is only hypothetical. The implication of reading an
    impaired data is insignificant and CRC cannot guarantee the validity with 100% accuracy anyway.
    """

    # Prepend the content by the timestamp and convert the whole thing to a binary sequence.
    ts_bytes = struct.pack('d', creation_time.timestamp())
    body = ts_bytes + content.encode('utf8')
    bin_body = _bytes_to_bin(body)

    # Compute the CRC of the content right-padded with n zeros.
    key_size = _get_key_size(key)
    padding = '0' * len(key)
    bin_cr = compute_crc(bin_body + padding, key)
    cr = int(bin_cr, 2)

    # Put together the content bytes and the CRC bytes.
    cont_size = len(body) + key_size
    enc_content = bytearray(cont_size)
    enc_content[:-key_size] = body
    enc_content[-key_size:] = cr.to_bytes(key_size, byteorder='big', signed=False)
    return cont_size, enc_content


def decode(enc_content: bytearray, key: str) -> (bool, datetime, str):
    """
    Decodes and validates a content encoded in a bytearray.
    Returns the validity flag, the datetime of the content creation and the textual content.
    If the CRC code is invalid the function returns (False, <arbitrary datetime>, '').
    Otherwise, it returns (True, <content creation datetime>, <content in a text form>).
    """

    # Compute the CRC code of the content that should include its own CRC code.
    key_size = _get_key_size(key)
    bin_body = _bytes_to_bin(enc_content[:-key_size])
    bin_cr = _bytes_to_bin(enc_content[-key_size:])[-len(key):]
    bin_cr = compute_crc(bin_body + bin_cr, key)

    # For a valid content the computed CRC should be zero.
    if int(bin_cr, 2) == 0:
        key_size = _get_key_size(key)
        # Decode the content creation timestamp.
        ts = struct.unpack('d', enc_content[:8])[0]
        # Decode the content.
        content = enc_content[8:-key_size].decode('utf8')
        return True, datetime.fromtimestamp(ts), content
    return False, datetime.min, ''


def _open_shared_memory(storage_name: str, max_size: int, must_exist: bool) -> Optional[SharedMemory]:
    """
    Creates and returns a shared memory accessor object. If must_exist == False creates the shared
    memory block if it doesn't exist. Otherwise, if the block doesn't exist returns None. 
    """

    try:
        return SharedMemory(name=storage_name, create=False, size=max_size)
    except FileNotFoundError:
        if must_exist:
            return None
        return SharedMemory(name=storage_name, create=True, size=max_size)


def write_to_sm(content: str, creation_time: Optional[datetime] = None, key: str = default_key,
                max_size: int = default_max_size, storage_name: str = default_storage_name) -> bool:
    """
    Saves a content and its creation time in a shared memory.

    The named shared memory block may or may not be already allocated. The function creates or opens
    the block, writes the encoded content and closes the block. Currently, there are no provisions
    for the destruction of the block.

    The content gets prepended by its length in bytes, so that a reading function knows how many
    bytes to read.

    If the total length of the content doesn't fit into the maximum size of the shared memory block
    the function does nothing and returns False. Otherwise, if the content is successfully stored
    into the shared memory, it returns True.
    
    Parameters:
    content       - The content string to be stored into the stored to the shared memory
    creation_time - Time when the content was created, which will also be stored to the shared memory.
                    If not provided the current time will be used.
    key           - A binary string used for computing the CRC.
    max_size      - Maximum size of the shared memory block in bytes.
    storage_name  - Name of the shared memory block.
    """

    # Encode the content and check if it fits into the shared memory block
    creation_time = creation_time or datetime.now()
    cont_size, enc_content = encode(content, key, creation_time)
    size_size = _get_byte_size(max_size)
    total_size = cont_size + size_size
    if total_size > max_size:
        return False

    # Open or create the named shared memory block.
    pwd_memory = _open_shared_memory(storage_name, max_size, False)
    try:
        # Write the content size followed by the content itself.
        pwd_memory.buf[:size_size] = cont_size.to_bytes(size_size, byteorder='big', signed=False)
        pwd_memory.buf[size_size:total_size] = enc_content
    finally:
        pwd_memory.close()
    return True


def read_from_sm(key: str = default_key, max_size: int = default_max_size,
                 storage_name: str = default_storage_name) -> (bool, datetime, str):
    """
    Reads from the shared memory a content and the time when it was created .

    The shared memory block must already exist and hold a valid content. Like its writing counterpart,
    this function opens and closes the shared memory block, but doesn't destroy it afterward.

    The content must be prepended by its length, so that the function knows how many bytes
    to read.

    The function returns (True, <content creation datetime>, <textual content>) if a valid content
    has been successfully retrieved from the shared memory. If the content is empty or too big (if the
    size is to be believed), or it has been deemed invalid the function returns (False, <any datetime>, '').

    Parameters:
    key           - A binary string used for computing the CRC.
    max_size      - Maximum size of the shared memory block in bytes.
    storage_name  - Name of the shared memory block.
    """

    size_size = _get_byte_size(max_size)

    pwd_memory = _open_shared_memory(storage_name, max_size, True)
    if pwd_memory is None:
        return False, datetime.min, ''
    try:
        cont_size = int.from_bytes(pwd_memory.buf[:size_size], byteorder='big')
        total_size = cont_size + size_size
        # Check if the size makes sense
        if cont_size == 0 or total_size > max_size:
            return False, datetime.min, ''
        # Reade and decode the content.
        enc_content = bytearray(pwd_memory.buf[size_size:total_size])
        return decode(enc_content, key)
    finally:
        pwd_memory.close()


def clear_sm(max_size: int = default_max_size, storage_name: str = default_storage_name,
             delete_storage: bool = False) -> None:
    """
    Invalidates the content stored in shared memory by setting its length to zero and optionally
    destroys the shared memory block. The latter may not take an immediate effect though.

    Parameters:
    max_size       - Maximum size of the shared memory block in bytes.
    storage_name   - Name of the shared memory block.
    delete_storage - If True will destroy the shared memory block.
    """

    pwd_memory = _open_shared_memory(storage_name, max_size, True)
    if pwd_memory is not None:
        try:
            size_size = _get_byte_size(max_size)
            if size_size <= max_size:
                cont_size = 0
                pwd_memory.buf[:size_size] = cont_size.to_bytes(size_size, byteorder='big', signed=False)
            if delete_storage:
                pwd_memory.unlink()
        finally:
            pwd_memory.close()
