---
name: endnote-word-cwyw
description: Convert Word manuscripts with plain numbered references into EndNote/Word CWYW-updatable citations, repair EndNote X9 "!!! INVALID CITATION !!!" failures, create clean RIS imports, map imported EndNote record numbers, and generate Word temporary citations such as "{Author, Year #1234}". Use when a user asks to make Word references update with EndNote, insert citations with EndNote, fix Update Citations and Bibliography, handle EndNote X9 invalid citations, convert a DOCX bibliography to EndNote, or prepare a manuscript for later EndNote editing.
---

# EndNote Word CWYW

## Core Rule

Do not hand-build `ADDIN EN.CITE` fields in DOCX XML. EndNote X9 may reject those fields and convert them to `!!! INVALID CITATION !!!`.

Use real EndNote records instead:

1. Extract the manuscript's numbered reference list.
2. Create a clean RIS import file.
3. Import the RIS into the user's EndNote library.
4. Determine the real EndNote record numbers assigned to the imported references.
5. Generate a Word document whose citations are EndNote temporary citations:
   `{Clarkson, 2013 #2538; Moore, 2012 #2539}`
6. Have Word/EndNote run `Update Citations and Bibliography`.

## Quick Workflow

1. Back up the EndNote library before any import.
   - Copy both `.enl` and the matching `.Data` folder.
   - If EndNote locks files, close it first or do not proceed with destructive operations.

2. Parse the DOCX and export clean RIS:

```powershell
& "C:\Path\To\python.exe" ".codex\skills\endnote-word-cwyw\scripts\docx_to_endnote_temp.py" `
  "C:\path\manuscript.docx" `
  --outdir "C:\path\citation" `
  --ris
```

3. Import the generated `.ris` into EndNote.
   - Prefer RIS over ENW for EndNote X9.
   - If EndNote skips duplicates by DOI, regenerate RIS with `--no-doi`.
   - Avoid ENW when `%J` appears in output; some EndNote X9 setups import `%J ...` into the title.

4. Find the first and last real EndNote record numbers for the imported batch.
   - Use EndNote UI if reliable: show Record Number column or inspect a record.
   - If UI is unstable, inspect the EndNote `.Data\rdb\refs.MYD` file for the import marker used in RIS notes.
   - Confirm the imported records are clean: title must not contain `%J`; journal should be in its own field.

5. Regenerate the Word temp-citation file using the real record base:

```powershell
& "C:\Path\To\python.exe" ".codex\skills\endnote-word-cwyw\scripts\docx_to_endnote_temp.py" `
  "C:\path\manuscript.docx" `
  --outdir "C:\path\citation" `
  --record-base 2538
```

6. Open the generated `*_EndNote_record_number_citations.docx` in Word and click:
   `EndNote X9 > Update Citations and Bibliography`.

## Validation

Before telling the user the file is ready, verify:

- The generated DOCX contains temporary citations with `#record` numbers.
- First citation resembles `{FirstAuthor, Year #N}`.
- The final citation reaches the expected last record number.
- No visible `%` or `INVALID CITATION` appears before update.
- The RIS-imported EndNote records have clean title and journal fields.

Read `references/troubleshooting.md` when Word update creates invalid citations, `%J` appears in titles, EndNote import skips duplicates, EndNote GUI hangs, or record numbers must be inferred from EndNote library files.

## Safety Notes

- Never delete the user's old EndNote records unless explicitly asked.
- Never overwrite the user's original manuscript; write a new file with a clear suffix.
- Keep a plain formatted DOCX backup for submission, but tell the user it is not EndNote-updatable.
- If automated Word/EndNote update macros hang in hidden Word sessions, stop and clean only the hidden test processes. Ask the user to update in foreground Word.
