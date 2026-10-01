# 키드 이카루스: 신화와 괴물 (GB) 한글 패치

*Kid Icarus: Of Myths and Monsters* (게임보이, 북미·유럽 공용판) 비공식 한국어 팬 패치입니다.
영문판 원문을 기준으로 번역했습니다.

**제작: arqhive** · **최신 버전: [v0.1](https://github.com/arqhive/kid-icarus-of-myths-and-monsters-korean-translation/releases/tag/v0.1)**

- 대사 테이블 39개를 모두 번역했습니다. 상점, 훈련, 무기, 저주 해제, 온천, 성장, 힌트, 최종 보스와 엔딩 대사가 들어 있습니다.
- 타이틀 로고·부제·오프닝, 새 게임·이어하기, 상태창, 결과 화면, 저장 질문, 일시 정지, 게임 오버와 마지막 엔딩 문구를 한글로 바꿨습니다.
- 대사는 Galmuri7로 그리고 받침은 글자 아래 칸에 따로 그려 읽기 쉽게 했습니다. 타이틀은 Galmuri11, 부제는 Galmuri9로 그립니다. 한글 글꼴이 ROM에 들어 있어 에뮬레이터에 별도 폰트를 설치할 필요가 없습니다.
- 배포본은 원본 영문 ROM에 적용하는 **IPS 패치**입니다. ROM은 128 KiB에서 256 KiB로 확장하며 MBC2 배터리 저장 방식을 유지합니다.

> Git 추적 대상에는 **게임 ROM, 추출한 원문 대사, 원본 그래픽, 스크린샷, 세이브가 들어 있지 않습니다.**
> 패치를 만들거나 적용하려면 본인이 소유한 게임에서 직접 덤프한 원본이 필요합니다. 빌드·분석·테스트 산출물은 Git에서 제외합니다.

## 사용자용: 패치 적용

### 준비물

- 수정하지 않은 `Kid Icarus - Of Myths and Monsters (USA, Europe).gb` (131,072바이트).
- IPS를 적용할 수 있는 패처. 동봉한 `apply_patch.py`를 쓰려면 Python 3.11 이상이 필요합니다.
- 게임보이 에뮬레이터. 아래 실행 환경과 검증 범위를 참고하세요.

| 항목 | 값 |
|---|---|
| 원본 SHA-256 | `92c1fbf422abb8f09ca7fdbb563d1284108cc042e60e1222422986d9a59f9d97` |
| v0.1 결과 SHA-256 | `8b881b554cd49b907512bd82d21f6b74c4815ecb13be720490c863a20538719f` |
| 결과 크기 | 262,144바이트 (256 KiB) |

### 적용 방법

[릴리즈 페이지](https://github.com/arqhive/kid-icarus-of-myths-and-monsters-korean-translation/releases/tag/v0.1)에서 `KidIcarus_KO_v0.1.zip`을 받습니다. 아래 개발자용 빌드 절차로 직접 만들 수도 있습니다. 준비된 ZIP은 다음 두 방법 중 하나로 적용합니다.

1. ZIP을 폴더째 풉니다.
2. 일반 IPS 패처에서 `KidIcarus_KO_v0.1.ips`와 **원본 영문 ROM**을 선택하고 별도 결과 파일을 만듭니다. 또는 압축을 푼 폴더에서 아래 명령을 실행합니다.
3. 만들어진 `Kid Icarus - Korean Full (Galmuri).gb`를 실행합니다. 이전 한글판의 강제 저장 상태(세이브 스테이트)를 불러오지 말고 ROM을 새로 실행하세요.

```bash
python apply_patch.py "원본.gb"
```

동봉 패처는 원본·패치·결과의 SHA-256을 확인하고 원본을 보존합니다. 결과 이름을 바꾸려면 `--output "결과.gb"`를 붙입니다. 타이틀과 오프닝도 포함된 통합 패치이므로 이전 한글 ROM 위에 덧씌우지 마세요.

자세한 방법은 [`README_한국어.txt`](release/README_한국어.txt)를 참고하세요.

### 실행 환경

- **확인함**: mGBA에서 오프닝·타이틀, 힌트 방 대사, 상태창, 남은 기회 화면.
- 처음부터 끝까지 직접 클리어하는 전 구간 플레이 검증과 실기 검증은 하지 않았습니다.

### 알려진 문제

- 현재 검사 범위에서 추가 번역 누락은 발견되지 않았습니다. 드문 조건의 장면 전환은 플레이 검수가 더 필요합니다.
- 대사 세 번째 줄의 받침은 대사 상자 바로 아래 줄에 표시됩니다. 장면에 따라 이 줄이 가려지거나 배경과 겹치는지 검수가 더 필요합니다.
- 기존 버전의 세이브 스테이트는 변경된 대사 주소·글꼴과 맞지 않을 수 있습니다.
- Nintendo 상표·저작권 표기와 내부 카트리지 제목은 유지했습니다. 사용하지 않는 원문 리소스도 ROM 안에 남아 있으나, 확인한 출력 경로는 한글 데이터를 사용합니다.

## 개발자용: 직접 빌드

### 요구 사항

- Python 3.11 이상과 [`requirements.txt`](requirements.txt)의 패키지(Pillow).
- 위 해시에 맞는 원본 ROM. `roms/Kid Icarus - Of Myths and Monsters (USA, Europe).gb`에 두거나 `KID_ICARUS_ROM` 환경 변수로 경로를 지정합니다. 기존 작업 폴더 호환을 위해 루트의 같은 파일명도 인식합니다.
- Galmuri7/Galmuri9/Galmuri11 BDF. `python tools/fetch_fonts.py`로 고정된 업스트림 커밋의 폰트를 내려받습니다. 폰트 파일은 Git에서 제외하고 출처·OFL 라이선스는 함께 보관합니다.

### 빌드

프로젝트 루트에서 실행합니다.

```powershell
python -m venv .venv
# Windows PowerShell에서 가상 환경 활성화
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python tools/fetch_fonts.py
python tools/build.py
python tools/verify_build.py
python tools/make_release.py v0.1
```

이미 구성한 `.venv`는 재사용할 수 있습니다. PowerShell에서 활성화 스크립트를 실행할 수 없다면 `python` 대신 `.\.venv\Scripts\python.exe`를 사용하세요. 다른 운영체제에서는 해당 환경의 가상 환경 활성화 명령을 사용합니다.

`build.py "원본.gb"`로 원본을 한 번 지정할 수도 있습니다. 이후 검증·패키징에도 같은 경로를 사용하려면 `KID_ICARUS_ROM`을 설정하거나 위 기본 위치에 원본을 두세요.

- `build.py`: 오프닝 → 타이틀 → 전체 텍스트를 메모리에서 차례로 빌드해 `work/Kid Icarus - Korean Full (Galmuri).gb` 하나와 `work/full/Kid_Icarus_Korean_Full.ips`를 만듭니다. Windows에서는 실제 바탕화면 위치를 찾아 완성본 한 개를 복사하고 해시 일치를 확인합니다.
- `verify_build.py`: 에뮬레이터 없이 ROM 데이터만 검사합니다. 체크섬·IPS 적용 결과, 원본 뱅크의 변경 위치, 코드 패치, 대사 39개의 글자·받침 그림과 줄 배치, UI 글자와 원본 그림 보존, 타이틀 ™·일시 정지·엔딩 글자를 확인합니다. 결과는 `work/full/verification.json`, 대사 재현 이미지는 `work/full/dialogue_pages.png`입니다. 화면 확인은 에뮬레이터에서 직접 합니다.
- `make_release.py v0.1`: 검증을 통과한 ROM인지, IPS 적용 결과가 같은지 확인한 뒤 IPS와 해시 확인 패처, 설명서·라이선스를 `release/KidIcarus_KO_v0.1.zip`으로 묶습니다. 원본 및 완성 ROM은 ZIP에 넣지 않습니다.

### 번역 수정

- [`translation/ko.json`](translation/ko.json)의 `opening`, `menu`, `dialogues`, `labels`, `sprites`, `pause`, `ending`, `title`, `subtitle`을 수정합니다.
- 일반 대사는 한 줄 18칸, 한 페이지 3줄, 위 글자와 받침 글자를 합쳐 26칸 이하입니다. 오프닝은 27줄의 페이지 구조와 한 줄 20칸 제한을 유지합니다. 빌드에서 제한을 검사합니다.
- 대사 번호·개수와 FD/FF 제어코드는 원본에서 가져옵니다. 연속 문장은 한국어 어순에 맞게 페이지 사이 표현을 조정했습니다.
- `python tools/extract_text.py`로 원문을 로컬 `work/full/dialogues_en.json`에 추출할 수 있습니다. 전체 빌드의 `manifest.json`에도 원문·번역문·위치가 기록됩니다. 이 파일들은 Git에서 제외합니다.
- 용어는 [`translation/GLOSSARY.md`](translation/GLOSSARY.md), 검수 범위는 [`docs/VERIFICATION.md`](docs/VERIFICATION.md)를 참고하세요.

### 폴더 구조

```
tools/           원문 추출, 글꼴·타이틀·본문 빌드, ROM 데이터 검증, IPS 적용·배포 도구
  fonts/         글꼴 출처·OFL 라이선스 (다운로드한 BDF는 Git 제외)
translation/     한국어 번역 데이터, 용어집
docs/            기술 문서, 검수 기록, 릴리즈 노트
release/         사용자 설명서 (생성된 IPS·ZIP·해시 목록은 Git 제외)
roms/            원본 ROM (Git 제외)
work/            최종 ROM·IPS·원문·미리보기·검증 결과 (Git 제외)
.venv/           로컬 Python 빌드·검증 환경 (Git 제외)
```

이전 `analysis/`, `korean_demo/`, `korean_full/` 폴더는 정리했습니다. 새 빌드는 추적 중인 소스, 원본 ROM, 글꼴, Python 의존성만 사용합니다. `work/`의 중간 산출물은 빌드·검증 시 다시 생성되며, 정리 후에는 최신 완성 ROM만 남겨 둡니다.

### 기술 문서

ROM 뱅크, 문자 인코딩, 동적 글꼴과 타이틀 처리 방식은 [`docs/TECHNICAL.md`](docs/TECHNICAL.md)에 정리했습니다.

## 변경 내역

전체 내역은 [`CHANGELOG.md`](CHANGELOG.md)에 있습니다.

## 크레딧·라이선스

- 이 저장소의 도구 코드, 한국어 번역문, 문서: [MIT License](LICENSE) (© 2026 arqhive).
- 글꼴: quiple / Lee Minseo의 Galmuri7·Galmuri9·Galmuri11, [SIL Open Font License 1.1](tools/fonts/OFL.txt). 사용한 커밋과 원본 파일 위치는 `tools/fonts/SOURCE*.txt`에 기록했습니다.
- 타이틀의 한글은 Galmuri 글립을 정수 배율로 그려 게임보이 타일로 변환합니다.

## 면책

비공식 팬 번역이며 Nintendo와 관련이 없습니다. 「Kid Icarus」 관련 상표·게임 저작권은 해당 권리자에게 있습니다.
패치를 적용한 게임 파일은 배포하지 마세요.
