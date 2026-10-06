import json, re, sys
import pdfplumber

PDF = sys.argv[1]
OUT_MD = sys.argv[2]
OUT_JSON = sys.argv[3]

def join_lines(s):
    parts = [p.strip() for p in s.split("\n") if p.strip()]
    out = ""
    for p in parts:
        if out.endswith("-"):
            out += p
        else:
            out += (" " if out else "") + p
    return out

def bullets(s):
    items = [b for b in s.split("►")]
    res = []
    for b in items:
        t = join_lines(b)
        if t:
            res.append(t)
    return res

faults, notes = [], []
with pdfplumber.open(PDF) as pdf:
    for i in range(84, 88):
        for tb in pdf.pages[i].extract_tables():
            for row in tb:
                if not row or not row[0] or row[0] in ("Storingscode", "Notificatie"):
                    continue
                code = join_lines(row[0]).replace(" t/m ", "-")
                desc = join_lines(row[1] or "")
                sol = bullets(row[2] or "")
                entry = {"code": code, "description": desc, "cause_solution": sol}
                m = re.fullmatch(r"n(\d{3})-n(\d{3})", code)
                if m:
                    entry["range"] = [int(m.group(1)), int(m.group(2))]
                (faults if code.startswith("F") else notes).append(entry)

data = {
    "source": {
        "document": "Intergas Xtend Eco installatievoorschrift, artikelnummer 88104401",
        "url": "https://www.intergas-verwarming.nl/app/uploads/2026/06/88104401-Xtend-Eco-installatievoorschrift.pdf",
        "chapters": "12.1 Storingscodes (pagina 85) en 12.2 Notificatiecodes (pagina 86-88)",
        "extracted": "2026-10-06",
        "language": "nl",
    },
    "fault_codes": faults,
    "notification_codes": notes,
}
json.dump(data, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def table(rows):
    lines = ["| Code | Omschrijving | Mogelijke oorzaak / oplossing |", "|---|---|---|"]
    for r in rows:
        sol = "<br>".join(r["cause_solution"]).replace("|", "\|")
        lines.append(f"| {r['code']} | {r['description']} | {sol} |")
    return "\n".join(lines)

md = f"""# Intergas Xtend fout- en notificatiecodes

Bron: {data['source']['document']}, {data['source']['chapters']}.
URL: {data['source']['url']}
Tekst letterlijk overgenomen op {data['source']['extracted']}, inclusief schrijfwijze uit het document.
Machineleesbare versie: `docs/fault-codes.json`.

Toepassing in de integratie:

- Storingscodes (F) horen bij veld `7e2c` (lockout code).
- Notificatiecodes (n) horen bij veld `7940` (notification code).
- Veld `8439` bevat de OpenTherm-foutcode van de CV-ketel zelf. Die codes staan niet in dit document.

## 12.1 Storingscodes

Als het systeem zich in een lockout bevindt, zal de warmtevraag automatisch worden doorgestuurd naar de CV-ketel. Deze zal de warmtevraag beantwoorden. Ga naar het wifibedieningsscherm om de foutcode af te lezen. Gebruik de resetknop in het wifibedieningsscherm of houd de knop op het toestel 8 seconden vast om het toestel te resetten.

{table(faults)}

## 12.2 Notificatiecodes

Naast storingscodes kan de regelunit ook notificaties weergeven. Notificaties worden getoond als er zich ergens in het systeem een afwijking voordoet die niet van invloed is op de vitale werking van het systeem. Notificaties verdwijnen als het systeem de afwijking kan herstellen. Bij herhaaldelijk terugkeren van een notificatie dient Intergas Verwarming geraadpleegd te worden.

In geval er gebruik gemaakt wordt van een kamerthermostaat die geen of beperkte notificatiemeldingen kan weergeven, zullen notificaties van de CV-ketel of warmtepomp als één van de volgende codes op de thermostaat worden weergegeven: F050 = Storing in de buitenunit of F051 = Storing in de CV-ketel.

{table(notes)}
"""
open(OUT_MD, "w", encoding="utf-8").write(md)
print(len(faults), "fault codes,", len(notes), "notification codes")
