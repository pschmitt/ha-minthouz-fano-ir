"""Light platform for the Minthouz Fano P12L (IR) integration.

The LED has a single physical button, not per-level commands: every press
advances a 4-state cycle (off -> low -> medium -> high -> off -> ...). To
reach a target level from the current (assumed) one, we send however many
presses are needed to advance around that cycle.
"""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_INFRARED_ENTITY_ID, FanoCode, LED_BRIGHTNESS_LEVELS
from .entity import MinthouzFanoEntity

# Delay between successive presses of the same cycle button, so the fan's
# receiver reliably registers each one as a separate press.
LED_PRESS_DELAY = 0.3

# Index 0 is "off"; indices 1-3 map to LED_BRIGHTNESS_LEVELS[0-2].
CYCLE_LENGTH = len(LED_BRIGHTNESS_LEVELS) + 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the LED light entity from a config entry."""
    async_add_entities([MinthouzFanoLed(entry)])


class MinthouzFanoLed(
    MinthouzFanoEntity, InfraredEmitterConsumerEntity, RestoreEntity, LightEntity
):
    """The fan's LED, modeled as a light with 3 brightness levels."""

    _attr_translation_key = "led"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_assumed_state = True
    _attr_is_on = False
    _attr_brightness: int | None = None

    def __init__(self, entry: ConfigEntry) -> None:
        """Set up the light entity."""
        super().__init__(entry, unique_id_suffix="led")
        self._infrared_emitter_entity_id = entry.data[CONF_INFRARED_ENTITY_ID]

    async def async_added_to_hass(self) -> None:
        """Restore the last known (assumed) state after a restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        self._attr_is_on = last_state.state == "on"
        self._attr_brightness = last_state.attributes.get("brightness")

    def _current_cycle_index(self) -> int:
        """Return this entity's position (0-3) in the physical 4-state cycle."""
        if not self._attr_is_on or self._attr_brightness is None:
            return 0
        return LED_BRIGHTNESS_LEVELS.index(self._attr_brightness) + 1

    async def _advance_to(self, target_index: int) -> None:
        """Press the LED button enough times to reach the target cycle state."""
        presses = (target_index - self._current_cycle_index()) % CYCLE_LENGTH
        for i in range(presses):
            await self._send_command(FanoCode.LED.to_command())
            if i < presses - 1:
                await asyncio.sleep(LED_PRESS_DELAY)

        if target_index == 0:
            self._attr_is_on = False
            self._attr_brightness = None
        else:
            self._attr_is_on = True
            self._attr_brightness = LED_BRIGHTNESS_LEVELS[target_index - 1]
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the LED, or cycle to the requested brightness level."""
        brightness = kwargs.get("brightness")
        if brightness is None:
            if self._attr_is_on:
                return  # Already on; no "stay put" command exists.
            target_index = 1
        else:
            closest = min(LED_BRIGHTNESS_LEVELS, key=lambda level: abs(level - brightness))
            target_index = LED_BRIGHTNESS_LEVELS.index(closest) + 1
        await self._advance_to(target_index)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Cycle the LED off."""
        await self._advance_to(0)
