#!/usr/bin/env python3
"""
i18n locale diff tool — compare a base locale file against target locale files.

Usage:
  python i18n_diff.py <base_file> <target_dir> [--scope key.path] [--lang zh-CN,ja,ko]

Examples:
  python i18n_diff.py i18n/locales/subscription/en.json i18n/locales/subscription/
  python i18n_diff.py i18n/locales/en.json i18n/locales/ --scope purchaseModule
  python i18n_diff.py i18n/locales/pricing/en.json i18n/locales/pricing/ --lang ar,de
"""

import json
import sys
import os
import argparse


def get_by_path(data, path):
    """Get a nested value by dot-separated path."""
    keys = path.split(".")
    current = data
    for key in keys:
        # Handle array indices like items[0]
        if "[" in key and key.endswith("]"):
            base_key = key[:key.index("[")]
            index = int(key[key.index("[")+1:key.index("]")])
            current = current[base_key][index]
        else:
            current = current[key]
    return current


def deep_diff(base, target, path=""):
    """Recursively compare two JSON structures and return differences."""
    missing = []
    extra = []
    mismatch = []

    if isinstance(base, dict) and isinstance(target, dict):
        for k in base:
            subpath = f"{path}.{k}" if path else k
            if k not in target:
                missing.append(subpath)
            else:
                m, e, x = deep_diff(base[k], target[k], subpath)
                missing += m
                extra += e
                mismatch += x
        for k in target:
            subpath = f"{path}.{k}" if path else k
            if k not in base:
                extra.append(subpath)
    elif isinstance(base, list) and isinstance(target, list):
        for i in range(len(base)):
            subpath = f"{path}[{i}]"
            if i >= len(target):
                missing.append(subpath)
            else:
                m, e, x = deep_diff(base[i], target[i], subpath)
                missing += m
                extra += e
                mismatch += x
        for i in range(len(target)):
            subpath = f"{path}[{i}]"
            if i >= len(base):
                extra.append(subpath)
    elif type(base) != type(target):
        mismatch.append(f"{path} (base: {type(base).__name__}, target: {type(target).__name__})")

    return missing, extra, mismatch


def get_key_structure(data, path=""):
    """Get all key paths in a JSON structure (leaf nodes only)."""
    paths = []
    if isinstance(data, dict):
        for k in data:
            subpath = f"{path}.{k}" if path else k
            if isinstance(data[k], (dict, list)):
                paths += get_key_structure(data[k], subpath)
            else:
                paths.append(subpath)
    elif isinstance(data, list):
        for i in range(len(data)):
            subpath = f"{path}[{i}]"
            if isinstance(data[i], (dict, list)):
                paths += get_key_structure(data[i], subpath)
            else:
                paths.append(subpath)
    else:
        paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description="Compare i18n locale files against a base file")
    parser.add_argument("base_file", help="Path to the base locale file (e.g. en.json)")
    parser.add_argument("target_dir", help="Directory containing target locale files")
    parser.add_argument("--scope", help="Only compare keys within this dot-separated path")
    parser.add_argument("--lang", help="Comma-separated language codes to compare (default: all non-en)")
    args = parser.parse_args()

    with open(args.base_file, "r", encoding="utf-8") as f:
        base_data = json.load(f)

    # Scope to a specific key path if requested
    if args.scope:
        base_compare = get_by_path(base_data, args.scope)
    else:
        base_compare = base_data

    # Find target files
    target_files = {}
    for fname in os.listdir(args.target_dir):
        if fname.endswith(".json") and fname != os.path.basename(args.base_file):
            lang_code = fname.replace(".json", "")
            target_files[lang_code] = os.path.join(args.target_dir, fname)

    # Filter by language if specified
    if args.lang:
        langs = [l.strip() for l in args.lang.split(",")]
        target_files = {k: v for k, v in target_files.items() if k in langs}

    all_clean = True

    for lang, fpath in sorted(target_files.items()):
        with open(fpath, "r", encoding="utf-8") as f:
            target_data = json.load(f)

        if args.scope:
            try:
                target_compare = get_by_path(target_data, args.scope)
            except (KeyError, IndexError, TypeError):
                print(f"\n{'='*60}")
                print(f"[{lang}] Scope path '{args.scope}' not found in {fpath}")
                print(f"{'='*60}")
                all_clean = False
                continue
        else:
            target_compare = target_data

        missing, extra, mismatch = deep_diff(base_compare, target_compare)

        has_diff = missing or extra or mismatch
        if has_diff:
            all_clean = False

        print(f"\n{'='*60}")
        print(f"[{lang}] {fpath}")
        print(f"{'='*60}")

        if missing:
            print(f"\n  Missing keys ({len(missing)}):")
            for m in missing:
                print(f"    - {m}")

        if extra:
            print(f"\n  Extra keys ({len(extra)}):")
            for e in extra:
                print(f"    + {e}")

        if mismatch:
            print(f"\n  Type mismatches ({len(mismatch)}):")
            for x in mismatch:
                print(f"    ~ {x}")

        if not has_diff:
            print("  OK - No differences")

    print(f"\n{'='*60}")
    if all_clean:
        print("RESULT: All locale files are in sync with the base file.")
    else:
        print("RESULT: Differences found. See details above.")
    print(f"{'='*60}")

    sys.exit(0 if all_clean else 1)


if __name__ == "__main__":
    main()
