# EndNote Word CWYW Skill

Codex skill for converting Word manuscripts with plain numbered references into EndNote/Word CWYW-updatable citations.

It was built for fragile EndNote X9 workflows where Word's **Update Citations and Bibliography** can produce `!!! INVALID CITATION !!!`.

## What It Does

- Parses a `.docx` manuscript reference list.
- Exports clean RIS records for EndNote import.
- Generates Word temporary citations with real EndNote record numbers, such as:

```text
{Clarkson, 2013 #2538; Moore, 2012 #2539}
```

- Documents the safer workflow: RIS import first, then Word temporary citations, then EndNote update.

## Install

Copy this folder into your Codex skills directory:

```powershell
Copy-Item -Recurse .\endnote-word-cwyw-skill "$env:USERPROFILE\.codex\skills\endnote-word-cwyw"
```

Or, inside a project-local Codex setup:

```powershell
Copy-Item -Recurse .\endnote-word-cwyw-skill .\.codex\skills\endnote-word-cwyw
```

Then start a new Codex session so the skill is discovered.

## Example Prompt

```text
Use $endnote-word-cwyw to convert this Word manuscript bibliography into EndNote-updatable citations and fix invalid citations.
```

## Important Notes

- Prefer RIS import over ENW for EndNote X9.
- Do not hand-build `ADDIN EN.CITE` fields in Word XML.
- Always back up the `.enl` file and matching `.Data` folder before importing.
- Do not delete old EndNote records unless the user explicitly asks.

## Contents

- `SKILL.md` - Codex skill instructions.
- `scripts/docx_to_endnote_temp.py` - reusable DOCX/RIS/temp-citation helper.
- `references/troubleshooting.md` - EndNote X9 failure modes and fixes.
- `agents/openai.yaml` - Codex UI metadata.
