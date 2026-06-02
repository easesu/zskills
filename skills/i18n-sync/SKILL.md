---
name: i18n-sync
description: Sync i18n translation keys across locale files. Use when the user asks to "补全翻译", "同步翻译", "sync translations", "i18n key diff", or any task involving comparing and aligning JSON locale files with a base language. Triggers on mentions of language packs, translation sync, missing keys, extra keys, or locale file alignment. Always use this skill when the user references en.json as a baseline and wants other language files updated.
---

# i18n Translation Sync Skill

Synchronize translation keys across locale JSON files, using a base language (typically `en.json`) as the source of truth.

## When to Use

- User wants to compare locale files against a base language and fix differences
- User mentions "补全翻译", "同步翻译", "对齐语言包", "补全其他语言"
- New keys were added to en.json and need to be propagated to other languages
- Old keys need to be removed from non-base language files
- Specific key paths need to be synced (e.g. only `purchaseModule`)

## Project Structure

This project uses `@nuxtjs/i18n` with JSON locale files. The directory layout is:

```
i18n/locales/
├── en.json              # Root-level translations
├── zh-CN.json
├── ja.json
├── ko.json
├── id.json
├── de.json
├── fr.json
├── pt.json
├── es.json
├── ar.json
├── subscription/        # Module-level translations
│   ├── en.json
│   ├── zh-CN.json
│   └── ...
├── pricing/
│   ├── en.json
│   └── ...
└── [other-module]/
    ├── en.json
    └── ...
```

Supported languages: `en, zh-CN, ja, ko, id, de, fr, pt, es, ar` (10 total).

File naming uses the language code (e.g. `ja.json`, `zh-CN.json`).

## Workflow

### Step 1: Identify scope

Determine from the user's request:

1. **Base file**: Which en.json to use as baseline (e.g. `i18n/locales/subscription/en.json`)
2. **Scope**: Full file comparison, or a specific key path (e.g. `purchaseModule`, `faq`, `components.BigSaleActivityPopup`)
3. **Target languages**: All non-en languages, or a subset
4. **Translation policy**:
   - **Translate**: Fill missing keys with translated content (default for content keys)
   - **Copy English**: Use English content as placeholder (for structural sync first, translate later)
   - **Preserve existing**: Keep existing translations, only add missing keys

Ask the user if any of these are ambiguous.

### Step 2: Read and compare

Read the base en.json and all target language files. For each target language, run `i18n_diff.py` to perform a **deep recursive comparison** against the base:

```bash
python scripts/i18n_diff.py <base_file> <target_dir> [--scope key.path] [--lang zh-CN,ja]
```

The script reports:
- **Missing keys**: Present in base but absent in target
- **Extra keys**: Present in target but absent in base
- **Structural mismatch**: Same key but different type (object vs string, array vs object, etc.)

If you need to inspect specific key values or the diff script isn't available, you can use the inline `deep_diff()` function from the script directly in a Python REPL.

### Step 3: Present the plan

Present a clear diff summary **before making any changes**. Include:

1. **Missing keys** per language (keys to add)
2. **Extra keys** per language (keys to remove)
3. **Structural mismatches** (keys to reshape)
4. **Translation approach**: How you'll fill in content (translate from English, copy English, etc.)

Wait for user confirmation before proceeding.

### Step 4: Execute changes

For each target language file:

1. **Run `i18n_sync.py` with `--dry-run`** to preview structural changes:

   ```bash
   python scripts/i18n_sync.py <base_file> <target_dir> [--scope key.path] [--lang zh-CN,ja] --dry-run
   ```

2. **Review the dry-run output** and confirm it matches the plan

3. **Execute the sync** (remove `--dry-run`) to apply structural changes:

   ```bash
   python scripts/i18n_sync.py <base_file> <target_dir> [--scope key.path] [--lang zh-CN,ja]
   ```

4. **Translate content** — the sync script adds English text as placeholder; you need to translate it:
   - Use the en.json value as the source text
   - Do NOT reference old/deprecated translations in the same file
   - Preserve interpolation syntax like `{variable}`, `{count}`, `{perMonth}`
   - Preserve rich text markers like `**bold**`, `{strong}...{/strong}`, or similar
   - Maintain consistent tone with existing translations in that language file
   - For RTL languages (ar), ensure proper sentence structure

### Step 5: Verify

After making all changes, run `i18n_diff.py` again to verify:

```bash
python scripts/i18n_diff.py <base_file> <target_dir> [--scope key.path] [--lang zh-CN,ja]
```

Confirm:

1. All target files have identical key structure to the base file
2. No extra keys remain
3. No missing keys remain
4. JSON is valid (no syntax errors)

