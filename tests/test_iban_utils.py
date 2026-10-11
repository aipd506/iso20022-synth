"""Unit tests for ISO 7064 MOD-97 IBAN and BIC utilities."""

import unittest
from iso20022_synth.iban_utils import (
    validate_iban,
    generate_valid_iban,
    generate_valid_bic,
    calculate_iban_checksum,
)


class TestIBANUtils(unittest.TestCase):
    def test_generate_and_validate_de(self):
        for _ in range(5):
            iban = generate_valid_iban("DE")
            valid, reason = validate_iban(iban)
            self.assertTrue(valid, f"Failed for {iban}: {reason}")
            self.assertEqual(len(iban), 22)
            self.assertTrue(iban.startswith("DE"))

    def test_generate_and_validate_gb(self):
        for _ in range(5):
            iban = generate_valid_iban("GB")
            valid, reason = validate_iban(iban)
            self.assertTrue(valid, f"Failed for {iban}: {reason}")
            self.assertEqual(len(iban), 22)
            self.assertTrue(iban.startswith("GB"))

    def test_generate_and_validate_fr(self):
        for _ in range(5):
            iban = generate_valid_iban("FR")
            valid, reason = validate_iban(iban)
            self.assertTrue(valid, f"Failed for {iban}: {reason}")
            self.assertEqual(len(iban), 27)
            self.assertTrue(iban.startswith("FR"))

    def test_corrupted_iban_fails(self):
        valid_iban = generate_valid_iban("DE")
        # Flip last digit
        last_digit = valid_iban[-1]
        new_digit = "0" if last_digit != "0" else "1"
        corrupted = valid_iban[:-1] + new_digit

        valid, reason = validate_iban(corrupted)
        self.assertFalse(valid)
        self.assertIn("MOD-97", reason)

    def test_bic_generation(self):
        bic = generate_valid_bic("DE")
        self.assertEqual(len(bic), 11)
        self.assertIn("DE", bic)


if __name__ == "__main__":
    unittest.main()
