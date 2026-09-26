#!/usr/bin/env python3
"""Extract immutable publisher XLSX phenotype cells without numeric conversion.

All worksheet rows are parsed for structure. GO GSEA content is not exported or
assessed. Numeric cells retain their literal OOXML <v> character strings.
"""
import csv
import hashlib
import json
import posixpath
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

BASE = Path(__file__).resolve().parents[1]
WORK = BASE.parents[1] / "work" / "ddr_target_bridge_stage0"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def colnum(ref):
    n = 0
    for c in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(c) - 64
    return n


def colname(n):
    result = ""
    while n:
        n, r = divmod(n - 1, 26)
        result = chr(65 + r) + result
    return result


def cell_text(cell, strings):
    kind = cell.get("t")
    value = cell.find(S + "v")
    value = value.text or "" if value is not None else ""
    if kind == "s":
        return strings[int(value)]
    if kind == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(S + "t"))
    return value


def rows(archive, part):
    with archive.open(part) as stream:
        for _, item in ET.iterparse(stream, events=("end",)):
            if item.tag == S + "row":
                yield item
                item.clear()


def row_values(row, strings, width):
    values = [""] * width
    for cell in row:
        if cell.tag == S + "c":
            values[colnum(cell.get("r")) - 1] = cell_text(cell, strings)
    return values


def record_digest(digest, row):
    digest.update(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode())
    digest.update(b"\n")


def inspect_sheet(archive, part, sheet, strings):
    result = {
        "name": sheet.get("name"), "sheet_id": sheet.get("sheetId"),
        "visibility": sheet.get("state", "visible"), "part": part,
        "declared_dimension": None, "merged_ranges": [], "raw_header_rows": {},
        "xml_row_records": 0, "nonempty_row_records": 0, "max_row": 0,
        "max_column": 0, "cell_count": 0, "nonempty_cells": 0,
        "cell_type_counts": {}, "formula_cells": [], "error_cells": [],
        "hidden_row_numbers": [], "hidden_column_ranges": [],
        "sheet_dependency_elements": [], "readme_text": [],
    }
    types = Counter()
    dependency_tags = {"drawing", "legacyDrawing", "legacyDrawingHF", "oleObjects",
                       "controls", "tableParts", "externalReferences", "hyperlinks"}
    with archive.open(part) as stream:
        for _, item in ET.iterparse(stream, events=("end",)):
            tag = item.tag.rsplit("}", 1)[-1]
            if tag == "dimension":
                result["declared_dimension"] = item.get("ref")
            elif tag == "mergeCell":
                result["merged_ranges"].append(item.get("ref"))
            elif tag == "col" and item.get("hidden") == "1":
                result["hidden_column_ranges"].append(dict(item.attrib))
            elif tag in dependency_tags:
                result["sheet_dependency_elements"].append(ET.tostring(item, encoding="unicode"))
            elif tag == "row":
                rownum = int(item.get("r"))
                result["xml_row_records"] += 1
                result["max_row"] = max(result["max_row"], rownum)
                if item.get("hidden") == "1":
                    result["hidden_row_numbers"].append(rownum)
                populated = {}
                for cell in item:
                    if cell.tag != S + "c":
                        continue
                    ref = cell.get("r")
                    value = cell_text(cell, strings)
                    result["cell_count"] += 1
                    result["max_column"] = max(result["max_column"], colnum(ref))
                    types[cell.get("t", "numeric_or_blank")] += 1
                    if value != "":
                        result["nonempty_cells"] += 1
                        populated[ref] = value
                    formula = cell.find(S + "f")
                    if formula is not None:
                        result["formula_cells"].append({"cell": ref, "formula": formula.text,
                                                        "attributes": dict(formula.attrib),
                                                        "cached_lexical_value": value})
                    if cell.get("t") == "e":
                        result["error_cells"].append({"cell": ref, "value": value})
                result["nonempty_row_records"] += bool(populated)
                if rownum <= 3:
                    result["raw_header_rows"][str(rownum)] = populated
                if sheet.get("name") == "Readme":
                    result["readme_text"].append({"excel_row": rownum, "cells": populated})
                item.clear()
    result["cell_type_counts"] = dict(types)
    result["observed_cell_rectangle"] = f"A1:{colname(result['max_column'])}{result['max_row']}"
    result["data_start_row"] = 4 if sheet.get("name") != "Readme" else None
    result["data_row_count"] = result["xml_row_records"] - sum(
        1 for key in result["raw_header_rows"] if int(key) < 4
    ) if sheet.get("name") != "Readme" else None
    result["assessment"] = ("structure_only_no_enrichment_or_ranking_assessment"
                            if sheet.get("name") == "GO GSEA Analysis" else "resource_schema")
    return result


