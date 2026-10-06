# Intergas Xtend fout- en notificatiecodes

Bron: Intergas Xtend Eco installatievoorschrift, artikelnummer 88104401, 12.1 Storingscodes (pagina 85) en 12.2 Notificatiecodes (pagina 86-88).
URL: https://www.intergas-verwarming.nl/app/uploads/2026/06/88104401-Xtend-Eco-installatievoorschrift.pdf
Tekst letterlijk overgenomen op 2026-10-06, inclusief schrijfwijze uit het document.
Machineleesbare versie: `docs/fault-codes.json`.

Toepassing in de integratie:

- Storingscodes (F) horen bij veld `7e2c` (lockout code).
- Notificatiecodes (n) horen bij veld `7940` (notification code).
- Veld `8439` bevat de OpenTherm-foutcode van de CV-ketel zelf. Die codes staan niet in dit document.

## 12.1 Storingscodes

Als het systeem zich in een lockout bevindt, zal de warmtevraag automatisch worden doorgestuurd naar de CV-ketel. Deze zal de warmtevraag beantwoorden. Ga naar het wifibedieningsscherm om de foutcode af te lezen. Gebruik de resetknop in het wifibedieningsscherm of houd de knop op het toestel 8 seconden vast om het toestel te resetten.

| Code | Omschrijving | Mogelijke oorzaak / oplossing |
|---|---|---|
| F001 | Tenminste 30 minuten geen doorstroming in het CV-circuit. | Controleer de CV pomp.<br>Controleer het systeem op lekkages.<br>Controleer de waterdruk in het systeem. |
| F003 | Condensor temperatuur warmtepomp te hoog. | Controleer de doorstroming in het systeem. |
| F009 | Geheugenfout storingscodes. | Reset de regelunit.<br>Vervang de regelunit. |
| F010 | Watertemperatuur tijdens ontdooifunctie te laag. | CV doorstroming te laag. Controleer doorstroming in het systeem. |
| F018 | Warmtepomptype niet goed geconfigureerd. | Raadpleeg Intergas Verwarming BV. |
| F019 | Foutief serienummer in geheugenmodule. | Raadpleeg Intergas Verwarming BV. |
| F020 | Foutieve software. | Raadpleeg Intergas Verwarming BV. |
| F022 | Softwareversie niet compatibel | Software vereist een update<br>Raadpleeg Intergas Verwarming BV. |
| F023 | XTP controller interne fout | Raadpleeg Intergas Verwarming BV. |
| F024 | XTP controller configuratiefout | Raadpleeg Intergas Verwarming BV. |
| F025 | XTP controller communicatiefout | Raadpleeg Intergas Verwarming BV. |
| F026 | Opstartfout | Trek de stekker voor 1 minuut uit de wandcontactdoos.<br>Vervang de regelunit. |
| F037 | Sensorfout retourleiding T04. | Controleer de bedrading van sensor T04 op breuk/sluiting.<br>Controleer of sensor T04 juist aangesloten is.<br>Vervang sensor T04. |
| F038 | Sensorfout aanvoerleiding T03. | Controleer de bedrading van sensor T03 op breuk/sluiting.<br>Controleer of sensor T03 juist aangesloten is.<br>Vervang sensor T03. |
| F039 | Sensorfout externe systeem aanvoertemperatuursensor T43. | Controleer bedrading sensor T43 op breuk/sluiting.<br>Controleer of sensor T43 juist aangesloten is.<br>Vervang sensor T43. |
| F040 | Sensorfout externe buitenvoeler T42. | Controleer bedrading buitenvoeler T42 op breuk/sluiting.<br>Controleer of buitenvoeler T42 juist aangesloten is.<br>Vervang buitenvoeler T42. |
| F050 | Storing in de buitenunit. | Raadpleeg het wifibedieningsscherm voor aanvullende informatie. |
| F051 | Storing in de CV-ketel. | Raadpleeg het wifibedieningsscherm voor aanvullende informatie. |
| F254 | Bypassmodus actief. | Geen echte fout, maar een geforceerde manier om de warmtevraag door te sturen naar de CV-ketel, zodat de warmtepomp niet in bedrijf komt.<br>Houd de bedieningsknop ingedrukt en stop de stekker van de binnenunit in de wandcontactdoos om dit te forceren. |

## 12.2 Notificatiecodes

Naast storingscodes kan de regelunit ook notificaties weergeven. Notificaties worden getoond als er zich ergens in het systeem een afwijking voordoet die niet van invloed is op de vitale werking van het systeem. Notificaties verdwijnen als het systeem de afwijking kan herstellen. Bij herhaaldelijk terugkeren van een notificatie dient Intergas Verwarming geraadpleegd te worden.

In geval er gebruik gemaakt wordt van een kamerthermostaat die geen of beperkte notificatiemeldingen kan weergeven, zullen notificaties van de CV-ketel of warmtepomp als één van de volgende codes op de thermostaat worden weergegeven: F050 = Storing in de buitenunit of F051 = Storing in de CV-ketel.

