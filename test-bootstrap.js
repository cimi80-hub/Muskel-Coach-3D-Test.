'use strict';

if (window.top === window && isMuskelTestOrigin(location)) {
  const testApp = document.getElementById('test-app');
  const notice = document.getElementById('test-origin-notice');
  const manifest = document.createElement('link');
  manifest.rel = 'manifest';
  manifest.href = 'manifest.webmanifest';
  document.head.append(manifest);

  testApp.style.display = 'contents';
  notice.hidden = true;

  const script = document.createElement('script');
  script.src = 'test-app.js';
  script.addEventListener('error', () => {
    testApp.style.display = 'none';
    notice.textContent = 'TESTVERSION · Die App konnte nicht geladen werden.';
    notice.hidden = false;
  });
  document.body.append(script);

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('test-sw.js', { scope: './', updateViaCache: 'none' })
      .catch(error => console.warn('TESTVERSION: Service Worker', error));
  }
}

function testKey(key) {
  return MUSKEL_TEST_NAMESPACE + key;
}

function testStorage(getStorage) {
  return {
    getItem: key => getStorage().getItem(testKey(key)),
    setItem: (key, value) => getStorage().setItem(testKey(key), value),
    removeItem: key => getStorage().removeItem(testKey(key)),
  };
}

const testLocal = testStorage(() => window.localStorage);
const testSession = testStorage(() => window.sessionStorage);
const testCookiePath = new URL('./', location.href).pathname;
