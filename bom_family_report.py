"""bom_family_report.py — Nomenclature (BOM) regroupee par famille.

Lit soit le netlist XML generique produit par Eeschema (mecanisme
"Generer Liste du Materiel Ancienne (BOM)"), soit un CSV exporte via
`kicad-cli sch export bom` — detection automatique du format a la
lecture, aucune option a changer. Produit un rapport texte style
Design Spark, les composants regroupes par famille (Resistances,
Inductances/Transformateurs, Condensateurs, Circuits integres,
Connecteurs, Transistors, Diodes), tries par repere a l'interieur de
chaque famille.

Pourquoi deux formats : le mecanisme "BOM Ancienne" (netlist XML +
script externe) est annonce pour suppression par les mainteneurs KiCad
une fois l'exporteur CSV de `kicad-cli` juge suffisant (cf. discussion
forum KiCad "kicad8 scripted BOM from Schematic"). Le jour ou ce menu
disparait d'Eeschema, ce script continue de fonctionner tel quel via :
    kicad-cli sch export bom -o bom.csv ... && python bom_family_report.py bom.csv rapport.txt

Aucune dependance externe (pas de pandas) : CSV lu avec le module
`csv` standard, XML lu avec `kicad_netlist_reader` fourni par
l'installation KiCad (ajoute a sys.path si besoin).

    @package
    Output: Texte (style Design Spark), regroupe par famille
    (Resistances, Inductances/Transformateurs, Condensateurs, Circuits
    integres, Connecteurs, Transistors, Diodes)
    Sorted By: Ref, a l'interieur de chaque famille
    Fields: Ref, Value, Footprint, Qty
    Accepte en entree un netlist XML (Eeschema) ou un CSV (kicad-cli)

    Command line:
    python "pathToFile/bom_family_report.py" "%I" "%O.txt"
"""

import csv
import datetime
import re
import sys
from pathlib import Path

_KICAD_PLUGINS_DIR = Path(r"C:\Program Files\KiCad\10.0\bin\scripting\plugins")
if str(_KICAD_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_KICAD_PLUGINS_DIR))


FAMILY_BY_PREFIX = {
    'R': 'Résistances', 'TH': 'Résistances',
    'L': 'Inductances / Transformateurs', 'T': 'Inductances / Transformateurs',
    'C': 'Condensateurs',
    'U': 'Circuits intégrés', 'REG': 'Circuits intégrés',
    'Q': 'Transistors',
    'D': 'Diodes',
}
CONNECTOR_PREFIXES = {'BIAS', 'CPUIN', 'CPUOUT', 'IN', 'J', 'OUT'}
FAMILY_ORDER = [
    'Résistances', 'Inductances / Transformateurs', 'Condensateurs',
    'Circuits intégrés', 'Connecteurs', 'Transistors', 'Diodes', 'Autres',
]


def get_prefix(ref):
    match = re.match(r"([A-Za-z#]+)", str(ref))
    return match.group(1).upper() if match else "AUTRE"


def get_family(prefix):
    if prefix in CONNECTOR_PREFIXES:
        return 'Connecteurs'
    return FAMILY_BY_PREFIX.get(prefix, 'Autres')


def sort_key(ref):
    m = re.match(r"([A-Za-z#]+)(\d+)?", str(ref))
    if not m:
        return (str(ref), 0)
    prefix, num = m.group(1), m.group(2)
    return (prefix, int(num) if num else 0)


