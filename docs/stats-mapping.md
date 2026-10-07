# Intergas Xtend — stats-mapping

Mapping van de sleutels uit `GET /api/stats/values?fields=…` (Xtend web-interface, standaard `http://10.20.30.1`), met voorbeelddata uit de eigen installatie (Xtend + Xtore 80L, firmware V1.20-).

**Bronnen**
- Namen en factoren: *Known Xtend Codes* (DSchoutsen/HA_connection_Xtend, gebaseerd op thomasvt1/xtend-bridge).
- Tapwatercodes (61xx): eigen waarneming, vergeleken met de Xtend summary-pagina.
- Eenheden, factoren en opsommingen: `app.js` van de Xtend web-interface (aangeleverd door de eigenaar, 2026-10-07). Dit bestand bevat geen veldnamen, alleen eenheid, factor en tabellen. Welke tabel bij welk veld hoort, volgt uit de volgorde in de code (de tabel staat direct na het veld). De tabellen staan in `docs/xtend-enums.json`; de bedrijfsmodi van 7e51 in `docs/operating-modes.json`.
- Statistiekenpagina: broncode van de pagina plus één antwoord van de bijbehorende aanvraag (stand-by, 2026-10-07), aangeleverd door de eigenaar. De pagina bouwt haar veldenlijst in dezelfde volgorde als de URL; zo is elk veld gekoppeld aan een label op de pagina. Het antwoord staat in `tests/fixtures/stats_values_statistics.json`.

**Conventies**
- Waarde = ruw × factor.
- `32767` = niet beschikbaar (geen sensor of geen waarde).
- `255` bij notificatie- of lockout-codes = geen melding.
- Bitvelden: bit n staat aan als `(waarde >> n) & 1 == 1` (zo leest `app.js` ze).
- Kolom *Bron*: **K** = Known Xtend Codes, **E** = eigen waarneming, **J** = eenheid en factor bevestigd door `app.js`, **S** = betekenis uit de statistiekenpagina, **A** = afgeleid, niet bevestigd.

## Meldingen

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 7940 | status_1_notification_code | Actieve notificatie (n-code) | 1 | | 95 | n095 | K, J |
| 7e2c | status_0_lockout_code | Lockout-code | 1 | | 255 | geen | K, J |
| 4133 | status_9_errorCode | Foutcode warmtepomp (opsomming, zie `docs/xtend-enums.json`) | 1 | | — | — | K, J, A |
| 651d | status_5_faultCode | Foutcode buitenunit | 1 | | — | — | K, J |
| 8439 | boiler_status_1_from_boiler_ot_oem_faultcode | Foutcode CV-ketel (OpenTherm) | 1 | | 0 | geen | K, J |

## Vermogen en COP

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 503e | status_S_currentHpPowerThermal | Thermisch vermogen warmtepomp | 0,001 | kW | 5000 | 5,000 kW | K, J |
| 5088 | status_S_currentBoilerPowerThermal | Thermisch vermogen ketel | 0,001 | kW | 0 | 0,000 kW | K, J |
| 5077 | status_S_currentPowerThermal | Thermisch vermogen totaal | 0,001 | kW | 5000 | 5,000 kW | K, J |
| 50f2 | status_S_currentPowerElectric | Elektrisch opgenomen vermogen | 0,001 | kW | 1419 | 1,419 kW | K, J |
| 5041 | status_S_currentCop | Actuele COP | 0,1 | | 35 | 3,5 | K, J |

`app.js` geeft de vermogens als W met factor 1; dat is gelijk aan factor 0,001 in kW.

## CV-water

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 629c | status_4_fSystem | Debiet systeem (dashboard *Flow*) | 0,01 | l/min | 1491 | 14,91 l/min | K, J |
| 6280 | status_4_tHpReturn | Retour warmtepomp (dashboard *Return*) | 0,01 | °C | 5283 | 52,83 °C | K, J, A |
| 62e7 | status_4_tHpSupply | Aanvoer warmtepomp | 0,01 | °C | — | — | K, J |
| 621d | status_4_tSystemSupply | Aanvoer systeem (dashboard *Supply*); geen doorstroming tijdens vatrun | 0,01 | °C | 2617 | 26,17 °C | K, J, A |
| 62ed | status_4_tTempSet | Watersetpoint (dashboard *Setpoint*) | 0,01 | °C | 5783 | 57,83 °C | K, J |
| 7ed3 | status_0_water_pressure | Waterdruk | 0,01 | bar | 194 | 1,94 bar | K, J |

