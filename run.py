from zona_controller.app import create_app
from zona_controller.config import ConfigManager


if __name__ == "__main__":
    # betöltjük a konfigot, HTTP host/port innen
    cfg = ConfigManager("zona.conf").get_config()
    net = cfg.get("network", {})
    host = net.get("http_host", "0.0.0.0")
    port = int(net.get("http_port", 51200))

    app = create_app("zona.conf")
    # FONTOS: use_reloader=False, így csak EGY processz indul
    app.run(host=host, port=port, debug=True, use_reloader=False)
