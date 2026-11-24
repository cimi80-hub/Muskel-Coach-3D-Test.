"""Package the static test PWA for a single Cloudflare Pages project."""
import argparse
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'index.html', 'test-environment.js', 'test-bootstrap.js', 'test-app.js',
    'test-sw.js', 'manifest.webmanifest', 'icon-180.png', 'icon-192.png',
    'icon-512.png',
)

HEADERS = """/*
  X-Robots-Tag: noindex, nofollow
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: no-referrer

/test-sw.js
  Cache-Control: no-cache

/test-environment.js
  Cache-Control: no-cache
"""


def build(host: str, output: Path) -> None:
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.pages\.dev', host):
        raise ValueError('Erwartet wird genau ein Projekt-Hostname wie mein-test.pages.dev.')
    entries = {name: (ROOT / name).read_bytes() for name in FILES}
    placeholder = b"const MUSKEL_TEST_ORIGIN = '';"
    config = entries['test-environment.js']
    if config.count(placeholder) != 1:
        raise ValueError('Der Origin-Platzhalter in test-environment.js fehlt oder ist mehrdeutig.')
    entries['test-environment.js'] = config.replace(
        placeholder, f"const MUSKEL_TEST_ORIGIN = 'https://{host}';".encode('ascii')
    )
    with ZipFile(output, mode='x', compression=ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
        archive.writestr('_headers', HEADERS)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', help='Exakter Projekt-Hostname ohne https:// oder Pfad')
    parser.add_argument('zip', type=Path, help='Pfad für das neue Upload-Archiv')
    args = parser.parse_args()
    try:
        build(args.host, args.zip)
    except (ValueError, OSError) as error:
        parser.error(str(error))
