# iso20022-synth

High-fidelity synthetic ISO 20022 XML financial message generator and validator for interbank payment rails.

Essential for sandbox testing of FedNow, SEPA Credit Transfer (SCT), and SWIFT MX rails without leaking production banking credentials, account balances, or personally identifiable customer data.

## Key Capabilities

1. Multi-Message Synthesis: Generates complete, compliant XML documents for:
   - `pacs.008.001.10`: Financial Institution to Financial Institution Customer Credit Transfer.
   - `pacs.009.001.09`: Financial Institution Credit Transfer (Interbank settlement).
   - `camt.053.001.10`: Bank-to-Customer Statement (End-of-day balances and transaction entries).
   - `pain.001.001.11`: Customer Credit Transfer Initiation (Corporate bulk payroll and payments).
2. ISO 7064 MOD-97 IBAN Engine: Pure-Python algorithm for calculating and verifying valid check digits across Germany (DE), United Kingdom (GB), France (FR), and generic international BBANs.
3. Cryptographic and Financial Integrity:
   - Dynamic UUIDv4 Unique End-to-End Transaction Reference (UETR).
   - Mathematical cross-reconciliation between Group Header Control Sum (`CtrlSum`) and individual transaction amounts (`IntrBkSttlmAmt` / `InstdAmt`).
   - Transaction count validation (`NbOfTxs`).
4. Schema & Tamper Detection: Detects corrupted control sums, count mismatches, invalid BICs, and illegal IBAN structures.
5. Zero External Dependencies: Engineered entirely in Python standard library (`xml.etree.ElementTree`, `decimal`, `uuid`, `re`, `argparse`).

## Installation

```bash
pip install iso20022-synth
```

Or install locally in editable mode:

```bash
git clone https://github.com/aipd506/iso20022-synth.git
cd iso20022-synth
pip install -e .
```

## Quick Start

### 1. Generate Synthetic Customer Credit Transfer (pacs.008)

```bash
isosynth generate pacs.008 --count 5 --currency USD --amount 12500.00 -o fednow_payment.xml
```

### 2. Generate Bank Statement (camt.053)

```bash
isosynth generate camt.053 --currency USD --amount 250000.00 -c 10 -o statement.xml
```

### 3. Validate Any ISO 20022 XML File

```bash
isosynth validate fednow_payment.xml
```

Output:
```text
Validation Status: PASSED
Message Type: pacs.008
Message ID: MSG20261011195745F0EC45
Transaction Count: Declared=5, Found=5
Control Sum: Declared=64500.00, Calculated=64500.00
```

### 4. Inspect Message Metadata

```bash
isosynth inspect fednow_payment.xml
```

## Python API Usage

```python
from iso20022_synth import generate_pacs008, ISO20022Validator

# Generate synthetic XML
xml_data = generate_pacs008(count=3, currency="USD")

# Validate
validator = ISO20022Validator()
result = validator.validate_xml(xml_data)

assert result.is_valid
print(f"Validated {result.calculated_transactions} transactions totalling {result.calculated_control_sum}")
```

## License

Apache-2.0
