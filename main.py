import argparse
import os
import subprocess

from LocalVPNExceptions import NoSuchDirectoryException, ServerConfigExistException


class WireGuardServer:
    """Utility for creating WireGuard connected configs"""

    def __init__(self, path: str, ip: str, name: str, port: str):
        self.current_client_ip = None
        self.current_client_public = self.current_client_private = None
        self.server_public = self.server_privet = None

        self.path = path
        self.ip = ip
        self.clients = []
        self.port = port
        self.name = name

        self._check_exist_config()
        self._setup_server_config()

    def _check_exist_config(self):
        if os.path.exists(os.path.join(self.path, "Data", "Configurations", self.name + ".conf")):
            message = f"Server config '{self.name + '.conf'}' already exists. Choose another name or delete existing"
            raise ServerConfigExistException(message)

    def _setup_server_config(self):
        if not os.path.exists(self.path):
            message = f"No such WireGuard directory '{self.path}'"
            raise NoSuchDirectoryException(message)
        self._gen_server_keys()
        self.server_public, self.server_privet = self._get_keys()
        os.mkdir(os.path.join(self.path, "clients_keys", self.name))
        os.mkdir(f"./clients_configs/{self.name}")
        with open(os.path.join(self.path, "Data", "Configurations", self.name + ".conf"), "w+",
                  encoding="utf-16") as config_file:
            config = self._server_config_text()
            config_file.write(config)

    def _gen_server_keys(self):
        command = f"cd \"{self.path}\" | wg.exe genkey | " \
                  f"Tee-Object -FilePath \"server_keys/{self.name + '_privet.key'}\" | " \
                  f"wg.exe pubkey | " \
                  f"Tee-Object -FilePath \"server_keys/{self.name + '_public.key'}\""
        self._execute_command(command)

    def _get_keys(self, client_id=None):
        if client_id is None:
            public = open(os.path.join(self.path, "server_keys", self.name + "_public.key"),
                          encoding='utf-16').read().split()[0]
            private = open(os.path.join(self.path, "server_keys", self.name + "_privet.key"),
                           encoding='utf-16').read().split()[0]
        else:
            public = open(os.path.join(self.path, "clients_keys", self.name,
                                       f"client{client_id}_public.key"), encoding='utf-16').read().split()[0]
            private = open(os.path.join(self.path, "clients_keys", self.name,
                                        f"client{client_id}_privet.key"), encoding='utf-16').read().split()[0]
        return public, private

    def _server_config_text(self):
        config = f"""[Interface]
PrivateKey = {self.server_privet}
Address = {self.ip}/24
ListenPort = {self.port}

"""
        return config

    def create_client(self):
        if self.server_public is None:
            pass
        current_client = self._check_last_client()
        command = f"cd \"{self.path}\" | wg.exe genkey | " \
                  f"Tee-Object -FilePath \"clients_keys/{self.name}/client{current_client}_privet.key\" | " \
                  f"wg.exe pubkey | " \
                  f"Tee-Object -FilePath \"clients_keys/{self.name}/client{current_client}_public.key\""
        self._execute_command(command)
        self.current_client_public, self.current_client_private = self._get_keys(client_id=current_client)
        self.current_client_ip = self._client_ip(current_client)
        client_config, server_config = self._client_config_text()
        with open(f"./clients_configs/{self.name}/client{current_client}.conf", mode="w+", encoding="utf-16") \
                as client_config_file:
            client_config_file.write(client_config)

        with open(os.path.join(self.path, "Data", "Configurations", self.name + ".conf"), mode="a",
                  encoding="utf-16") as client_config_file:
            client_config_file.write(server_config)

    def _check_last_client(self):
        return len(os.listdir(os.path.join(self.path, "clients_keys", self.name)))

    def _client_ip(self, client_id: int):
        current_client_ip = self.ip.split(".")
        return ".".join(current_client_ip[:-1]) + "." + str(int(current_client_ip[-1]) + client_id + 1)

    def _client_config_text(self):
        client_config = f"""[Interface]
PrivateKey = {self.current_client_private}
Address = {self.current_client_ip}/32
[Peer]
PublicKey = {self.server_public}
Endpoint = {self.ip}:{self.port}
AllowedIPs = {self.ip}/24"""

        server_config = f"""
[Peer]
PublicKey = {self.current_client_public}
AllowedIPs = {self.current_client_ip}/32
"""

        return client_config, server_config

    @staticmethod
    def _execute_command(command):
        completed_process = subprocess.run(
            ["powershell.exe", "-Command", command],
            capture_output=True,
            text=True,
        )
        return completed_process


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Local_VPN_starter",
        description="Creates a server and clients WireGuard configs",
        add_help=True
    )
    parser.add_argument("--name", default="server_test", help="Server config name", type=str)
    parser.add_argument("--path", default=r"C:\Program Files\WireGuard", help="Absolute path to WireGuard files",
                        type=str)
    parser.add_argument("--ip", default="10.0.0.1", help="Ip endpoint", type=str)
    parser.add_argument("--port", default="51820", help="Local VPN port", type=str)
    parser.add_argument("-c", "--clients", default=1, help="Count of clients configs", type=int)
    args = parser.parse_args()

    configs_create: WireGuardServer = WireGuardServer(args.path, args.ip, args.name, args.port)
    for i in range(args.clients):
        configs_create.create_client()


if __name__ == "__main__":
    main()
