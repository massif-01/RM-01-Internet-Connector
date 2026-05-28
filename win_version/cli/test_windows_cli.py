import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest import mock


CLI_PATH = Path(__file__).with_name("cli.py")
SERVICE_PATH = Path(__file__).with_name("network_service_windows.py")


def load_cli_as_windows():
    module_name = "rm01_windows_cli_under_test"
    sys.modules.pop(module_name, None)
    with mock.patch("platform.system", return_value="Windows"):
        spec = importlib.util.spec_from_file_location(module_name, CLI_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
    return module


def load_windows_service():
    module_name = "rm01_windows_service_under_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SERVICE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@dataclass
class FakeInterface:
    name: str
    description: str
    mac: str


class FakeWindowsService:
    STATIC_IP = "10.10.99.100"

    def __init__(self, is_admin=True, adapter=True, upstream=True, sharing=True, last_error=None):
        self._is_admin = is_admin
        self._adapter = adapter
        self._upstream = upstream
        self._sharing = sharing
        self.last_error = last_error
        self.calls = []

    def is_admin(self):
        self.calls.append(("is_admin",))
        return self._is_admin

    def detect_adapter(self):
        self.calls.append(("detect_adapter",))
        if not self._adapter:
            return None
        return FakeInterface("Ethernet 3", "AX88179A USB Ethernet Adapter", "00:11:22:33:44:55")

    def find_upstream_interface(self, exclude):
        self.calls.append(("find_upstream_interface", exclude))
        if not self._upstream:
            return None
        return FakeInterface("Wi-Fi", "Upstream Network", "AA:BB:CC:DD:EE:FF")

    def enable_sharing(self, rm01_iface, upstream_iface, password=None):
        self.calls.append(("enable_sharing", rm01_iface, upstream_iface, password))
        return True, "ok"

    def disable_sharing(self, rm01_iface, upstream_iface=None, password=None, restore_dhcp=False):
        self.calls.append(("disable_sharing", rm01_iface, upstream_iface, password, restore_dhcp))
        return True, "ok"

    def is_sharing_enabled(self, private_iface, public_iface=None):
        self.calls.append(("is_sharing_enabled", private_iface, public_iface))
        return self._sharing

    def get_interface_ip(self, interface):
        self.calls.append(("get_interface_ip", interface))
        return "10.10.99.100"

    def get_interface_stats(self, interface):
        self.calls.append(("get_interface_stats", interface))
        return (1024, 2048)


class WindowsCliTests(unittest.TestCase):
    def setUp(self):
        self.cli_module = load_cli_as_windows()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def make_cli(self, service):
        self.cli_module.NetworkService = lambda: service
        cli = self.cli_module.CLI()
        cli._state_file = os.path.join(self.tmpdir.name, "state")
        return cli

    def capture(self, func, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = func(*args)
        return rc, output.getvalue()

    def test_windows_connect_requires_admin_before_detection(self):
        service = FakeWindowsService(is_admin=False)
        cli = self.make_cli(service)

        rc, output = self.capture(cli.cmd_connect)

        self.assertEqual(rc, 1)
        self.assertIn("Administrator privileges", output)
        self.assertEqual(service.calls, [("is_admin",)])

    def test_windows_connect_ignores_password_prompt_and_uses_windows_nat_service(self):
        service = FakeWindowsService()
        cli = self.make_cli(service)

        rc, output = self.capture(cli.cmd_connect)

        self.assertEqual(rc, 0)
        self.assertNotIn("Password", output)
        self.assertIn(("enable_sharing", "Ethernet 3", "Wi-Fi", None), service.calls)

    def test_windows_status_uses_windows_nat_status_instead_of_linux_checks(self):
        service = FakeWindowsService()
        cli = self.make_cli(service)
        cli._save_state("Ethernet 3", "Wi-Fi")

        rc, output = self.capture(cli.cmd_status)

        self.assertEqual(rc, 0)
        self.assertIn("Status: Connected", output)
        self.assertIn(("is_sharing_enabled", "Ethernet 3", "Wi-Fi"), service.calls)
        self.assertIn(("get_interface_ip", "Ethernet 3"), service.calls)
        self.assertIn(("get_interface_stats", "Ethernet 3"), service.calls)

    def test_detect_failure_prints_service_diagnostic(self):
        service = FakeWindowsService(adapter=False, last_error="PowerShell command failed")
        cli = self.make_cli(service)

        rc, output = self.capture(cli.cmd_detect)

        self.assertEqual(rc, 1)
        self.assertIn("Diagnostic: PowerShell command failed", output)

    def test_status_failure_prints_service_diagnostic(self):
        service = FakeWindowsService(sharing=False, last_error="Windows NAT query failed")
        cli = self.make_cli(service)

        rc, output = self.capture(cli.cmd_status)

        self.assertEqual(rc, 0)
        self.assertIn("Status: Not Connected", output)
        self.assertIn("Diagnostic: Windows NAT query failed", output)


class WindowsServiceTests(unittest.TestCase):
    def setUp(self):
        self.service_module = load_windows_service()

    def test_powershell_json_failure_records_diagnostic(self):
        service = self.service_module.WindowsNetworkService()
        completed = subprocess.CompletedProcess(
            args=["powershell.exe"],
            returncode=1,
            stdout="",
            stderr="access is denied",
        )

        with mock.patch.object(service, "_run_powershell", return_value=completed):
            payload = service._run_powershell_json("[pscustomobject]@{} | ConvertTo-Json", timeout=1)

        self.assertIsNone(payload)
        self.assertEqual(service.last_error, "Permission denied. Please run as Administrator.")

    def test_enable_sharing_restores_dhcp_when_windows_nat_fails(self):
        service = self.service_module.WindowsNetworkService()
        success_result = subprocess.CompletedProcess(args=["netsh"], returncode=0, stdout="", stderr="")
        calls = []

        def fake_netsh(args, timeout):
            calls.append(tuple(args))
            return success_result

        with mock.patch.object(service, "_run_netsh", side_effect=fake_netsh), \
                mock.patch.object(service, "_assert_nat_available", return_value=(True, "Windows NAT provider available")), \
                mock.patch.object(service, "_has_target_address", return_value=False), \
                mock.patch.object(service, "_disable_nat", return_value=(True, "Windows NAT disabled")), \
                mock.patch.object(service, "_enable_nat", return_value=(False, "Windows NAT failed")), \
                mock.patch("subprocess.run", return_value=success_result):
            success, error = service.enable_sharing("Ethernet 3", "Wi-Fi")

        self.assertFalse(success)
        self.assertEqual(error, "Windows NAT failed")
        self.assertIn(("interface", "ip", "set", "address", "name=Ethernet 3", "source=dhcp"), calls)
        self.assertIn(("interface", "ip", "set", "dns", "name=Ethernet 3", "source=dhcp"), calls)

    def test_enable_sharing_fails_before_network_mutation_when_nat_provider_missing(self):
        service = self.service_module.WindowsNetworkService()

        with mock.patch.object(service, "_assert_nat_available", return_value=(False, "WinNAT unavailable")), \
                mock.patch.object(service, "_run_netsh") as netsh, \
                mock.patch.object(service, "_disable_nat") as disable_nat, \
                mock.patch.object(service, "_enable_nat") as enable_nat:
            success, error = service.enable_sharing("Ethernet 3", "Wi-Fi")

        self.assertFalse(success)
        self.assertEqual(error, "WinNAT unavailable")
        netsh.assert_not_called()
        disable_nat.assert_not_called()
        enable_nat.assert_not_called()


if __name__ == "__main__":
    unittest.main()
