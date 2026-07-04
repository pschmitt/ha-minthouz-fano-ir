"""The Minthouz Fano P12L (IR) integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = ["fan", "light", "button"]

type MinthouzFanoConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: MinthouzFanoConfigEntry) -> bool:
    """Set up Minthouz Fano P12L from a config entry."""
    # Per-entry scratch space: the timer buttons need to reach the fan
    # entity, since pressing one also turns the fan on (to speed 1) when
    # it's currently off — see button.py / fan.py.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MinthouzFanoConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
