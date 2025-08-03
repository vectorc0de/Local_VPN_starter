from os import path

import pytest

from configs_setup.LocalVPNExceptions import *
from configs_setup.main import WireGuardServer


class TestWireGuardStarter:
    PATH: str = "tests\\WireGuard"

    @staticmethod
    def check_all_files(starter: WireGuardServer, clients_count) -> bool:
        clients = path.exists(path.join(".\\clients_configs", starter.name, f"client{clients_count - 1}.conf"))
        server = path.exists(path.join(starter.path, "Data", "Configurations", starter.name + ".conf")) or \
                 path.exists(path.join(starter.path, "Data", "Configurations", starter.name + ".conf.dpapi"))
        if clients and server:
            return True
        return False

    def test_v0_2_0(self):
        version = WireGuardServer.VERSION[1:].split(".")
        if not (version[0] == "0" and version[1] == "2"):
            return None
        with pytest.raises(Exception):
            starter = WireGuardServer(path=self.PATH, ip="10.0.0.1", name="test0", port="10000")
            starter.setup_server_config()
            starter.append_clients(clients_count=1)
            assert self.check_all_files(starter, clients_count=1)
            with pytest.raises(ServerConfigExistException):
                assert WireGuardServer(path=self.PATH, ip="10.0.0.1", name="test0", port="10000")
            with pytest.raises(NoSuchDirectoryException):
                assert WireGuardServer(path=".", ip="10.0.0.1", name="test0", port="10000")