Report the results to the user.

## Scripts

This skill includes two companion Python scripts in `scripts/`. Use them instead of manual inspection or inline Python — they are faster, more reliable, and produce consistent output.

### `scripts/i18n_diff.py` — Compare locale files

Recursively compares a base locale file against target locale files and reports missing keys, extra keys, and structural mismatches.

**Usage:**

```bash
python scripts/i18n_diff.py <base_file> <target_dir> [--scope key.path] [--lang zh-CN,ja,ko]
```

**Arguments:**

| Argument | Description |
|---|---|
| `base_file` | Path to the base locale file (e.g. `en.json`) |
| `target_dir` | Directory containing target locale files |
| `--scope` | Only compare keys within this dot-separated path |
| `--lang` | Comma-separated language codes to compare (default: all non-en) |

**Examples:**

```bash
# Compare all files in a module directory
python scripts/i18n_diff.py i18n/locales/subscription/en.json i18n/locales/subscription/

# Compare only a specific key path
python scripts/i18n_diff.py i18n/locales/en.json i18n/locales/ --scope purchaseModule

# Compare only specific languages
python scripts/i18n_diff.py i18n/locales/pricing/en.json i18n/locales/pricing/ --lang ar,de
```

**When to use:** Step 2 (Read and compare) and Step 5 (Verify) of the workflow.

### `scripts/i18n_sync.py` — Sync key structure

Syncs the key structure of target locale files to match the base file. Adds missing keys (with English text as placeholder), removes extra keys, and fixes structural mismatches.

> **Note:** This script does **NOT** translate content. It only syncs the key structure. After running it, you still need to translate the English placeholder text to each language.

**Usage:**

```bash
python scripts/i18n_sync.py <base_file> <target_dir> [--scope key.path] [--lang zh-CN,ja] [--dry-run]
```

**Arguments:**

| Argument | Description |
|---|---|
| `base_file` | Path to the base locale file (e.g. `en.json`) |
| `target_dir` | Directory containing target locale files |
| `--scope` | Only sync keys within this dot-separated path |
| `--lang` | Comma-separated language codes to sync (default: all non-en) |
| `--dry-run` | Preview changes without writing files |

**Examples:**

```bash
# Preview what would change (recommended before actual sync)
python scripts/i18n_sync.py i18n/locales/subscription/en.json i18n/locales/subscription/ --dry-run

# Sync only a specific key path
python scripts/i18n_sync.py i18n/locales/en.json i18n/locales/ --scope purchaseModule

# Sync and write changes
python scripts/i18n_sync.py i18n/locales/subscription/en.json i18n/locales/subscription/
```

**When to use:** Step 4 (Execute changes) of the workflow. Always run with `--dry-run` first and review the output before writing.

## Common Patterns from Past Work

### Pattern: Scope-limited sync

User only wants to sync a specific key path (e.g. `purchaseModule`). In this case:
- Only compare and modify keys within that path
- Do NOT touch any keys outside the specified scope

### Pattern: Incremental sync

User has modified a specific value in en.json (e.g. `purchaseModule.planFeature.videoDuration`) and wants only that key synced to other languages. In this case:
- Only translate and update that specific key path across all target files
- Skip full file comparison

### Pattern: Full restructure

Base en.json has restructured a section (e.g. replaced flat keys with nested arrays/objects). In this case:
- Delete the old structure in target files
- Insert the new structure from base
- Translate all content fresh from English — old translations for removed keys are discarded

### Pattern: Extract hardcoded text

User wants to extract hardcoded text from a Vue component into locale files. In this case:
- Identify all hardcoded text in the component
- Create appropriate key structure in en.json
- Use arrays for list data to avoid excessive key names
- Preserve HTML/formatting markers as separate fields (e.g. `strong`, `after`)
- Add translations to all other language files
- Replace hardcoded text in the component with `$t()` or `t()` calls

## Important Rules

1. **Always present the plan first**, wait for confirmation before executing
2. **Never modify keys outside the specified scope** unless explicitly asked
3. **Use deep recursive comparison** — don't stop at the top level; nested objects and arrays must be fully compared
4. **Discard old translations when told** — if user says "旧翻译废弃", translate fresh from English
5. **Preserve JSON formatting** — maintain consistent indentation and structure
6. **Preserve interpolation syntax** — `{variable}`, `{count}`, etc. must not be translated or removed
7. **Arabic (ar) is RTL** — sentence structure may differ significantly from English
8. **zh-CN is Simplified Chinese** — not Traditional Chinese (zh-TW)
9. **Portuguese (pt) is European Portuguese** — not Brazilian Portuguese (pt-BR)
