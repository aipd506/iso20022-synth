"""Command-line interface for iso20022-synth."""

import argparse
import sys
from decimal import Decimal
from pathlib import Path
from .generators import generate_pacs008, generate_pacs009, generate_camt053, generate_pain001
from .validator import ISO20022Validator


def cmd_generate(args) -> int:
    msg_type = args.type.lower()
    count = args.count
    currency = args.currency.upper()
    amount = Decimal(str(args.amount))

    if msg_type in ["pacs.008", "pacs008"]:
        xml_out = generate_pacs008(count=count, currency=currency, base_amount=amount)
    elif msg_type in ["pacs.009", "pacs009"]:
        xml_out = generate_pacs009(count=count, currency=currency, base_amount=amount)
    elif msg_type in ["camt.053", "camt053"]:
        xml_out = generate_camt053(currency=currency, opening_balance=amount, entries_count=count)
    elif msg_type in ["pain.001", "pain001"]:
        xml_out = generate_pain001(count=count, currency=currency, base_amount=amount)
    else:
        sys.stderr.write(f"Error: Unsupported message type '{args.type}'. Supported: pacs.008, pacs.009, camt.053, pain.001\n")
        return 1

    if args.output:
        out_p = Path(args.output)
        out_p.write_text(xml_out, encoding="utf-8")
        print(f"Generated synthetic {msg_type} saved to {out_p}")
    else:
        sys.stdout.write(xml_out)

    return 0


def cmd_validate(args) -> int:
    file_p = Path(args.file)
    if not file_p.exists():
        sys.stderr.write(f"Error: File '{file_p}' not found.\n")
        return 1

    xml_text = file_p.read_text(encoding="utf-8")
    validator = ISO20022Validator()
    result = validator.validate_xml(xml_text)

    print(result.summary())
    return 0 if result.is_valid else 1


def cmd_inspect(args) -> int:
    file_p = Path(args.file)
    if not file_p.exists():
        sys.stderr.write(f"Error: File '{file_p}' not found.\n")
        return 1

    xml_text = file_p.read_text(encoding="utf-8")
    validator = ISO20022Validator()
    result = validator.validate_xml(xml_text)

    print("=" * 60)
    print(f"ISO 20022 Message Inspection: {file_p.name}")
    print("=" * 60)
    print(f"Detected Type:       {result.message_type}")
    print(f"Message ID:          {result.message_id}")
    print(f"Transaction Count:   {result.calculated_transactions}")
    if result.calculated_control_sum is not None:
        print(f"Calculated Total:    {result.calculated_control_sum:.2f}")
    print(f"Schema Status:       {'VALID' if result.is_valid else 'INVALID'}")
    if result.errors:
        print(f"Errors Found:        {len(result.errors)}")
        for err in result.errors:
            print(f"  - {err}")
    if result.warnings:
        print(f"Warnings:            {len(result.warnings)}")
        for w in result.warnings:
            print(f"  - {w}")
    print("=" * 60)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="isosynth",
        description="High-fidelity synthetic ISO 20022 XML financial message generator and validator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate synthetic ISO 20022 XML")
    p_gen.add_argument("type", choices=["pacs.008", "pacs.009", "camt.053", "pain.001"], help="Message type")
    p_gen.add_argument("-c", "--count", type=int, default=1, help="Number of transactions or entries (default: 1)")
    p_gen.add_argument("--currency", default="USD", help="ISO 4217 Currency code (default: USD)")
    p_gen.add_argument("--amount", type=float, default=2500.00, help="Base transaction amount (default: 2500.00)")
    p_gen.add_argument("-o", "--output", help="Output file path (default: stdout)")
    p_gen.set_defaults(func=cmd_generate)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate an ISO 20022 XML file")
    p_val.add_argument("file", help="Path to XML file")
    p_val.set_defaults(func=cmd_validate)

    # inspect
    p_ins = subparsers.add_parser("inspect", help="Inspect metadata and elements in an ISO 20022 XML file")
    p_ins.add_argument("file", help="Path to XML file")
    p_ins.set_defaults(func=cmd_inspect)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
