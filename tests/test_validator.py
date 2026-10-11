"""Unit tests for ISO 20022 XML validation engine and tamper detection."""

import unittest
from decimal import Decimal
from iso20022_synth.generators import generate_pacs008, generate_pacs009, generate_camt053, generate_pain001
from iso20022_synth.validator import ISO20022Validator


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ISO20022Validator()

    def test_validate_fresh_pacs008(self):
        xml_str = generate_pacs008(count=2, currency="USD", base_amount=Decimal("1000.00"))
        res = self.validator.validate_xml(xml_str)
        self.assertTrue(res.is_valid, f"Validation failed: {res.errors}")
        self.assertEqual(res.message_type, "pacs.008")
        self.assertEqual(res.calculated_transactions, 2)
        self.assertEqual(res.calculated_control_sum, Decimal("2100.00"))

    def test_validate_fresh_pacs009(self):
        xml_str = generate_pacs009(count=3, currency="EUR", base_amount=Decimal("50000.00"))
        res = self.validator.validate_xml(xml_str)
        self.assertTrue(res.is_valid, f"Validation failed: {res.errors}")
        self.assertEqual(res.message_type, "pacs.009")
        self.assertEqual(res.calculated_transactions, 3)

    def test_validate_fresh_camt053(self):
        xml_str = generate_camt053(currency="USD", opening_balance=Decimal("20000.00"), entries_count=3)
        res = self.validator.validate_xml(xml_str)
        self.assertTrue(res.is_valid, f"Validation failed: {res.errors}")
        self.assertEqual(res.message_type, "camt.053")

    def test_validate_fresh_pain001(self):
        xml_str = generate_pain001(count=2, currency="USD", base_amount=Decimal("1500.00"))
        res = self.validator.validate_xml(xml_str)
        self.assertTrue(res.is_valid, f"Validation failed: {res.errors}")
        self.assertEqual(res.message_type, "pain.001")

    def test_detect_corrupted_control_sum(self):
        xml_str = generate_pacs008(count=1, base_amount=Decimal("1000.00"))
        # Tamper control sum
        tampered = xml_str.replace("<CtrlSum>1000.00</CtrlSum>", "<CtrlSum>9999.00</CtrlSum>")
        res = self.validator.validate_xml(tampered)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Control sum mismatch" in err for err in res.errors))

    def test_detect_corrupted_transaction_count(self):
        xml_str = generate_pacs008(count=2)
        # Tamper transaction count
        tampered = xml_str.replace("<NbOfTxs>2</NbOfTxs>", "<NbOfTxs>99</NbOfTxs>")
        res = self.validator.validate_xml(tampered)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Transaction count mismatch" in err for err in res.errors))

    def test_detect_corrupted_iban(self):
        xml_str = generate_pacs008(count=1)
        # Replace IBAN with invalid checksum
        tampered = xml_str.replace("<IBAN>DE", "<IBAN>DE00")
        res = self.validator.validate_xml(tampered)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Invalid IBAN" in err for err in res.errors))

    def test_detect_corrupted_uetr(self):
        xml_str = generate_pacs008(count=1)
        # Replace UETR with invalid non-uuid
        tampered = xml_str.replace("<UETR>", "<UETR>NOT-A-VALID-UUID-")
        res = self.validator.validate_xml(tampered)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Invalid UETR" in err for err in res.errors))


if __name__ == "__main__":
    unittest.main()
