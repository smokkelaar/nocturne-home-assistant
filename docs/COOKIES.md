# Official en Daily: gescheiden aanmeldingen

## Waarom kon inloggen blijven terugkeren naar het inlogscherm?

Cookies zijn aan een domeinnaam/pad gekoppeld, niet aan een poort. Nocturne gebruikt
standaard dezelfde cookienamen. Official op `:8448` en Latest op `:8449` konden
daardoor elkaars sessie overschrijven. Een schoon incognitovenster hielp, maar
dat was geen blijvende scheiding. De databases en accounts waren wel afzonderlijk.

## Vanaf wrapper 0.1.5

De HTTPS-ingang vertaalt de sessiecookies automatisch:

| Kanaal | Browsercookie voor het toegangstoken |
|---|---|
| Official | `NocturneOfficial_.Nocturne.AccessToken` |
| Latest | `NocturneLatest_.Nocturne.AccessToken` |

Dit geldt ook voor vernieuwings-/herstel-/gasttokens, OIDC-state en setupcookies.
De server ontvangt alleen de cookies van zijn eigen kanaal, onder de oorspronkelijke
Nocturne-namen. Uitloggen en verversen wijzigen alleen dat kanaal. De namespace
staat vast in pakketmetadata: hij hangt niet af van de poort of een gebruikersoptie.

**Ongewijzigd:** URL, TLS-certificaat, passkey-domein, database, accounts, passkeys,
herstelcodes, sleutels, extra gateway-instelling en upstream-versie. Deze update
kopieert of wist geen gegevens. Er is geen nieuwe registratie nodig.

## Wat moet je na publicatie/installatie doen?

1. Maak zoals gebruikelijk een back-up vóór een app-update.
2. Werk beide apps bij naar wrapper **0.1.5** of nieuwer en herstart alleen de
   bijgewerkte apps. Verander geen URL, poort of certificaat.
3. Sluit oude Nocturne-tabbladen. Open Official en meld je eenmaal opnieuw aan
   met zijn bestaande passkey. Doe hetzelfde voor Latest met zijn eigen passkey.
4. Open beide in twee tabbladen van **dezelfde normale browser**. Herlaad beide.
5. Log uit bij Official: Latest moet na herladen aangemeld blijven. Test ook andersom.
6. Test na een app-herstart opnieuw. De updater verwijdert geen oude cookies:
   oude gedeelde sessiecookies worden genegeerd, niet stilzwijgend overgenomen.

Bij terugrollen naar 0.1.4 geldt opnieuw de oude beperking. Gebruik dan aparte
browserprofielen. Verwijder nooit passkeys of een database om een cookieprobleem
op te lossen. Deel geen cookie-inhoud, tokens of onbewerkte HAR-bestanden.

## Technical design and limits

`cookies.mjs` is a small nginx njs **header-only** adapter. `js_set` selects the
own-channel Cookie header before proxying. `js_header_filter` translates each
individual Set-Cookie header, including deletions, on both the Web and direct-API
routes. Values and attributes (Secure, HttpOnly, SameSite, Domain, Path, expiry)
are preserved. Multiple headers are never comma-split. Duplicate same-name
credentials fail closed. Unscoped/foreign credentials are discarded, never
silently migrated. Domain-wide Clear-Site-Data is suppressed to avoid deleting
the other channel's cookies; upstream's scoped cookie deletions still work.

Upstream browser JS, including already cached bundles, reads a literal
`IsAuthenticated` cookie as a **hint to fetch the real session**, not as proof of
authentication. We therefore retain a constant, non-secret `IsAuthenticated=true`
hint on successful HTML/auth-cookie responses. It never means the user is logged
in: the edge drops that unscoped hint before every upstream request. An isolated,
namespaced marker and real credentials determine the server session. A hint-only
request must remain anonymous and protected data must return 401. This avoids
rewriting compiled frontend bundles or their immutable cache keys. It can cause
an extra anonymous session check in the browser; it cannot grant access.

Client-written display cookies (`nocturne-language`, `nocturne-prefs`,
`sidebar:state`) remain shared, intentionally; they carry no authentication
authority. Unknown client-written unscoped cookies are not forwarded. New upstream
cookie behavior requires compatibility review. This is session-collision
prevention between trusted apps, **not** a security boundary between hostile
applications sharing a domain. Passkey chooser entries can still both appear
because their relying-party domain has not changed.

## Verification

Offline Node tests cover both namespaces, setup/guest/recovery/OIDC cookies,
header arrays, preserved flags/deletions, duplicate/old/foreign-cookie rejection,
and the hint's lack of authority. Python tests verify trusted channel metadata
and both nginx routes.

`tools/cookie_smoke.py` uses two real, unpublished Docker containers with separate
disposable databases and a single same-host cookie jar. It seeds **synthetic**
refresh-token records, then exercises the real Nocturne SSR/API session machinery:
SSR refresh-cookie propagation, interleaved sessions, explicit refresh, isolated
logout, restart, and rejection of old unscoped credentials/hint-only requests.
It neither uses real health data nor performs a WebAuthn ceremony. CI results for
the exact commit are authoritative; the six user steps above remain the real
browser/passkey acceptance check. Never run fixtures against a user's volume.

[Kanalen](CHANNELS.md) · [Versies](VERSIES.md) · [Testbereik](TESTING.md)
