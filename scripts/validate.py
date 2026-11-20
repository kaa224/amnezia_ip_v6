#!/usr/bin/env python3
"""Static repository checks only; never validate or display production secrets."""
import ast
import configparser
import ipaddress
import json
from pathlib import Path
import re
import shlex
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DOC4 = tuple(ipaddress.ip_network(n) for n in ('192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24'))
DOC6 = ipaddress.ip_network('2001:db8::/32')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rules_check(path):
    """Conservative shape check, NOT a replacement for kernel restore --test."""
    table = None
    defined = set()
    for line in path.read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        if line.startswith('*'):
            require(table is None and line in ('*filter', '*nat'), 'invalid table')
            table = line[1:]
            defined = set()
        elif line == 'COMMIT':
            require(table is not None, 'unmatched COMMIT')
            table = None
        else:
            require(table is not None, 'rule outside table')
            parts = shlex.split(line)
            require(parts[0] in ('-N', '-A', '-I'), 'non-additive command')
            if parts[0] == '-N':
                require(parts[1].startswith('PV31') and parts[1] not in defined, 'chain collision')
                defined.add(parts[1])
            elif parts[0] == '-A':
                require(parts[1] in defined, 'body must belong to own chain')
            else:
                require(parts[1] in ('INPUT', 'FORWARD', 'POSTROUTING') and parts[2] == '1', 'jump shape')
            if '-j' in parts:
                jump = parts[parts.index('-j') + 1]
                require(jump in defined or jump in ('ACCEPT', 'DROP', 'MASQUERADE'), 'unknown target')
    require(table is None, 'missing COMMIT')


def check(root=ROOT):
    v = json.loads((root / 'examples/variables.json').read_text())
    for name in ('EXIT4', 'RELAY4', 'DIRECT_NET4', 'RELAY_NET4'):
        net = ipaddress.ip_network(v[name], strict=False)
        require(any(net.subnet_of(n) for n in DOC4), 'non-documentation IPv4')
    for name in ('EXIT6', 'RELAY6', 'DIRECT_NET6', 'RELAY_NET6'):
        require(ipaddress.ip_network(v[name], strict=False).subnet_of(DOC6), 'non-documentation IPv6')
    require(not ipaddress.ip_network(v['DIRECT_NET4']).overlaps(ipaddress.ip_network(v['RELAY_NET4'])), 'overlap')
    require(not ipaddress.ip_network(v['DIRECT_NET6']).overlaps(ipaddress.ip_network(v['RELAY_NET6'])), 'overlap6')
    require(len({v[k] for k in ('DIRECT_PORT', 'BACKEND_PORT', 'FRONTEND_PORT')}) == 3, 'port collision')
    realm = tomllib.loads((root / 'examples/realm.toml.example').read_text())
    require(realm['network']['no_tcp'] and realm['network']['use_udp'], 'UDP only')
    ep, = realm['endpoints']
    require(ep == {'listen': f"{v['RELAY4']}:{v['FRONTEND_PORT']}", 'remote': f"[{v['EXIT6']}]:{v['BACKEND_PORT']}", 'through': v['RELAY6']}, 'backend/source mismatch')
    for p in (root / 'examples').glob('*.rules.example'):
        rules_check(p)
    for name in ('client', 'awg-server'):
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.read(root / f'examples/{name}.conf.example')
        require({'Interface', 'Peer'} <= set(parser.sections()), 'missing section')
    for path in list((root / 'scripts').glob('*.py')) + list((root / 'tests').glob('*.py')):
        ast.parse(path.read_text(), filename=str(path))
    for path in root.rglob('*.md'):
        if '.git' in path.parts:
            continue
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' in link or link.startswith('#'):
                continue
            require((path.parent / link.split('#')[0]).exists(), 'broken relative link')
    # Only placeholder values allowed in sensitive fields in all example configs.
    for path in (root / 'examples').glob('*.conf.example'):
        for line in path.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                name, value = map(str.strip, line.split('=', 1))
                if name in ('PrivateKey', 'PublicKey', 'PresharedKey', 'HeaderProtectionKey'):
                    require(value.startswith('REPLACE_'), 'non-placeholder key material')
    return True


if __name__ == '__main__':
    try:
        check()
    except (ValueError, KeyError, OSError, SyntaxError, configparser.Error):
        print('Static validation failed; no input values displayed.', file=sys.stderr)
        sys.exit(1)
    print('Static template checks passed. No kernel, service or end-to-end validation performed.')
