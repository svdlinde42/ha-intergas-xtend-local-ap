# Intergas Xtend — stats-mapping

Mapping van de sleutels uit `GET /api/stats/values?fields=…` (Xtend web-interface, standaard `http://10.20.30.1`), met voorbeelddata uit de eigen installatie (Xtend + Xtore 80L, firmware V1.20-).

**Bronnen**
- Namen en factoren: *Known Xtend Codes* (DSchoutsen/HA_connection_Xtend, gebaseerd op thomasvt1/xtend-bridge).
- Tapwatercodes (61xx): eigen waarneming, vergeleken met de Xtend summary-pagina.

**Conventies**
- Waarde = ruw × factor.
- `32767` = niet beschikbaar (geen sensor of geen waarde).
- `255` bij notificatie- of lockout-codes = geen melding.
- Kolom *Bron*: **K** = Known Xtend Codes, **E** = eigen waarneming, **A** = afgeleid, niet bevestigd.

## Meldingen

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 7940 | status_1_notification_code | Actieve notificatie (n-code) | 1 | | 95 | n095 | K |
| 7e2c | status_0_lockout_code | Lockout-code | 1 | | 255 | geen | K |
| 4133 | status_9_errorCode | Foutcode warmtepomp | 1 | | — | — | K |
| 651d | status_5_faultCode | Foutcode buitenunit | 1 | | — | — | K |
| 8439 | boiler_status_1_from_boiler_ot_oem_faultcode | Foutcode CV-ketel (OpenTherm) | 1 | | 0 | geen | K |

## Vermogen en COP

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 503e | status_S_currentHpPowerThermal | Thermisch vermogen warmtepomp | 0,001 | kW | 5000 | 5,000 kW | K |
| 5088 | status_S_currentBoilerPowerThermal | Thermisch vermogen ketel | 0,001 | kW | 0 | 0,000 kW | K |
| 5077 | status_S_currentPowerThermal | Thermisch vermogen totaal | 0,001 | kW | 5000 | 5,000 kW | K |
| 50f2 | status_S_currentPowerElectric | Elektrisch opgenomen vermogen | 0,001 | kW | 1419 | 1,419 kW | K |
| 5041 | status_S_currentCop | Actuele COP | 0,1 | | 35 | 3,5 | K |

## CV-water

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 629c | status_4_fSystem | Debiet systeem (dashboard *Flow*) | 0,01 | l/min | 1491 | 14,91 l/min | K |
| 6280 | status_4_tHpReturn | Retour warmtepomp (dashboard *Return*) | 0,01 | °C | 5283 | 52,83 °C | K, A |
| 62e7 | status_4_tHpSupply | Aanvoer warmtepomp | 0,01 | °C | — | — | K |
| 621d | status_4_tSystemSupply | Aanvoer systeem (dashboard *Supply*); geen doorstroming tijdens vatrun | 0,01 | °C | 2617 | 26,17 °C | K, A |
| 62ed | status_4_tTempSet | Watersetpoint (dashboard *Setpoint*) | 0,01 | °C | 5783 | 57,83 °C | K |
| 7ed3 | status_0_water_pressure | Waterdruk | 0,01 | bar | 194 | 1,94 bar | K |

## Buitenunit

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 65a7 | status_5_actualFrequency | Compressorfrequentie | 0,01 | Hz | — | — | K |
| 655c | status_5_inletWaterTemperature | Water in buitenunit | 0,01 | °C | — | — | K |
| 65d2 | status_5_outletWaterTemperature | Water uit buitenunit | 0,01 | °C | — | — | K |
| 6c8a | status_6_actualFan1Speed | Ventilatortoerental | 1 | rpm | — | — | K |

## Tapwater (Xtore)

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 610b | — | Tapwater werkelijk | 0,01 | °C | 2975 | 29,75 °C | E |
| 61eb | — | Tapwater streefwaarde (65 °C tijdens legionellarun) | 0,01 | °C | 5000 | 50,00 °C | E |
| 6115 | — | Tapwater beschikbaar | 0,01 | % | 10000 | 100 % | E |
| 61ba | — | Tapwater inhoud | 1 | liter | 80 | 80 L | E |
| 620f | status_4_tTempAux1 | Aux1-sensor; hier vatsensor (P076 = 2) | 0,01 | °C | 2472 | 24,72 °C | K |
| 6206 | status_4_tTempAux2 | Aux2-sensor (P077 = 0, niet aangesloten) | 0,01 | °C | 32767 | n.v.t. | K |

## Ruimte en buiten

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 79b3 | status_1_roomtemperature_1 | Kamertemperatuur | 0,01 | °C | 2480 | 24,80 °C | K |
| 7921 | status_1_roomtemperature_set_1 | Kamersetpoint | 0,01 | °C | 2000 | 20,00 °C | K |
| 62d1 | status_4_tOutdoor | Buitentemperatuur | 0,01 | °C | 1548 | 15,48 °C | K |

## Systeem

| Sleutel | API-naam | Omschrijving | Factor | Eenheid | Voorbeeld ruw | Voorbeeld waarde | Bron |
|---|---|---|---|---|---|---|---|
| 47e0 | CPUinfo_software_version | Firmwareversie | — | | "V1.20-" | V1.20- | K |

## Bitvelden en ongeduide sleutels

Waarden ruw weergegeven; betekenis van de afzonderlijke bits is niet bekend.

| Sleutel | API-naam | Omschrijving | Voorbeeld ruw | Bron |
|---|---|---|---|---|
| 7e51 | status_0_heatdemand_status | Warmtevraagstatus (bitveld) | 206 | K |
| 7e7a | status_0_burner_status | Branderstatus (bitveld) | 64 | K |
| 77c3 | status_3_Flags | Statusvlaggen | 194 | K |
| 77d2 | status_3_SystemIo | Systeem-I/O (bitveld) | 17134 | K |
| f9f2 | bivalent_service_flags | Vlaggen hybride regeling | 136 | K |
| 6101 | — | Onbekend (tapwatergroep) | 7079 | — |
| 6117 | — | Onbekend; mogelijk tapwaterstatus | 3 | A |
| 7774 | — | Onbekend | 255 | — |
| 77de | — | Onbekend | 255 | — |

## Voorbeeldaanroep

```
GET http://10.20.30.1/api/stats/values?fields=7940,7e2c,503e,5088,5077,50f2,5041,629c,6280,621d,62ed,610b,61eb,6115,61ba,620f,79b3,7921,62d1,47e0
```

Antwoord: `{"stats":{"<sleutel>":<ruwe waarde>, …}}`
