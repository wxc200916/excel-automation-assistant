#!/usr/bin/env python3
"""Excel Automation Assistant v0.1.0
Merge CSV files, remove empty rows, remove duplicates, and create a simple report.
"""

import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path


def clean(value):
    return "" if value is None else str(value).strip()


def read_csv_file(path):
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                rows = list(csv.reader(f))
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"Cannot read file: {path}")

    if not rows:
        return [], []

    headers = [clean(x) or f"column_{i + 1}" for i, x in enumerate(rows[0])]
    records = []
    for row in rows[1:]:
        row = row + [""] * (len(headers) - len(row))
        record = {h: clean(row[i]) for i, h in enumerate(headers)}
        if any(record.values()):
            records.append(record)
    return headers, records


def merge_headers(groups):
    headers = []
    for group in groups:
        for item in group:
            if item not in headers:
                headers.append(item)
    if "source_file" not in headers:
        headers.append("source_file")
    return headers


def remove_duplicates(records, keys):
    if not records:
        return [], 0
    if not keys:
        keys = [k for k in records[0].keys() if k != "source_file"]

    seen = set()
    output = []
    removed = 0
    for record in records:
        marker = tuple(record.get(k, "") for k in keys)
        if marker in seen:
            removed += 1
            continue
        seen.add(marker)
        output.append(record)
    return output, removed


def write_csv_file(path, headers, records):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def write_report(path, source_counts, original_count, final_count, duplicate_count, headers, records):
    lines = [
        "Excel 自动化助手处理报告",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "处理概览",
        f"- 原始有效行数：{original_count}",
        f"- 去重后行数：{final_count}",
        f"- 删除重复行数：{duplicate_count}",
        "",
        "来源文件",
    ]
    for source, count in source_counts.items():
        lines.append(f"- {source}: {count} 行")

    lines += ["", "字段缺失统计"]
    for header in headers:
        if header == "source_file":
            continue
        blank_count = sum(1 for record in records if not record.get(header, ""))
        lines.append(f"- {header}: {blank_count} 个空值")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Clean and merge CSV tables.")
    parser.add_argument("files", nargs="+", help="CSV files to process")
    parser.add_argument("--output-dir", default="output", help="Output folder")
    parser.add_argument("--dedupe-by", nargs="*", default=[], help="Column names used for duplicate detection")
    args = parser.parse_args()

    paths = [Path(x).expanduser().resolve() for x in args.files]
    for path in paths:
        if not path.exists():
            raise SystemExit(f"Missing file: {path}")

    header_groups = []
    all_records = []
    source_counts = Counter()
    for path in paths:
        headers, records = read_csv_file(path)
        header_groups.append(headers)
        for record in records:
            record["source_file"] = path.name
        all_records.extend(records)
        source_counts[path.name] = len(records)

    headers = merge_headers(header_groups)
    cleaned, duplicate_count = remove_duplicates(all_records, args.dedupe_by)

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv_file(output_dir / "cleaned_data.csv", headers, cleaned)
    write_report(output_dir / "summary_report.txt", source_counts, len(all_records), len(cleaned), duplicate_count, headers, cleaned)

    print("处理完成")
    print(f"- 清洗结果: {output_dir / 'cleaned_data.csv'}")
    print(f"- 处理报告: {output_dir / 'summary_report.txt'}")


if __name__ == "__main__":
    main()
