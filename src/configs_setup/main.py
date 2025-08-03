import argparse
import os
import subprocess

from configs_setup.LocalVPNExceptions import NoSuchDirectoryException, ServerConfigExistException


class WireGuardServer:
    VERSION = "v0.2.0"
    # TODO: make config delete function
    """Utility for creating WireGuard connected configs"""

    def __init__(self, path: str, ip: str, name: str, port: str):
        # TODO: make program's start setup less complicated
        self.current_client_ip = None
        self.current_client_public = self.current_client_private = None
        self.server_public = self.server_privet = None

        self.server_config = ""
        self.path = path
        self.ip = ip
        self.port = port
        self.name = name

        self._check_wg_exist()
        self._check_exist_config()

    def _check_wg_exist(self):
        if not os.path.exists(self.path) or not os.path.isfile(os.path.join(self.path, "wg.exe")):
            message = f"No such WireGuard directory '{os.path.abspath(self.path)}'"
            raise NoSuchDirectoryException(message)

    def _check_exist_config(self):
        if os.path.exists(os.path.join(self.path, "Data", "Configurations", self.name + ".conf")):
            message = f"Server config '{self.name + '.conf'}' already exists. Choose another name or delete existing"
            raise ServerConfigExistException(message)

    def setup_server_config(self):
        if not os.path.exists(os.path.join(self.path, "server_keys")):
            os.mkdir(os.path.join(self.path, "server_keys"))
        if not os.path.exists(os.path.join(self.path, "clients_keys")):
            os.mkdir(os.path.join(self.path, "clients_keys"))
        self._gen_server_keys()
        self.server_public, self.server_privet = self._get_keys()
        os.mkdir(os.path.join(self.path, "clients_keys", self.name))
        if not os.path.exists("clients_configs"):
            os.mkdir(".\\clients_configs\\")
        os.mkdir(f".\\clients_configs\\{self.name}")
        self.server_config = self._server_config_text()

    def _gen_server_keys(self):
        command = f"cd \"{self.path}\" | .\\wg.exe genkey | " \
                  f"Tee-Object \"server_keys\\{self.name + '_privet.key'}\" | " \
                  f".\\wg.exe pubkey | " \
                  f"Tee-Object \"server_keys\\{self.name + '_public.key'}\""
        self._execute_command(command)

    def _get_keys(self, client_id=None):
        if client_id is None:
            public = open(os.path.join(self.path, "server_keys", self.name + "_public.key")).read().split()[0]
            private = open(os.path.join(self.path, "server_keys", self.name + "_privet.key"),
                           encoding='utf-16').read().split()[0]
        else:
            public = open(os.path.join(self.path, "clients_keys", self.name,
                                       f"client{client_id}_public.key"), encoding='utf-16').read().split()[0]
            private = open(os.path.join(self.path, "clients_keys", self.name,
                                        f"client{client_id}_privet.key"), encoding='utf-16').read().split()[0]
        return public, private

    def _server_config_text(self):
        # TODO: create templates for configs
        config = f"""[Interface]
PrivateKey = {self.server_privet}
Address = {self.ip}/24
ListenPort = {self.port}

"""
        return config

    def append_clients(self, clients_count: int, last_client_id: int = 0):
        # TODO: function to append clients later to config
        for i in range(last_client_id, clients_count + last_client_id):
            self._create_client(i)
        self._create_server_config()

    def _create_client(self, current_client: int):
        command = f"cd \"{self.path}\" | .\\wg.exe genkey | " \
                  f"Tee-Object -FilePath \"clients_keys/{self.name}/client{current_client}_privet.key\" | " \
                  f".\\wg.exe pubkey | " \
                  f"Tee-Object -FilePath \"clients_keys/{self.name}/client{current_client}_public.key\""
        self._execute_command(command)
        self.current_client_public, self.current_client_private = self._get_keys(client_id=current_client)
        self.current_client_ip = self._client_ip(current_client)
        client_config, server_config = self._client_config_text()
        with open(f"./clients_configs/{self.name}/client{current_client}.conf", mode="w+", encoding="utf-16") \
                as client_config_file:
            client_config_file.write(client_config)

        self.server_config += server_config

    def _client_ip(self, client_id: int):
        current_client_ip = self.ip.split(".")
        return ".".join(current_client_ip[:-1]) + "." + str(int(current_client_ip[-1]) + client_id + 1)

    def _client_config_text(self):
        # TODO: create templates for configs
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

    def _create_server_config(self):
        with open(os.path.join(self.path, "Data", "Configurations", self.name + ".conf"), "w+",
                  encoding="utf-16") as config_file:
            config_file.write(self.server_config)

    @staticmethod
    def _execute_command(command):
        completed_process = subprocess.run(
            ["powershell.exe", "-Command", command],
            capture_output=True,
            text=True,
        )
        print(completed_process.stderr)
        return completed_process


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Local_VPN_starter",
        description="Creates a server and clients WireGuard configs",
        add_help=True
    )
    parser.add_argument("--name", default="server_TEsttS", help="Server config name", type=str)
    parser.add_argument("--path", default=r"C:\Program Files\WireGuard", help="Absolute path to WireGuard files",
                        type=str)
    parser.add_argument("--ip", default="10.0.0.1", help="Ip endpoint", type=str)
    parser.add_argument("--port", default="51820", help="Local VPN port", type=str)
    parser.add_argument("-c", "--clients", default=1, help="Count of clients configs", type=int)
    args = parser.parse_args()

    configs_create: WireGuardServer = WireGuardServer(args.path, args.ip, args.name, args.port)
    configs_create.setup_server_config()
    configs_create.append_clients(args.clients)


if __name__ == "__main__":
    main()
