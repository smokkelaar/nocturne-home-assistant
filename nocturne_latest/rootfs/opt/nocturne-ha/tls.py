"""Validate immutable TLS snapshots; replace only after a verified nginx reload.

No CA/client trust claim, no writes to /ssl, no secret material in diagnostics.
OpenSSL is already a runtime dependency; Python needs no third-party package.
"""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import tempfile
import time


MESSAGES = {
    'CERT_FILES': 'Certificaat/sleutel ontbreken, zijn onleesbaar of te groot; controleer de /ssl-bestandsnamen.',
    'CERT_PARSE': 'Certificaat of onversleutelde privésleutel kan niet worden gelezen.',
    'CERT_SAN': 'Certificaat mist een DNS Subject Alternative Name (SAN).',
    'CERT_HOSTNAME': 'Certificaat past niet bij public_url; controleer domeinnaam en certificaat.',
    'CERT_KEY_MISMATCH': 'Certificaat en privésleutel horen niet bij elkaar.',
    'CERT_NOT_YET_VALID': 'Certificaat is nog niet geldig; controleer ook de systeemtijd.',
    'CERT_EXPIRED': 'Certificaat is verlopen; controleer de certificaatvernieuwer.',
    'CERT_RELOAD': 'HTTPS-herlading niet bevestigd; vorige configuratie behouden, controleer de app-log.',
}


class CertificateError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code + ': ' + MESSAGES[code])


def openssl(*args, data=None, code='CERT_PARSE'):
    try:
        result = subprocess.run(['openssl', *args], input=data, capture_output=True,
                                timeout=10, env=dict(os.environ, LC_ALL='C'))
    except (OSError, subprocess.TimeoutExpired):
        raise CertificateError(code) from None
    if result.returncode:
        raise CertificateError(code)
    return result.stdout


@dataclass(frozen=True)
class CertificateInfo:
    not_before: float
    not_after: float
    leaf_sha256: str

    def check_time(self, now=None):
        now = time.time() if now is None else now
        if now < self.not_before:
            raise CertificateError('CERT_NOT_YET_VALID')
        if now >= self.not_after:
            raise CertificateError('CERT_EXPIRED')

    def summary(self):
        until = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(self.not_after))
        try:
            self.check_time()
        except CertificateError as error:
            return str(error) + ' Einddatum: ' + until
        days = max(0, int((self.not_after - time.time()) / 86400))
        prefix = 'BINNENKORT VERLOPEN — ' if days < 14 else ''
        return f'{prefix}SAN/domeinnaam en sleutelpaar gecontroleerd. Geldig tot {until} ({days} dagen).'


def inspect_pair(cert, key, hostname, now=None):
    """Inspect the leaf, require SAN, hostname, key match and current validity.

    This deliberately does not assert trust in the client CA store. nginx -t
    separately verifies that the full PEM chain/configuration can be loaded.
    """
    san = openssl('x509', '-in', str(cert), '-noout', '-ext', 'subjectAltName')
    if b'DNS:' not in san:
        raise CertificateError('CERT_SAN')
    host_check = openssl('x509', '-in', str(cert), '-noout', '-checkhost', hostname, code='CERT_HOSTNAME')
    # x509 -checkhost can exit zero even for a mismatch (notably OpenSSL 1.1).
    # Require the explicit positive C-locale result; unknown output fails closed.
    if host_check.strip() != f'Hostname {hostname} does match certificate'.encode('ascii'):
        raise CertificateError('CERT_HOSTNAME')
    public = openssl('x509', '-in', str(cert), '-noout', '-pubkey')
    cert_public = openssl('pkey', '-pubin', '-outform', 'DER', data=public)
    key_public = openssl('pkey', '-in', str(key), '-passin', 'pass:', '-pubout', '-outform', 'DER')
    if cert_public != key_public:
        raise CertificateError('CERT_KEY_MISMATCH')
    dates = openssl('x509', '-in', str(cert), '-noout', '-startdate', '-enddate')
    try:
        fields = dict(line.split('=', 1) for line in dates.decode('ascii').splitlines())
        start = ssl.cert_time_to_seconds(fields['notBefore'])
        end = ssl.cert_time_to_seconds(fields['notAfter'])
    except (ValueError, KeyError, UnicodeError):
        raise CertificateError('CERT_PARSE') from None
    der = openssl('x509', '-in', str(cert), '-outform', 'DER')
    info = CertificateInfo(start, end, hashlib.sha256(der).hexdigest())
    info.check_time(now)
    return info