def is_xml_netlist(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        head = f.read(256).lstrip()
    return head.startswith('<?xml') or head.startswith('<export')


def read_rows_from_xml(netlist_path):
    """Lit le netlist generique Eeschema -- regroupe par (Value, Footprint)
    via kicad_netlist_reader, comme le ferait le dialogue BOM natif."""
    import kicad_netlist_reader

    net = kicad_netlist_reader.netlist(netlist_path)
    components = net.getInterestingComponents(excludeBOM=True)
    grouped = net.groupComponents(components)

    rows = []
    meta = {
        'source': net.getSource(),
        'date': net.getDate(),
        'tool': net.getTool(),
    }
    for group in grouped:
        refs = sorted((c.getRef() for c in group), key=sort_key)
        c = group[0]
        rows.append({
            'Reference': ",".join(refs),
            'Value': c.getValue(),
            'Footprint': c.getFootprint(),
            'Qty': len(group),
        })
    return rows, meta


def read_rows_from_csv(csv_path):
    """Lit un CSV exporte via `kicad-cli sch export bom` -- deja groupe
    si --group-by a ete utilise a l'export, sinon une ligne par repere."""
    rows = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'Reference': row.get('Reference', row.get('Refs', '')),
                'Value': row.get('Value', ''),
                'Footprint': row.get('Footprint', ''),
                'Qty': int(row.get('Qty', row.get('QUANTITY', 1)) or 1),
            })
    meta = {'source': csv_path, 'date': '', 'tool': 'kicad-cli (CSV)'}
    return rows, meta


def generate_report(input_path, output_txt_path):
    if is_xml_netlist(input_path):
        rows, meta = read_rows_from_xml(input_path)
    else:
        rows, meta = read_rows_from_csv(input_path)

    for r in rows:
        r['Prefix'] = get_prefix(r['Reference'].split(",")[0])
        r['Family'] = get_family(r['Prefix'])

    rows.sort(key=lambda r: sort_key(r['Reference'].split(",")[0]))

    total_components = sum(r['Qty'] for r in rows)
    unique_components = len(rows)
    stats_by_type = {}
    for r in rows:
        stats_by_type[r['Prefix']] = stats_by_type.get(r['Prefix'], 0) + r['Qty']

    now = datetime.datetime.now().strftime("%A, %B %d, %Y")
    report = []
    report.append("Bill of Materials")
    report.append("-----------------\n")
    report.append(f"Report Written: {now}")
    report.append(f"Project Path:   {meta['source']}")
    report.append("Design Title:   KICAD-C2000-powershield")
    if meta['date']:
        report.append(f"Netlist Date:   {meta['date']}")
    report.append(f"Source Tool:    {meta['tool']}")
    report.append("Units:          mm (precision 2)\n")

    report.append("--- STATISTIQUES GLOBALES DE LA CARTE ---")
    report.append(f"  * Références / Lignes uniques : {unique_components}")
    report.append(f"  * Nombre total de composants : {total_components}")
    report.append("  * Ventilation par préfixe :")
    for pref, qty in sorted(stats_by_type.items()):
        report.append(f"    - Type [{pref}] : {qty} unité(s)")
    report.append("------------------------------------------\n")

    ref_w, val_w, fp_w, qty_w = 38, 16, 48, 5
    header = f"{'Reference':<{ref_w}} {'Value':<{val_w}} {'Footprint':<{fp_w}} {'Qty':<{qty_w}}"
    sep = "-" * (ref_w + val_w + fp_w + qty_w + 3)

    for family in FAMILY_ORDER:
        group_rows = [r for r in rows if r['Family'] == family]
        if not group_rows:
            continue
        family_qty = sum(r['Qty'] for r in group_rows)
        report.append(f"=== {family} ({family_qty} unité(s), {len(group_rows)} référence(s)) ===")
        report.append(header)
        report.append(sep)
        for r in group_rows:
            report.append(
                f"{r['Reference']:<{ref_w}} {r['Value']:<{val_w}} {r['Footprint']:<{fp_w}} {r['Qty']:<{qty_w}}"
            )
        report.append(sep)
        report.append("")

    report.append(f"{'TOTAL':<{ref_w + val_w + fp_w + 1}} {total_components}")

    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))

    print(f"BOM avec statistiques générée avec succès : {output_txt_path}")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        # appel KiCad (legacy BOM: netlist XML) ou manuel (CSV kicad-cli)
        generate_report(sys.argv[1], sys.argv[2])
    else:
        sys.exit(
            "Usage: python bom_family_report.py <netlist.xml | bom.csv> <sortie.txt>\n"
            "  - netlist.xml : fourni automatiquement par Eeschema (BOM Ancienne)\n"
            "  - bom.csv     : genere via `kicad-cli sch export bom -o bom.csv ...`"
        )