def column_mapping(resource, info):
    raw = info["raw_header_rows"]
    groups = {}
    for merged in info["merged_ranges"]:
        start, end = merged.split(":")
        if start.endswith("1") and end.endswith("1"):
            label = raw["1"].get(start, "")
            for number in range(colnum(start), colnum(end) + 1):
                groups[number] = label
    result = []
    for number in range(1, info["max_column"] + 1):
        col = colname(number)
        group = groups.get(number, raw.get("1", {}).get(col + "1", ""))
        field = raw.get("2", {}).get(col + "2", "")
        identifier = raw.get("3", {}).get(col + "3", "")
        name = f"{group}|{field}" if group else identifier or "__original_index"
        result.append({"excel_column_number": number, "excel_column": col,
                       "raw_row1": raw.get("1", {}).get(col + "1", ""),
                       "raw_row2": field, "raw_row3": identifier,
                       "merged_group": group, "output_field": name})
    names = [r["output_field"] for r in result]
    assert len(names) == len(set(names)), (resource, "duplicate output headers")
    return result


def extract(resource, filename):
    path = BASE / "raw" / filename
    output = WORK / f"{resource}_phenotypes.csv"
    result = {"resource_id": resource, "filename": filename, "bytes": path.stat().st_size,
              "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "numeric_extraction": "literal OOXML <v> strings; no float conversion or rounding",
              "sheets": [], "relationships": [], "external_relationships": [], "notices": []}
    with ZipFile(path) as archive:
        result["zip_integrity_bad_member"] = archive.testzip()
        result["zip_parts"] = archive.namelist()
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(t.text or "" for t in entry.iter(S + "t"))
                       for entry in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        result["shared_strings_count"] = len(strings)
        for part in archive.namelist():
            if part.endswith(".rels"):
                for relationship in ET.fromstring(archive.read(part)):
                    entry = {"part": part, **relationship.attrib}
                    result["relationships"].append(entry)
                    if relationship.get("TargetMode") == "External":
                        result["external_relationships"].append(entry)
        result["potential_object_dependency_parts"] = [
            p for p in archive.namelist() if any(t in p.lower() for t in
                ["externallinks/", "embeddings/", "connections", "querytables/", "pivot", "vbaproject", "drawings/"])
        ]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        result["workbook_defined_names"] = [dict(x.attrib, text=x.text or "")
                                             for x in workbook.iter(S + "definedName")]
        result["workbook_absolute_path_notices"] = [dict(x.attrib) for x in workbook.iter()
                                                     if x.tag.rsplit("}", 1)[-1] == "absPath"]
        relationships = {x["Id"]: x["Target"] for x in result["relationships"]
                         if x["part"] == "xl/_rels/workbook.xml.rels"}
        for sheet in workbook.find(S + "sheets"):
            target = relationships[sheet.get(R + "id")]
            part = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            info = inspect_sheet(archive, part, sheet, strings)
            if sheet.get("name") == "Gene Level Phenotypes":
                mapping = column_mapping(resource, info)
                info["column_mapping"] = mapping
                digest = hashlib.sha256()
                count = 0
                with output.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(["__excel_row"] + [m["output_field"] for m in mapping])
                    for row in rows(archive, part):
                        if int(row.get("r")) < 4:
                            continue
                        values = [row.get("r")] + row_values(row, strings, info["max_column"])
                        writer.writerow(values)
                        record_digest(digest, values)
                        count += 1
                verify = hashlib.sha256()
                verify_count = 0
                with output.open(newline="", encoding="utf-8") as handle:
                    reader = csv.reader(handle)
                    next(reader)
                    for values in reader:
                        record_digest(verify, values)
                        verify_count += 1
                assert count == verify_count == info["data_row_count"]
                assert digest.hexdigest() == verify.hexdigest()
                info["extraction"] = {"path": str(output), "data_rows": count,
                                      "columns_including_excel_row": info["max_column"] + 1,
                                      "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                                      "all_cells_csv_roundtrip_lexical_digest": digest.hexdigest(),
                                      "all_cells_csv_roundtrip_verified": True}
            result["sheets"].append(info)
        result["notices"].append("GO GSEA Analysis sheet parsed for structure only; no enrichment values or ranks assessed or exported.")
        result["notices"].append("Workbook absPath records an author save location; it is not an external relationship or required score dependency.")
        if resource == "R2":
            result["notices"].append("Excel column A is an unnamed original row key; each contrast has its own target and transcript columns, which are preserved separately.")
            result["notices"].append("Header row3 is absent from sheet XML. Data start at row4. Missing/blank cells remain empty strings.")
        else:
            result["notices"].append("Identifier headers sgID_AB,target,transcript are on row3. All WT/parent and PRDX1KO contrast groups remain separate.")
        result["dependency_assessment"] = "No external relationships or object-dependency parts found; extracted scores are stored as values." if (
            not result["external_relationships"] and not result["potential_object_dependency_parts"]
            and all(not s["formula_cells"] for s in result["sheets"])) else "Review recorded dependencies/formulas."
    return result


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    records = [extract("R2", "DDRi_Dataset1_v2.xlsx"), extract("R3", "DDRi_Dataset3_v3.xlsx")]
    destination = BASE / "provenance" / "xlsx_structure.json"
    destination.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({r["resource_id"]: [{"sheet": s["name"], "rows": s["xml_row_records"],
                                         "data_rows": s["data_row_count"], "dimension": s["declared_dimension"]}
                                        for s in r["sheets"]] for r in records}, indent=2))


