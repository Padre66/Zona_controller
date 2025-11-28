from typing import List


class PermissionChecker:
    def __init__(self, config):
        # config: pyhocon ConfigTree
        self.config = config
        perms = config.get("permissions", {})
        self.admin_editable: List[str] = perms.get("admin_editable", [])
        self.root_only: List[str] = perms.get("root_only", [])

    def can_modify_path(self, role: str, path: str) -> bool:
        """
        path: felső szintű szekció (pl. system/network/tdoa)
        diag: semmit
        admin: admin_editable, ami nem root_only
        root: bármit
        """
        if role == "diag":
            return False
        if role == "root":
            return True
        if role == "admin":
            if self._matches(path, self.root_only):
                return False
            return self._matches(path, self.admin_editable)
        return False

    @staticmethod
    def _matches(path: str, patterns):
        for p in patterns:
            if p.endswith(".*"):
                prefix = p[:-2]
                if path == prefix or path.startswith(prefix + "."):
                    return True
            else:
                if path == p:
                    return True
        return False
