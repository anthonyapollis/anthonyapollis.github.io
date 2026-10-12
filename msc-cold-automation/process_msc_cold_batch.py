import argparse
import os
from pathlib import Path


def process_batch(base_dir: Path, suffix: str) -> tuple[int, list[str]]:
    input_dir = base_dir / "IN"
    output_dir = base_dir / "OUT"

    if not input_dir.is_dir():
        raise SystemExit(f"IN folder not found: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped: list[str] = []

    for input_file_path in sorted(input_dir.iterdir()):
        if not input_file_path.is_file():
            continue

        filename = input_file_path.name
        base_name, extension = os.path.splitext(filename)
        if len(extension) > 1:
            new_extension = extension[:-2] + suffix
            new_filename = base_name + new_extension
        else:
            new_filename = filename

        output_file_path = output_dir / new_filename

        try:
            with input_file_path.open("r", encoding="utf-8") as input_file:
                lines = input_file.readlines()

            modified_lines = []
            for index, line in enumerate(lines):
                if index >= 6 and len(line) >= 219:
                    modified_lines.append(line[:214] + "00:00" + line[219:])
                else:
                    modified_lines.append(line)

            with output_file_path.open(
                "w", encoding="utf-8", newline="\n"
            ) as output_file:
                output_file.writelines(modified_lines)

            processed += 1
            print(f"Processed: {filename} -> {new_filename}")
        except Exception as exc:
            skipped.append(f"{filename}: {exc}")
            print(f"Skipped: {filename} ({exc})")

    return processed, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clean and rename an MSC Cold batch."
    )
    parser.add_argument(
        "base_dir", type=Path, help="Batch folder containing an IN directory"
    )
    parser.add_argument(
        "--suffix", required=True, help="Two-letter batch suffix, for example AW"
    )
    args = parser.parse_args()

    suffix = args.suffix.upper()
    if len(suffix) != 2 or not suffix.isalpha():
        raise SystemExit("Suffix must contain exactly two letters.")
    if suffix.endswith("Z"):
        raise SystemExit("Suffix must not end with Z.")

    processed, skipped = process_batch(args.base_dir, suffix)
    print(f"Total processed: {processed}")
    print(f"Total skipped: {len(skipped)}")
    return 1 if skipped else 0


if __name__ == "__main__":
    raise SystemExit(main())
