"""Startet und prüft den unveränderten PWA-Dateibaum auf isolierten HTTPS-Origins."""
import functools
import os
from pathlib import Path
import ssl
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FILES = {'/', '/index.html', '/test-sw.js', '/manifest.webmanifest',
         '/test-app.js', '/test-bootstrap.js', '/test-environment.js', '/icon-180.png', '/icon-192.png', '/icon-512.png'}


class App(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.headers['Host'] != self.server.expected_host:
            self.send_error(403)
        elif urlsplit(self.path).path not in FILES:
            self.send_error(404)
        elif self.path == '/test-sw.js' and self.server.update:
            # Simuliert neue SW-Bytes ausschließlich in dieser HTTP-Antwort.
            body = (ROOT / 'test-sw.js').read_bytes().replace(b"section + 'v1'", b"section + 'v2'")
            self.send_response(200)
            self.send_header('Content-Type', 'text/javascript')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def end_headers(self):
        self.send_header('Content-Security-Policy',
                         "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                         "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
                         "connect-src 'self'; worker-src 'self' blob:; form-action 'self'; "
                         "object-src 'none'; base-uri 'none'")
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, *args):
        pass


class DenyProxy(BaseHTTPRequestHandler):
    def deny(self):
        self.server.denied.append(self.command)
        self.send_error(403)

    do_CONNECT = do_GET = do_POST = deny

    def log_message(self, *args):
        pass


