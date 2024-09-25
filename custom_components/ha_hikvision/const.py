from enum import IntFlag

DOMAIN = 'ha_hikvision'

GET = 'get'
PUT = 'put'

class CameraFeature(IntFlag):
  DEFAULT = 0x0
  SUPPLEMENT_LIGHT = 0x1
  REMOTE_DOOR = 0x2
