import hashlib
import zlib


HASH_CHUNK_SIZE = 1024 * 1024
CRC64_XZ_MASK = (1 << 64) - 1
CRC64_XZ_REFLECTED_POLYNOMIAL = 0xC96C5795D7870F42
CRC64_XZ_INITIAL = CRC64_XZ_MASK


def _build_crc64_xz_table() -> tuple[int, ...]:
    table = []
    for value in range(256):
        checksum = value
        for _ in range(8):
            if checksum & 1:
                checksum = (checksum >> 1) ^ CRC64_XZ_REFLECTED_POLYNOMIAL
            else:
                checksum >>= 1
        table.append(checksum & CRC64_XZ_MASK)
    return tuple(table)


CRC64_XZ_TABLE = _build_crc64_xz_table()


def _update_crc64_xz(checksum: int, chunk: bytes) -> int:
    for value in chunk:
        checksum = CRC64_XZ_TABLE[(checksum ^ value) & 0xFF] ^ (checksum >> 8)
    return checksum & CRC64_XZ_MASK


def hash_file(path) -> dict[str, str | int]:
    """Return hashes and byte count for one file's raw bytes."""
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    crc32 = 0
    crc64 = CRC64_XZ_INITIAL
    size = 0
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_SIZE), b""):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)
            crc32 = zlib.crc32(chunk, crc32)
            crc64 = _update_crc64_xz(crc64, chunk)
            size += len(chunk)
    return {
        "md5": md5_hash.hexdigest(),
        "sha256": sha256_hash.hexdigest(),
        "crc32": f"{crc32 & 0xFFFFFFFF:08x}",
        "crc64": f"{crc64 ^ CRC64_XZ_MASK:016x}",
        "size": size,
    }
