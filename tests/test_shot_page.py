import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
from pathlib import Path
import tempfile
import hashlib
import shutil
import subprocess
import threading
import unittest
from urllib.request import urlopen
from urllib.error import HTTPError

SCRIPT = Path(__file__).resolve().parents[1] / 'packages/shot-page/skill/scripts/shot-page.py'
spec = importlib.util.spec_from_file_location('shot_page', SCRIPT)
shot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shot)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class ShotPageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'pages'
        shot.initialize(self.root, 'https://example.test.ts.net:8443')
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(
            QuietHandler, directory=str(self.root / 'public')))
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.pages = shot.Pages(self.root, self.base)

    def stage(self, name='demo'):
        asset = Path(self.tmp.name) / f'{name}.png'
        asset.write_bytes(b'explicit test asset')
        folder = self.pages.add(name, [asset])
        (folder / 'index.html').write_text('<!doctype html><title>Review</title><p>Before and after</p>')
        return folder

    def test_private_staging_publish_and_verified_removal(self):
        folder = self.stage()
        with self.assertRaises(HTTPError) as absent:
            urlopen(self.pages.url('demo'))
        self.assertEqual(absent.exception.code, 404)
        absent.exception.close()
        url = self.pages.publish('demo')
        with urlopen(url + 'demo.png') as response:
            self.assertEqual(response.read(), b'explicit test asset')
        self.pages.remove('demo')
        self.assertFalse(folder.exists())
        self.assertEqual(list((self.root / 'retained').iterdir()), [])
        with self.assertRaises(HTTPError) as absent:
            urlopen(url)
        self.assertEqual(absent.exception.code, 404)
        absent.exception.close()

    def test_wrong_content_rolls_back_publication(self):
        folder = self.stage()
        self.pages.check = lambda url: (200, b'another service')
        with self.assertRaises(ValueError):
            self.pages.publish('demo')
        self.assertTrue((folder / 'index.html').exists())
        self.assertFalse((self.root / 'public/demo').exists())

    def test_failed_withdrawal_check_retains_recoverable_copy(self):
        self.stage()
        self.pages.publish('demo')
        self.pages.check = lambda url: (200, b'stale')
        with self.assertRaisesRegex(ValueError, 'Retained copy'):
            self.pages.remove('demo')
        retained = list((self.root / 'retained').iterdir())
        self.assertEqual(len(retained), 1)
        self.assertTrue((retained[0] / 'demo.png').is_file())
        self.assertFalse((self.root / 'public/demo').exists())

    def test_symlinks_and_traversal_cannot_publish_other_files(self):
        folder = self.stage()
        (folder / 'secret.html').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):
            self.pages.publish('demo')
        for name in ('../demo', '.', 'a/b', 'A', '-demo'):
            with self.assertRaises(ValueError):
                self.pages.publish(name)
        self.assertFalse((self.root / 'public/demo').exists())

    def test_one_page_cannot_replace_or_remove_another(self):
        self.stage('first')
        self.stage('second')
        self.pages.publish('first')
        self.pages.publish('second')
        with self.assertRaises(ValueError):
            self.pages.publish('first')
        self.pages.remove('first')
        with urlopen(self.pages.url('second')) as response:
            self.assertEqual(response.status, 200)

    def test_missing_asset_leaves_existing_stage_unchanged(self):
        folder = self.stage()
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        with self.assertRaises(ValueError):
            self.pages.add('demo', [Path(self.tmp.name) / 'missing.png'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})

    def test_initialization_refuses_foreign_storage_and_public_urls(self):
        with self.assertRaises(ValueError):
            shot.initialize(self.root, 'https://example.test.ts.net')
        for url in ('http://example.test.ts.net', 'https://public.example.com',
                    'https://example.test.ts.net/private', 'https://user@example.test.ts.net'):
            with self.assertRaises(ValueError):
                shot.initialize(Path(self.tmp.name) / 'invalid', url)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required for recording verification')
    def test_recording_frames_show_different_moments(self):
        video = Path(self.tmp.name) / 'motion.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi',
                        '-i', 'testsrc2=size=160x90:rate=15', '-t', '2',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(video)], check=True)
        output = Path(self.tmp.name) / 'frames'
        shot.frames(video, output)
        frames = list(output.glob('*.png'))
        self.assertEqual(len(frames), 6)
        self.assertEqual(len({hashlib.sha256(p.read_bytes()).digest() for p in frames}), 6)
        with self.assertRaises(FileExistsError):
            shot.frames(video, output)

    def test_inventory_distinguishes_drafts_from_published_pages(self):
        self.assertEqual(self.pages.listing(), 'No pages')
        self.stage('draft')
        self.stage('review')
        self.pages.publish('review')
        self.assertEqual(self.pages.listing(), 'staged: draft\npublic: review')
