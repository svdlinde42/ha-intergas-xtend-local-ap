"""Fault (F) and notification (n) code tables of the Intergas Xtend.

Source: docs/fault-codes.json, generated from Intergas document 88104401
chapter 12.1 and 12.2. Regenerate, do not edit by hand:

    python -I -X utf8 scripts/gen_codes_py.py docs/fault-codes.json \
        custom_components/intergas_xtend/codes.py

The Dutch text is quoted verbatim from the manual and shown as sensor
attributes; it must not be paraphrased or translated. Fault codes belong to
stats field 7e2c (lockout code), notification codes to field 7940. Field 8439
holds the CV boiler's own OpenTherm code and is not covered here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CodeInfo:
    """The manual's description of one code and its cause/solution items."""

    description: str
    cause_solution: tuple[str, ...]


# Source: docs/fault-codes.json, generated from Intergas document 88104401
# chapter 12.1 and 12.2. Regenerate, do not edit by hand.
FAULT_CODES: dict[str, CodeInfo] = {
    "F001": CodeInfo(
        description="Tenminste 30 minuten geen doorstroming in het CV-circuit.",
        cause_solution=(
            "Controleer de CV pomp.",
            "Controleer het systeem op lekkages.",
            "Controleer de waterdruk in het systeem.",
        ),
    ),
    "F003": CodeInfo(
        description="Condensor temperatuur warmtepomp te hoog.",
        cause_solution=("Controleer de doorstroming in het systeem.",),
    ),
    "F009": CodeInfo(
        description="Geheugenfout storingscodes.",
        cause_solution=(
            "Reset de regelunit.",
            "Vervang de regelunit.",
        ),
    ),
    "F010": CodeInfo(
        description="Watertemperatuur tijdens ontdooifunctie te laag.",
        cause_solution=(
            "CV doorstroming te laag. Controleer doorstroming in het systeem.",
        ),
    ),
    "F018": CodeInfo(
        description="Warmtepomptype niet goed geconfigureerd.",
        cause_solution=("Raadpleeg Intergas Verwarming BV.",),
    ),
    "F019": CodeInfo(
        description="Foutief serienummer in geheugenmodule.",
        cause_solution=("Raadpleeg Intergas Verwarming BV.",),
    ),
    "F020": CodeInfo(
        description="Foutieve software.",
        cause_solution=("Raadpleeg Intergas Verwarming BV.",),
    ),
    "F022": CodeInfo(
        description="Softwareversie niet compatibel",
        cause_solution=(
            "Software vereist een update",
            "Raadpleeg Intergas Verwarming BV.",
        ),
    ),
    "F023": CodeInfo(
        description="XTP controller interne fout",
        cause_solution=("Raadpleeg Intergas Verwarming BV.",),
    ),
    "F024": CodeInfo(
        description="XTP controller configuratiefout",
        cause_solution=("Raadpleeg Intergas Verwarming BV.",),
    ),
    "F025": CodeInfo(
        description="XTP controller communicatiefout",
        cause_solution=("Raadpleeg Intergas Verwarming BV.",),
    ),
    "F026": CodeInfo(
        description="Opstartfout",
        cause_solution=(
            "Trek de stekker voor 1 minuut uit de wandcontactdoos.",
            "Vervang de regelunit.",
        ),
    ),
    "F037": CodeInfo(
        description="Sensorfout retourleiding T04.",
        cause_solution=(
            "Controleer de bedrading van sensor T04 op breuk/sluiting.",
            "Controleer of sensor T04 juist aangesloten is.",
            "Vervang sensor T04.",
        ),
    ),
    "F038": CodeInfo(
        description="Sensorfout aanvoerleiding T03.",
        cause_solution=(
            "Controleer de bedrading van sensor T03 op breuk/sluiting.",
            "Controleer of sensor T03 juist aangesloten is.",
            "Vervang sensor T03.",
        ),
    ),
    "F039": CodeInfo(
        description="Sensorfout externe systeem aanvoertemperatuursensor T43.",
        cause_solution=(
            "Controleer bedrading sensor T43 op breuk/sluiting.",
            "Controleer of sensor T43 juist aangesloten is.",
            "Vervang sensor T43.",
        ),
    ),
    "F040": CodeInfo(
        description="Sensorfout externe buitenvoeler T42.",
        cause_solution=(
            "Controleer bedrading buitenvoeler T42 op breuk/sluiting.",
            "Controleer of buitenvoeler T42 juist aangesloten is.",
            "Vervang buitenvoeler T42.",
        ),
    ),
    "F050": CodeInfo(
        description="Storing in de buitenunit.",
        cause_solution=(
            "Raadpleeg het wifibedieningsscherm voor aanvullende informatie.",
        ),
    ),
    "F051": CodeInfo(
        description="Storing in de CV-ketel.",
        cause_solution=(
            "Raadpleeg het wifibedieningsscherm voor aanvullende informatie.",
        ),
    ),
    "F254": CodeInfo(
        description="Bypassmodus actief.",
        cause_solution=(
            "Geen echte fout, maar een geforceerde manier om de warmtevraag door te sturen naar de CV-ketel, zodat de warmtepomp niet in bedrijf komt.",
            "Houd de bedieningsknop ingedrukt en stop de stekker van de binnenunit in de wandcontactdoos om dit te forceren.",
        ),
    ),
}

