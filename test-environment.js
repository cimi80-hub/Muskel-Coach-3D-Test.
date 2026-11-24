'use strict';

// Add the exact dedicated HTTPS origin here after it has been provisioned.
const MUSKEL_TEST_ORIGIN = '';
const MUSKEL_TEST_NAMESPACE = 'muskel-coach-test/';

function isMuskelTestOrigin(url) {
  const host = url.hostname.toLowerCase().replace(/\.$/, '');
  if (host === 'github.io' || host.endsWith('.github.io')) return false;
  if (['localhost', '127.0.0.1', '[::1]'].includes(host)) {
    return url.protocol === 'https:' || url.protocol === 'http:';
  }
  return url.protocol === 'https:' && url.origin === MUSKEL_TEST_ORIGIN;
}
