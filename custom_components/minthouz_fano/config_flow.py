"""Config flow for the Minthouz Fano P12L (IR) integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.infrared import DOMAIN as INFRARED_DOMAIN, async_get_emitters
from homeassistant.config_entries import SOURCE_RECONFIGURE, ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import CONF_INFRARED_ENTITY_ID, DOMAIN


class MinthouzFanoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Minthouz Fano P12L fan."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask the user which infrared emitter drives this fan."""
        return await self._async_step_infrared_entity(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user switch the fan to a different infrared emitter."""
        return await self._async_step_infrared_entity(user_input)

    async def _async_step_infrared_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        emitter_entity_ids = async_get_emitters(self.hass)
        if not emitter_entity_ids:
            return self.async_abort(reason="no_infrared_entities")

        if user_input is not None:
            if self.source == SOURCE_RECONFIGURE:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=user_input,
                )
            return self.async_create_entry(
                title="Minthouz Fano P12L",
                data={CONF_INFRARED_ENTITY_ID: user_input[CONF_INFRARED_ENTITY_ID]},
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_INFRARED_ENTITY_ID): EntitySelector(
                    EntitySelectorConfig(
                        domain=INFRARED_DOMAIN,
                        include_entities=emitter_entity_ids,
                    )
                ),
            }
        )
        step_id = "reconfigure" if self.source == SOURCE_RECONFIGURE else "user"
        return self.async_show_form(step_id=step_id, data_schema=schema)
