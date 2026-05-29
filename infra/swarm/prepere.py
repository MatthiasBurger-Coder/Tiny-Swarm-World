import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "multipass")))

from multipass.multipass_network_setup import MultipassNetworkSetup


class PrepareMultipass:
    def __init__(self):
        self.multipass_network_setup = MultipassNetworkSetup()

    def setup(self):
        self.multipass_network_setup.setup()

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script requires administrator privileges. Restarting with sudo...")
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    prepare_multipass = PrepareMultipass()
    prepare_multipass.setup()
