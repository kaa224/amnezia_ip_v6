import importlib.util
import os
from pathlib import Path
import shlex
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class ProjectTests(unittest.TestCase):
    def test_repository_static(self):
        self.assertTrue(module('validate').check())

    def test_private_copy_and_refusal(self):
        prepare = module('prepare').prepare
        with tempfile.TemporaryDirectory() as tmp:
            target = prepare(Path(tmp) / 'draft')
            self.assertEqual(target.stat().st_mode & 0o777, 0o700)
            for folder in target.iterdir():
                self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
                for path in folder.iterdir():
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                    self.assertEqual(path.read_bytes(), (ROOT / folder.name / path.name).read_bytes())
            with self.assertRaises(ValueError):
                prepare(target)
        with self.assertRaises(ValueError):
            prepare(ROOT / '.secrets')

    def test_no_network_or_process_apis(self):
        for path in (ROOT / 'scripts').glob('*.py'):
            code = path.read_text()
            for forbidden in ('import socket', 'import subprocess', 'import requests', 'os.system(', 'os.popen(', 'urllib', 'eval(', 'exec('):
                self.assertNotIn(forbidden, code)

    def test_reject_global_flush(self):
        validate = module('validate')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.rules'
            for body in ('*filter\n-F\nCOMMIT\n', '*filter\n-A INPUT -j ACCEPT\nCOMMIT\n', '*filter\n-N OTHER\nCOMMIT\n', '*filter\n-N PV31_TEST\n'):
                path.write_text(body)
                with self.assertRaises(ValueError):
                    validate.rules_check(path)

    def test_firewall_boundaries(self):
        v4 = (ROOT / 'examples/exit.v4.rules.example').read_text()
        v6 = (ROOT / 'examples/exit.v6.rules.example').read_text()
        for pre, iface, net in [('PV31D', 'awg31d', '203.0.113.0/26'), ('PV31R', 'awg31r', '203.0.113.64/26')]:
            self.assertIn(f'-A {pre}_H -j DROP', v4)
            self.assertNotIn(f'-A {pre}_H -p tcp --dport 22', v4)
            for block in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '169.254.0.0/16', '100.64.0.0/10'):
                self.assertLess(v4.index(f'-A {pre}_O -d {block} -j DROP'), v4.index(f'-A {pre}_O -s {net}'))
            for suffix in ('H6', 'O6', 'I6'):
                self.assertIn(f'-A {pre}_{suffix} -j DROP', v6)
            self.assertGreater(v4.index(f'-I INPUT 1 -i {iface}'), v4.index('-I INPUT 1 -p udp'))
        self.assertNotIn('-A PV31R_P -d', v4)
        self.assertNotIn('-A PV31D_P6 -s', v6)
        self.assertIn('-A PV31R_P6 -s 2001:db8:20::20/128 -d 2001:db8:10::10/128 -j ACCEPT', v6)
        self.assertNotIn('MASQUERADE', v6)
        for line in v4.splitlines():
            if line.startswith('-A') and '_H ' in line:
                self.assertTrue(line.endswith('-j DROP'))  # optional HTTPS is commented

    def test_client_server_separation(self):
        server = (ROOT / 'examples/awg-server.conf.example').read_text()
        client = (ROOT / 'examples/client.conf.example').read_text()
        self.assertNotIn('AllowedIPs = 0.0.0.0/0', server)
        self.assertIn('AllowedIPs = 0.0.0.0/0, ::/0', client)
        self.assertIn('MTU = 1280', client)
        for p in (ROOT / 'systemd').glob('*'):
            self.assertNotIn('route replace default', p.read_text())
            self.assertNotIn('awg-quick up', p.read_text())

    def test_systemd_shell_syntax(self):
        # sh -n is invoked only by the TEST harness, not any shipped scripts.
        import subprocess
        for path in (ROOT / 'systemd').glob('*.example'):
            for line in path.read_text().splitlines():
                if line.startswith('ExecStartPost=/bin/sh -c '):
                    argv = shlex.split(line.split('=', 1)[1])
                    subprocess.run(['/bin/sh', '-n', '-c', argv[-1].replace('$$', '$')], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
