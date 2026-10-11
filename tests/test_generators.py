"""Unit tests for synthetic ISO 20022 message generators."""

import unittest
from decimal import Decimal
from iso20022_synth.generators import (
    generate_pacs008,
    generate_pacs009,
    generate_camt053,
    generate_pain001,
)


class TestGenerators(unittest.TestCase):
    def test_generate_pacs008(self):
        xml_str = generate_pacs008(count=3, currency="USD", base_amount=Decimal("1500.00"))
        self.assertIn("urn:iso:std:iso:20022:tech:xsd:pacs.008.001.10", xml_str)
        self.assertIn("<FIToFICstmrCdtTrf>", xml_str)
        self.assertIn("<NbOfTxs>3</NbOfTxs>", xml_str)
        # 1500 + 1600 + 1700 = 4800.00
        self.assertIn("<CtrlSum>4800.00</CtrlSum>", xml_str)
        self.assertIn('Ccy="USD"', xml_str)

    def test_generate_pacs009(self):
        xml_str = generate_pacs009(count=2, currency="EUR", base_amount=Decimal("100000.00"))
        self.assertIn("urn:iso:std:iso:20022:tech:xsd:pacs.009.001.09", xml_str)
        self.assertIn("<FICdtTrf>", xml_str)
        self.assertIn("<NbOfTxs>2</NbOfTxs>", xml_str)
        self.assertIn("<CtrlSum>200000.00</CtrlSum>", xml_str)
        self.assertIn('Ccy="EUR"', xml_str)

    def test_generate_camt053(self):
        xml_str = generate_camt053(currency="USD", opening_balance=Decimal("50000.00"), entries_count=4)
        self.assertIn("urn:iso:std:iso:20022:tech:xsd:camt.053.001.10", xml_str)
        self.assertIn("<BkToCstmrStmt>", xml_str)
        self.assertIn("<Cd>OPBD</Cd>", xml_str)
        self.assertIn("<Cd>CLBD</Cd>", xml_str)
        self.assertIn("<Ntry>", xml_str)

    def test_generate_pain001(self):
        xml_str = generate_pain001(count=2, currency="USD", base_amount=Decimal("2000.00"))
        self.assertIn("urn:iso:std:iso:20022:tech:xsd:pain.001.001.11", xml_str)
        self.assertIn("<CstmrCdtTrfInitn>", xml_str)
        self.assertIn("<CtrlSum>4000.00</CtrlSum>", xml_str)


if __name__ == "__main__":
    unittest.main()