def identity_structure():
    """Count existing labels and identity keys; do not infer hits or score effects."""
    result = {}
    for resource in ("R2", "R3"):
        with (WORK / f"{resource}_phenotypes.csv").open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            data = list(reader)
        core = "rho:DNAPKi_vs_DMSO" if resource == "R2" else "parent::rho:DNAPKi_vs_vehicle"
        target = core + "|target" if resource == "R2" else "target"
        transcript = core + "|transcript" if resource == "R2" else "transcript"
        ids = ["__original_index"] if resource == "R2" else ["sgID_AB", "target", "transcript"]
        labels = [f for f in fields if f.endswith("|label")]
        genes = [r for r in data if r[target] not in ("", "negative_control")]
        gene_counts = Counter(r[target] for r in genes)
        gene_transcript_counts = Counter((r[target], r[transcript]) for r in genes)
        examples = {}
        for label_field in labels:
            group = label_field.rsplit("|", 1)[0]
            relevant = ["__excel_row"] + ids + ([group + "|target", group + "|transcript"]
                                               if resource == "R2" else []) + [label_field]
            examples[label_field] = {}
            for row in data:
                label = row[label_field]
                if label in ("", "negative_control") and len(examples[label_field].setdefault(label, [])) < 3:
                    examples[label_field][label].append({k: row[k] for k in relevant})
        result[resource] = {
            "assessment": "Publisher label inventory and identity structure only; no effect calculation or hit recovery.",
            "label_counts": {f: dict(Counter(r[f] for r in data)) for f in labels},
            "last10_identity_rows": [{k: r[k] for k in ["__excel_row"] + ids} for r in data[-10:]],
            "negative_control_and_blank_label_identity_examples": examples,
            "core_identity_counts": {
                "total_rows": len(data), "gene_rows": len(genes),
                "negative_control_rows": sum(r[target] == "negative_control" for r in data),
                "unique_gene_strings": len(gene_counts),
                "duplicate_gene_string_keys": sum(v > 1 for v in gene_counts.values()),
                "duplicate_gene_transcript_keys": sum(v > 1 for v in gene_transcript_counts.values()),
                "gene_rows_with_blank_core_score": sum(r[core + "|score"] == "" for r in genes),
                "gene_rows_with_nonblank_core_score": sum(r[core + "|score"] != "" for r in genes),
            },
        }
    (BASE / "provenance" / "identity_label_structure.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
    identity_structure()
