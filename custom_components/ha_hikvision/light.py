import logging
from typing import Any
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.util import slugify
from .coordinator import Coordinator, Camera
from .util import safe_request_data, deep_get
from .const import PUT, DOMAIN, CameraFeature
from . import HikvisionConfigEntry

_LOGGER = logging.getLogger(__name__)

ON = 'colorVuWhiteLight'
OFF = 'close'

PARAM_ROOT = 'SupplementLight'
PARAM_STATE = 'supplementLightMode'
PARAM_BRIGHTNESS = 'whiteLightBrightness'

async def async_setup_entry(
  hass: HomeAssistant, 
  entry: HikvisionConfigEntry, 
  async_add_entities: AddEntitiesCallback
) -> None:
  coordinator: Coordinator = entry.runtime_data.coordinator

  entities = []

  for camera in coordinator.get_cameras():
    if camera.features & CameraFeature.SUPPLEMENT_LIGHT:
      entities.append(SupplementLight(camera, coordinator))
  
  async_add_entities(entities)

class SupplementLight(CoordinatorEntity[Coordinator], LightEntity):
  def __init__(self, dev: Camera, coordinator: Coordinator):
    super().__init__(coordinator)
    self._coordinator = coordinator
    self._dev = dev

    self._attr_device_info = DeviceInfo(
      identifiers={(DOMAIN, f"hikvision_{dev.serial_no}")},
      name=dev.name,
      manufacturer="Hikvision",
      model=dev.model,
    )
    self.entity_id = f"{DOMAIN}.{slugify(dev.serial_no.lower())}_light"
    self._attr_unique_id = self.entity_id
    self._attr_name = "light"
    self._attr_color_mode = ColorMode.BRIGHTNESS
    self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

  @callback
  def _handle_coordinator_update(self) -> None:
    self._update_state()
    self.async_write_ha_state()

  def _update_state(self) -> None:
    supplement_light = self._dev.state.get('supplement_light')
    _LOGGER.debug(f"supplement_light:")
    _LOGGER.debug(supplement_light)
    if supplement_light is not None:
      self._attr_brightness = int(int(deep_get(supplement_light, 'whiteLightBrightness', 0))*2.55)
      self._attr_is_on = deep_get(supplement_light, 'supplementLightMode', 0) == ON
    _LOGGER.debug(f"light attr: {self._attr_is_on} {self._attr_brightness}")
  
  async def async_turn_on(self, **kwargs: Any) -> None:
    self._attr_is_on = True
    if ATTR_BRIGHTNESS in kwargs:
      self._attr_brightness = kwargs[ATTR_BRIGHTNESS]

    payload = {
      PARAM_ROOT: {
        PARAM_STATE: ON,
        PARAM_BRIGHTNESS: int(self._attr_brightness/2.55),
      }
    }

    res = await self._coordinator.set_supplement_light(self._dev.id, payload)
    _LOGGER.debug(f"light turn on res: {res}")

    self.async_write_ha_state()

  async def async_turn_off() -> None:
    self._attr_is_off = False
    payload = {
      PARAM_ROOT: {
        PARAM_STATE: OFF,
      }
    }

    res = await self._coordinator.set_supplement_light(self._dev.id, payload)
    _LOGGER.debug(f"light turn off res: {res}")
    self.async_write_ha_state()
