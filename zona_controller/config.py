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
        self._config_lock = threading.Lock()

    def get_config(self) -> Dict[str, Any]:
        with self._config_lock:
            return self._config.as_plain_ordered_dict()

    def save_config(self):
        with self._config_lock:
            text = HOCONConverter.convert(self._config, "hocon")
            self._path.write_text(text, encoding="utf-8")

    def update_from_dict(self, updates: Dict[str, Any], role: str):
        """
        Szekciónkénti shallow merge: 'system', 'network', 'tdoa', stb.
        Role-alapú jogosultság a PermissionChecker-rel.
        """
        checker = PermissionChecker(self._config)
        with self._config_lock:
            for section, value in updates.items():
                if not checker.can_modify_path(role, section):
                    raise PermissionError(f"Role {role} cannot modify section {section}")
                self._config[section] = value
            self.save_config()
