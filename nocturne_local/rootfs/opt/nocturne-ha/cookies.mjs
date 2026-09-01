// Browser-facing cookie isolation. Internal Web/API traffic keeps upstream names.
// No cookie values, headers, or credentials may be logged from this module.
const PREFIXES = ['NocturneOfficial_', 'NocturneLatest_'];
// These client-written display preferences have no authentication authority.
// Keeping them unchanged avoids modifying/cache-busting upstream JS bundles.
const PREFERENCES = ['nocturne-language', 'nocturne-prefs', 'sidebar:state'];
const UI_HINT = 'IsAuthenticated=true; Path=/; Secure; SameSite=Lax';

function prefixFor(namespace) {
    if (PREFIXES.indexOf(namespace) === -1) throw Error('Invalid cookie namespace');
    return namespace;
}

function preference(name) {
    return PREFERENCES.indexOf(name) !== -1;
}

function validName(name) {
    return /^[!#$%&'*+.^_`|~0-9A-Za-z-]+$/.test(name);
}

function decode(header, namespace) {
    const prefix = prefixFor(namespace);
    const found = Object.create(null);
    const duplicates = Object.create(null);
    for (const part of (header || '').split(';')) {
        const pair = part.trim();
        const separator = pair.indexOf('=');
        if (separator < 1) continue;
        const external = pair.slice(0, separator);
        let name;
        if (external.startsWith(prefix)) {
            name = external.slice(prefix.length);
            if (!validName(name) || preference(name)
                    || PREFIXES.some(p => name.startsWith(p))) continue;
        } else if (preference(external)) {
            name = external;
        } else {
            // Ignore old unscoped credentials, other channels, setup/guest state,
            // and the shared, non-authoritative UI hint. Never migrate a session.
            continue;
        }
        if (Object.prototype.hasOwnProperty.call(found, name)) duplicates[name] = true;
        found[name] = pair.slice(separator + 1);
    }
    // Ambiguous same-name cookies (different domain/path) fail closed.
    return Object.keys(found).filter(name => !duplicates[name])
        .map(name => name + '=' + found[name]).join('; ');
}

function encode(headers, namespace, htmlPage) {
    const prefix = prefixFor(namespace);
    const result = [];
    let needsHint = htmlPage;
    for (const header of headers || []) {
        const separator = header.indexOf('=');
        if (separator < 1) continue;
        const name = header.slice(0, separator).trim();
        if (!validName(name) && !preference(name)) continue;
        // Preserve value and ALL attributes, including expiry/deletion, HttpOnly,
        // Secure, SameSite, Domain and Path. Never split Set-Cookie on commas.
        const target = preference(name) ? name : prefix + name;
        result.push(target + header.slice(separator));
        if (name === 'IsAuthenticated') needsHint = true;
    }
    // Upstream's browser JS reads the literal IsAuthenticated marker to decide
    // whether to query its session endpoint. It is NOT a credential. Keep a
    // constant hint for cached/unmodified upstream JS; discard it on ingress.
    // Logout only removes the namespaced authoritative cookies, never this hint.
    // A hint alone must still yield an anonymous session / protected-data 401.
    if (needsHint) result.push(UI_HINT);
    return result;
}

function requestCookies(r) {
    return decode(r.headersIn.Cookie, r.variables.ha_cookie_namespace);
}

function responseCookies(r) {
    const raw = r.headersOut['Set-Cookie'];
    const headers = raw === undefined ? [] : Array.isArray(raw) ? raw : [raw];
    const htmlPage = r.status === 200
        && (r.headersOut['Content-Type'] || '').split(';')[0].trim() === 'text/html';
    const output = encode(headers, r.variables.ha_cookie_namespace, htmlPage);
    if (output.length) r.headersOut['Set-Cookie'] = output;
    else delete r.headersOut['Set-Cookie'];
    // A domain-wide clear would erase the OTHER app's cookies as well.
    // Scoped Set-Cookie deletions above are the supported logout mechanism.
    delete r.headersOut['Clear-Site-Data'];
}

export default { decode, encode, requestCookies, responseCookies };