## Buitenunit

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 65a7 | status_5_actualFrequency | Compressorfrequentie | 0,01 | Hz | — | — | K, J |
| 655c | status_5_inletWaterTemperature | Water in buitenunit | 0,01 | °C | — | — | K, J |
| 65d2 | status_5_outletWaterTemperature | Water uit buitenunit | 0,01 | °C | — | — | K, J |
| 6c8a | status_6_actualFan1Speed | Ventilatortoerental | 1 | rpm | — | — | K, J |

## Tapwater (Xtore)

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 610b | — | Tapwater werkelijk | 0,01 | °C | 2975 | 29,75 °C | E, J |
| 61eb | — | Tapwater streefwaarde (65 °C tijdens legionellarun) | 0,01 | °C | 5000 | 50,00 °C | E, J |
| 6115 | — | Tapwater beschikbaar | 0,01 | % | 10000 | 100 % | E, J |
| 61ba | — | Tapwater inhoud | 1 | liter | 80 | 80 L | E, J |
| 6117 | — | Tapwaterstatus (*DHW State*, opsomming, zie `docs/xtend-enums.json`); bevestigd door de eigenaar 2026-10-07 | 1 | | 3 | DHW_ACTIVE | E, J |
| 6101 | — | Volume in liter; betekenis onbekend | 0,01 | liter | 7079 | 70,79 L | J |
| 620f | status_4_tTempAux1 | Aux1-sensor; hier vatsensor (P076 = 2) | 0,01 | °C | 2472 | 24,72 °C | K, J |
| 6206 | status_4_tTempAux2 | Aux2-sensor (P077 = 0, niet aangesloten) | 0,01 | °C | 32767 | n.v.t. | K, J |

## Ruimte en buiten

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 79b3 | status_1_roomtemperature_1 | Kamertemperatuur | 0,01 | °C | 2480 | 24,80 °C | K, J |
| 7921 | status_1_roomtemperature_set_1 | Kamersetpoint | 0,01 | °C | 2000 | 20,00 °C | K, J |
| 62d1 | status_4_tOutdoor | Buitentemperatuur | 0,01 | °C | 1548 | 15,48 °C | K, J |

## Systeem

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 47e0 | CPUinfo_software_version | Firmwareversie | — | | "V1.20-" | V1.20- | K, J |
| 7e51 | status_0_heatdemand_status | Bedrijfsmodus (opsomming, 38 codes, zie `docs/operating-modes.json`; de en/nl-labels daarin zijn onze eigen vertaling, ch_rf en dhw_hreco zijn geraden uit de afkorting (RF, HRECO)); geen bitveld; pagina: *Device status* | 1 | | 206 | DHW_LEGIONELLA_PREVENTION | K, E, J, S |

## Bitvelden

Bitnamen staan in `docs/xtend-enums.json`. Voor 77c3 en f9f2 bevestigt de statistiekenpagina de koppeling (bron S): *Silent mode* = 77c3 bit 3, *Heat demand* warmtepomp = f9f2 bit 7, *Heat demand* ketel = f9f2 bit 8, *Flame* = f9f2 bit 9. Voor 77d2 volgt de koppeling alleen uit `app.js` (bron A).

| Sleutel | API-naam | Omschrijving | Voorbeeld ruw | Bits aan in voorbeeld | Bron |
|---|---|---|---|---|---|
| 77d2 | status_3_SystemIo | Systeem-I/O: pompen, druk, debiet, compressor, OpenTherm, gateway | 17134 | 1 chPumpOn, 2 pressureDetected, 3 systemFlowDetected, 5 compressorRunning, 6 switched_on, 7 boiler_opentherm_connected, 9 thermostat_ot1_opentherm_connected, 14 gateway_connected | K, J, A |
| 77c3 | status_3_Flags | Regelvlaggen warmtepomp, o.a. bit 3 SilentModeActive | 194 | 1 ControlSupplyTemperature, 6 HeatWasAtMinimumFreq, 7 CompressorWasOn | K, J, S |
| f9f2 | bivalent_service_flags | Vlaggen hybride regeling, o.a. bit 7 HeatpumpRequested, bit 8 BoilerRequested, bit 9 BoilerActualState (vlam), bit 14 DefrostActive | 136 | 3 HPCopEfficiencyOkay, 7 HeatpumpRequested | K, J, S |

