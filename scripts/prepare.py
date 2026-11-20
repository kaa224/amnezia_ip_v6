#!/usr/bin/env python3
"""Create a private local template copy. No SSH, network or service operations."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def prepare(destination):
    target = Path(destination).expanduser().resolve()
    if target == ROOT or ROOT in target.parents:
        raise ValueError('destination must be outside checkout')
    if target.exists():
        raise ValueError('destination already exists; refusing overwrite')
    # Avoid changing permissions of pre-existing parent directories.
    if not target.parent.is_dir():
        raise ValueError('parent directory must already exist')
    target.mkdir(mode=0o700)
    for folder in ('examples', 'systemd'):
        output = target / folder
        output.mkdir(mode=0o700)
        for source in sorted((ROOT / folder).iterdir()):
            if source.is_file() and not source.is_symlink():
                with (output / source.name).open('xb') as stream:
                    os.chmod(stream.name, 0o600)
                    stream.write(source.read_bytes())
    return target


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: prepare.py /absolute/path/outside-checkout/new-directory')
        prepare(sys.argv[1])
    except (ValueError, OSError):
        print('Preparation refused; use a new writable directory outside checkout.', file=sys.stderr)
        sys.exit(1)
    print('Private local template copy created; placeholders remain. No servers contacted.')
