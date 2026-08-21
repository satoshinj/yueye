# Yueye · 阅页

<p align="center">
  <strong>Transformez les documents en ligne auxquels vous avez accès en copies hors ligne indexables et consultables.</strong>
</p>

<p align="center">
  <a href="https://yueye.jingzhiacademy.com/"><img src="https://img.shields.io/badge/Site_Web-yueye.jingzhiacademy.com-blue?style=flat-square" alt="Website" /></a>
  <a href="https://github.com/satoshinj/yueye/releases"><img src="https://img.shields.io/github/v/release/satoshinj/yueye?style=flat-square&color=success" alt="Release" /></a>
  <img src="https://img.shields.io/badge/Plateforme-Windows%2010%20%2F%2011-lightgrey?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/Licence-MIT-orange?style=flat-square" alt="License" />
</p>

<p align="center">
  <a href="README.md">简体中文</a> |
  <a href="README_EN.md">English</a> |
  <a href="README_JA.md">日本語</a> |
  <a href="README_KO.md">한국어</a> |
  <a href="README_ES.md">Español</a> |
  <b>Français</b> |
  <a href="README_DE.md">Deutsch</a> |
  <a href="README_RU.md">Русский</a>
</p>

---

> [!IMPORTANT]
> **Avis de conformité et légalité** : Cet outil est conçu uniquement pour la lecture hors ligne personnelle de contenus auxquels vous avez **accès légitime et êtes connecté**. Les serveurs n'envoient pas les pages hors autorisation. Il ne contourne aucun verrou, ne résout pas les CAPTCHA ni les puzzles de sécurité. Consultez [DISCLAIMER.md](DISCLAIMER.md).

---

## ✨ Fonctionnalités Clés

| Module | Fonction | Avantages |
|---|---|---|
| **Détection Intelligente du Type de Page** | Sélection auto : Article Web / Lecteur Paginé / Capture Complète | Les articles génèrent un **PDF texte avec recherche** (taille réduite de 90%) ; les lecteurs Canvas extraient les pixels originaux |
| **Performances Exceptionnelles** | Extraction directe `canvas.toDataURL` + sonde de stabilité par hachage | **26 ms/page** (8x plus rapide qu'une capture d'écran classique), exportation de 100 pages en quelques secondes |
| **Essai Dynamique de Navigation** | Champ de page → Bouton suivant → Conteneur → Clavier | **Aucun sélecteur codé en dur** ; découvre et verrouille automatiquement la pagination fonctionnelle |
| **Résilience et Arrêt Immédiat** | Préchauffage du lecteur + nouvelle tentative exponentielle + arrêt réactif | Fermeture automatique des popups ; le bouton "Arrêter" coupe l'exécution en quelques millisecondes |
| **Compatibilité Étendue des Navigateurs** | Détection automatique d'Edge, Chrome, 360, QQ Browser, Brave, Cent | Nettoyage des verrous zombies (`SingletonLock`), suppression des bannières de test, prise en charge des proxy/SSL |
| **Formats Multiples & Sélection de Pages** | PDF (Texte/Image) / Word / Markdown / Texte Brut / Images | Support des intervalles de pages (ex: `1-10`) ; exportation asynchrone sans blocage de l'interface |

---

## 🚀 Démarrage Rapide

### Option A : Version Portable (Recommandée · Sans Python)

1. Téléchargez `Yueye-v1.0.3-win-x64.zip` depuis les [GitHub Releases](https://github.com/satoshinj/yueye/releases) et décompressez-le.
2. Lancez `阅页.exe` :
   - Cliquez d'abord sur **「登录浏览器」(Connexion)** pour vous connecter à votre compte.
   - Collez l'URL du document, choisissez le format et la plage de pages, puis cliquez sur **「开始抓取」(Démarrer)**.

### Option B : Mode Ligne de Commande (CLI & Automatisation)

```cmd
# Exporter le document complet en PDF
阅页.exe --url "https://..." --format pdf

# Exporter les pages 1 à 10 en Markdown dans un dossier spécifique
阅页.exe --url "https://..." --format markdown --range 1-10 --out ./output

# Utiliser un navigateur personnalisé
阅页.exe --url "https://..." --browser "C:\Path\To\Chrome.exe"
```

---

## 📝 Licence

Distribué sous [Licence MIT](LICENSE). Veuillez consulter [DISCLAIMER.md](DISCLAIMER.md).
