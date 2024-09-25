import httpx
from typing import Any
from .const import GET, PUT

def deep_get(data: dict, path: str, default: Any = None) -> Any:
    """Get safely nested dictionary attribute."""
    try:
        # 分割路径
        keys = path.split('.')
        value = data
        for key in keys:
            # 如果当前值是字典，尝试获取对应的键
            if isinstance(value, dict):
                value = value.get(key)
            # 如果当前值是列表，尝试获取对应的索引
            elif isinstance(value, list) and key.isdigit():
                key = int(key)  # 将索引转换为整数
                value = value[key]
            else:
                # 如果路径中的某个键不是字典或列表，返回默认值
                return default
        return value if value is not None else default
    except (IndexError, KeyError, TypeError):
        # 如果索引错误、键错误或类型错误，返回默认值
        return default

async def safe_request_data(async_func, path=None, default=None, method=GET, data=None):
    try:
        res = await async_func(method=method, data=data)
        if path is not None:
          return deep_get(res, path, default)
        else:
          return res
    except httpx.RequestError as exc:
        _LOGGER.debug(f"An error occurred while requesting {exc.request.url}")
    except httpx.HTTPStatusError as exc:
        _LOGGER.debug(f"Error response {exc.response.status_code} while requesting {exc.request.url}")
    except httpx.HTTPError as exc:
        _LOGGER.debug(f"Error while requesting {exc.request.url}")
    return default
