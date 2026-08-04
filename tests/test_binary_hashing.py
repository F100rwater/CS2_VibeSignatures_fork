import hashlib
import unittest
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory

from binary_hashing import HASH_CHUNK_SIZE, hash_file


class TestHashFile(unittest.TestCase):
    def test_returns_standard_hashes_and_crc_test_vectors(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "binary.bin"
            path.write_bytes(b"123456789")
            metadata = hash_file(path)

        self.assertEqual(
            {
                "md5": "25f9e794323b453885f5181f1b624d0b",
                "sha256": "15e2b0d3c33891ebb0f1ef609ec419420c20e320ce94c65fbc8c3312448eb225",
                "crc32": "cbf43926",
                "crc64": "995dc9bbdf1939fa",
                "size": 9,
            },
            metadata,
        )

    def test_reads_all_chunks_as_one_raw_byte_stream(self) -> None:
        payload = (b"chunk-boundary" * ((HASH_CHUNK_SIZE // len(b"chunk-boundary")) + 2)) + b"tail"
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "binary.bin"
            path.write_bytes(payload)
            metadata = hash_file(path)

        self.assertEqual(hashlib.md5(payload).hexdigest(), metadata["md5"])
        self.assertEqual(hashlib.sha256(payload).hexdigest(), metadata["sha256"])
        self.assertEqual(f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}", metadata["crc32"])
        self.assertEqual(len(payload), metadata["size"])


if __name__ == "__main__":
    unittest.main()
