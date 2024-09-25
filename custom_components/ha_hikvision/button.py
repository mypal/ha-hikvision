from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify
import logging
from .coordinator import Coordinator, Camera
from .util import safe_request_data
from .const import PUT, DOMAIN
from . import HikvisionConfigEntry

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
  hass: HomeAssistant, 
  entry: HikvisionConfigEntry, 
  async_add_entities: AddEntitiesCallback
) -> None:
  coordinator: Coordinator = entry.runtime_data.coordinator

  entities = []

  for camera in coordinator.get_cameras():
    entities.append(RebootButton(camera, coordinator))
  
  async_add_entities(entities)

class RebootButton(CoordinatorEntity[Coordinator], ButtonEntity):
  def __init__(self, dev: Camera, coordinator: Coordinator):
    super().__init__(coordinator)
    self._coordinator = coordinator
    self._dev = dev

    self._attr_device_class = ButtonDeviceClass.RESTART
    self._attr_device_info = DeviceInfo(
      identifiers={(DOMAIN, f"hikvision_{dev.serial_no}")},
      name=dev.name,
      manufacturer="Hikvision",
      model=dev.model,
    )
    self.entity_id = f"{DOMAIN}.{slugify(dev.serial_no.lower())}_reboot"
    self._attr_unique_id = self.entity_id
    self._attr_name = f"{dev.name} reboot"

  # @callback
  # def _handle_coordinator_update(self) -> None:
  #   """TODO"""
  #   self.async_write_ha_state()

  async def async_press(self) -> None:
    await self._coordinator.api.System.reboot(method=PUT)