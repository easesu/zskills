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

Read the base en.json and all target language files. For each target language, perform a **deep recursive comparison** against the base:

- **Missing keys**: Present in base but absent in target
- **Extra keys**: Present in target but absent in base
- **Structural mismatch**: Same key but different type (object vs string, array vs object, etc.)
- **Content drift**: Same key path but the value structure differs (e.g. nested children changed)

Use a script to do the diff rather than manual inspection — it's faster and more reliable:

```python
import json

def deep_diff(base, target, path=""):
    missing, extra, mismatch = [], [], []
    if isinstance(base, dict) and isinstance(target, dict):
        for k in base:
            if k not in target:
                missing.append(f"{path}.{k}" if path else k)
            else:
                m, e, x = deep_diff(base[k], target[k], f"{path}.{k}" if path else k)
                missing += m; extra += e; mismatch += x
        for k in target:
            if k not in base:
                extra.append(f"{path}.{k}" if path else k)
    elif isinstance(base, list) and isinstance(target, list):
        for i in range(len(base)):
            if i >= len(target):
                missing.append(f"{path}[{i}]")
            else:
                m, e, x = deep_diff(base[i], target[i], f"{path}[{i}]")
                missing += m; extra += e; mismatch += x
        for i in range(len(target)):
            if i >= len(base):
                extra.append(f"{path}[{i}]")
    elif type(base) != type(target):
        mismatch.append(f"{path} (base: {type(base).__name__}, target: {type(target).__name__})")
    return missing, extra, mismatch
```

### Step 3: Present the plan

Present a clear diff summary **before making any changes**. Include:

1. **Missing keys** per language (keys to add)
2. **Extra keys** per language (keys to remove)
3. **Structural mismatches** (keys to reshape)
4. **Translation approach**: How you'll fill in content (translate from English, copy English, etc.)

Wait for user confirmation before proceeding.

### Step 4: Execute changes

For each target language file:

1. **Remove extra keys** that don't exist in base
2. **Add missing keys** at the correct position in the JSON structure
3. **Fix structural mismatches** to match base structure
4. **Translate content** — when translating:
   - Use the en.json value as the source text
   - Do NOT reference old/deprecated translations in the same file
   - Preserve interpolation syntax like `{variable}`, `{count}`, `{perMonth}`
   - Preserve rich text markers like `**bold**`, `{strong}...{/strong}`, or similar
   - Maintain consistent tone with existing translations in that language file
   - For RTL languages (ar), ensure proper sentence structure

### Step 5: Verify

After making all changes, run a verification script to confirm:

1. All target files have identical key structure to the base file
2. No extra keys remain
3. No missing keys remain
4. JSON is valid (no syntax errors)

Report the results to the user.

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
