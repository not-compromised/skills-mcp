#!/usr/bin/env python3
"""Stage, publish, and withdraw temporary private screenshot pages."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen


def slug(value):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value) or len(value) > 64:
        raise ValueError('Use a page name of at most 64 lowercase letters, digits, and dashes')
    return value


def regular(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Expected a regular file, not a link: {path}')
    return path


def fetch(url):
    try:
        with urlopen(url, timeout=10) as response:
            if response.url != url:
                raise ValueError('Unexpected redirect while checking the page')
            return response.status, response.read()
    except HTTPError as error:
        error.close()
        return error.code, b''


class Pages:
    def __init__(self, root, base_url, check=fetch):
        self.root = Path(root)
        self.base_url = base_url.rstrip('/')
        self.check = check

    @contextmanager
    def lock(self):
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError('Run init before managing pages')
        with (self.root / 'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for name in ('staged', 'public', 'retained'):
                path = self.root / name
                if path.is_symlink() or not path.is_dir():
                    raise ValueError(f'Invalid page storage directory: {path}')
            yield

    def page(self, section, name):
        path = self.root / section / slug(name)
        if path.is_symlink():
            raise ValueError(f'Refusing a page symlink: {path}')
        return path

    def url(self, name):
        return f'{self.base_url}/{slug(name)}/'

    def add(self, name, files):
        with self.lock():
            target = self.page('staged', name)
            if self.page('public', name).exists():
                raise ValueError('Page is published; choose a new name')
            sources = [regular(Path(f)) for f in files]
            names = [f.name for f in sources]
            if len(names) != len(set(names)):
                raise ValueError('Input filenames must be unique')
            for source in sources:
                if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', source.name):
                    raise ValueError(f'Use a simple asset filename: {source.name}')
                if source.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp4', '.css'):
                    raise ValueError(f'Unsupported asset: {source.name}')
                if (target / source.name).exists() or (target / source.name).is_symlink():
                    raise ValueError(f'Asset already exists: {source.name}')
            target.mkdir(mode=0o700, exist_ok=True)
            for source in sources:
                with source.open('rb') as src, (target / source.name).open('xb') as dst:
                    shutil.copyfileobj(src, dst)
            return target

    def publish(self, name):
        with self.lock():
            stage, live = self.page('staged', name), self.page('public', name)
            if live.exists():
                raise ValueError('Page is already published; choose a new name')
            regular(stage / 'index.html')
            for path in stage.iterdir():
                regular(path)
                if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', path.name):
                    raise ValueError(f'Unexpected filename in page: {path}')
                if path.suffix.lower() not in ('.html', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp4', '.css'):
                    raise ValueError(f'Unexpected file in page: {path}')
            expected = hashlib.sha256((stage / 'index.html').read_bytes()).digest()
            stage.rename(live)
            try:
                code, body = self.check(self.url(name))
                if code != 200 or hashlib.sha256(body).digest() != expected:
                    raise ValueError(f'Page verification failed, HTTP {code} or content mismatch')
            except Exception:
                live.rename(stage)
                raise
            return self.url(name)

    def remove(self, name):
        with self.lock():
            live = self.page('public', name)
            if not live.is_dir():
                raise ValueError('No published page with this name')
            retained = self.root / 'retained' / f'{slug(name)}-{time.time_ns()}'
            live.rename(retained)
            try:
                code, _ = self.check(self.url(name))
                if code != 404:
                    raise ValueError(f'Expected 404, received {code}')
            except Exception as error:
                raise ValueError(f'Page withdrawn, cleanup unverified. Retained copy: {retained}. {error}') from error
            shutil.rmtree(retained)
            return f'Removed {name}; verified HTTP 404'

    def listing(self):
        with self.lock():
            return '\n'.join(f'{section}: {p.name}' for section in ('staged', 'public', 'retained')
                             for p in sorted((self.root / section).iterdir())
                             if p.is_dir() or p.is_symlink()) or 'No pages'


def initialize(root, base_url):
    if not root.is_absolute():
        raise ValueError('Storage must use an absolute path outside version control')
    url = urlsplit(base_url)
    if (url.scheme != 'https' or not url.hostname or not url.hostname.endswith('.ts.net')
            or url.username or url.password or url.path not in ('', '/') or url.query or url.fragment):
        raise ValueError('Use an HTTPS Tailscale hostname, optionally with a dedicated port; no URL path')
    if root.exists() or root.is_symlink():
        raise ValueError(f'Storage already exists: {root}; inspect it before changing setup')
    root.mkdir(mode=0o700, parents=True)
    for name in ('staged', 'public', 'retained'):
        (root / name).mkdir(mode=0o700)
    (root / 'public' / 'index.html').write_text('<!doctype html><title>Shot Page</title><p>Open the review link shared with you.</p>\n')
    (root / 'config.json').write_text(json.dumps({'base_url': base_url.rstrip('/')}, indent=2) + '\n')


def frames(video, output):
    regular(video)
    # An exclusive directory prevents mixing frames from different recordings.
    output.mkdir(mode=0o700)
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                             '-of', 'csv=p=0', str(video.resolve())], check=True, capture_output=True, text=True)
    duration = float(result.stdout)
    if not 0 < duration < float('inf'):
        raise ValueError('Video must have a finite positive duration')
    for index in range(6):
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(duration * index / 6),
                        '-i', str(video.resolve()), '-frames:v', '1', str(output / f'frame-{index + 1}.png')], check=True)
        regular(output / f'frame-{index + 1}.png')
    return str(output)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.home() / '.local/share/shot-page')
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init')
    init.add_argument('--base-url', required=True)
    add = commands.add_parser('add')
    add.add_argument('name')
    add.add_argument('files', nargs='+')
    for command in ('publish', 'remove'):
        commands.add_parser(command).add_argument('name')
    commands.add_parser('list')
    extract = commands.add_parser('frames')
    extract.add_argument('video', type=Path)
    extract.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'frames':
            print(frames(args.video, args.output))
            return
        if args.command == 'init':
            initialize(args.root, args.base_url)
            print(f'Initialized {args.root}. Hosting is not enabled; follow the package setup guide.')
            return
        config = json.loads(regular(args.root / 'config.json').read_text())
        pages = Pages(args.root, config['base_url'])
        if args.command == 'add':
            print(pages.add(args.name, args.files))
        elif args.command == 'list':
            print(pages.listing())
        else:
            print(getattr(pages, args.command)(args.name))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