NOTIFICATION_CODES: dict[str, CodeInfo] = {
    "n000": CodeInfo(
        description="Parameter instellingen buiten bereik.",
        cause_solution=("Controleer de instellingen.",),
    ),
    "n001": CodeInfo(
        description="Waterdruk te laag, parameter P020.",
        cause_solution=(
            "Controleer op lekkages.",
            "Vul het systeem bij.",
        ),
    ),
    "n002": CodeInfo(
        description="Geen waterdruk.",
        cause_solution=(
            "Controleer op lekkages.",
            "Vul het systeem bij.",
        ),
    ),
    "n007": CodeInfo(
        description="Probleem met MODBUS adressen.",
        cause_solution=(
            "Check de DIP switch settings in de ODU (Modbus slave adres 1 of 2)",
        ),
    ),
    "n008": CodeInfo(
        description="Beveiligingscircuit fout buitenunit.",
        cause_solution=(
            "Start Xtend opnieuw op.",
            "Raadpleeg Intergas Verwarming BV.",
        ),
    ),
    "n011": CodeInfo(
        description="Communicatie met buitenunit is weggevallen of de buitenunit heeft een interne fout.",
        cause_solution=(
            "Raadpleeg het wifibedieningsscherm voor aanvullende informatie.",
            "Controleer bedrading tussen binnenunit en buitenunit op breuk/ sluiting.",
            "Controleer de A en B aansluitingen van de communicatiekabel in de binnen- en buitenunit.",
        ),
    ),
    "n013": CodeInfo(
        description="Condensor temperatuur te hoog: warmtepomp uitgeschakeld.",
        cause_solution=(
            "Mogelijk te weinig doorstroming.",
            "Mogelijk de CV-ketel aanvoertemperatuur te hoog ingesteld.",
            "Systeem kan warmte moeilijk kwijt.",
        ),
    ),
    "n014": CodeInfo(
        description="Kamerthermostaat niet aangesloten.",
        cause_solution=("Sluit de Comfort Touch kamerthermostaat aan, zie §8.8.8.",),
    ),
    "n015": CodeInfo(
        description="Fout carterverwarmer in buitenunit.",
        cause_solution=(
            "Controleer de bekabeling carterverwarmer, vervang indien nodig.",
            "Controleer carterverwarmer, vervang indien nodig.",
        ),
    ),
    "n016": CodeInfo(
        description="Abnormale relatie tussen de retour- en aanvoerwaarden.",
        cause_solution=(
            "Controleer of de bekabeling van de retour-en aanvoersensor juist is aangesloten.",
            "Controleer de flow (mogelijke oorzaak is een externe pomp).",
        ),
    ),
    "n018": CodeInfo(
        description="Probleem met geheugen.",
        cause_solution=("Raadpleeg Intergas Verwarming BV.",),
    ),
    "n019": CodeInfo(
        description="Fout geheugenmodule.",
        cause_solution=(
            "Controleer de bekabeling.",
            "Vervang de geheugenmodule.",
        ),
    ),
    "n021": CodeInfo(
        description="Tenminste 30 seconden geen doorstroming in het CV circuit.",
        cause_solution=(
            "Ontluchtingsprogramma (max. 15 minuten) wordt gestart. Overige systeemfuncties worden geblokkeerd en na afloop van het programma hervat.",
            "Pomp gaat gedurende 60 seconden uit.",
            "Pomp gaat op maximaal vermogen draaien.",
            "Indien gedurende 30 seconden weer voldoende doorstroming wordt gemeten zal het programma stoppen en de notificatie verdwijnen.",
        ),
    ),
    "n022": CodeInfo(
        description="Probleem met automatische debietregeling.",
        cause_solution=("Mogelijk lucht in het systeem, ontlucht.",),
    ),
    "n023": CodeInfo(
        description="Te lage flow tijdens inbedrijfname.",
        cause_solution=("Controleer het CV-circuit op restricties.",),
    ),
    "n024": CodeInfo(
        description="Externe systeem aanvoertemperatuursensor T43 heeft een abnormale waarde.",
        cause_solution=(
            "Controleer de montage van de sensor om de buis.",
            "Controleer de aansluiting op de print.",
        ),
    ),
    "n026": CodeInfo(
        description="Klok niet ingesteld.",
        cause_solution=("Stel klok in.",),
    ),
    "n027": CodeInfo(
        description="Fout in de werking van de klok.",
        cause_solution=(
            "Mogelijk een hardwarefout.",
            "Raadpleeg Intergas Verwarming BV.",
        ),
    ),
    "n028": CodeInfo(
        description="Notificatiecode die ontstaat doordat de buitenunit regelmatig problemen ondervindt.",
        cause_solution=("Raadpleeg Intergas Verwarming BV.",),
    ),
    "n029": CodeInfo(
        description="Geen dauwpunt signaal beschikbaar (koeliing)",
        cause_solution=(
            "De Comfort touch thermostaat levert geen relatieve vochtigheidssignaal. Stel een andere modus in.",
        ),
    ),
    "n030": CodeInfo(
        description="Externe systeem aanvoertemperatuursensor T43 niet aangesloten.",
        cause_solution=(
            "Controleer in het wifibedieningsscherm: P066 = 4 (CV-ketel aansturing Aan/Uit), P123 = 1 (Ja), P123 = 3 (vrij instelbare relais uitgang).",
        ),
    ),
    "n032": CodeInfo(
        description="Ontdooien duurde te lang.",
        cause_solution=(
            "Mogelijk een koeltechnische fout .",
            "Mogelijk de buitenunit vol in de wind.",
        ),
    ),
    "n039": CodeInfo(
        description="Probleem met externe systeem aanvoertemperatuursensor T43.",
        cause_solution=(
            "Controleer de montage van de sensor op de aanvoerbuis.",
            "Controleer bedrading, vervang indien nodig.",
        ),
    ),
    "n040": CodeInfo(
        description="Probleem met externe buitentemperatuursensor T42.",
        cause_solution=("Controleer bedrading, vervang indien nodig.",),
    ),
    "n041": CodeInfo(
        description="Probleem met koudemiddel vloeistoftemperatuursensor.",
        cause_solution=("Controleer bedrading, vervang indien nodig.",),
    ),
    "n042": CodeInfo(
        description="Probleem met koudemiddel gastemperatuursensor.",
        cause_solution=("Controleer bedrading, vervang indien nodig.",),
    ),
    "n043": CodeInfo(
        description="Probleem met sensor 1 (Xtore) (X4, contacten 6 en 7).",
        cause_solution=(
            "Controleer bedrading.",
            "Controleer de sensor.",
        ),
    ),
    "n044": CodeInfo(
        description="Probleem met sensor 2 (Xtore)",
        cause_solution=(
            "Controleer bedrading.",
            "Controleer de sensor.",
        ),
    ),
    "n051": CodeInfo(
        description="CV-ketel in lockout.",
        cause_solution=("Controleer fout in CV-ketel.",),
    ),
    "n052": CodeInfo(
        description="Fout in OpenTherm verbinding met CV-ketel.",
        cause_solution=("Controleer bedrading, vervang indien nodig.",),
    ),
    "n053": CodeInfo(
        description="Aanvoertemperatuur van de CV-ketel staat te laag.",
        cause_solution=(
            "Stel de aanvoertemperatuur van de CV-ketel minimaal 10ºC hoger in als de maximale aanvoertemperatuur van de Xtend (P194)",
        ),
    ),
    "n054": CodeInfo(
        description="CV-ketel geeft geen reactie op warmtevraag vanuit Xtend.",
        cause_solution=("Controleer of de CV-ketel of cv-functie niet uit staat.",),
    ),
    "n055": CodeInfo(
        description="CV-ketel heeft een notificatie.",
        cause_solution=("Los de storing van de Intergas CV-ketel op.",),
    ),
    "n056": CodeInfo(
        description="CV-ketel maakt te warm water in CV-bedrijf.",
        cause_solution=(
            "Controleer de ingestelde aanvoertemperatuur van de CV-ketel.",
            "Controleer het ingestelde vermogen van de CV-ketel.",
        ),
    ),
    "n057": CodeInfo(
        description="Aanvoertemperatuur van de CV-ketel staat te laag.",
        cause_solution=(
            "Stel de aanvoertemperatuur van de CV-ketel minimaal op 75ºC om zeker te stellen dat het legionellapreventie programma uitgevoerd kan worden.",
        ),
    ),
    "n058": CodeInfo(
        description="Temperatuur van de tempearatuurbeveiligingssensor (CV) te hoog.",
        cause_solution=(
            "Controleer bedrading.",
            "Mogelijk probleem met de driewegklep.",
        ),
    ),
    "n060": CodeInfo(
        description="Software versie van thermostaat niet up to date, indien gebruik wordt gemaakt van de Intergas Comfort Touch thermostaat.",
        cause_solution=(
            "Plaats de nieuwste versie van de Intergas Comfort Touch Thermostaat.",
        ),
    ),
    "n070": CodeInfo(
        description="Warmtepomp fout (regeling binnenunit).",
        cause_solution=(
            "Raadpleeg het wifibedieningsscherm voor aanvullende informatie.",
            "Raadpleeg Intergas Verwarming BV.",
        ),
    ),
    "n071": CodeInfo(
        description="Debiet fout tijdens WP-bedrijf.",
        cause_solution=(
            "Raadpleeg het wifibedieningsscherm voor aanvullende informatie.",
            "Raadpleeg Intergas Verwarming BV.",
        ),
    ),
    "n072": CodeInfo(
        description="Debiet fout tijdens het ontdooien.",
        cause_solution=("Controleer de flow, ontlucht en vul eventueel water bij.",),
    ),
    "n073": CodeInfo(
        description="Koudemiddeltemperatuur te laag tijdens ontdooien.",
        cause_solution=(
            "Controleer het koudemiddelcircuit op lekkages.",
            "Mogelijk een koudemiddeltekort.",
        ),
    ),
    "n074": CodeInfo(
        description="Ontdooifunctie gestopt vanwege een te lage watertemperatuur.",
        cause_solution=(
            "Controleer de flow.",
            "Mogelijk te weinig buffer.",
        ),
    ),
    "n075": CodeInfo(
        description="Compressor start te vaak.",
        cause_solution=(
            "Controleer instellingen thermostaat etc.",
            "Controleer afgiftesysteem.",
        ),
    ),
    "n076": CodeInfo(
        description="Lucht recirculatie over verdamper gedetecteerd.",
        cause_solution=(
            "Te weinig ruimte rondom de Xtend.",
            "Door omkasting geen scheiding tussen luchtaanvoer en luchtafvoer.",
        ),
    ),
    "n077": CodeInfo(
        description="Warmtepomp zelftest gefaald.",
        cause_solution=(
            "Het systeem dient koudemiddelzijdig gecontroleerd te worden. Neem hiervoor contact op met Intergas Verwarming BV.",
        ),
    ),
    "n078": CodeInfo(
        description="Buitentemperatuursensor vastgevroren aan verdamper",
        cause_solution=(
            "Check of de buitentemperatuursensor vrij ligt van de verdamper.",
            "Check of er geen ijs aangevroren is tussen senor en verdamper.",
            "Zonodig de sensor ontdooien en iets wegbuigen van de verdamper.",
        ),
    ),
    "n080": CodeInfo(
        description="Probleem met de gebruikersinterface.",
        cause_solution=(
            "Strat Xtend opnieuw op.",
            "Raadpleeg Intergas Verwarming BV.",
        ),
    ),
    "n081": CodeInfo(
        description="Kalibratie fout van de aanvoersensor T03.",
        cause_solution=(
            "Controleer of de sensor goed contact maakt.",
            "Controleer de bedrading.",
            "Mogelijk defecte sensor, vervang indien nodig.",
        ),
    ),
    "n082": CodeInfo(
        description="Kalibratie fout van de externe systeem aanvoertemperatuur-sensor T43.",
        cause_solution=(
            "Controleer of de sensor goed contact maakt.",
            "Controleer de bedrading.",
            "Mogelijk defecte sensor.",
        ),
    ),
    "n085": CodeInfo(
        description="Buitenunit kan niet koelen.",
        cause_solution=(
            "Koelfunctie is niet beschikbaar en wordt automatisch gedeactiveerd.",
        ),
    ),
    "n086": CodeInfo(
        description="Afgiftesysteem is niet geschikt om te koelen.",
        cause_solution=(
            "Controleer parameter P200 deze moet op “vloerverwarming” staan.",
        ),
    ),
    "n090": CodeInfo(
        description="Warmwatervat temperatuursensor niet goed geconfigureerd.",
        cause_solution=("Controleer de instellingen.",),
    ),
    "n091": CodeInfo(
        description="Onlogische waarde van de warmwatervat temperatuursensor.",
        cause_solution=(
            "Controleer de bedrading.",
            "Mogelijk sensor kapot.",
        ),
    ),
    "n094": CodeInfo(
        description="Legionellapreventie programma mislukt (vanaf 3 pogingen).",
        cause_solution=(
            "Mogelijk te vaak onderbreking door tapwatervraag.",
            "Verplaats de dag of tijdstip van het legionellapreventie programma.",
        ),
    ),
    "n095": CodeInfo(
        description="Probleem met driewegklep.",
        cause_solution=(
            "Controleer de bedrading.",
            "Controleer de motor van de driewegklep.",
            "Controleer de behuizing van de driewegklep.",
            "Controleer parameter P047, P068 en P069.",
        ),
    ),
    "n096": CodeInfo(
        description="Geen temperatuurverhoging gemeten tijdens opwarming Xtore.",
        cause_solution=(
            "Controleer warmwatervat temperatuursensor.",
            "Controleer driewegklep.",
        ),
    ),
    "n097": CodeInfo(
        description="CV-ketel brandt bij tapwatervat opwarmen te kort.",
        cause_solution=("Controleer flow en CV-ketel instellingen.",),
    ),
}

# Notification codes that share one entry: (first, last, info), both
# ends included.
NOTIFICATION_RANGES: tuple[tuple[int, int, CodeInfo], ...] = (
    (
        100,
        165,
        CodeInfo(
            description="FOTA gerelateerde melding.",
            cause_solution=(
                "Neem contact op met Intergas. (FOTA = Firmware Over-The-Air)",
            ),
        ),
    ),
)


def fault_info(code: str) -> CodeInfo | None:
    """Return the manual's entry for a lockout code such as "F037", or None."""
    return FAULT_CODES.get(code)


def notification_info(code: str) -> CodeInfo | None:
    """Return the manual's entry for a notification code such as "n095", or None.

    Codes that are not listed one by one are looked up in NOTIFICATION_RANGES,
    e.g. n100 up to and including n165 share one FOTA entry.
    """
    if (info := NOTIFICATION_CODES.get(code)) is not None:
        return info
    if len(code) == 4 and code[0] == "n" and code[1:].isdigit():
        number = int(code[1:])
        for first, last, info in NOTIFICATION_RANGES:
            if first <= number <= last:
                return info
    return None
