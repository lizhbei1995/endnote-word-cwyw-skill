import argparse
import csv
import re
import zipfile
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
NS = {"w": W_NS}

FULL_JOURNAL_NAMES = {
    "Energy Fuels": "Energy & Fuels",
    "Energy Sci Eng": "Energy Science & Engineering",
    "Environ Earth Sci": "Environmental Earth Sciences",
    "Front Earth Sci": "Frontiers in Earth Science",
    "Int J Coal Geol": "International Journal of Coal Geology",
    "Int J Coal Sci Technol": "International Journal of Coal Science & Technology",
    "Int J Min Sci Technol": "International Journal of Mining Science and Technology",
    "J China Univ Min Technol": "Journal of China University of Mining and Technology",
    "J Nat Gas Sci Eng": "Journal of Natural Gas Science and Engineering",
    "J Pet Technol": "Journal of Petroleum Technology",
    "Nat Hazards": "Natural Hazards",
    "Nat Resour Res": "Natural Resources Research",
    "Pet Sci Technol": "Petroleum Science and Technology",
    "Phys Fluids": "Physics of Fluids",
    "Sci Rep": "Scientific Reports",
    "SPE Annu Tech Conf Exhib": "SPE Annual Technical Conference and Exhibition",
    "SPE East Reg Meet": "SPE Eastern Regional Meeting",
    "SPE J": "SPE Journal",
    "Trans Soc Min Metall Explor": "Transactions of the Society for Mining, Metallurgy & Exploration",
}


def para_text(paragraph):
    parts = []
    for node in paragraph.iter():
        if node.tag == W + "t":
            parts.append(node.text or "")
        elif node.tag == W + "tab":
            parts.append("\t")
        elif node.tag == W + "br":
            parts.append("\n")
    return "".join(parts)


def find_references_start(paragraphs):
    for i, paragraph in enumerate(paragraphs):
        text = re.sub(r"\s+", " ", para_text(paragraph).strip()).lower()
        if re.fullmatch(r"(references|reference|bibliography)\s*[:：]?", text):
            return i
    return None


def parse_numbered_reference(text):
    for pattern in (r"^\s*\[(\d+)\]\s*(.+)$", r"^\s*(\d+)[\.\)]\s+(.+)$"):
        match = re.match(pattern, text)
        if match:
            return int(match.group(1)), match.group(2).strip()
    return None


def split_authors(raw):
    return [re.sub(r"\s+", " ", part.strip()) for part in raw.strip().rstrip(".").split(",") if part.strip()]


def endnote_author(author):
    parts = author.split()
    if len(parts) >= 2 and "," not in author:
        return f"{parts[0]}, {' '.join(parts[1:])}"
    return author


def author_surname(author):
    return author.split()[0].strip(",") if author else "Unknown"


def full_journal_name(journal):
    journal = journal.rstrip(".")
    return FULL_JOURNAL_NAMES.get(journal, journal)


def parse_reference(ref_text):
    text = re.sub(r"\s+", " ", ref_text).strip().replace("..", ".")
    doi_match = re.search(r"https?://doi\.org/([^\s]+)", text, flags=re.I)
    doi = doi_match.group(1).rstrip(".") if doi_match else ""
    before_doi = text[: doi_match.start()].strip() if doi_match else text
    before_doi = before_doi.rstrip(". ")

    year_match = re.search(r"\b((?:19|20)\d{2})\b", before_doi)
    year = year_match.group(1) if year_match else ""
    before_year = before_doi[: year_match.start()].strip(" .") if year_match else before_doi
    after_year = before_doi[year_match.end() :].strip(" .") if year_match else ""

    parts = [p.strip(" .") for p in re.split(r"\.\s+", before_year) if p.strip(" .")]
    authors_raw = parts[0] if parts else ""
    title = ""
    journal = ""
    if len(parts) >= 3:
        title = ". ".join(parts[1:-1]).strip(" .")
        journal = parts[-1].strip(" .")
    elif len(parts) == 2:
        title = parts[1].strip(" .")

    volume = ""
    issue = ""
    pages = ""
    if after_year:
        if ";" in after_year:
            possible_journal, rest = after_year.split(";", 1)
            if possible_journal.strip(" ."):
                journal = possible_journal.strip(" .")
            rest = rest.strip(" .")
            page_match = re.match(r"([^:]+):(.+)", rest)
            if page_match:
                vol_issue = page_match.group(1).strip()
                pages = page_match.group(2).strip(" .")
                vi_match = re.match(r"([^()]+)\(([^()]+)\)$", vol_issue)
                if vi_match:
                    volume = vi_match.group(1).strip()
                    issue = vi_match.group(2).strip()
                else:
                    volume = vol_issue
            else:
                volume = rest
        else:
            journal = after_year.strip(" .")

    return {
        "authors": split_authors(authors_raw),
        "title": title,
        "journal": journal,
        "year": year,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "doi": doi,
        "raw": text,
    }


def read_references(root):
    body = root.find("w:body", NS)
    paragraphs = body.findall("w:p", NS)
    ref_index = find_references_start(paragraphs)
    if ref_index is None:
        raise RuntimeError("References heading not found")
    refs = {}
    current_number = None
    current_text = []
    for paragraph in paragraphs[ref_index + 1 :]:
        text = para_text(paragraph).strip()
        if not text:
            continue
        parsed = parse_numbered_reference(text)
        if parsed:
            if current_number is not None:
                refs[current_number] = parse_reference(" ".join(current_text))
            current_number, first_text = parsed
            current_text = [first_text]
        elif current_number is not None:
            current_text.append(text)
    if current_number is not None:
        refs[current_number] = parse_reference(" ".join(current_text))
    return refs


