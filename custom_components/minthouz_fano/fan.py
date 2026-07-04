"""Fan platform for the Minthouz Fano P12L (IR) integration.

The remote has no feedback path — every state below is assumed/optimistic.
Using the physical remote (or power-cycling the fan) will desync this
entity's state from reality until the next command is sent.
"""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import CONF_INFRARED_ENTITY_ID, DOMAIN, FanoCode, SPEED_CODES, SPEED_RANGE
from .entity import MinthouzFanoEntity

DEFAULT_SPEED = SPEED_RANGE[0]

# The fan's speed buttons only take effect while it's already powered on —
# they do not turn it on themselves, unlike the dedicated (toggle) power
# button. Give the unit a moment to wake up before sending a speed code.
POWER_ON_SETTLE_DELAY = 0.5


def _speed_to_percentage(speed: int) -> int:
    """Map an integer speed level (1-3) to a percentage."""
    return ranged_value_to_percentage(SPEED_RANGE, speed)


def _percentage_to_speed(percentage: int) -> int:
    """Map a percentage to the nearest integer speed level (1-3).

    Uses round() (not HA's ordered_list_item_to_percentage, which floors
    bucket boundaries) so e.g. a slightly-rounded-up 67% still lands on
    speed 2/"medium" rather than jumping to speed 3/"high".
    """
    speed = round(percentage_to_ranged_value(SPEED_RANGE, percentage))
    return max(SPEED_RANGE[0], min(SPEED_RANGE[1], speed))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fan entity from a config entry."""
    async_add_entities([MinthouzFanoFan(entry)])


class MinthouzFanoFan(
    MinthouzFanoEntity, InfraredEmitterConsumerEntity, RestoreEntity, FanEntity
):
    """Fan entity that drives the Minthouz Fano P12L over IR."""

    _attr_name = None
    _attr_speed_count = SPEED_RANGE[1] - SPEED_RANGE[0] + 1
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_assumed_state = True
    _attr_is_on = False
    _attr_percentage = 0

    def __init__(self, entry: ConfigEntry) -> None:
        """Set up the fan entity."""
        super().__init__(entry, unique_id_suffix="fan")
        self._infrared_emitter_entity_id = entry.data[CONF_INFRARED_ENTITY_ID]

    async def async_added_to_hass(self) -> None:
        """Restore the last known (assumed) state and register for lookup.

        The timer buttons (button.py) need to reach this entity, since
        pressing one also turns the fan on when it's currently off.
        """
        await super().async_added_to_hass()
        self.hass.data[DOMAIN][self._entry.entry_id]["fan_entity"] = self

        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        self._attr_is_on = last_state.state == "on"
        self._attr_percentage = last_state.attributes.get("percentage", 0)

    def mark_on_at_speed_1_if_off(self) -> None:
        """Reflect that a timer button implicitly powered the fan on.

        Called by the timer buttons, which — unlike the plain speed buttons
        — turn the fan on (at speed 1) by themselves when it's currently
        off. Does nothing if we already believe the fan is on.
        """
        if self._attr_is_on:
            return
        self._attr_is_on = True
        self._attr_percentage = _speed_to_percentage(DEFAULT_SPEED)
        self.async_write_ha_state()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan, defaulting to the last known (or lowest) speed."""
        await self.async_set_percentage(
            percentage or self._attr_percentage or _speed_to_percentage(DEFAULT_SPEED)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan.

        The remote's power button is a toggle, so this only makes sense if
        our assumed state still matches reality.
        """
        await self._send_command(FanoCode.POWER.to_command())
        self._attr_is_on = False
        self._attr_percentage = 0
        self.async_write_ha_state()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed, powering it on first if it's currently off.

        The speed buttons are a no-op while the fan is off, so an explicit
        power-on (toggle) is only sent when we believe it's currently off.
        """
        if percentage == 0:
            await self.async_turn_off()
            return

        if not self._attr_is_on:
            await self._send_command(FanoCode.POWER.to_command())
            self._attr_is_on = True
            self.async_write_ha_state()
            await asyncio.sleep(POWER_ON_SETTLE_DELAY)

        speed = _percentage_to_speed(percentage)
        await self._send_command(SPEED_CODES[speed].to_command())
        self._attr_percentage = _speed_to_percentage(speed)
        self.async_write_ha_state()
