#!/usr/bin/env python3
"""
i18n locale sync tool — automatically sync keys from base to target files.

This script handles:
- Adding missing keys (copied from base, NOT translated)
- Removing extra keys
- Fixing structural mismatches

Note: This script does NOT translate content. It only syncs the key structure.
      After running this, you need to translate the English content to each language.

Usage:
  python i18n_sync.py <base_file> <target_dir> [--scope key.path] [--lang zh-CN,ja] [--dry-run]

Examples:
  python i18n_sync.py i18n/locales/subscription/en.json i18n/locales/subscription/ --dry-run
  python i18n_sync.py i18n/locales/en.json i18n/locales/ --scope purchaseModule
"""

import json
import sys
import os
import argparse
import copy


def get_by_path(data, path):
    keys = path.split(".")
    current = data
    for key in keys:
        if "[" in key and key.endswith("]"):
            base_key = key[:key.index("[")]
            index = int(key[key.index("[")+1:key.index("]")])
            current = current[base_key][index]
        else:
            current = current[key]
    return current


def set_by_path(data, path, value):
    keys = path.split(".")
    current = data
    for key in keys[:-1]:
        if "[" in key and key.endswith("]"):
            base_key = key[:key.index("[")]
            index = int(key[key.index("[")+1:key.index("]")])
            current = current[base_key][index]
        else:
            current = current[key]
    last_key = keys[-1]
    if "[" in last_key and last_key.endswith("]"):
        base_key = last_key[:last_key.index("[")]
        index = int(last_key[last_key.index("[")+1:last_key.index("]")])
        current[base_key][index] = value
    else:
        current[last_key] = value


def delete_by_path(data, path):
    keys = path.split(".")
    current = data
    for key in keys[:-1]:
        if "[" in key and key.endswith("]"):
            base_key = key[:key.index("[")]
            index = int(key[key.index("[")+1:key.index("]")])
            current = current[base_key][index]
        else:
            current = current[key]
    last_key = keys[-1]
    if "[" in last_key and last_key.endswith("]"):
        base_key = last_key[:last_key.index("[")]
        index = int(last_key[last_key.index("[")+1:last_key.index("]")])
        del current[base_key][index]
    else:
        del current[last_key]


def deep_sync(base, target):
    """
    Recursively sync target to match base structure.
    - Add missing keys (with base values as placeholder)
    - Remove extra keys
    - Fix type mismatches (replace with base structure)

    Returns (modified_target, changes_list) where changes_list describes what was done.
    """
    changes = []

    if isinstance(base, dict):
        if not isinstance(target, dict):
            # Type mismatch — replace entirely
            return copy.deepcopy(base), [f"Replaced non-dict with dict"]

        # Remove extra keys
        for k in list(target.keys()):
            if k not in base:
                del target[k]
                changes.append(f"Removed extra key: {k}")

        # Add/sync keys from base
        for k in base:
            if k not in target:
                target[k] = copy.deepcopy(base[k])
                changes.append(f"Added missing key: {k}")
            else:
                sub_changes = deep_sync(base[k], target[k])
                for c in sub_changes:
                    changes.append(f"{k}.{c}")

    elif isinstance(base, list):
        if not isinstance(target, list):
            return copy.deepcopy(base), [f"Replaced non-list with list"]

        # Sync list length and items
        while len(target) > len(base):
            removed = target.pop()
            changes.append(f"Removed extra list item at index {len(target)}")

        for i in range(min(len(base), len(target))):
            sub_changes = deep_sync(base[i], target[i])
            for c in sub_changes:
                changes.append(f"[{i}].{c}")

        while len(target) < len(base):
            target.append(copy.deepcopy(base[len(target)]))
            changes.append(f"Added missing list item at index {len(target)-1}")

    return target, changes


def main():
    parser = argparse.ArgumentParser(description="Sync i18n locale files from a base file")
    parser.add_argument("base_file", help="Path to the base locale file (e.g. en.json)")
    parser.add_argument("target_dir", help="Directory containing target locale files")
    parser.add_argument("--scope", help="Only sync keys within this dot-separated path")
    parser.add_argument("--lang", help="Comma-separated language codes to sync (default: all non-en)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    args = parser.parse_args()

    with open(args.base_file, "r", encoding="utf-8") as f:
        base_data = json.load(f)

    # Find target files
    target_files = {}
    for fname in os.listdir(args.target_dir):
        if fname.endswith(".json") and fname != os.path.basename(args.base_file):
            lang_code = fname.replace(".json", "")
            target_files[lang_code] = os.path.join(args.target_dir, fname)

    if args.lang:
        langs = [l.strip() for l in args.lang.split(",")]
        target_files = {k: v for k, v in target_files.items() if k in langs}

    total_changes = 0

    for lang, fpath in sorted(target_files.items()):
        with open(fpath, "r", encoding="utf-8") as f:
            target_data = json.load(f)

        if args.scope:
            try:
                target_scope = get_by_path(target_data, args.scope)
                base_scope = get_by_path(base_data, args.scope)
            except (KeyError, IndexError, TypeError) as e:
                print(f"[{lang}] Cannot access scope '{args.scope}': {e}")
                continue

            synced_scope, changes = deep_sync(base_scope, copy.deepcopy(target_scope))

            if changes:
                set_by_path(target_data, args.scope, synced_scope)
                print(f"\n[{lang}] {len(changes)} changes in scope '{args.scope}':")
                for c in changes[:20]:
                    print(f"  - {c}")
                if len(changes) > 20:
                    print(f"  ... and {len(changes) - 20} more")
                total_changes += len(changes)
            else:
                print(f"[{lang}] No changes needed in scope '{args.scope}'")
        else:
            synced_data, changes = deep_sync(base_data, copy.deepcopy(target_data))

            if changes:
                target_data = synced_data
                print(f"\n[{lang}] {len(changes)} changes:")
                for c in changes[:20]:
                    print(f"  - {c}")
                if len(changes) > 20:
                    print(f"  ... and {len(changes) - 20} more")
                total_changes += len(changes)
            else:
                print(f"[{lang}] No changes needed")

        if not args.dry_run and changes:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(target_data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"  -> Written to {fpath}")

    print(f"\n{'='*60}")
    if args.dry_run:
        print(f"DRY RUN: {total_changes} changes would be made.")
    else:
        print(f"RESULT: {total_changes} changes applied.")
        if total_changes > 0:
            print("NOTE: Added keys contain English text as placeholder.")
            print("      You need to translate them to each language.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
