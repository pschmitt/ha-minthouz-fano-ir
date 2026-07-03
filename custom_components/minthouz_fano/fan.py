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
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import CONF_INFRARED_ENTITY_ID, FanoCode, ORDERED_SPEEDS, SPEED_CODES
from .entity import MinthouzFanoEntity

DEFAULT_SPEED = ORDERED_SPEEDS[0]

# The fan's speed buttons only take effect while it's already powered on —
# they do not turn it on themselves, unlike the dedicated (toggle) power
# button. Give the unit a moment to wake up before sending a speed code.
POWER_ON_SETTLE_DELAY = 0.5


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
    _attr_speed_count = len(ORDERED_SPEEDS)
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
        """Restore the last known (assumed) state after a restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        self._attr_is_on = last_state.state == "on"
        self._attr_percentage = last_state.attributes.get("percentage", 0)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan, defaulting to the last known (or lowest) speed."""
        await self.async_set_percentage(
            percentage
            or self._attr_percentage
            or ordered_list_item_to_percentage(ORDERED_SPEEDS, DEFAULT_SPEED)
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

        speed = percentage_to_ordered_list_item(ORDERED_SPEEDS, percentage)
        await self._send_command(SPEED_CODES[speed].to_command())
        self._attr_percentage = ordered_list_item_to_percentage(ORDERED_SPEEDS, speed)
        self.async_write_ha_state()
