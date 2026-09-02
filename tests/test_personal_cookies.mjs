import { test } from 'node:test';
import assert from 'node:assert/strict';
import personal from '../nocturne_personal/rootfs/opt/nocturne-ha/cookies.mjs';
import official from '../nocturne_local/rootfs/opt/nocturne-ha/cookies.mjs';
import latest from '../nocturne_latest/rootfs/opt/nocturne-ha/cookies.mjs';

test('three independent sessions in one browser cookie jar', () => {
  const modules = [official, latest, personal];
  const prefixes = ['NocturneOfficial_', 'NocturneLatest_', 'NocturnePersonal_'];
  for (const cookie of ['.Nocturne.AccessToken', '.Nocturne.RefreshToken', 'nocturne-setup-tenant']) {
    const jar = prefixes.map((prefix, i) => `${prefix}${cookie}=test-${i}`).join('; ');
    modules.forEach((module, i) => {
      assert.equal(module.decode(jar, prefixes[i]), `${cookie}=test-${i}`);
      const logout = module.encode([`${cookie}=; Path=/; Max-Age=0; Secure; HttpOnly`], prefixes[i], false);
      assert.ok(logout[0].startsWith(prefixes[i] + cookie + '='));
      prefixes.filter(prefix => prefix !== prefixes[i]).forEach(prefix => {
        assert.ok(!logout.some(header => header.startsWith(prefix)));
      });
    });
  }
});

test('Personal rejects legacy, foreign, ambiguous and double-namespaced credentials', () => {
  for (const raw of ['.Nocturne.AccessToken=test', 'IsAuthenticated=true',
    'NocturneOfficial_.Nocturne.AccessToken=test', 'NocturneLatest_.Nocturne.AccessToken=test',
    'NocturnePersonal_NocturneLatest_.Nocturne.AccessToken=test',
    'NocturnePersonal_.Nocturne.AccessToken=one; NocturnePersonal_.Nocturne.AccessToken=two']) {
    assert.equal(personal.decode(raw, 'NocturnePersonal_'), '');
  }
});
