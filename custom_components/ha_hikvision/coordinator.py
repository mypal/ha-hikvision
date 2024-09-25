import logging
from datetime import timedelta, datetime
from dataclasses import dataclass
from .hikvisionapi import AsyncClient, set_hass
import xmltodict

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CameraFeature, PUT
from .util import deep_get, safe_request_data

_LOGGER = logging.getLogger(__name__)
INTERVAL = timedelta(seconds=10)

@dataclass
class Camera:
  id: int
  name: str
  model: str
  serial_no: str
  features: list
  state: dict

class Coordinator(DataUpdateCoordinator[dict]):
  """"""
  _cameras: list[Camera] = []

  def __init__(self, hass, host, username, password):
    super().__init__(hass, _LOGGER, name="Hikvision", update_interval=INTERVAL, always_update=True)
    set_hass(hass)
    self._hass = hass
    self._host = host
    self._username = username
    self._password = password
  
  async def _async_setup(self):
    """setup"""
    api = AsyncClient(self._host, self._username, self._password)
    self.api = api
    input_num = await safe_request_data(api.System.capabilities, 'RacmCap.inputProxyNums', 0)
    if input_num > 0:
      """nvr"""
      channels = await safe_request_data(api.ContentMgmt.InputProxy.channels, 'InputProxyChannelList.InputProxyChannel', [])
      for channel in channels:
        self._cameras.append(Camera(
          id=channel.get('id'),
          name=channel.get('name'),
          model=deep_get(channel, 'sourceInputPortDescriptor.model', ''),
          serial_no=deep_get(channel, 'sourceInputPortDescriptor.serialNumber', ''),
          state={},
        ))
    else:
      """camera"""
      device_info = await safe_request_data(api.System.deviceInfo)
      features = CameraFeature.DEFAULT

      supplement_light = await safe_request_data(api.Image.channels['1'].capabilities, 'ImageChannel.SupplementLight')
      if supplement_light is not None:
        features |= CameraFeature.SUPPLEMENT_LIGHT
      
      # not implement
      # remote_door = await safe_request_data(api.AccessControl.RemoteControl.door.capabilities) is not None
      # if remote_door:
      #   features |= CameraFeature.REMOTE_DOOR

      self._cameras.append(Camera(
        id=1,
        name=deep_get(device_info, 'DeviceInfo.deviceName', 'name'),
        model=deep_get(device_info, 'DeviceInfo.model', 'model'),
        serial_no=deep_get(device_info, 'DeviceInfo.serialNumber', 'serial_no'),
        features=features,
        state={},
      ))


  async def _async_update_data(self) -> dict:
    for camera in self._cameras:
      if camera.features & CameraFeature.SUPPLEMENT_LIGHT:
        supplement_light = await safe_request_data(self.api.Image.channels[camera.id].SupplementLight, 'SupplementLight')
        if supplement_light is not None:
          _LOGGER.debug('update value:')
          _LOGGER.debug(supplement_light)
          camera.state['supplement_light'] = supplement_light

  def get_cameras(self) -> list[Camera]:
    return self._cameras

  async def set_supplement_light(self, id: int, data: dict):
    return (await safe_request_data(self.api.Image.channels[id].SupplementLight, 'ResponseStatus.statusString', '', method=PUT, data=xmltodict.unparse(data))) == 'OK'
