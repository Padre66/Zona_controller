import threading
from pathlib import Path
from typing import Any, Dict

from pyhocon import ConfigFactory, HOCONConverter

from .permissions import PermissionChecker


class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, path: str = "zona.conf"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init(path)
        return cls._instance

    def _init(self, path: str):
        self._path = Path(path)
        if not self._path.exists():
            raise FileNotFoundError(f"Config file not found: {self._path}")
        self._config = ConfigFactory.parse_file(str(self._path))
        self._config_lock = threading.RLock()

    @staticmethod
    def _deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> None:
        """
        Egyszerű rekurzív merge:
        - ha mindkét oldalon dict van → rekurzívan mergelünk
        - egyébként a src érték felülírja a dst-t
        """
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                ConfigManager._deep_merge(dst[k], v)
            else:
                dst[k] = v

    def get_config(self) -> Dict[str, Any]:
        with self._config_lock:
            return self._config.as_plain_ordered_dict()

    def save_config(self):
        with self._config_lock:
            text = HOCONConverter.convert(self._config, "hocon")
            self._path.write_text(text, encoding="utf-8")

    def update_from_dict(self, updates: Dict[str, Any], role: str):
        """
        Szekciónkénti merge: 'system', 'network', 'tdoa', stb.
        Role-alapú jogosultság a PermissionChecker-rel.
        """
        checker = PermissionChecker(self._config)
        with self._config_lock:
            for section, value in updates.items():
                if not checker.can_modify_path(role, section):
                    raise PermissionError(
                        f"Role {role} cannot modify section {section}"
                    )

                # Eredeti szekció lekérése dict formában
                orig_section = self._config.get(section, None)
                if hasattr(orig_section, "as_plain_ordered_dict"):
                    base = orig_section.as_plain_ordered_dict()
                elif isinstance(orig_section, dict):
                    base = dict(orig_section)
                else:
                    base = {}

                # Mély merge: csak a küldött mezők frissülnek, a többi megmarad
                self._deep_merge(base, value)

                # Visszakonvertálás ConfigTree-re, hogy HOCONConverter tudja kezelni
                subtree = ConfigFactory.from_dict({section: base})[section]
                self._config[section] = subtree

            self.save_config()
