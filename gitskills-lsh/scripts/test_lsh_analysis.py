import hashlib
import struct
import unittest

from lsh_analysis import body, minhash_signature, shingles


class PilotTests(unittest.TestCase):
    def test_signature_matches_previous_pilot(self):
        signature = minhash_signature({0, 1, 2, 2**64 - 1})
        digest = hashlib.sha256(struct.pack('<128Q', *signature)).hexdigest()
        self.assertEqual(digest, 'a438794f3758f8add195ff775c562eaa35b7e00278cb0eb839ae533c1f5c837e')

    def test_frontmatter_and_word_normalization(self):
        text = '---\nname: test\n---\nAla ma kota, a kot psa!'
        self.assertEqual(body(text), 'Ala ma kota, a kot psa!')
        self.assertEqual(shingles(body(text)), shingles('ALA ma kota a KOT psa'))
        self.assertEqual(body('---\nbez zamknięcia'), '---\nbez zamknięcia')

    def test_empty_shingle_set_is_rejected(self):
        with self.assertRaises(ValueError):
            minhash_signature(set())


if __name__ == '__main__':
    unittest.main()
