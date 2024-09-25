"""init"""

import logging
from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from .coordinator import Coordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.BUTTON, Platform.LIGHT]

@dataclass
class HikvisionData:
    coordinator: Coordinator

type HikvisionConfigEntry = ConfigEntry[HikvisionData]

async def async_setup_entry(
        hass: HomeAssistant, entry: HikvisionConfigEntry
):
    hass.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    coordinator = Coordinator(hass, host, username, password)
    entry.runtime_data = HikvisionData(coordinator=coordinator)

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
