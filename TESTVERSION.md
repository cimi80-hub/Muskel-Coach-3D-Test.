# Muskel-Coach TESTVERSION

Die PWA startet lokal aus diesem Verzeichnis mit `python3 -m http.server 8000 --bind 127.0.0.1`. Öffne im Browser der Testmaschine `http://localhost:8000/`. Der Browser muss Service Worker unterstützen. Für eine Veröffentlichung braucht die PWA einen eigenen HTTPS-Host. Das Cloudflare-Uploadpaket enthält die exakte Projekt-Origin. Im Quell-Checkout bleibt der Platzhalter leer. Ein anderer Pfad unter `cimi80-hub.github.io` reicht für die Trennung von Browserdaten und Service Workern nicht aus. Die App verweigert den Lauf auf allen `github.io`-Hosts und auf anderen öffentlichen Hosts als der im Paket erlaubten Test-Origin.

## Produktionsdienste und Testdaten

| Original | Testversion |
| --- | --- |
| Stripe und PayPal, Kaufanfrage über WhatsApp, Live-Chat über Tawk | Käufe, Live-Chat und Versand von Freischaltcodes deaktiviert |
| Abacus und CountAPI für Nutzungszähler und Code-Einlösung | Zähler und einmalig einlösbare Testcodes bleiben im Browserprofil |
| Link zur veröffentlichten Original-App | Teilen bezieht sich auf den aktuellen Teststandort |
| Google Fonts, YouTube-Suche, Teilen über WhatsApp, Kalenderlink | Bleiben erhalten. YouTube, WhatsApp und Google Kalender öffnen sich erst nach einer Nutzeraktion. Verwende dafür nur synthetische Testdaten. |

Im Entwicklermenü (fünfmal auf das Logo tippen) öffnet `TEST-DEV` die lokalen Testwerkzeuge. Dort erzeugte Codes beginnen mit `TEST-` und sind im selben Browserprofil einmalig einlösbar. `TEST-MASTER` ist ein öffentlicher Testschalter für die unbegrenzte Testfreischaltung und kein Passwort für ein produktives System.

Local Storage, Session Storage, IndexedDB, Cookies und Exportdateien verwenden eigene Kennungen. Produktionssicherungen werden beim Import abgewiesen. Der Test-Service-Worker registriert sich nur auf freigegebenen Origins, beschränkt sich auf den App-Pfad und entfernt bei Updates nur alte Testcaches seines eigenen Geltungsbereichs. Er speichert nur feste App-Dateien. Bei einer PWA-Aktualisierung den Cache-Stand in `test-sw.js` erhöhen, damit alte Testdateien bei Aktivierung bereinigt werden.

Die separate Expo-App verwendet eigene iOS- und Android-IDs, einen eigenen Speicherschlüssel und deaktivierte native OTA-Updates. Expo Web ist auf Loopback beschränkt.

## Sicherung der vorherigen Testversion

Der annotierte Git-Tag `archiv-testversion-vor-originalkopie` zeigt auf den alten Stand `60d835a`. Der vollständige versionierte Stand samt 3D-Modellen und ZIP-Dateien bleibt außerdem Vorfahr der vorbereiteten Kopie. Der vorbereitete Commit `f8b5066` und der Sicherungstag wurden nach Freigabe ins **Testrepository** übertragen. Der Commit liegt dort auf `testversion-vorbereitung`. `main` blieb unverändert. Die Cloudflare-Vorbereitung liegt lokal vor.

## Prüfungen

`python3 tests/web_isolation.py` benötigt Playwright für Python, Chromium unter `/usr/bin/chromium`, OpenSSL und `certutil`. Der Test nutzt ein temporäres Browserprofil, lokale HTTPS-Server und einen Sperrproxy. Der GitHub-Pages-Aufruf wird lokal simuliert. Der Test veröffentlicht keine Seite und greift auf keine Produktionsdienste zu.

Der lokale Prüflauf hat die Sperre auf der gemeinsam genutzten Pages-Origin, den Katalog mit 90 Übungen, eine Übungsdetailseite, Trainingsplan und Kalender bestätigt. Der Browser lehnte einen sechsstelligen Code ab und akzeptierte einen lokal erzeugten Testcode genau einmal. Ein Service-Worker-Update entfernte den alten Testcache und erhielt den simulierten Produktionscache. Die App startete danach offline. Die Expo-Typprüfung und ESLint für die geänderten Expo-Quelldateien waren erfolgreich. Ein nativer Gerätebuild und eine Veröffentlichung wurden nicht ausgeführt.

## Cloudflare Pages per Direct Upload

1. Melde dich im Cloudflare-Dashboard an und öffne **Workers & Pages → Create application → Get started → Drag and drop your files**. Verwende ein neues Pages-Projekt per Direct Upload, ohne GitHub-Integration und ohne eigene Domain.
2. Gib als Projektnamen `muskel-coach-test-cimi80` ein. Der vorgeschlagene Host ist `muskel-coach-test-cimi80.pages.dev`. Falls Cloudflare einen abweichenden Namen anzeigt, muss das ZIP mit dem exakt angezeigten Host neu gebaut werden. Die App bleibt auf einem abweichenden Host gesperrt.
3. Halte vor dem Upload und Deployment an. Nach Freigabe das fertige ZIP in die Uploadfläche ziehen und **Deploy site** beziehungsweise **Save and Deploy** auswählen. Der neue Host ist öffentlich erreichbar. Die Paket-Header bitten Suchmaschinen, die Testseite nicht zu indexieren. Verwende ausschließlich synthetische Testdaten.
4. Nach der Veröffentlichung auf der Hauptadresse mit einem frischen Browserprofil die TESTVERSION-Kennzeichnung, einen lokalen Testcode und einen Offline-Neustart prüfen. Hash- und Branch-Vorschauadressen sind gesperrt.

Das Upload-ZIP lässt sich lokal ohne npm erzeugen:

```bash
python3 scripts/build_cloudflare_pages.py muskel-coach-test-cimi80.pages.dev muskel-coach-test-pages.zip
```

Das Paket enthält nur die statischen PWA-Dateien und die Cloudflare-Header. Die Startseite liegt direkt im ZIP-Stamm. Expo, Git-Daten und Sicherungsdateien gehören nicht zum Upload.

[Offizielle Cloudflare-Anleitung](https://developers.cloudflare.com/pages/get-started/direct-upload/)
