# Yueye · 阅页

<p align="center">
  <strong>Verwandeln Sie Online-Dokumente, auf die Sie autorisierten Zugriff haben, in durchsuchbare Offline-Kopien.</strong>
</p>

<p align="center">
  <a href="https://yueye.jingzhiacademy.com/"><img src="https://img.shields.io/badge/Webseite-yueye.jingzhiacademy.com-blue?style=flat-square" alt="Website" /></a>
  <a href="https://github.com/satoshinj/yueye/releases"><img src="https://img.shields.io/github/v/release/satoshinj/yueye?style=flat-square&color=success" alt="Release" /></a>
  <img src="https://img.shields.io/badge/Plattform-Windows%2010%20%2F%2011-lightgrey?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/Lizenz-MIT-orange?style=flat-square" alt="License" />
</p>

<p align="center">
  <a href="README.md">简体中文</a> |
  <a href="README_EN.md">English</a> |
  <a href="README_JA.md">日本語</a> |
  <a href="README_KO.md">한국어</a> |
  <a href="README_ES.md">Español</a> |
  <a href="README_FR.md">Français</a> |
  <b>Deutsch</b> |
  <a href="README_RU.md">Русский</a>
</p>

---

> [!IMPORTANT]
> **Rechtlicher Hinweis**: Dieses Tool dient ausschließlich der persönlichen Offline-Lektüre von Inhalten, für die Sie **angemeldet und autorisiert** sind. Nicht freigegebene Seiten werden vom Server nicht übertragen. Es umgeht keine Bezahlschranken und löst keine Sicherheits-CAPTCHAs. Siehe [DISCLAIMER.md](DISCLAIMER.md).

---

## ✨ Hauptfunktionen

| Modul | Funktionalität | Vorteile |
|---|---|---|
| **Intelligente Routen-Erkennung** | Automatische Wahl: Webartikel / Dokumenten-Viewer / Vollbild-Screenshot | Artikel erzeugen **durchsuchbare Text-PDFs** (90% kleiner); Canvas-Viewer erfassen Original-Pixel |
| **Maximale Performance** | Direktes `canvas.toDataURL` + Hash-Stabilitätssonde | **26 ms/Seite** (8x schneller als Screenshots), Export von 100 Seiten in wenigen Sekunden |
| **Dynamisches Umblättern** | Seiteneingabe → Weiter-Schaltfläche → Scroll-Container → Tastatur | **Keine fest codierten Selektoren**; ermittelt und speichert funktionierende Blättermethoden zur Laufzeit |
| **Fehlertoleranz & Sofort-Stopp** | Viewer-Vorwärmung + Backoff-Wiederholung + Millisekunden-Stopp | Schließt überlagerte Popups automatisch; „Stopp“-Schaltfläche reagiert sofort |
| **Breite Browser-Kompatibilität** | Automatische Erkennung von Edge, Chrome, 360, QQ, Brave, Cent | Bereinigung verwaister Sperrdateien (`SingletonLock`), Entfernung von Automatisierungs-Bannern, Proxy/SSL-Toleranz |
| **Multi-Format & Seitenbereiche** | PDF (Text/Bild) / Word / Markdown / Reintext / Bilder | Unterstützt benutzerdefinierte Seitenbereiche (z. B. `1-10`); asynchroner Export verhindert UI-Einfrieren |

---

## 🚀 Schnellstart

### Option A: Portable Version (Empfohlen · Kein Python erforderlich)

1. Laden Sie `Yueye-v1.0.3-win-x64.zip` von den [GitHub Releases](https://github.com/satoshinj/yueye/releases) herunter und entpacken Sie es.
2. Starten Sie `阅页.exe`:
   - Klicken Sie zuerst auf **「登录浏览器」(Browser-Login)**, um sich bei Ihrem Zielkonto anzumelden.
   - Dokumenten-URL einfügen, Format und Seitenbereich wählen und auf **「开始抓取」(Start)** klicken.

### Option B: CLI-Modus (Kommandozeile & Automatisierung)

```cmd
# Gesamtes Dokument als PDF exportieren
阅页.exe --url "https://..." --format pdf

# Seiten 1 bis 10 als Markdown in einen Zielordner exportieren
阅页.exe --url "https://..." --format markdown --range 1-10 --out ./output

# Benutzerdefinierten Browserpfad angeben
阅页.exe --url "https://..." --browser "C:\Path\To\Chrome.exe"
```

---

## 📝 Lizenz

Veröffentlicht unter der [MIT-Lizenz](LICENSE). Bitte beachten Sie [DISCLAIMER.md](DISCLAIMER.md).