def expand_numbers(cite_text):
    numbers = []
    inside = cite_text.strip()[1:-1]
    for part in inside.split(","):
        part = part.strip()
        if "-" in part:
            start, end = [int(x.strip()) for x in part.split("-", 1)]
            numbers.extend(range(start, end + 1))
        elif part:
            numbers.append(int(part))
    return numbers


def temp_label(number, meta, record_base=None):
    surname = author_surname(meta["authors"][0]) if meta["authors"] else "Unknown"
    year = meta["year"] or "n.d."
    if record_base:
        return f"{surname}, {year} #{record_base + number - 1}"
    return f"{surname}, {year}"


def replace_citations(root, refs, record_base=None):
    cite_pattern = re.compile(r"\[(?:\d+(?:\s*[-,]\s*\d+)*)\]")
    replaced = 0
    for node in root.iter(W + "t"):
        text = node.text or ""
        if cite_pattern.search(text):
            def sub(match):
                labels = []
                for n in expand_numbers(match.group(0)):
                    if n in refs:
                        labels.append(temp_label(n, refs[n], record_base))
                return "{" + "; ".join(labels) + "}"
            node.text = cite_pattern.sub(sub, text)
            replaced += 1
    return replaced


def replace_split_citations(root, refs, record_base=None):
    cite_pattern = re.compile(r"\[(?:\d+(?:\s*[-,]\s*\d+)*)\]")
    replaced = 0
    for paragraph in root.findall(".//w:p", NS):
        text_nodes = [node for node in paragraph.iter(W + "t")]
        if len(text_nodes) < 2:
            continue
        combined = "".join(node.text or "" for node in text_nodes)
        if not cite_pattern.search(combined):
            continue

        def sub(match):
            labels = []
            for n in expand_numbers(match.group(0)):
                if n in refs:
                    labels.append(temp_label(n, refs[n], record_base))
            return "{" + "; ".join(labels) + "}"

        new_text = cite_pattern.sub(sub, combined)
        if new_text == combined:
            continue
        text_nodes[0].text = new_text
        for node in text_nodes[1:]:
            node.text = ""
        replaced += 1
    return replaced


def remove_reference_list(root):
    body = root.find("w:body", NS)
    paragraphs = body.findall("w:p", NS)
    ref_index = find_references_start(paragraphs)
    if ref_index is None:
        return 0
    removed = 0
    for paragraph in paragraphs[ref_index + 1 :]:
        body.remove(paragraph)
        removed += 1
    return removed


def write_docx(src, dest, root):
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/document.xml":
                zout.writestr(item, xml_bytes)
            else:
                zout.writestr(item, zin.read(item.filename))


def write_ris(path, refs, marker_prefix, no_doi=False):
    with Path(path).open("w", encoding="utf-8", newline="\r\n") as f:
        for number in sorted(refs):
            meta = refs[number]
            journal = full_journal_name(meta["journal"])
            f.write("TY  - JOUR\n")
            for author in meta["authors"]:
                f.write(f"AU  - {endnote_author(author)}\n")
            if meta["title"]:
                f.write(f"TI  - {meta['title']}\n")
            if journal:
                f.write(f"T2  - {journal}\nJO  - {journal}\n")
            if meta["year"]:
                f.write(f"PY  - {meta['year']}\n")
            if meta["volume"]:
                f.write(f"VL  - {meta['volume']}\n")
            if meta["issue"]:
                f.write(f"IS  - {meta['issue']}\n")
            if meta["pages"]:
                if "-" in meta["pages"]:
                    sp, ep = meta["pages"].split("-", 1)
                    f.write(f"SP  - {sp}\nEP  - {ep}\n")
                else:
                    f.write(f"SP  - {meta['pages']}\n")
            if meta["doi"] and not no_doi:
                f.write(f"DO  - {meta['doi']}\nUR  - https://doi.org/{meta['doi']}\n")
            f.write(f"N1  - {marker_prefix}_{number}\n")
            f.write("ER  - \n\n")


def write_mapping(path, refs):
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["number", "title", "journal", "year", "doi", "raw"])
        for number in sorted(refs):
            meta = refs[number]
            writer.writerow([number, meta["title"], full_journal_name(meta["journal"]), meta["year"], meta["doi"], meta["raw"]])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("docx")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--record-base", type=int)
    parser.add_argument("--ris", action="store_true")
    parser.add_argument("--no-doi", action="store_true")
    parser.add_argument("--marker-prefix", default="CLEAN_ENDNOTE_IMPORT_ORIGINAL_REF")
    args = parser.parse_args()

    docx = Path(args.docx)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(docx, "r") as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    refs = read_references(root)
    if not refs:
        raise RuntimeError("No numbered references parsed")

    map_path = outdir / "endnote_reference_mapping.csv"
    write_mapping(map_path, refs)
    if args.ris:
        ris_path = outdir / "endnote_clean_import.ris"
        write_ris(ris_path, refs, args.marker_prefix, no_doi=args.no_doi)
        print(f"ris={ris_path}")

    temp_root = deepcopy(root)
    replaced = replace_citations(temp_root, refs, args.record_base)
    replaced += replace_split_citations(temp_root, refs, args.record_base)
    removed = remove_reference_list(temp_root)
    suffix = "EndNote_record_number_citations" if args.record_base else "EndNote_temp_citations"
    out_docx = outdir / f"{docx.stem}_{suffix}.docx"
    write_docx(docx, out_docx, temp_root)
    print(f"references={len(refs)}")
    print(f"citations_replaced={replaced}")
    print(f"reference_paragraphs_removed={removed}")
    print(f"docx={out_docx}")
    print(f"mapping={map_path}")


if __name__ == "__main__":
    main()
