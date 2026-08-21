# Yueye · 阅页

<p align="center">
  <strong>Convierte documentos en línea a los que tienes acceso en copias sin conexión con capacidad de búsqueda.</strong>
</p>

<p align="center">
  <a href="https://yueye.jingzhiacademy.com/"><img src="https://img.shields.io/badge/Sitio_Web-yueye.jingzhiacademy.com-blue?style=flat-square" alt="Website" /></a>
  <a href="https://github.com/satoshinj/yueye/releases"><img src="https://img.shields.io/github/v/release/satoshinj/yueye?style=flat-square&color=success" alt="Release" /></a>
  <img src="https://img.shields.io/badge/Plataforma-Windows%2010%20%2F%2011-lightgrey?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/Licencia-MIT-orange?style=flat-square" alt="License" />
</p>

<p align="center">
  <a href="README.md">简体中文</a> |
  <a href="README_EN.md">English</a> |
  <a href="README_JA.md">日本語</a> |
  <a href="README_KO.md">한국어</a> |
  <b>Español</b> |
  <a href="README_FR.md">Français</a> |
  <a href="README_DE.md">Deutsch</a> |
  <a href="README_RU.md">Русский</a>
</p>

---

> [!IMPORTANT]
> **Aviso de cumplimiento y legalidad**: Esta herramienta está diseñada exclusivamente para la lectura personal fuera de línea de contenido al que usted tiene **acceso autorizado y ha iniciado sesión**. No elude muros de pago, no descifra CAPTCHA ni resuelve controles deslizantes. Consulte [DISCLAIMER.md](DISCLAIMER.md).

---

## ✨ Características Principales

| Módulo | Capacidad | Ventajas |
|---|---|---|
| **Detección Inteligente de Ruta** | Selección automática: Artículo web / Visor paginado / Captura completa | Artículos generan **PDF con texto buscable** (90% menor tamaño); Visores Canvas guardan píxeles nativos |
| **Rendimiento Ultra Rápido** | `canvas.toDataURL` nativo + sonda de estabilidad por hash | **26 ms/página** (8 veces más rápido que capturas estándar), exportación de 100 páginas en segundos |
| **Exploración Dinámica de Páginas** | Entrada de página → Botón siguiente → Contenedor → Teclado | **Sin selectores CSS rígidos**; detecta y fija automáticamente el mecanismo de paginación funcional |
| **Resiliencia y Parada Instantánea** | Precalentamiento de visor + reintentos + parada inmediata | Cierre automático de anuncios superpuestos; botón "Detener" responde en milisegundos |
| **Compatibilidad con Navegadores** | Detección automática de Edge, Chrome, 360, QQ, Brave, Cent | Limpieza de bloqueos (`SingletonLock`), eliminación de banners de automatización, soporte de proxy/SSL |
| **Multi-Formato y Rango de Páginas** | PDF (Texto/Imagen) / Word / Markdown / Texto plano / Imágenes | Permite seleccionar páginas específicas (ej. `1-10`); exportación asíncrona en segundo plano |

---

## 🚀 Inicio Rápido

### Opción A: Versión Portátil (Recomendada · Sin necesidad de Python)

1. Descarga `Yueye-v1.0.3-win-x64.zip` desde [GitHub Releases](https://github.com/satoshinj/yueye/releases) y descomprímelo.
2. Ejecuta `阅页.exe`:
   - Haz clic primero en **「登录浏览器」(Iniciar sesión)** para autenticarte en tu cuenta.
   - Pega la URL, selecciona el formato y rango de páginas, y haz clic en **「开始抓取」(Iniciar captura)**.

### Opción B: Modo CLI (Línea de Comandos / Automatización)

```cmd
# Exportar documento completo a PDF
阅页.exe --url "https://..." --format pdf

# Exportar páginas 1 a 10 como Markdown a una carpeta específica
阅页.exe --url "https://..." --format markdown --range 1-10 --out ./output

# Especificar un navegador personalizado
阅页.exe --url "https://..." --browser "C:\Path\To\Chrome.exe"
```

---

## 📝 Licencia

Distribuido bajo la [Licencia MIT](LICENSE). Consulta [DISCLAIMER.md](DISCLAIMER.md) para más detalles.