Controle met de fixtures in `tests/fixtures`:
- `stats_values` (ketel 7917 W): f9f2 = 265 → 0 HeatpumpNotAllowed, 3, 8 BoilerRequested; 77d2 = 17102 (zonder bit 5, compressor uit).
- `stats_values_standby`: f9f2 = 8 → alleen 3 HPCopEfficiencyOkay; 77c3 = 0; 6117 = 0 (DHW_IDLE, pagina toont *Standby*).
- `stats_values_n095` (warmtepomp 5000 W): f9f2 = 136, 77d2 = 17134 (bit 5 compressorRunning aan).

## Ongeduide sleutels

Waarden ruw weergegeven. `app.js` gebruikt deze velden, maar geeft geen eenheid en geen tabel.

| Sleutel | API-naam | Omschrijving | Voorbeeld ruw | Bron |
|---|---|---|---|---|
| 7e7a | status_0_burner_status | Branderstatus (volgens K); betekenis niet bevestigd | 64 | K |
| 7774 | — | Onbekend | 255 | — |
| 77de | — | Onbekend | 255 | — |

## Energie totaal (statistiekenpagina, kolom *Total*)

Tellers sinds inbedrijfstelling, in hele kWh. Controle met de schermafbeelding van 2026-10-07: CV-totaal 34 + 1 = 35 kWh, tapwatertotaal 46 + 76 = 122 kWh.

| Sleutel | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Bron |
|---|---|---|---|---|---|
| 63b3 | CV, warmtepomp verbruikt (elektrisch) | 1 | kWh | 3 | J, S |
| 63f0 | CV, warmtepomp opgewekt (thermisch) | 1 | kWh | 34 | J, S |
| 63df | CV, ketel opgewekt | 1 | kWh | 1 | J, S |
| 6358 | Tapwater, warmtepomp verbruikt (elektrisch) | 1 | kWh | 8 | J, S |
| 6339 | Tapwater, warmtepomp opgewekt (thermisch) | 1 | kWh | 46 | J, S |
| 4a76 | Tapwater, ketel opgewekt | 1 | kWh | 76 | J, S |

De pagina berekent de COP totaal zelf: opgewekt / verbruikt (CV: 63f0 / 63b3 = 11,3; tapwater: 6339 / 6358 = 5,8), afgerond op 1 decimaal. Er is geen apart veld voor.

## Tellers (statistiekenpagina)

| Sleutel | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Bron |
|---|---|---|---|---|---|
| 6a8e | Compressorstarts CV | 1 | | 9 | S |
| 6a8d | Compressorstarts tapwater | 1 | | 6 | S |
| 6ac5 | Draaiuren compressor CV | 1 | h | 9 | J, S |
| 6a6c | Draaiuren compressor tapwater | 1 | h | 6 | J, S |
| 71a7 | Uptime | 1 | h | 100 | J, S |
| 7160 | Aantal keer spanning aan (power cycles) | 1 | | 13 | S |
| 6a53 | Ontdooicycli | 1 | | 0 | S |
| 4e13 | Draaiuren waterpomp | 1 | h | 99 | J, S |
| 4eeb | Uren carterverwarming | 1 | h | 7 | J, S |
| 4e3a | Uren bodemplaatverwarming | 1 | h | 0 | J, S |
| 4a22 | Starts waterpomp | 1 | | 8 | S |
| 4a3c | Starts carterverwarming | 1 | | 58 | S |
| 4aeb | Starts bodemplaatverwarming | 1 | | 0 | S |
| 8e00 | Starts ketel | 1 | | 10277 | S |
| 8ef9 | Branduren ketel CV | 1 | h | 658 | J, S |
| 8e37 | Branduren ketel tapwater | 1 | h | 85 | J, S |
| 8e18 | Vlamverlies ketel | 1 | | 1 | S |

De pagina toont *Compressor starts* als som 6a8e + 6a8d (+ 6a28 bij koeling) en *Runtime* als som 6ac5 + 6a6c (+ 6a78 bij koeling).

## Statistiekenpagina, niet gepold

Bekend uit de pagina, maar niet opgevraagd door de integratie. Tabellen staan in `docs/xtend-enums.json`.

