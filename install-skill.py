#!/usr/bin/env python3
"""Link a packaged skill into an agent CLI without replacing existing skills."""
import argparse
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def install(name, client, home, environ):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
        raise ValueError('Use a package name such as unslop')
    package = ROOT / 'packages' / name
    if (package / 'install.py').exists():
        raise ValueError(f'{name} requires its own runtime installer: {package / "install.py"}')
    source = package / 'skill'
    if not (source / 'SKILL.md').is_file():
        raise ValueError(f'No standalone skill in package: {name}')
    if client == 'codex':
        config = Path(environ.get('CODEX_HOME', home / '.codex'))
    else:
        config = Path(environ.get('CLAUDE_CONFIG_DIR', home / '.claude'))
    if not config.is_absolute():
        raise ValueError('The agent configuration directory must be an absolute path')
    target = config / 'skills' / name
    if target.is_symlink() and target.resolve() == source.resolve():
        return target
    if target.exists() or target.is_symlink():
        raise FileExistsError(f'{target} already exists; inspect it before replacing it')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source.resolve(), target_is_directory=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package')
    parser.add_argument('--client', choices=['codex', 'claude'], required=True)
    args = parser.parse_args()
    try:
        target = install(args.package, args.client, Path.home(), os.environ)
    except (ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Installed {args.package}: {target} -> {target.resolve()}')
    print('Restart your agent CLI to load the skill. Keep this checkout at its current path.')


if __name__ == '__main__':
    main()