def read_pair(cert, key):
    try:
        values = []
        for path in (cert, key):
            with Path(path).open('rb') as handle:
                data = handle.read(1_048_577)
            if not data or len(data) > 1_048_576:
                raise OSError('Invalid size')
            values.append(data)
        return tuple(values)
    except OSError:
        raise CertificateError('CERT_FILES') from None


class Snapshot:
    def __init__(self, root, pair, hostname):
        self.directory = tempfile.TemporaryDirectory(prefix='pair-', dir=root)
        directory = Path(self.directory.name)
        directory.chmod(0o700)
        self.cert, self.key = directory / 'fullchain.pem', directory / 'private.pem'
        try:
            for path, data in zip((self.cert, self.key), pair):
                with path.open('xb') as handle:
                    handle.write(data)
                path.chmod(0o600)
            self.info = inspect_pair(self.cert, self.key, hostname)
        except Exception:
            self.close()
            raise

    def close(self):
        self.directory.cleanup()


class CertificateWatcher:
    """Two identical observations >=10s apart before staging renewed files."""
    def __init__(self, cert, key, hostname, root):
        self.cert, self.key, self.hostname = cert, key, hostname
        self.root = Path(root)
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.root.chmod(0o700)
        self.active_pair = read_pair(cert, key)
        self.active = Snapshot(self.root, self.active_pair, hostname)
        self.pending_pair = None
        self.pending_since = 0
        self.message = 'Startcertificaat gecontroleerd; automatische controle iedere 15 seconden.'

    def poll(self, reload, now=None):
        now = time.monotonic() if now is None else now
        staged = None
        try:
            pair = read_pair(self.cert, self.key)
            if pair == self.active_pair:
                self.pending_pair = None
                self.active.info.check_time()
                self.message = 'Geen nieuwe certificaatbestanden; geladen certificaat is nog geldig.'
                return
            if pair != self.pending_pair:
                self.pending_pair, self.pending_since = pair, now
                self.message = 'Gewijzigde bestanden gezien; wacht op een stabiel, passend paar.'
                return
            if now - self.pending_since < 10:
                return
            staged = Snapshot(self.root, pair, self.hostname)
            # Reload reads THIS immutable private snapshot, not changing /ssl files.
            if not reload(staged):
                raise CertificateError('CERT_RELOAD')
            previous = self.active
            self.active, self.active_pair = staged, pair
            staged = None
            self.pending_pair = None
            self.message = 'Nieuw certificaat geladen en via een nieuwe lokale TLS-verbinding bevestigd.'
            previous.close()
        except CertificateError as error:
            self.message = str(error) + ' Huidige HTTPS-server niet gestopt.'
        except OSError:
            self.message = str(CertificateError('CERT_FILES')) + ' Huidige HTTPS-server niet gestopt.'
        finally:
            if staged:
                staged.close()

    def checks(self):
        return {'Geladen certificaat': self.active.info.summary(), 'Certificaatvernieuwing': self.message}


def peer_fingerprint(hostname):
    # Loopback identity probe ONLY; trust is checked separately by the browser.
    # No credentials or app data are sent over this unverified handshake.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection(('127.0.0.1', 8448), timeout=2) as connection:
        with context.wrap_socket(connection, server_hostname=hostname) as tls_socket:
            return hashlib.sha256(tls_socket.getpeercert(binary_form=True)).hexdigest()


def atomic_config(path, content):
    """Same-directory replace; never leave a partially written active config."""
    fd, name = tempfile.mkstemp(prefix='nginx-', suffix='.conf', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def reload_nginx(process, conf, content, fingerprint, hostname):
    """Test candidate, HUP only nginx, verify leaf; roll config back on failure."""
    old = conf.read_bytes()
    candidate = conf.with_name('nginx-check.conf')
    try:
        atomic_config(candidate, content.encode())
        result = subprocess.run(['nginx', '-t', '-c', str(candidate)],
                                capture_output=True, timeout=10)
        if result.returncode or process.poll() is not None:
            return False
        atomic_config(conf, content.encode())
        process.send_signal(signal.SIGHUP)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            time.sleep(0.25)
            try:
                if peer_fingerprint(hostname) == fingerprint:
                    return True
            except OSError:
                pass
        atomic_config(conf, old)
        if process.poll() is None:
            process.send_signal(signal.SIGHUP)
        return False
    except (OSError, subprocess.TimeoutExpired):
        atomic_config(conf, old)
        if process.poll() is None:
            process.send_signal(signal.SIGHUP)
        return False
    finally:
        candidate.unlink(missing_ok=True)
