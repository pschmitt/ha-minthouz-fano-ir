# Minthouz Fano P12L Fan (IR) for Home Assistant

<img src="docs/images/fano-p12l.webp" alt="Minthouz Fano P12L clip fan" width="280" align="right">

A custom Home Assistant integration that controls a **Minthouz Fano P12L**
clip fan (an unbranded/generic NEC-IR remote fan, likely shared by many
rebadged clones) through Home Assistant's built-in **Infrared** building-block
integration.

It does not talk to hardware directly — it sends commands through whichever
`infrared.*` emitter entity you already have set up (e.g. an ESPHome device
using the `infrared`/`ir_rf_proxy` platform, pointed at a real IR LED).

<br clear="right">

## Hardware

- **Product:** [Minthouz Fano P12L — 12000mAh Portable Fan with Clip](https://www.minthouz.com/12000mah-portable-fan-with-clip-p12l)
- **Control:** 8-button IR remote (NEC protocol), no Bluetooth/Wi-Fi
- **Manufacturer:** Minthouz — unofficial/reverse-engineered integration, not affiliated

<p align="center">
  <img src="docs/images/remote.png" alt="Minthouz Fano P12L remote" width="220">
</p>

<p align="center"><sub>The 8-button remote this integration replaces.</sub></p>

## Requirements

- Home Assistant **2026.3.0+** (for the `infrared` building-block integration
  and for custom-integration branding support).
- An existing `infrared.*` **emitter** entity in your Home Assistant instance.
  See <https://www.home-assistant.io/integrations/infrared/> for background.
  Don't have one? See below.

## Building your own IR blaster

A ready-to-flash, generic ESPHome config lives at
[`esphome/ir-blaster.yaml`](esphome/ir-blaster.yaml) — it works on any ESP32
with an IR LED (ideally through a transistor/driver for real range) wired to
a GPIO pin, and exposes it as an `infrared.*` emitter entity via ESPHome's
experimental `infrared`/`ir_rf_proxy` platform, which is all this integration
(or any other Infrared-based one) needs.

```sh
cd esphome
cp secrets.yaml.example secrets.yaml   # fill in your wifi + a fresh api key
esphome run ir-blaster.yaml
```

Adjust `board` and `ir_led_pin` in the substitutions at the top of the file
to match your hardware first.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pschmitt&repository=ha-minthouz-fano-ir&category=integration)

1. Click the badge above, or open HACS → Integrations → ⋮ → Custom repositories
   and add `https://github.com/pschmitt/ha-minthouz-fano-ir` as an **Integration**.
2. Install **Minthouz Fano P12L Fan (IR)**, then restart Home Assistant.

### Manual

Copy `custom_components/minthouz_fano` into your Home Assistant
`config/custom_components/` directory and restart.

## Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=minthouz_fano)

Or: **Settings → Devices & Services → Add Integration → Minthouz Fano P12L Fan
(IR)**, then pick the infrared emitter entity to send commands through.

## Entities

| Entity | Domain | Notes |
|---|---|---|
| Fan | `fan` | Power on/off + 3-speed (`33%`/`66%`/`100%`) |
| LED | `light` | 3 brightness levels; see below — it's a single cycling button |
| Timer 2H / 4H / 6H | `button` | Fires the corresponding timer preset |

## A note on state (and remote quirks)

This remote has **no feedback path** — every state is optimistic/assumed
(`iot_class: assumed_state`), and `light`/`button` state can still desync
from reality if you use the physical remote. The `fan` entity is more
robust than that, though: since power is a toggle and speed buttons are a
no-op while off, a naive "toggle if we think it's off" approach would
misfire the moment our assumed state drifted. Instead it exploits a quirk
confirmed against the real hardware — **Timer 2H unconditionally turns the
fan on (a no-op if it already was)**, unlike the power button, which
blindly toggles. Chaining Timer 2H → Power → Power therefore
deterministically forces "on at speed 1" regardless of the fan's actual
prior state, and Timer 2H → Power deterministically forces "off". Both
`fan.turn_on`/`set_percentage`/`turn_off` use this — at the cost of the fan
briefly cycling through off/on — instead of trusting assumed state at all.
(The intermediate power-off also clears the 2h-timer LED Timer 2H arms, so
there's no lingering side effect from using it this way.)

- **Timer buttons *do* turn the fan on** (at speed 1) by themselves when it's
  off — no power press needed. Pressing one updates the `fan` entity's
  assumed state to match.
- **The LED has one physical button, not per-level commands.** Every press
  advances a 4-state cycle: off → low → medium → high → off → ... The `light`
  entity works out how many presses (with a short delay between each) are
  needed to get from its current assumed state to the requested one.

## How the codes were captured

NEC codes were learned off the physical remote using `ir-keytable` against a
USB IR receiver (`address=0x00`, single-byte commands per button — see
`custom_components/minthouz_fano/const.py`). If your remote/fan uses
different codes, this integration will not work as-is.

## License

[GPL-3.0](LICENSE)
