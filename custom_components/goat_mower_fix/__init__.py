"""Make the Ecovacs GOAT O1200 mower start from Home Assistant.

deebot-client sends the vacuum command "clean_V2" to the GOAT O1200 (classes 2i0fns / 0jbd6s).
The mower firmware never answers it, so Start/Pause/Resume fail in Home Assistant while Dock works.
The mower does accept "clean" with the nested V2 content: {"act": ..., "content": {"type": "auto"}}.

This integration only swaps that one command in the device capabilities of these classes.
The built-in Ecovacs integration itself stays untouched. Once deebot-client handles the mower
correctly, the swap no longer applies (a warning is logged) and this integration can be removed.

Upstream fix: https://github.com/DeebotUniverse/client.py (pull request "fix(2i0fns): send clean ...").
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

DOMAIN = "goat_mower_fix"
CLASSES = ("2i0fns", "0jbd6s")  # GOAT O1200; 0jbd6s shares the same hardware file
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)
_LOGGER = logging.getLogger(__name__)


def _mower_command():
    from deebot_client.commands.json.clean import Clean

    class CleanMower(Clean):
        """'clean' with nested content; an empty type is rejected with code 20003."""

        def _get_args(self, action) -> dict[str, Any]:
            return {"act": action.value, "content": {"type": "auto"}}

    return CleanMower


def _swap(info, command, cls: str) -> bool:
    action = info.capabilities.clean.action
    if action.command is command:
        return True
    name = getattr(action.command, "NAME", None)
    if name == "clean":  # already fixed (newer deebot-client or another patch)
        _LOGGER.info("GOAT mower fix not needed: class %s already sends 'clean'", cls)
        return True
    if name != "clean_V2":
        _LOGGER.warning(
            "GOAT mower fix not applied: class %s already uses %s (deebot-client updated?). "
            "You can probably remove this integration.",
            cls, getattr(action.command, "__name__", action.command),
        )
        return False
    object.__setattr__(action, "command", command)  # capabilities are frozen dataclasses
    return True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    from deebot_client import hardware

    command = _mower_command()
    for cls in CLASSES:
        try:
            module = await hass.async_add_executor_job(importlib.import_module, f"deebot_client.hardware.{cls}")
        except ModuleNotFoundError:
            continue
        original = module.get_device_info

        def get_device_info(_original=original, _cls=cls):
            info = _original()
            _swap(info, command, _cls)
            return info

        module.get_device_info = get_device_info
        # capabilities already loaded (Ecovacs started before us): patch them directly
        info = hardware._DEVICES.get(cls) or get_device_info()
        if _swap(info, command, cls):
            _LOGGER.info("GOAT mower fix active: class %s starts with 'clean'", cls)
    return True
