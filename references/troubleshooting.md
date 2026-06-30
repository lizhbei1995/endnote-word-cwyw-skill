# EndNote Word CWYW Troubleshooting

## `!!! INVALID CITATION !!!` after Word update

Likely causes:

- The document contains manually constructed `ADDIN EN.CITE` fields rather than EndNote-created fields.
- Temporary citations omit real EndNote record numbers and EndNote matches the wrong reference.
- Temporary citations use record numbers from a different EndNote library.
- A multi-reference field includes invalid embedded citation data.

Fix:

Use real EndNote record numbers in temporary citations:

```text
{Clarkson, 2013 #2538; Moore, 2012 #2539}
```

Do not rely on `{Clarkson, 2013}` or hand-built XML fields when accuracy matters.

## `%J` appears in titles or bibliography

Some EndNote X9 file-association ENW imports can treat EndNote tagged lines as literal text, placing `%J Journal Name` into the title field.

Fix:

- Prefer RIS import (`TY`, `AU`, `TI`, `T2`, `JO`, `PY`, `VL`, `IS`, `SP`, `EP`, `N1`).
- If EndNote skips records as duplicates, create a RIS without DOI/URL fields and with a unique `N1` marker.
- Verify imported records in the `.Data\rdb\refs.MYD` file or in EndNote UI: titles must not include `%J`.

## EndNote skips clean records as duplicates

EndNote may identify existing dirty records by DOI and refuse to import a clean duplicate.

Fix:

Generate a force-import RIS without DOI/URL fields and with a marker:

```text
N1  - CLEAN_IMPORT_ORIGINAL_REF_1
```

After import, use the newly assigned clean record numbers.

## EndNote GUI hangs during File menu/import

Observed with EndNote X9 on some Windows systems.

Fix:

- Back up the library first.
- Try Windows file association import: `Invoke-Item clean_import.ris`.
- If EndNote hangs, terminate only after a backup exists.
- Avoid broad UI automation that clicks menus repeatedly.

## Extracting Record Numbers From `refs.MYD`

EndNote X9 stores library data in:

```text
<Library>.Data\rdb\refs.MYD
```

Search for a unique marker from RIS `N1`, for example:

```text
CLEAN_TAHMOOR_RIS_FORCE_IMPORT_ORIGINAL_REF_1
```

Only use inferred record numbers after verifying:

- all imported markers are present;
- markers appear in the expected reference order;
- the first and last numbers form a contiguous range;
- the generated Word temporary citations contain that exact range.

## Word Update Testing

Hidden Word COM update tests can hang because EndNote displays invisible dialogs or waits for foreground interaction. If this happens:

- Do not treat timeout as document failure.
- Close only hidden Word test processes you created.
- Leave user-visible Word documents untouched.
- Ask the user to open the final temp-citation DOCX and click Update in foreground Word.