| Code | Omschrijving | Mogelijke oorzaak / oplossing |
|---|---|---|
| n000 | Parameter instellingen buiten bereik. | Controleer de instellingen. |
| n001 | Waterdruk te laag, parameter P020. | Controleer op lekkages.<br>Vul het systeem bij. |
| n002 | Geen waterdruk. | Controleer op lekkages.<br>Vul het systeem bij. |
| n007 | Probleem met MODBUS adressen. | Check de DIP switch settings in de ODU (Modbus slave adres 1 of 2) |
| n008 | Beveiligingscircuit fout buitenunit. | Start Xtend opnieuw op.<br>Raadpleeg Intergas Verwarming BV. |
| n011 | Communicatie met buitenunit is weggevallen of de buitenunit heeft een interne fout. | Raadpleeg het wifibedieningsscherm voor aanvullende informatie.<br>Controleer bedrading tussen binnenunit en buitenunit op breuk/ sluiting.<br>Controleer de A en B aansluitingen van de communicatiekabel in de binnen- en buitenunit. |
| n013 | Condensor temperatuur te hoog: warmtepomp uitgeschakeld. | Mogelijk te weinig doorstroming.<br>Mogelijk de CV-ketel aanvoertemperatuur te hoog ingesteld.<br>Systeem kan warmte moeilijk kwijt. |
| n014 | Kamerthermostaat niet aangesloten. | Sluit de Comfort Touch kamerthermostaat aan, zie §8.8.8. |
| n015 | Fout carterverwarmer in buitenunit. | Controleer de bekabeling carterverwarmer, vervang indien nodig.<br>Controleer carterverwarmer, vervang indien nodig. |
| n016 | Abnormale relatie tussen de retour- en aanvoerwaarden. | Controleer of de bekabeling van de retour-en aanvoersensor juist is aangesloten.<br>Controleer de flow (mogelijke oorzaak is een externe pomp). |
| n018 | Probleem met geheugen. | Raadpleeg Intergas Verwarming BV. |
| n019 | Fout geheugenmodule. | Controleer de bekabeling.<br>Vervang de geheugenmodule. |
| n021 | Tenminste 30 seconden geen doorstroming in het CV circuit. | Ontluchtingsprogramma (max. 15 minuten) wordt gestart. Overige systeemfuncties worden geblokkeerd en na afloop van het programma hervat.<br>Pomp gaat gedurende 60 seconden uit.<br>Pomp gaat op maximaal vermogen draaien.<br>Indien gedurende 30 seconden weer voldoende doorstroming wordt gemeten zal het programma stoppen en de notificatie verdwijnen. |
| n022 | Probleem met automatische debietregeling. | Mogelijk lucht in het systeem, ontlucht. |
| n023 | Te lage flow tijdens inbedrijfname. | Controleer het CV-circuit op restricties. |
| n024 | Externe systeem aanvoertemperatuursensor T43 heeft een abnormale waarde. | Controleer de montage van de sensor om de buis.<br>Controleer de aansluiting op de print. |
| n026 | Klok niet ingesteld. | Stel klok in. |
| n027 | Fout in de werking van de klok. | Mogelijk een hardwarefout.<br>Raadpleeg Intergas Verwarming BV. |
| n028 | Notificatiecode die ontstaat doordat de buitenunit regelmatig problemen ondervindt. | Raadpleeg Intergas Verwarming BV. |
| n029 | Geen dauwpunt signaal beschikbaar (koeliing) | De Comfort touch thermostaat levert geen relatieve vochtigheidssignaal. Stel een andere modus in. |
| n030 | Externe systeem aanvoertemperatuursensor T43 niet aangesloten. | Controleer in het wifibedieningsscherm: P066 = 4 (CV-ketel aansturing Aan/Uit), P123 = 1 (Ja), P123 = 3 (vrij instelbare relais uitgang). |
| n032 | Ontdooien duurde te lang. | Mogelijk een koeltechnische fout .<br>Mogelijk de buitenunit vol in de wind. |
| n039 | Probleem met externe systeem aanvoertemperatuursensor T43. | Controleer de montage van de sensor op de aanvoerbuis.<br>Controleer bedrading, vervang indien nodig. |
| n040 | Probleem met externe buitentemperatuursensor T42. | Controleer bedrading, vervang indien nodig. |
| n041 | Probleem met koudemiddel vloeistoftemperatuursensor. | Controleer bedrading, vervang indien nodig. |
| n042 | Probleem met koudemiddel gastemperatuursensor. | Controleer bedrading, vervang indien nodig. |
| n043 | Probleem met sensor 1 (Xtore) (X4, contacten 6 en 7). | Controleer bedrading.<br>Controleer de sensor. |
| n044 | Probleem met sensor 2 (Xtore) | Controleer bedrading.<br>Controleer de sensor. |
| n051 | CV-ketel in lockout. | Controleer fout in CV-ketel. |
| n052 | Fout in OpenTherm verbinding met CV-ketel. | Controleer bedrading, vervang indien nodig. |
| n053 | Aanvoertemperatuur van de CV-ketel staat te laag. | Stel de aanvoertemperatuur van de CV-ketel minimaal 10ºC hoger in als de maximale aanvoertemperatuur van de Xtend (P194) |
| n054 | CV-ketel geeft geen reactie op warmtevraag vanuit Xtend. | Controleer of de CV-ketel of cv-functie niet uit staat. |
| n055 | CV-ketel heeft een notificatie. | Los de storing van de Intergas CV-ketel op. |
| n056 | CV-ketel maakt te warm water in CV-bedrijf. | Controleer de ingestelde aanvoertemperatuur van de CV-ketel.<br>Controleer het ingestelde vermogen van de CV-ketel. |
| n057 | Aanvoertemperatuur van de CV-ketel staat te laag. | Stel de aanvoertemperatuur van de CV-ketel minimaal op 75ºC om zeker te stellen dat het legionellapreventie programma uitgevoerd kan worden. |
| n058 | Temperatuur van de tempearatuurbeveiligingssensor (CV) te hoog. | Controleer bedrading.<br>Mogelijk probleem met de driewegklep. |
| n060 | Software versie van thermostaat niet up to date, indien gebruik wordt gemaakt van de Intergas Comfort Touch thermostaat. | Plaats de nieuwste versie van de Intergas Comfort Touch Thermostaat. |
| n070 | Warmtepomp fout (regeling binnenunit). | Raadpleeg het wifibedieningsscherm voor aanvullende informatie.<br>Raadpleeg Intergas Verwarming BV. |
| n071 | Debiet fout tijdens WP-bedrijf. | Raadpleeg het wifibedieningsscherm voor aanvullende informatie.<br>Raadpleeg Intergas Verwarming BV. |
| n072 | Debiet fout tijdens het ontdooien. | Controleer de flow, ontlucht en vul eventueel water bij. |
| n073 | Koudemiddeltemperatuur te laag tijdens ontdooien. | Controleer het koudemiddelcircuit op lekkages.<br>Mogelijk een koudemiddeltekort. |
| n074 | Ontdooifunctie gestopt vanwege een te lage watertemperatuur. | Controleer de flow.<br>Mogelijk te weinig buffer. |
| n075 | Compressor start te vaak. | Controleer instellingen thermostaat etc.<br>Controleer afgiftesysteem. |
| n076 | Lucht recirculatie over verdamper gedetecteerd. | Te weinig ruimte rondom de Xtend.<br>Door omkasting geen scheiding tussen luchtaanvoer en luchtafvoer. |
| n077 | Warmtepomp zelftest gefaald. | Het systeem dient koudemiddelzijdig gecontroleerd te worden. Neem hiervoor contact op met Intergas Verwarming BV. |
| n078 | Buitentemperatuursensor vastgevroren aan verdamper | Check of de buitentemperatuursensor vrij ligt van de verdamper.<br>Check of er geen ijs aangevroren is tussen senor en verdamper.<br>Zonodig de sensor ontdooien en iets wegbuigen van de verdamper. |
| n080 | Probleem met de gebruikersinterface. | Strat Xtend opnieuw op.<br>Raadpleeg Intergas Verwarming BV. |
| n081 | Kalibratie fout van de aanvoersensor T03. | Controleer of de sensor goed contact maakt.<br>Controleer de bedrading.<br>Mogelijk defecte sensor, vervang indien nodig. |
| n082 | Kalibratie fout van de externe systeem aanvoertemperatuur-sensor T43. | Controleer of de sensor goed contact maakt.<br>Controleer de bedrading.<br>Mogelijk defecte sensor. |
| n085 | Buitenunit kan niet koelen. | Koelfunctie is niet beschikbaar en wordt automatisch gedeactiveerd. |
| n086 | Afgiftesysteem is niet geschikt om te koelen. | Controleer parameter P200 deze moet op “vloerverwarming” staan. |
| n090 | Warmwatervat temperatuursensor niet goed geconfigureerd. | Controleer de instellingen. |
| n091 | Onlogische waarde van de warmwatervat temperatuursensor. | Controleer de bedrading.<br>Mogelijk sensor kapot. |
| n094 | Legionellapreventie programma mislukt (vanaf 3 pogingen). | Mogelijk te vaak onderbreking door tapwatervraag.<br>Verplaats de dag of tijdstip van het legionellapreventie programma. |
| n095 | Probleem met driewegklep. | Controleer de bedrading.<br>Controleer de motor van de driewegklep.<br>Controleer de behuizing van de driewegklep.<br>Controleer parameter P047, P068 en P069. |
| n096 | Geen temperatuurverhoging gemeten tijdens opwarming Xtore. | Controleer warmwatervat temperatuursensor.<br>Controleer driewegklep. |
| n097 | CV-ketel brandt bij tapwatervat opwarmen te kort. | Controleer flow en CV-ketel instellingen. |
| n100-n165 | FOTA gerelateerde melding. | Neem contact op met Intergas. (FOTA = Firmware Over-The-Air) |
