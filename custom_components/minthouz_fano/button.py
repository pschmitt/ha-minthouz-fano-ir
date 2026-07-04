"""Button platform for the Minthouz Fano P12L (IR) integration.

Covers the three timer presets — the only remote buttons that don't map
onto the `fan`/`light` entity models. Unlike the plain speed buttons, the
timer buttons also turn the fan on (at speed 1) by themselves when it's
currently off, so pressing one updates the fan entity's assumed state too.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_INFRARED_ENTITY_ID, DOMAIN, FanoCode
from .entity import MinthouzFanoEntity


@dataclass(frozen=True, kw_only=True)
class MinthouzFanoButtonDescription(ButtonEntityDescription):
    """Describes a Minthouz Fano P12L IR button."""

    code: FanoCode
    turns_on_fan: bool = False


BUTTON_DESCRIPTIONS: tuple[MinthouzFanoButtonDescription, ...] = (
    MinthouzFanoButtonDescription(
        key="timer_2h",
        translation_key="timer_2h",
        icon="mdi:timer-outline",
        code=FanoCode.TIMER_2H,
        turns_on_fan=True,
    ),
    MinthouzFanoButtonDescription(
        key="timer_4h",
        translation_key="timer_4h",
        icon="mdi:timer-outline",
        code=FanoCode.TIMER_4H,
        turns_on_fan=True,
    ),
    MinthouzFanoButtonDescription(
        key="timer_6h",
        translation_key="timer_6h",
        icon="mdi:timer-outline",
        code=FanoCode.TIMER_6H,
        turns_on_fan=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button entities from a config entry."""
    async_add_entities(
        MinthouzFanoButton(entry, description) for description in BUTTON_DESCRIPTIONS
    )


class MinthouzFanoButton(MinthouzFanoEntity, InfraredEmitterConsumerEntity, ButtonEntity):
    """A single learned IR button on the Minthouz Fano P12L remote."""

    entity_description: MinthouzFanoButtonDescription

    def __init__(
        self, entry: ConfigEntry, description: MinthouzFanoButtonDescription
    ) -> None:
        """Set up the button entity."""
        super().__init__(entry, unique_id_suffix=description.key)
        self.entity_description = description
        self._infrared_emitter_entity_id = entry.data[CONF_INFRARED_ENTITY_ID]

    async def async_press(self) -> None:
        """Send the IR code for this button."""
        await self._send_command(self.entity_description.code.to_command())

        if not self.entity_description.turns_on_fan:
            return
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        if fan_entity := entry_data.get("fan_entity"):
            fan_entity.mark_on_at_speed_1_if_off()
