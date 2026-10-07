# ha-intergas-xtend-local-ap

Monitor and manage Intergas Xtend in HomeAssistant using the Xtend's local AP

This is a Home Assistant custom integration, installed with HACS. It reads the status of an
Intergas Xtend through the Wi-Fi access point (AP) of the Xtend. Version 0.1 is read-only: it
does not change any setting on the boiler.

## Installation

1. In HACS, add this repository as a custom repository with type **Integration**.
2. Install **Intergas Xtend** and restart Home Assistant.
3. Go to Settings, Devices & services, Add integration, and choose **Intergas Xtend**.
4. Enter the IP address of the Xtend (default `10.20.30.1`) and the poll interval in seconds
   (default 10, minimum 5, maximum 60). You can change the interval later in the options.

The integration does one request to the Xtend before it creates the entry. If that fails, check
the network (see below).

## Network

The Xtend only answers on its own Wi-Fi access point. The Home Assistant host must stay wired to
your LAN and must also be joined to the Xtend Wi-Fi network. The Xtend has the IP address
`10.20.30.1` on that network by default.

## Access point timeout

The access point of the Xtend switches itself off after about 15 minutes without requests.
Polling every few seconds keeps it alive. Once the AP is off, the integration cannot switch it
on again.

When the Xtend does not answer:

- The sensors become unavailable.
- From the 3rd failed poll the integration waits longer between polls: the wait doubles each
  time, up to at most 5 minutes. It also creates a repair issue in Home Assistant.
- One successful poll puts the interval back to the configured value and removes the issue.

How to recover:

1. Switch the access point on again on the Xtend.
2. Reconnect the Wi-Fi on the Home Assistant host if it did not reconnect by itself.
3. Press the **Poll now** button of the Xtend device (Dutch: **Nu pollen**).

## Entities

All entities belong to one device, **Intergas Xtend**. The device page links to the web page of
the Xtend and shows the firmware version. Names follow the labels of the Xtend summary page.
Field meanings, scale factors and units come from [docs/stats-mapping.md](docs/stats-mapping.md).

There is one button, **Poll now** (diagnostic). It is always available, also when the Xtend is
unreachable.

There are 32 sensors. A value of 32767 from the device means "not available" and shows as
unknown.

| Sensor | Unit | Enabled by default |
| --- | --- | --- |
| Room temperature | °C | yes |
| Room target temperature | °C | yes |
| Outside temperature | °C | yes |
| CH water return | °C | yes |
| CH water supply | °C | yes |
| CH water setpoint | °C | yes |
| Aux 1 temperature | °C | yes |
| Aux 2 temperature | °C | yes |
| DHW actual | °C | yes |
| DHW setpoint | °C | yes |
| Heat pump power | W | yes |
| Boiler power | W | yes |
| Total thermal power | W | yes |
| Retrieved power | W | yes |
| COP | none | yes |
| CH water flow | L/min | yes |
| CH water pressure | bar | yes |
| DHW available | % | yes |
| DHW volume | L | yes (diagnostic) |
| Notification code | none | yes (diagnostic) |
| Lockout code | none | yes (diagnostic) |
| Boiler fault code | none | yes (diagnostic) |
| Firmware version | none | yes (diagnostic) |
| Operating mode | enum | yes |
| DHW state | enum | yes |
| Burner status (raw) | none | no (diagnostic) |
| Status flags (raw) | none | no (diagnostic) |
| System I/O (raw) | none | no (diagnostic) |
| Bivalent service flags (raw) | none | no (diagnostic) |
| Raw 6101 | none | no (diagnostic) |
| Raw 7774 | none | no (diagnostic) |
| Raw 77de | none | no (diagnostic) |

The raw sensors show the number from the device without any meaning. Their meaning is not known
yet. You can enable them in the entity registry.

### Notification and lockout codes

The **Notification code** (for example `n095`) and **Lockout code** (for example `F037`) sensors
show the code as the display of the Xtend shows it. The sensor is unknown when there is no code.
Each sensor has two attributes:

- `description`: the description of the code.
- `cause_solution`: a list with the possible causes and solutions.

Both attributes are in Dutch, quoted word for word from the Intergas installation manual
(document 88104401, chapter 12.1 and 12.2). Home Assistant cannot translate attribute values.
The full list is in [docs/fault-codes.md](docs/fault-codes.md). A code that is not in the manual
shows `description: null`.

The **Boiler fault code** sensor shows the own fault code of the CH boiler (OpenTherm). The
manual of the Xtend does not cover it, so it has no attributes.

## Notes

- The unique ID of the entry is the host. The status data has no serial number or MAC address.
  If you change the IP address of the Xtend, Home Assistant creates a new entry.
- The minimum Home Assistant version is 2025.11.0, the first release that runs on Python 3.14.