def launch(server):
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run():
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        cert, key = path / 'cert.pem', path / 'key.pem'
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
            '-subj', '/CN=Muskel-Coach local test',
            '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1',
            '-keyout', key, '-out', cert,
        ], check=True, capture_output=True)
        nss = path / '.local/share/pki/nssdb'
        nss.mkdir(parents=True)
        subprocess.run(['certutil', '-N', '--empty-password', '-d', f'sql:{nss}'], check=True)
        subprocess.run(['certutil', '-A', '-d', f'sql:{nss}', '-n', 'Local test',
                        '-t', 'P,,', '-i', cert], check=True)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(cert, key)
        proxy = ThreadingHTTPServer(('127.0.0.1', 0), DenyProxy)
        proxy.denied = []
        launch(proxy)

        def serve(host):
            app = ThreadingHTTPServer(('127.0.0.1', 0),
                                      functools.partial(App, directory=ROOT))
            app.expected_host = f'{host}:{app.server_port}'
            app.update = False
            app.socket = tls.wrap_socket(app.socket, server_side=True)
            return launch(app), f'https://{app.expected_host}'

        first, url = serve('localhost')
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path='/usr/bin/chromium',
                proxy={'server': f'http://127.0.0.1:{proxy.server_port}', 'bypass': 'localhost,127.0.0.1'},
                args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
                env={**os.environ, 'HOME': temporary},
            )
            ctx = browser.new_context()
            probe = ctx.new_page()
            try:
                probe.goto('https://example.com/', timeout=5000)
            except Exception:
                pass
            assert 'CONNECT' in proxy.denied, 'Externer Testaufruf muss am Sperrproxy enden'
            probe.close()
            shared = ctx.new_page()
            shared_requests = []
            shared.on('request', lambda request: shared_requests.append(urlsplit(request.url).path))
            def serve_shared(route):
                file = urlsplit(route.request.url).path.rsplit('/',1)[-1]
                if file not in {'index.html', 'test-environment.js', 'test-bootstrap.js'}:
                    route.abort()
                    return
                route.fulfill(body=(ROOT / file).read_bytes(),
                              content_type='text/html' if file.endswith('.html') else 'application/javascript')
            shared.route('https://cimi80-hub.github.io/**', serve_shared)
            shared.add_init_script("""
                localStorage.setItem('mc_trial','12345');
                window.registerCalled = false;
                navigator.serviceWorker.register = () => { window.registerCalled = true; };
            """)
            assert shared.goto('https://cimi80-hub.github.io/Muskel-Coach-3D-Test./index.html').ok
            shared.locator('#test-origin-notice').wait_for()
            assert not shared.evaluate('window.registerCalled')
            assert shared.evaluate("localStorage.getItem('mc_trial')") == '12345'
            assert shared.evaluate("Object.keys(localStorage).length") == 1
            assert not any(name.endswith('test-app.js') for name in shared_requests)
            shared.close()
            print('Gemeinsame Pages-Origin verweigert App-Start und SW-Registrierung', flush=True)

            page = ctx.new_page()
            errors = []
            requests = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: requests.append(request.url))
            page.add_init_script("""
                localStorage.setItem('mc_trial','12345');
                document.cookie = 'mc_trial=12345; Secure; Path=/';
            """)
            response = page.goto(url, wait_until='load')
            assert response.ok and response.body() == (ROOT / 'index.html').read_bytes()
            page.wait_for_function('() => navigator.serviceWorker.controller !== null')
            page.wait_for_function("() => document.querySelector('#grid').childElementCount > 0")
            assert page.evaluate('EX.length') == 90
            assert 'TESTVERSION' in page.title()
            assert page.evaluate("localStorage.getItem('mc_trial')") == '12345'
            assert page.evaluate("Number(testLocal.getItem('mc_trial')) > 12345")
            assert page.evaluate("document.cookie.includes('muskel_coach_test_trial=')")
            await_names = page.evaluate("async () => (await indexedDB.databases()).map(db=>db.name)")
            assert await_names and all(name.startswith('muskel-coach-test/') for name in await_names)
            page.locator('#gatePw').fill('123456')
            page.locator('#gateForm').evaluate('(form) => form.requestSubmit()')
            page.wait_for_function(
                """() => /Falscher Code|wrong code/i.test(document.querySelector('#gateErr').textContent)"""
            )
            assert page.evaluate("testLocal.getItem('mc_unlock') === null")
            page.locator('#gateLater').evaluate('(button) => button.click()')
            page.evaluate('devLogin()')
            page.locator('#devPw').fill('TEST-DEV')
            page.locator('#devForm').evaluate('(form) => form.requestSubmit()')
            page.locator('#devGen').evaluate('(button) => button.click()')
            code = page.locator('#devNew .devcode').inner_text()
            assert code.startswith('TEST-')
            page.evaluate('devClose(); MC_GATE.code()')
            page.locator('#gatePw').fill(code)
            page.locator('#gateForm').evaluate('(form) => form.requestSubmit()')
            page.wait_for_function("() => testLocal.getItem('mc_unlock') === 'muskel-coach-test-unlock-v1'")
            assert page.evaluate('code => redeemCode(code)', code) == 'used'
            assert page.evaluate("localStorage.getItem('mc_unlock')") is None
            page.evaluate("setView('ex'); openEx(EX[0].id)")
            page.locator('#detail .dtitle').wait_for()
            assert page.locator('#detail .steps li').count() > 0
            page.evaluate("closeEx(); setView('plan')")
            assert page.locator('#vPlan').is_visible()
            page.evaluate("setView('cal')")
            assert page.locator('#vCal').is_visible()
            assert not any(any(host in request for host in (
                'stripe.com','paypal.me','abacus.jasoncameron.dev','countapi.mileshilliard.com','embed.tawk.to'
            )) for request in requests)
            page.evaluate("""async () => {
                await caches.open('muskel-coach-v67');
            }""")
            print('90 Übungen, Testkennzeichnung, getrennte Daten, eigener Code und Einmalnutzung geprüft', flush=True)
            page.evaluate("""() => {
                window.didChangeController = false;
                navigator.serviceWorker.addEventListener('controllerchange', () => {
                    window.didChangeController = true;
                }, {once: true});
            }""")
            first.update = True
            page.evaluate("(async () => (await navigator.serviceWorker.ready).update())()")
            page.wait_for_function("() => window.didChangeController")
            page.wait_for_function(
                "() => navigator.serviceWorker.controller?.state === 'activated'"
            )
            assert cache_isolation_preserved(page)
            ctx.set_offline(True)
            cached = page.goto(url + '/index.html', wait_until='load')
            assert cached.from_service_worker and cached.body() == (ROOT / 'index.html').read_bytes()
            page.wait_for_function("() => document.querySelector('#grid').childElementCount > 0")
            ctx.set_offline(False)
            assert not errors, errors
            print('Offline-Start, SW-Update und Erhalt des fremden Caches geprüft')
            browser.close()


def cache_isolation_preserved(page):
    return page.evaluate('''async () => {
        const scope = (await navigator.serviceWorker.ready).scope;
        return await caches.has('muskel-coach-v67') &&
          await caches.has('muskel-coach-test:' + scope + ':v2') &&
          !(await caches.has('muskel-coach-test:' + scope + ':v1'));
    }''')


if __name__ == '__main__':
    run()
