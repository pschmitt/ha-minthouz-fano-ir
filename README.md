# Minthouz Fano P12L Fan (IR) for Home Assistant

A custom Home Assistant integration that controls a **Minthouz Fano P12L**
standing fan (an unbranded/generic NEC-IR remote fan, likely shared by many
rebadged clones) through Home Assistant's built-in **Infrared** building-block
integration.

It does not talk to hardware directly — it sends commands through whichever
`infrared.*` emitter entity you already have set up (e.g. an ESPHome device
using the `infrared`/`ir_rf_proxy` platform, pointed at a real IR LED).

## Requirements

- Home Assistant **2026.3.0+** (for the `infrared` building-block integration
  and for custom-integration branding support).
- An existing `infrared.*` **emitter** entity in your Home Assistant instance.
  See <https://www.home-assistant.io/integrations/infrared/> for background,
  and ESPHome's experimental `infrared`/`ir_rf_proxy` component for a DIY
  way to build one out of any ESP32 with an IR LED.

## Installation

### HACS (custom repository)

1. HACS → Integrations → ⋮ → Custom repositories.
2. Add `https://github.com/pschmitt/ha-minthouz-fano-ir` as an "Integration".
3. Install "Minthouz Fano P12L Fan (IR)", then restart Home Assistant.

### Manual

Copy `custom_components/minthouz_fano` into your Home Assistant `config/custom_components/`
directory and restart.

## Setup

Settings → Devices & Services → Add Integration → "Minthouz Fano P12L Fan (IR)",
then pick the infrared emitter entity to send commands through.

## Entities

| Entity | Domain | Notes |
|---|---|---|
| Fan | `fan` | Power on/off + 3-speed (`33%`/`66%`/`100%`) |
| LED | `button` | Toggles the fan's status LED |
| Timer 2H / 4H / 6H | `button` | Fires the corresponding timer preset |

## A note on state

This remote has **no feedback path** — every state is optimistic/assumed
(`iot_class: assumed_state`). The power button on the physical remote is a
toggle, so if you use the physical remote (or power-cycle the fan) alongside
this integration, the `fan` entity's on/off state can desync from reality
until the next command is sent from Home Assistant.

## How the codes were captured

NEC codes were learned off the physical remote using `ir-keytable` against a
USB IR receiver (`address=0x00`, single-byte commands per button — see
`custom_components/minthouz_fano/const.py`). If your remote/fan uses
different codes, this integration will not work as-is.

## License

[GPL-3.0](LICENSE)
