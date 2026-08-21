# 월야 · Yueye (阅页)

<p align="center">
  <strong>열람 권한이 있는 온라인 문서를 검색 가능한 오프라인 사본으로 저장하세요.</strong>
</p>

<p align="center">
  <a href="https://yueye.jingzhiacademy.com/"><img src="https://img.shields.io/badge/공식사이트-yueye.jingzhiacademy.com-blue?style=flat-square" alt="Website" /></a>
  <a href="https://github.com/satoshinj/yueye/releases"><img src="https://img.shields.io/github/v/release/satoshinj/yueye?style=flat-square&color=success" alt="Release" /></a>
  <img src="https://img.shields.io/badge/플랫폼-Windows%2010%20%2F%2011-lightgrey?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/라이선스-MIT-orange?style=flat-square" alt="License" />
</p>

<p align="center">
  <a href="README.md">简体中文</a> |
  <a href="README_EN.md">English</a> |
  <a href="README_JA.md">日本語</a> |
  <b>한국어</b> |
  <a href="README_ES.md">Español</a> |
  <a href="README_FR.md">Français</a> |
  <a href="README_DE.md">Deutsch</a> |
  <a href="README_RU.md">Русский</a>
</p>

---

> [!IMPORTANT]
> **준법 및 법적 고지**: 본 도구는 사용자가 **로그인하여 합법적인 접근 권한을 보유한** 콘텐츠를 개인적인 오프라인 열람용으로 저장하기 위해 제작되었습니다. 권한이 없는 문서는 서버에서 전송되지 않습니다. 보안 해제, 캡차 우회, 슬라이더 자동 입력을 수행하지 않습니다. 자세한 내용은 [DISCLAIMER.md](DISCLAIMER.md)를 참조하십시오.

---

## ✨ 주요 기능

| 기능 모듈 | 핵심 기능 | 장점 및 특징 |
|---|---|---|
| **스마트 경로 감지** | 웹 기사 / 뷰어 / 전체 스크린샷 자동 선택 | 본문 텍스트는 **검색 가능한 텍스트 PDF**로 출력(용량 90% 절감), 뷰어는 원본 픽셀 보존 |
| **초고속 성능** | `canvas.toDataURL` 원본 픽셀 직접 추출 + 해시 프로브 | 페이지당 **26ms** 추출(일반 스크린샷 대비 8배 빠름), 백 페이지 몇 초 내보내기 |
| **동적 페이지 넘김 탐색** | 입력창 → 다음 페이지 버튼 → 스크롤 → 키보드 | **CSS 선택자 하드코딩 없음**, 런타임에 유효한 페이지 넘김 방식을 자동 감지 및 고정 |
| **오류 복구 및 즉각 중지** | 뷰어 예열 + 백오프 재시도 + 밀리초 단위 중지 | 오버레이 팝업 자동 닫기, "중지" 버튼 클릭 시 즉시 종료 |
| **다양한 브라우저 지원** | Edge, Chrome, 360, QQ, Brave, Cent 브라우저 자동 탐색 | 좀비 락(`SingletonLock`) 자동 정리, 자동화 제어 배너 제거, 프록시/SSL 오류 무시 |
| **다양한 포맷 & 페이지 범위** | PDF(텍스트/이미지) / Word / Markdown / 텍스트 / 이미지 | 지정 페이지 구간(예: `1-10`) 지원, 백그라운드 비동기 내보내기로 UI 멈춤 없음 |

---

## 🚀 빠른 시작

### 방법 A: 무설치 포터블 버전 (권장 · Python 불필요)

1. [GitHub Releases](https://github.com/satoshinj/yueye/releases)에서 `Yueye-v1.0.3-win-x64.zip`을 다운로드하고 압축을 풉니다.
2. `阅页.exe` 실행:
   - 먼저 **「登录浏览器」(브라우저 로그인)**을 클릭하여 대상 사이트에 로그인합니다.
   - 문서 URL을 붙여넣고 포맷 및 페이지 범위를 선택한 후 **「开始抓取」(추출 시작)**을 누릅니다.

### 방법 B: CLI 명령줄 모드 (배치 자동화)

```cmd
# 전체 문서를 PDF로 내보내기
阅页.exe --url "https://..." --format pdf

# 1~10페이지만 Markdown으로 지정 폴더에 내보내기
阅页.exe --url "https://..." --format markdown --range 1-10 --out ./output

# 특정 브라우저 경로 지정
阅页.exe --url "https://..." --browser "C:\Path\To\Chrome.exe"
```

### 방법 C: 소스코드 실행 (개발자)

```bash
git clone https://github.com/satoshinj/yueye.git
cd yueye
pip install -r requirements.txt
playwright install chromium
python app.py
```

---

## 📝 라이선스

본 프로젝트는 [MIT License](LICENSE)에 따라 제공됩니다. 사용 전 [DISCLAIMER.md](DISCLAIMER.md)를 확인하세요.
