import { test } from 'node:test';
import assert from 'node:assert/strict';
import cookies from '../nocturne_local/rootfs/opt/nocturne-ha/cookies.mjs';

const official = 'NocturneOfficial_';
const latest = 'NocturneLatest_';
const access = '.Nocturne.AccessToken';

test('same-host browser jar is separated, never selected by port or a request header', () => {
  const jar = `${official}${access}=one; ${latest}${access}=two; ${access}=old; IsAuthenticated=true`;
  assert.equal(cookies.decode(jar, official), `${access}=one`);
  assert.equal(cookies.decode(jar, latest), `${access}=two`);
});

test('legacy credentials and foreign/unknown cookies fail closed', () => {
  for (const value of [undefined, '', 'IsAuthenticated=true',
    `${access}=old; .Nocturne.RefreshToken=old; nocturne-setup-tenant=old`,
    `${latest}${access}=foreign; session=unexpected`]) {
    assert.equal(cookies.decode(value, official), '');
  }
});

test('all server cookie types round-trip, including setup, guest and OIDC state', () => {
  for (const name of [access, '.Nocturne.RefreshToken', '.Nocturne.PlatformAccess',
    '.Nocturne.RecoverySession', '.Nocturne.OidcState', '.Nocturne.OidcLinkState',
    'nocturne-setup-tenant', 'nocturne-guest-session', 'nocturne-onboarding-complete',
    'IsAuthenticated', 'future-server-cookie']) {
    const header = `${name}=opaque==; Path=/; Secure; HttpOnly; SameSite=Lax`;
    const encoded = cookies.encode([header], official, false)[0];
    assert.equal(encoded, official + header);
    assert.equal(cookies.decode(encoded.split(';')[0], official), name + '=opaque==');
  }
});

test('expiry commas, domains, paths and deletions are preserved exactly', () => {
  const header = `${access}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; domain=example.net; path=/; secure; httponly; samesite=lax`;
  assert.deepEqual(cookies.encode([header], latest, false), [latest + header]);
});

test('reserved browser security prefixes keep their original meaning', () => {
  for (const security of ['__Host-', '__Secure-']) {
    const header = security + 'session=opaque; Path=/; Secure; HttpOnly';
    const scoped = security + official + 'session=opaque; Path=/; Secure; HttpOnly';
    assert.deepEqual(cookies.encode([header], official, false), [scoped]);
    assert.equal(cookies.decode(scoped.split(';')[0], official), security + 'session=opaque');
    assert.equal(cookies.decode(scoped.split(';')[0], latest), '');
    assert.equal(cookies.decode(header.split(';')[0], official), '');
  }
});

test('duplicate same-name credentials are not forwarded in either order', () => {
  for (const values of ['one; ' + official + access + '=two', 'two; ' + official + access + '=one']) {
    assert.equal(cookies.decode(`${official}${access}=${values}`, official), '');
  }
});

test('malformed and double-namespaced credentials are ignored', () => {
  assert.equal(cookies.decode(`${official}=x; ${official}${latest}${access}=x; ${official}bad name=x`, official), '');
  assert.deepEqual(cookies.encode(['bad header', 'bad name=x'], official, false), []);
});

test('invalid trusted namespace stops processing', () => {
  for (const prefix of ['', undefined, 'attacker_', 'NocturneOfficial_;']) {
    assert.throws(() => cookies.decode('', prefix), /Invalid cookie namespace/);
    assert.throws(() => cookies.encode([], prefix, false), /Invalid cookie namespace/);
  }
});

test('only harmless client-written appearance preferences pass through unscoped', () => {
  for (const name of ['nocturne-language', 'nocturne-prefs', 'sidebar:state']) {
    assert.equal(cookies.decode(name + '=value', official), name + '=value');
    assert.equal(cookies.encode([name + '=value; Path=/'], official, false)[0], name + '=value; Path=/');
  }
});

test('legacy browser hint is constant and has no server-side auth authority', () => {
  const set = cookies.encode(['IsAuthenticated=; Path=/; Max-Age=0'], official, false);
  assert.equal(set[0], official + 'IsAuthenticated=; Path=/; Max-Age=0');
  assert.equal(set[1], 'IsAuthenticated=true; Path=/; Secure; SameSite=Lax');
  assert.equal(cookies.decode(set[1].split(';')[0], official), '');
  assert.equal(cookies.decode(set[1].split(';')[0], latest), '');
  assert.deepEqual(cookies.encode([], latest, true), [set[1]]);
  assert.deepEqual(cookies.encode([], latest, false), []);
});

test('nginx wrapper accepts multiple Set-Cookie headers and blocks domain-wide clearing', () => {
  const r = {
    status: 200, variables: {ha_cookie_namespace: official},
    headersIn: {Cookie: `${official}${access}=token`},
    headersOut: {'Set-Cookie': [`${access}=token; HttpOnly`, 'setup=state; Secure'],
      'Content-Type': 'application/json', 'Clear-Site-Data': '"cookies"'},
  };
  assert.equal(cookies.requestCookies(r), `${access}=token`);
  cookies.responseCookies(r);
  assert.deepEqual(r.headersOut['Set-Cookie'], [`${official}${access}=token; HttpOnly`, official + 'setup=state; Secure']);
  assert.equal(r.headersOut['Clear-Site-Data'], undefined);
});

test('only successful HTML or an upstream auth-marker write gets the UI hint', () => {
  for (const [status, type, expected] of [[200, 'text/html; charset=utf-8', true],
    [401, 'text/html', false], [200, 'application/javascript', false], [200, 'application/json', false]]) {
    const r = {status, variables: {ha_cookie_namespace: latest}, headersOut: {'Content-Type': type}};
    cookies.responseCookies(r);
    assert.equal(!!r.headersOut['Set-Cookie'], expected);
  }
});