| Sleutel | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Bron |
|---|---|---|---|---|---|
| 5099 | CV, warmtepomp verbruikt, vorige dag | 0,1 | kWh | 2 | J, S |
| 50ae | CV, warmtepomp opgewekt, vorige dag | 0,1 | kWh | 0 | J, S |
| 50f7 | CV, COP vorige dag | 0,1 | | 0 | J, S |
| 506a | CV, ketel opgewekt, vorige dag | 0,1 | kWh | 0 | J, S |
| 50ff | Tapwater, warmtepomp verbruikt, vorige dag | 0,1 | kWh | 1 | J, S |
| 5098 | Tapwater, warmtepomp opgewekt, vorige dag | 0,1 | kWh | 0 | J, S |
| 5031 | Tapwater, COP vorige dag | 0,1 | | 0 | J, S |
| 2963 | Tapwater, ketel opgewekt, vorige dag | 0,1 | kWh | 0 | J, S |
| 63a7 | Koeling, verbruikt, totaal (alleen bij P005 = 1) | 1 | kWh | 0 | J, S |
| 63e4 | Koeling, opgewekt, totaal; pagina toont −1 × waarde | 1 | kWh | 0 | J, S |
| 503f | Koeling, verbruikt, vorige dag | 0,1 | kWh | 0 | J, S |
| 5008 | Koeling, opgewekt, vorige dag; pagina toont −1 × waarde | 0,1 | kWh | 0 | J, S |
| 5051 | Koeling, COP vorige dag | 0,1 | | 0 | J, S |
| 6a28 | Compressorstarts koeling | 1 | | 0 | S |
| 6a78 | Draaiuren compressor koeling | 1 | h | 0 | J, S |
| 7767 | Watersetpoint warmtepomp (*Setpoint* onder CH water) | 0,01 | °C | 2000 | J, S |
| 6578 | Werkmodus warmtepomp (*Operational mode*, opsomming) | 1 | | 1 | J, S |
| 7fec | Blokkeerreden warmtepomp (*Block reason*, getoond als ≠ 0, opsomming) | 1 | | 1 | J, S |
| 4133 | Foutcode warmtepomp (*Heat pump code*, getoond als 7940 = 11; opsomming, bron A) | 1 | | 0 | K, J, S |
| 65d0 | Uitgangen warmtepomp (bitveld; bit 2 = *4-way valve position*, aan = koelen) | 1 | | 0 | J, S |
| 65b0 | Hoge gasdruk koudemiddel | 0,01 | bar | 834 | J, S |
| 6579 | Lage gasdruk koudemiddel | 0,01 | bar | 834 | J, S |
| 65d9 | Persgastemperatuur (*Exhaust temp*) | 0,01 | °C | 3846 | J, S |
| 6505 | Zuiggastemperatuur | 0,01 | °C | 2697 | J, S |
| 65c1 | Verdampertemperatuur | 0,01 | °C | 1994 | J, S |
| 6c26 | Condensortemperatuur gas | 0,01 | °C | 2941 | J, S |
| 6ceb | Condensortemperatuur vloeistof | 0,01 | °C | 2692 | J, S |
| 6cfb | Oververhitting zuigzijde | 0,01 | °C | 703 | J, S |
| 6c33 | Oververhitting perszijde | 0,01 | °C | 1602 | J, S |
| 6c53 | Nakoeling | 0,01 | °C | 0 | J, S |
| 6c66 | Stand expansieventiel | 1 | steps | 500 | J, S |
| 7ee6 | Ketel aanvoer | 0,01 | °C | 4165 | J, S |
| 7e81 | Ketel retour | 0,01 | °C | 32767 | J, S |
| 7e31 | Ketel setpoint | 0,01 | °C | 32767 | J, S |
| 84d1 | Modulatiegraad ketel | 0,01 | % | 0 | J, S |
| 658a | In de aanvraag, niet getoond op de pagina | 0,01 | Hz | 0 | J |
| 6c61 | In de aanvraag, niet getoond op de pagina | 1 | rpm | 0 | J |
| b38c | In de aanvraag, niet getoond op de pagina | 1 | | 0 | — |
| b3bc | In de aanvraag, niet getoond op de pagina | 1 | | 0 | — |

Al gepold en ook op de pagina: 79b3, 7921, 62d1, 7ed3, 629c, 6280, 62e7, 65a7, 6c8a, 7e51, 77c3, f9f2, 77d2, 7940, 7e2c, 8439. De pagina toont 8439 alleen als 7940 = 51.

## Voorbeeldaanroep

```
GET http://10.20.30.1/api/stats/values?fields=7940,7e2c,503e,5088,5077,50f2,5041,629c,6280,621d,62ed,610b,61eb,6115,61ba,620f,79b3,7921,62d1,47e0
```

Antwoord: `{"stats":{"<sleutel>":<ruwe waarde>, …}}`
