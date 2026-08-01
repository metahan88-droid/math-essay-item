판정부터 말하면, 현재 버전은 **실제 최종 업무 투입 불가(No-Go)** 입니다.

가장 큰 이유는 다음 다섯 가지입니다.

- 정상 PNG처럼 보이지만 실제로는 열 수 없는 IDAT, `IEND` 뒤 잉여 바이트가 build와 check를 모두 통과합니다.
- 제공된 정상 JSON/PNG로 build는 성공하지만, 그 산출물은 템플릿의 미사용 `image1.bmp`, `image2.bmp` 때문에 check 5.6에서 실패합니다.
- 같은 출력 파일명으로 동시에 빌드하면 잠금과 원자적 공개가 없어 손상 ZIP 또는 다른 교사의 내용이 조용히 남을 수 있습니다.
- 문장 중간에 남은 미매핑 `[그림 N]`은 최종 검사에서 `PASS/0`이 됩니다.
- 5.6은 ZIP에만 있는 파일, `_figs` 밖의 손상 payload, 중복 manifest ID/ZIP 엔트리를 전체 `PASS/0`으로 통과시킵니다.

## 실행 범위와 제약

직접 검토한 소스는 요청된 네 파일뿐입니다.

- [build_tpl2.py](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:1>)
- [check_tpl2.py](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:1>)
- [img_embed.py](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/img_embed.py:1>)
- [figlib.py](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:1>)

입력은 지정된 `valid-similarity-20pt.json`과 세 PNG를 사용했습니다.

다만 현재 세션은 파일시스템이 전역 읽기 전용이어서 지정된 scratchpad에도 파일을 만들 수 없었습니다.

```text
mkdir .../scratchpad/cx6a/png_agent
mkdir: ...: Operation not permitted

node fs.writeFile(...)
EPERM: operation not permitted
```

따라서 다음 방식으로 실제 코드를 실행했습니다.

- CLI 인자 시험은 원본 스크립트를 그대로 subprocess로 실행했습니다.
- build/check 본체는 원본 파일을 `runpy`/모듈 로더로 그대로 실행했습니다.
- `mkdtemp`, 작업 트리 파일 쓰기와 최종 ZIP 출력만 메모리 파일시스템 및 `io.BytesIO`로 연결했습니다.
- build의 템플릿 복사, XML 조립, `img_embed` 호출, `register_images`, ZIP 엔트리 작성은 원본 코드가 수행했습니다.
- check는 전체 1~7절과 실제 `SystemExit`까지 실행했습니다.
- HWPX 변조는 메모리 ZIP의 해당 엔트리만 교체했습니다.
- 스킬 폴더와 scratchpad 모두 실제 파일 변경은 없습니다.

이 방식으로 변경 1·2·4는 전체 코드 경로를 실행했지만, 변경 3의 **실제 macOS 파일시스템 동시 쓰기와 종료 후 잔여 디렉터리 시험만은 수행하지 못했습니다.** 해당 부분은 실행했다고 꾸미지 않고 코드상 확정되는 결과와 미검증 부분을 구분했습니다.

---

# 1. PNG 유효성 확인

## 요청된 비정상 PNG 5종

정상 build의 전체 check는 뒤에서 설명할 기존 오류 때문에 이미 `오류 3건 / 경고 1건`입니다. 따라서 PNG 검출 여부는 다음 두 조건으로 판정했습니다.

- check 5.5에 `삽입된 BinData가 정상 PNG가 아님`이 추가되는가
- 전체 오류 수가 기준 3건에서 4건으로 증가하는가

| 입력 | build 결과 | check 5.5 | 판정 |
|---|---|---|---|
| PNG 서명 + 완전한 IHDR만 있는 33바이트 파일 | `ValueError`, 산출 없음 | `IDAT 없음` 오류 추가 | 정상 검출 |
| IHDR + IEND, IDAT 없음 | `ValueError`, 산출 없음 | `IDAT 없음` 오류 추가 | 정상 검출 |
| IDAT CRC 1비트 오류 | `ValueError`, 산출 없음 | `IDAT CRC 불일치` 오류 추가 | 정상 검출 |
| 정상 IEND 뒤 `EXTRA` 5바이트 | **build 0, 산출 성공** | **PNG 오류 없음** | **조용히 통과** |
| IHDR 폭·높이 0 | `ValueError`, 산출 없음 | `크기 0x0` 오류 추가 | 정상 검출 |

핵심 로그는 다음과 같습니다.

```text
BUILD_CASE M1_IHDR_only
RESULT exception ValueError
정상 PNG가 아님: ...: IDAT 없음(그림 데이터가 없다)
ZIP 0
```

```text
BUILD_CASE M3_bad_CRC
RESULT exception ValueError
정상 PNG가 아님: ...: b'IDAT' 청크 CRC 불일치
ZIP 0
```

```text
BUILD_CASE M4_trailing
RESULT exit 0
그림 3개 삽입: ['fig1', 'fig5', 'fig6']
wrote .../b_M4_trailing.hwpx
```

```text
CHECK_CASE M4_trailing
### 5.5 그림 게이트 (최종 모드)
  _figs 선언 3건, 삽입·등록·PNG 확인, BinData 5개
FAIL — 오류 3건 / 경고 1건
```

마지막 `FAIL`은 다른 검사 오류 때문이고, PNG 오류 수는 기준본과 같습니다. 즉 `IEND` 뒤 잉여 바이트는 PNG 게이트에서 완전히 놓쳤습니다.

원인은 [img_embed.py 46–48행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/img_embed.py:46>)입니다.

```python
if typ == b'IEND':
    ended = True
    break
```

`IEND`를 만나자마자 순회를 멈추고 `end == len(data)`를 보지 않습니다.

## 정상 PNG 오탐

요청된 정상 사례에서는 false positive가 없었습니다.

| 정상 입력 | 크기 | build | check 5.5 |
|---|---:|---:|---|
| 동봉 `fig1_three_sizes.png` | 1220×620, 72,102B | 0 | PNG 오류 없음 |
| 동봉 `fig5_menu_board.png` | 1480×600, 72,700B | 0 | PNG 오류 없음 |
| 동봉 `fig6_owner_memo.png` | 1520×788, 175,077B | 0 | PNG 오류 없음 |
| 실제 Adam7 인터레이스 PNG | 17×13, interlace=1 | 0 | PNG 오류 없음 |
| 팔레트/PLTE PNG | color type 3 | 0 | PNG 오류 없음 |
| tEXt 보조 청크 PNG | IHDR–tEXt–IDAT–IEND | 0 | PNG 오류 없음 |
| 큰 grayscale PNG | 4096×4096 | 0 | PNG 오류 없음 |

인터레이스 파일은 IHDR의 interlace 바이트가 실제로 `1`인지 확인한 뒤 `verified_png_path`에 넣었습니다.

```text
bytes 313
IHDR_interlace 1
verified_png_path (19, 13)
```

## 추가로 조용히 통과한 잘못된 PNG

현재 validator는 “청크 이름이 존재하는지”만 보고 IDAT의 실제 압축 데이터를 복원하지 않습니다. 다음 입력은 CRC를 올바르게 계산했음에도 build가 모두 0으로 성공했고, check 5.5도 오류를 내지 않았습니다.

| 입력 | 잘못된 이유 | 실제 결과 |
|---|---|---|
| 빈 IDAT | zlib 스트림 자체가 없음 | build 0, check PNG 오류 없음 |
| IDAT 바디가 `not-zlib` | CRC는 맞지만 압축 해제 불가 | build 0, check PNG 오류 없음 |
| IHDR 두 번 | PNG 구조 위반 | build 0, check PNG 오류 없음 |
| 데이터 1바이트가 든 IEND | IEND 길이는 0이어야 함 | build 0, check PNG 오류 없음 |
| interlace 값 2 | 허용값은 0 또는 1 | build 0, check PNG 오류 없음 |
| 알 수 없는 critical chunk `ABCD` | 디코더가 거부해야 하는 critical chunk | build 0, check PNG 오류 없음 |
| IDAT 사이에 tEXt | IDAT 비연속 | build 0, check PNG 오류 없음 |
| 폭 `0xFFFFFFFF` | PNG 규격/조판 가능 범위 초과 | 직접 validator 호출에서 PASS |

대표 로그:

```text
BUILD_CASE P_bad_zlib
RESULT exit 0
그림 3개 삽입: ['fig1', 'fig5', 'fig6']

CHECK_CASE P_bad_zlib
### 5.5 그림 게이트 (최종 모드)
  _figs 선언 3건, 삽입·등록·PNG 확인, BinData 5개
```

현재 [verified_png_bytes](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/img_embed.py:21>)는 다음만 확인합니다.

- PNG 서명
- 청크 범위와 CRC
- 첫 청크가 IHDR
- IDAT이라는 이름의 청크가 한 번 이상 있음
- IEND라는 이름의 청크가 있음
- 폭·높이가 양수

따라서 함수 이름과 오류 문구의 “정상 PNG”가 실제로는 “일부 청크 외형이 맞는 바이트열”에 가깝습니다.

## 검증 바이트와 실제 BinData가 다른 TOCTOU

build는 [build_tpl2.py 322행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:322>)에서 원본을 한 번 읽어 크기와 CRC를 확인한 뒤, 경로만 저장합니다.

```python
pw, ph = IE.png_size(path)
...
USED_FIGS[bin_id] = path
```

나중에 [img_embed.py 125행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/img_embed.py:125>)에서 같은 파일을 다시 열어 재검증 없이 복사합니다.

```python
open(dst, 'wb').write(open(path, 'rb').read())
```

첫 read는 정상 PNG, 두 번째 read는 IDAT CRC가 틀린 PNG가 되도록 재현했습니다.

```text
RACE_BUILD exit 0
source_reads 2
그림 1개 삽입: ['fig1']
wrote .../race.hwpx
```

산출 BinData를 다시 validator에 넣으면 다음과 같습니다.

```text
embedded_validator REJECT
정상 PNG가 아님: embedded: b'IDAT' 청크 CRC 불일치
```

두 read가 모두 정상 PNG라도 중간에 다른 크기의 파일로 교체되면 XML의 크기·종횡비와 실제 BinData가 어긋납니다.

## 변경 1 잔여 지적

- **A-1 — 비렌더링 PNG가 최종 게이트를 통과함.** 빈 IDAT와 잘못된 zlib 데이터가 build/check를 모두 통과합니다.
- **A-2 — “IEND 종료” 계약 위반.** IEND 뒤 잉여 바이트가 조용히 통과합니다.
- **B-1 — 검증/복사 TOCTOU.** 검증한 바이트가 아닌 두 번째 read를 BinData로 씁니다.
- **B-2 — figlib 검증 불일치.** [figlib.py 77–83행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:77>)도 아직 파일 크기와 8바이트 서명만 봅니다.
- **C-1 — 오류가 난 뒤에도 check가 `삽입·등록·PNG 확인`이라고 출력함.** “검사 완료”로 바꾸는 편이 안전합니다.

---

# 2. 초안/최종 모드와 CLI

## 그림 파일 누락 시 build

제공 JSON의 실제 `[그림 1] ...` 줄과 `_figs` 매핑을 사용하고 그림 경로만 없는 경로로 바꿨습니다.

```text
CASE final
EXCEPTION FileNotFoundError
최종 조판에 필요한 그림 파일이 없음:
figs/fig1_three_sizes.png
그림을 만들어 두거나, 초안이면 --draft를 붙여라.
```

```text
CASE draft
[그림 없음] figs/fig1_three_sizes.png — 초안 자리표시 텍스트로 유지
contains_placeholder=True
used_figs={}
RETURN
```

판정:

- final 기본 모드는 문서대로 중단합니다. 전체 CLI 종료 코드는 1입니다.
- draft는 문서대로 자리표시 텍스트를 남기고 계속합니다.
- 이 build 분기 자체는 맞습니다.

## build draft와 check draft의 비대칭

build `--draft`가 만드는 상태와 같이 다음을 구성했습니다.

- 본문에는 `[그림 1] 누락 그림` 텍스트가 남음
- XML 그림 참조 없음
- manifest 등록 없음
- JSON의 `_figs` 선언은 그대로 있음
- 원본 PNG는 없음

final check:

```text
CASE final RC 1
### 5.5 그림 게이트 (최종 모드)
  [ERR] 그림 원본 파일 없음/손상: ...
  [ERR] 선언한 그림이 문서에 삽입되지 않음: [그림 1] → fig1
  [ERR] 그림이 content.hpf에 등록되지 않음: fig1
FAIL — 오류 3건 / 경고 0건
```

draft check:

```text
CASE draft RC 1
### 5.5 그림 게이트 (초안 모드)
  [ERR] 그림 원본 파일 없음/손상: ...
  [ERR] 선언한 그림이 문서에 삽입되지 않음: [그림 1] → fig1
  [ERR] 그림이 content.hpf에 등록되지 않음: fig1
FAIL — 오류 3건 / 경고 0건
```

즉 정상적인 동일 JSON 흐름이 다음처럼 깨집니다.

```text
build --draft: placeholder HWPX 생성
                ↓
check --draft: FAIL, rc=1
```

check의 draft 완화는 “자리표시는 있는데 `_figs` 키가 없는 경우”에만 적용됩니다. build draft의 주된 사용 사례인 “`_figs`는 있지만 PNG가 아직 없음”은 전혀 완화하지 않습니다.

- **B-3 — build/check draft 계약 불일치.**

## `_figs` 없는 시작 위치 placeholder

이 경우 문서대로 동작했습니다.

final:

```text
CASE final_unmapped_at_start RC 1
[ERR] 최종본의 미선언 그림 자리표시: ['[그림 9]']
FAIL — 오류 1건 / 경고 0건
```

draft:

```text
CASE draft_unmapped_at_start RC 2
[WARN] 초안의 미선언 그림 자리표시: ['[그림 9]']
DRAFT-ONLY — 최종 제출 불가 / 완화 1건 / 오류 0건 / 경고 1건
```

## 문장 중간 placeholder가 최종에서 조용히 통과

현재 [check_tpl2.py 310–315행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:310>)은 `re.match`만 사용합니다.

```python
re.match(r"\[그림 \d+\]", s.strip())
```

입력:

```text
설명 뒤 [그림 9] 자리
```

결과:

```text
CASE final_unmapped_mid_sentence RC 0
### 5.5 그림 게이트 (최종 모드)
  그림 없음(자리표시도 없음)
PASS — 오류 0건 / 경고 0건
```

- **A-3 — 최종본에 미처리 placeholder가 남아도 PASS/0.**

빌더가 문자열 시작의 placeholder만 그림으로 처리한다는 사실은 중간 placeholder를 정상으로 인정할 근거가 아니라, 오히려 final에서 미처리 입력으로 거부할 근거입니다.

## 완화를 쓰지 않은 정상 `--draft`

오류도 placeholder도 없는 입력에서 실제 결과는 다음과 같습니다.

```text
CASE draft_no_waiver_clean RC 0
### 5.5 그림 게이트 (초안 모드)
  그림 없음(자리표시도 없음)
PASS — 오류 0건 / 경고 0건
```

질문에 대한 직접 답은 다음과 같습니다.

- 완화를 쓰지 않은 정상 `--draft`의 종료 코드는 **0**입니다.
- footer는 final과 똑같은 **`PASS`**입니다.
- 모드 표시는 중간의 `### 5.5 ... (초안 모드)`에만 있습니다.
- 종료 코드와 마지막 줄만 읽는 자동화에서는 최종 승인으로 오인할 여지가 있습니다.

현재 구현에서 waiver가 0이면 실제 검사 강도는 final과 같으므로 문서 내용이 즉시 덜 검증되는 것은 아닙니다. 그러나 승인 신호로는 모호합니다.

- **B-4 — draft 실행이 final과 같은 PASS/0을 냄.**

## draft waiver가 다른 실제 오류를 가림

미매핑 placeholder로 waiver를 만들고, 동시에 글꼴 오류를 넣었습니다.

```text
CASE draft_unmapped_plus_bad_font RC 2
[WARN] 초안의 미선언 그림 자리표시: ['[그림 9]']
[ERR] 통일 스타일 속성 이상: 본문(h=900, ...)
DRAFT-ONLY — 최종 제출 불가 / 완화 1건 / 오류 1건 / 경고 1건
```

원인은 [check_tpl2.py 488–496행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:488>)의 순서입니다.

```python
if DRAFT_MODE and _draft_waivers:
    ...
    sys.exit(2)

_result = "PASS" if errs == 0 else "FAIL"
```

`errs > 0`보다 waiver 분기를 먼저 처리하여, 실제 오류가 있어도 `FAIL/1` 대신 `DRAFT-ONLY/2`가 됩니다.

- **A-4 — draft 오류 분류가 실제 FAIL을 덮음.** 자동화가 2를 “그림만 미완성인 정상 draft”로 해석하면 다른 오류가 가려집니다.

## CLI 인자 순서와 미지 플래그

원본 스크립트를 직접 subprocess로 실행했습니다.

| 실행 | 코드 | 핵심 출력 |
|---|---:|---|
| `build --draft OUT JSON` | 1 | `위치 인자 1번에 플래그` |
| `build OUT --draft` | 1 | `위치 인자 2번에 플래그` |
| `build OUT JSON --bogus` | 1 | `모르는 인자: --bogus` |
| `build OUT JSON extra` | 1 | `모르는 인자: extra` |
| `check --draft OUT JSON` | 1 | `위치 인자 1번에 플래그` |
| `check OUT --draft` | 1 | `위치 인자 2번에 플래그` |
| `check OUT JSON --bogus` | 1 | `모르는 인자: --bogus` |
| `check OUT JSON extra` | 1 | `모르는 인자: extra` |

문서에 적힌 “플래그는 위치 인자 둘 뒤에만”과 미지 플래그 거부는 맞습니다.

다만 다음 잔여 문제가 있습니다.

- `OUT JSON --draft --draft`는 파싱상 허용됩니다.
- 정확한 인자 개수를 먼저 검사하지 않습니다.
- `build OUT`은 사용법 오류가 아니라 작업 폴더 생성과 숨은 `content2.json` fallback까지 진행합니다.
- `check` 무인자는 `IndexError`, `check OUT`은 HWPX open까지 진행합니다.
- 사용법에는 `content.json`이 필수인데 구현에는 문서화되지 않은 fallback이 있습니다.

등급:

- **B-5 — 필수 인자 개수와 문서가 불일치**
- **C-2 — 중복 `--draft` 허용**

---

# 3. 작업 폴더와 동시성

## 실제 디스크 시험 상태

다음 네 항목은 현재 환경의 쓰기 금지 때문에 OS 수준 실행을 완료할 수 없었습니다.

- 사용자 `out2/` 폴더를 둔 실제 빌드
- 서로 다른 출력 두 개의 실제 병렬 빌드
- 실패 프로세스 종료 후 임시 폴더 잔류 확인
- 같은 출력명으로 실제 파일을 동시에 쓰는 반복 경합

차단 로그:

```text
mkdir .../cx6a/temp_agent
Operation not permitted
```

따라서 아래의 “통과”는 소스에서 확정되는 동작이고, macOS 디스크에서 반복 실행한 통계가 아닙니다.

## 사용자 `out2/` 보존

[build_tpl2.py 46–51행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:46>)은 다음 이름을 사용합니다.

```python
OUT_DIR = tempfile.mkdtemp(
    prefix=f'.{_out_stem}.out2-',
    dir=_out_parent,
)
```

정리 대상도 정확한 `OUT_DIR` 하나입니다.

```python
atexit.register(shutil.rmtree, OUT_DIR, ignore_errors=True)
```

따라서 문자 그대로의 사용자 `out2/`는 삭제·재사용되지 않습니다. 이 변경 방향은 맞습니다.

## 서로 다른 출력 파일의 병렬 빌드

각 프로세스의 작업 트리는 `mkdtemp`가 만든 고유 경로이고, `USED_FIGS` 등도 프로세스별입니다. 최종 출력 파일명이 다르면 공유 쓰기 지점이 없습니다.

소스상 작업 트리 충돌은 해결됐습니다. 다만 실제 두 프로세스 성공/종료 코드 0은 이번 권한 환경에서 확인하지 못했습니다.

## 중간 실패 후 임시 폴더

일반적인 미처리 Python 예외나 `sys.exit()`이면 interpreter 종료 시 `atexit`가 실행되므로 보통 삭제됩니다.

하지만 다음 경우는 남습니다.

- `SIGKILL`
- 기본 신호 종료
- `os._exit()`
- Python 치명적 종료
- 전원 차단
- `rmtree` 자체 실패

특히 `ignore_errors=True` 때문에 정리 실패가 완전히 숨겨집니다.

또한 스크립트를 CLI가 아니라 장시간 살아 있는 프로세스가 import해서 사용하고 예외를 외부에서 잡는다면, 임시 폴더는 그 프로세스가 최종 종료될 때까지 유지됩니다.

- **B-6 — “실패 시 항상 정리” 보장이 아니며 실패도 숨김.**

## 같은 산출 파일명 동시 쓰기

이 부분은 명백히 안전하지 않습니다. [build_tpl2.py 972–983행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:972>)은 다음 순서입니다.

```python
if os.path.exists(out_path):
    os.remove(out_path)

zf = zipfile.ZipFile(out_path, 'w')
...
zf.close()
```

잠금, staged 파일, `os.replace()`가 모두 없습니다.

가능한 결과는 다음과 같습니다.

1. 두 프로세스가 모두 `exists()`를 참으로 보고 한쪽이 삭제한 뒤, 다른 쪽 `remove()`가 `FileNotFoundError`를 냅니다.
2. 두 프로세스가 같은 pathname을 `w`로 열어 truncate와 ZIP 쓰기를 섞어 손상 ZIP을 만듭니다.
3. 한쪽이 쓰는 pathname을 다른 쪽이 unlink한 뒤 새 inode로 쓰면, 첫 프로세스도 `wrote ...`까지 출력하지만 그 결과는 경로에서 사라집니다.
4. 손상 없이 끝나더라도 마지막 프로세스의 결과가 비결정적으로 남습니다.
5. 서로 다른 문항 JSON을 같은 출력명에 썼다면, 구조적으로 정상인 HWPX인데 다른 교사의 내용이 남는 침묵 오출력이 가능합니다.
6. 기존 정상본을 먼저 삭제하므로 새 ZIP 쓰기 실패 시 정상 구본도 잃습니다.

- **A-5 — 동일 출력명 동시 빌드가 침묵 교차 콘텐츠를 만들 수 있음.**
- **B-7 — 기존 정상 산출물을 쓰기 전에 삭제함.**

고유 임시 작업 트리는 중간 파일 경합만 해결했을 뿐 최종 공개 경합은 해결하지 않았습니다.

---

# 4. BinData 정합

## 문서에 적힌 세 방향의 검사는 맞음

제공 JSON의 모든 검사 대상 문자열과 실제 PNG 3개를 사용해, 다른 절도 모두 통과하는 최소 정상 HWPX를 만들었습니다. 기준본은 전체 `PASS/0`입니다.

정상:

```text
CASE normal rc=0
### 5.6 BinData 정합
  고아 0건 / 참조 누락 0건 (등록 3개, 참조 3개)
PASS — 오류 0건 / 경고 0건
```

manifest에만 있고 참조되지 않음:

```text
CASE manifest_only_orphan rc=1
[ERR] 고아 BinData(아무도 참조하지 않음):
      {'orphan': 'BinData/orphan.png'}
FAIL — 오류 1건 / 경고 0건
```

참조되지만 manifest에 없음:

```text
CASE reference_missing_manifest rc=1
[ERR] 참조되나 매니페스트에 없음: ['ghost']
FAIL — 오류 1건 / 경고 0건
```

manifest에는 있지만 ZIP에 없음:

```text
CASE manifest_href_missing_zip rc=1
[ERR] 매니페스트에 있으나 ZIP에 없음:
      ['BinData/ghost.png']
FAIL — 오류 1건 / 경고 0건
```

따라서 변경 설명의 세 핵심 비교 자체는 실제와 일치합니다.

## 현재 build의 정상 산출물이 바로 5.6에서 실패

제공된 정상 JSON과 PNG로 실제 build 전체 경로를 실행했습니다.

```text
build rc=0
HWPX 크기 768295 bytes
ZIP 엔트리 16개
BinData 엔트리 5개

그림 3개 삽입: ['fig1', 'fig5', 'fig6']
wrote .../baseline-memory.hwpx
lineseg 922개, SQUEEZE 다중줄 위반 0건
```

그 직후 check:

```text
check rc=1

### 5.6 BinData 정합
  [ERR] 고아 BinData(아무도 참조하지 않음):
        {'image1': 'BinData/image1.bmp',
         'image2': 'BinData/image2.bmp'}

FAIL — 오류 3건 / 경고 1건
```

원인은 명확합니다.

- build는 템플릿 전체를 `copytree()`합니다.
- `register_images()`는 새 PNG와 manifest 항목을 추가만 합니다.
- 문서 편집으로 참조가 사라진 기존 `image1`, `image2`를 삭제하는 코드가 없습니다.

두 manifest 항목과 두 실제 BMP를 제거하자 5.6은 통과했습니다.

```text
고아 0건 / 참조 누락 0건 (등록 3개, 참조 3개)
```

전체 오류도 3에서 2로 정확히 하나 줄었습니다.

즉 “정리 단계를 건너뛴 산출물은 실패한다”는 checker의 동작은 맞지만, **현재 builder가 항상 정리 단계를 건너뛰고 있습니다.**

- **A-6 — 기본 build→check 계약이 깨짐.**

수동 정리 뒤에도 전체 check는 다음 두 별도 문제 때문에 실패합니다.

```text
[RISK] 1줄 캐시인데 폭 초과: '영역/단원'
[RISK] 1줄 캐시인데 폭 초과: '문항 번호'
[RISK] 1줄 캐시인데 폭 초과: '(채점요소)'

[ERR] 표내 비통일 charPr: {...}

FAIL — 오류 2건 / 경고 1건
```

이는 이번 네 변경 밖의 기존 레이아웃/글꼴 검사 문제이지만, 제공된 “valid” 입력이 최종 `PASS`가 되지 않는다는 점에서 별도 릴리스 차단 사유입니다.

## 5.6이 놓치는 사례

아래 사례는 다른 검사까지 포함한 전체 check가 모두 `rc=0`, `PASS — 오류 0건 / 경고 0건`으로 끝났습니다.

| 잘못된 입력 | 실제 결과 |
|---|---|
| ZIP에만 정상 `BinData/ziponly.png` 추가 | PASS/0 |
| ZIP에만 `b"not a png"` 추가 | PASS/0 |
| XML·manifest·ZIP 관계는 맞지만 `_figs` 밖 `ghost` payload가 `b"not a png"` | PASS/0 |
| 같은 manifest ID·같은 href 중복 | PASS/0 |
| 같은 manifest ID·서로 다른 href 중복 | PASS/0 |
| 첫 중복 ID의 href는 ZIP에 없고 뒤 항목만 정상 | PASS/0 |
| 서로 다른 ID가 동일 href 공유 | PASS/0 |
| `binaryItemIDRef=""` | PASS/0 |
| ZIP에 같은 `BinData/fig1.png` 이름 두 번, 첫 payload는 garbage | PASS/0 |
| `media-type="application/octet-stream"`, `isEmbeded="0"` | PASS/0 |

원인은 [check_tpl2.py 333–351행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:333>)입니다.

```python
_used = set(re.findall(..., xml))
_items = dict(re.findall(..., _hpf))
```

구체적으로:

- ZIP의 BinData 집합에서 manifest href 집합을 빼는 역방향 비교가 없습니다.
- `dict()`가 중복 ID를 마지막 항목 하나로 축약합니다.
- payload 검증은 5.5의 `_figs`에 선언된 ID만 합니다.
- 빈 ID는 `+` 정규식 때문에 수집되지 않습니다.
- `set(z.namelist())`가 중복 ZIP 이름을 숨깁니다.
- media type과 `isEmbeded`를 보지 않습니다.

등급:

- **A-7 — ZIP-only 파일과 데이터 잔존을 PASS.** 시험 자료나 다른 문항 그림이 HWPX에 숨어 배포될 수 있습니다.
- **A-8 — `_figs` 밖에서 참조되는 손상 payload를 PASS.**
- **B-8 — 중복 manifest ID가 결함을 숨김.**
- **B-9 — 중복 href와 중복 ZIP 이름 미검사.**
- **B-10 — manifest metadata와 빈 참조 미검사.**

## 정상 XML을 잘못 거절하는 경우

5.6은 다음 직렬 문자열에 의존합니다.

```python
r'<opf:item id="([^"]+)" href="(BinData/[^"]+)"'
```

따라서 의미상 같은 정상 XML에서 속성 순서만 바꾸면 실패합니다.

```xml
<opf:item
    href="BinData/fig1.png"
    id="fig1"
    media-type="image/png"
    isEmbeded="1"/>
```

결과:

```text
CASE valid_xml_reversed_attribute_order rc=1

### 5.5 그림 게이트
  _figs 선언 3건, 삽입·등록·PNG 확인, BinData 3개

### 5.6 BinData 정합
  [ERR] 참조되나 매니페스트에 없음:
        ['fig1', 'fig5', 'fig6']

FAIL — 오류 1건 / 경고 0건
```

5.5는 ElementTree로 같은 manifest를 정상 해석했습니다. 5.6만 prefix·속성 순서·공백에 의존합니다.

- **B-11 — 유효 XML 직렬화를 false reject.**
- **C-3 — section0만 참조 집합으로 사용.** 향후 다중 section 문서에서는 다른 section의 정상 참조를 고아로 오인합니다.

---

# 등급별 잔여 지적 요약

## A — 치명

1. 비렌더링 IDAT와 IEND 뒤 잉여 바이트가 build/check를 모두 통과함.
2. 최종 JSON의 문장 중간 `[그림 N]`이 PASS/0.
3. draft waiver가 다른 실제 오류의 FAIL/1을 DRAFT-ONLY/2로 덮음.
4. 동일 출력명 동시 빌드가 손상 ZIP 또는 다른 콘텐츠를 조용히 남길 수 있음.
5. 정상 build 산출물이 stale `image1.bmp`, `image2.bmp` 때문에 기본 check에서 실패함.
6. ZIP-only BinData와 `_figs` 밖의 손상 payload가 전체 PASS/0.
7. 제공된 valid 입력의 build→check가 전체적으로 green이 아님.

## B — 권고

1. PNG 검증과 실제 BinData 복사가 서로 다른 read임.
2. figlib는 여전히 서명만 확인함.
3. build draft와 check draft의 누락 그림 정책이 다름.
4. 완화를 쓰지 않은 draft가 final과 같은 PASS/0을 냄.
5. 인자 개수와 문서화되지 않은 fallback 문제.
6. atexit 정리가 비정상 종료·삭제 실패를 보장하지 않음.
7. 기존 정상 HWPX를 먼저 삭제한 뒤 새 ZIP을 직접 씀.
8. 중복 manifest ID/href, ZIP 이름, metadata, 빈 참조 미검사.
9. 5.6이 XML 의미가 아니라 prefix와 속성 순서에 의존함.

## C — 사소

1. PNG 오류가 있어도 `PNG 확인`이라는 성공처럼 보이는 문구 출력.
2. 중복 `--draft` 허용.
3. `os.walk()` 정렬과 ZIP timestamp가 고정되지 않아 raw HWPX 해시가 재현성 기준으로 부적합.
4. 현재 단일 section 전제에 묶여 있음.

---

# 그대로 붙여 쓸 수 있는 수정안

## 1. CLI를 정확한 인자 개수로 고정

두 파일의 현재 수동 검사 블록을 다음으로 교체하십시오. build에서는 반드시 `OUT_DIR` 계산보다 앞에 둡니다.

```python
_args = sys.argv[1:]

if len(_args) not in (2, 3):
    sys.exit(
        f"{USAGE}\n"
        "  위치 인자 2개와 선택적인 --draft 하나가 필요하다"
    )

for _i, _a in enumerate(_args[:2], 1):
    if _a.startswith("-"):
        sys.exit(
            f"{USAGE}\n"
            f"  위치 인자 {_i}번에 플래그가 왔다: {_a}"
        )

if len(_args) == 3 and _args[2] != "--draft":
    sys.exit(f"{USAGE}\n  모르는 인자: {_args[2]}")

OUT_PATH, CONTENT_PATH = _args[:2]
DRAFT_MODE = len(_args) == 3
```

이후 `sys.argv[1]`, `sys.argv[2]`와 `content2.json` fallback을 각각 `OUT_PATH`, `CONTENT_PATH`로 교체합니다.

## 2. placeholder를 문자열 전체에서 찾기

기존:

```python
_json_fig_ph = {
    m.group(0)
    for s in _walk_strings(_c)
    for m in [re.match(r"\[그림 \d+\]", s.strip())]
    if m
}
```

교체:

```python
_json_fig_ph = {
    m.group(0)
    for s in _walk_strings(_c)
    for m in re.finditer(r"\[그림 \d+\]", s)
}
```

## 3. draft footer보다 실제 오류를 먼저 처리

강한 승인 정책을 권고합니다. `--draft`가 붙은 실행은 waiver가 없어도 최종 승인 코드 0을 내지 않도록 합니다.

```python
if errs:
    print(
        f"\n{'=' * 60}\n"
        f"FAIL — {'초안' if DRAFT_MODE else '최종'} 모드 / "
        f"오류 {errs}건 / 경고 {warns}건 / "
        f"완화 {_draft_waivers}건"
    )
    sys.exit(1)

if DRAFT_MODE:
    print(
        f"\n{'=' * 60}\n"
        f"DRAFT-ONLY — 최종 제출 불가 / "
        f"완화 {_draft_waivers}건 / "
        f"오류 0건 / 경고 {warns}건"
    )
    sys.exit(2)

print(
    f"\n{'=' * 60}\n"
    f"FINAL-PASS — 오류 0건 / 경고 {warns}건"
)
sys.exit(0)
```

최종 승인 자동화는 종료 코드 0뿐 아니라 footer가 `FINAL-PASS`인지 확인해야 합니다.

## 4. build draft의 미삽입 그림을 check draft에서도 waiver 처리

5.5의 `_figs` 반복에서 원본 검증 결과와 문서 상태를 먼저 모읍니다.

```python
for _ph, (_fid, _rel) in _figs.items():
    _fid = str(_fid)
    _png = os.path.join(_base, _rel)

    _src_error = None
    try:
        IE.verified_png_path(_png)
    except ValueError as _ex:
        _src_error = _ex

    _in_section = _fid in _sec_ids
    _href = _hpf_items.get(_fid)

    # build --draft가 만드는 완전한 placeholder 상태만 완화한다.
    if (
        DRAFT_MODE
        and _src_error is not None
        and not _in_section
        and not _href
    ):
        warns += 1
        _draft_waivers += 1
        print(
            f"  [WARN] 초안의 미삽입 그림: "
            f"{_ph} → {_fid}, {_rel}: {_src_error}"
        )
        continue

    # 부분적으로 등록된 손상 상태는 draft에서도 오류다.
    if _src_error is not None:
        errs += 1
        print(
            f"  [ERR] 그림 원본 파일 없음/손상: "
            f"{_rel}: {_src_error}"
        )

    if not _in_section:
        errs += 1
        print(
            f"  [ERR] 선언한 그림이 문서에 삽입되지 않음: "
            f"{_ph} → {_fid}"
        )

    if not _href:
        errs += 1
        print(
            f"  [ERR] 그림이 content.hpf에 등록되지 않음: {_fid}"
        )
        continue

    if _href not in _names:
        errs += 1
        print(
            f"  [ERR] 등록된 그림 BinData가 ZIP에 없음: "
            f"{_fid} → {_href}"
        )
        continue

    try:
        IE.verified_png_bytes(z.read(_href), _href)
    except ValueError as _ex:
        errs += 1
        print(
            f"  [ERR] 삽입된 BinData가 정상 PNG가 아님: "
            f"{_fid} → {_href}: {_ex}"
        )
```

## 5. IEND 종료 최소 수정

[img_embed.py](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/img_embed.py:46>)의 IEND 분기를 최소한 다음처럼 바꿔야 합니다.

```python
if typ == b"IEND":
    if ln != 0:
        raise ValueError(
            f"정상 PNG가 아님: {label}: IEND 길이 {ln}"
        )
    if end != len(data):
        raise ValueError(
            f"정상 PNG가 아님: {label}: "
            f"IEND 뒤 잉여 {len(data) - end}바이트"
        )
    ended = True
    pos = end
    break
```

이것만으로는 빈/비정상 IDAT 문제는 해결되지 않습니다. 승인용 validator에는 추가로 다음을 구현해야 합니다.

- IHDR 중복 금지
- bit depth/color type 허용 조합
- compression/filter 값 0
- interlace 값 0 또는 1
- PLTE 순서·길이·필수 여부
- IDAT 연속성
- 알 수 없는 critical chunk 거부
- 모든 IDAT를 이어 `zlib.decompressobj()`로 복원
- zlib `eof`, `unused_data`, `unconsumed_tail` 확인
- 색상형식·인터레이스별 예상 scanline 길이와 실제 길이 비교
- 각 scanline filter byte가 0~4인지 확인
- 최대 픽셀·압축 해제 크기 상한

회귀시험에는 이번에 사용한 정상 7종과 비정상 12종을 그대로 고정해야 합니다.

## 6. 검증한 PNG 바이트를 그대로 복사

`img_embed.py`에 다음 함수를 추가합니다.

```python
def read_verified_png(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as ex:
        raise ValueError(
            f"정상 PNG가 아님: {path}: {ex}"
        ) from ex

    w, h = verified_png_bytes(data, path)
    return data, w, h
```

build에서:

```python
png_data, pw, ph = IE.read_verified_png(path)
...
USED_FIGS[bin_id] = (path, png_data)
```

`register_images`는 경로를 다시 읽지 말고 snapshot을 씁니다.

```python
def register_images(out_dir, images):
    """images: {bin_id: (source_path, verified_png_bytes)}."""
    os.makedirs(
        os.path.join(out_dir, "BinData"),
        exist_ok=True,
    )

    hpf_path = os.path.join(
        out_dir,
        "Contents",
        "content.hpf",
    )

    with open(hpf_path, encoding="utf-8") as f:
        hpf = f.read()

    for bid, source in images.items():
        path, data = source
        data = bytes(data)

        # 잘못된 호출자도 방어한다.
        verified_png_bytes(data, path)

        dst = os.path.join(
            out_dir,
            "BinData",
            f"{bid}.png",
        )
        with open(dst, "wb") as f:
            f.write(data)

        if f'id="{bid}"' not in hpf:
            item = (
                f'<opf:item id="{bid}" '
                f'href="BinData/{bid}.png" '
                f'media-type="image/png" '
                f'isEmbeded="1"/>'
            )
            hpf = hpf.replace(
                '<opf:item id="section0"',
                item + '<opf:item id="section0"',
            )

    with open(hpf_path, "w", encoding="utf-8") as f:
        f.write(hpf)
```

`figlib.save()`도 서명 확인 대신 다음을 사용해야 합니다.

```python
try:
    IE.verified_png_path(pp)
except ValueError as ex:
    raise RuntimeError(
        f"rsvg-convert 결과가 정상 PNG가 아님({name}): {ex}"
    ) from ex
```

## 7. stale BinData 정리

build에 다음 함수를 추가하십시오.

```python
def prune_unused_bindata(out_dir, section_xml):
    """최종 XML에서 참조하지 않는 manifest/BinData를 제거한다."""
    used_ids = set(
        re.findall(
            r'binaryItemIDRef="([^"]+)"',
            section_xml,
        )
    )

    hpf_path = os.path.join(
        out_dir,
        "Contents",
        "content.hpf",
    )

    for _event, (prefix, uri) in ET.iterparse(
        hpf_path,
        events=("start-ns",),
    ):
        if prefix != "xml":
            ET.register_namespace(prefix, uri)

    tree = ET.parse(hpf_path)
    root = tree.getroot()

    kept_hrefs = set()
    removed_manifest = []

    for parent in root.iter():
        for child in list(parent):
            if child.tag.rsplit("}", 1)[-1] != "item":
                continue

            href = child.attrib.get("href", "")
            if not href.startswith("BinData/"):
                continue

            bin_id = child.attrib.get("id", "")
            if not bin_id or bin_id not in used_ids:
                parent.remove(child)
                removed_manifest.append((bin_id, href))
            else:
                kept_hrefs.add(href)

    tree.write(
        hpf_path,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )

    bin_root = os.path.join(out_dir, "BinData")
    removed_files = []

    if os.path.isdir(bin_root):
        for root_dir, _dirs, files in os.walk(bin_root):
            for filename in files:
                full = os.path.join(root_dir, filename)
                rel = (
                    os.path.relpath(full, out_dir)
                    .replace(os.sep, "/")
                )

                if rel not in kept_hrefs:
                    os.remove(full)
                    removed_files.append(rel)

    return removed_manifest, removed_files
```

`register_images()` 이후에 호출합니다.

```python
if USED_FIGS:
    IE.register_images(OUT_DIR, USED_FIGS)
    print(
        f"   그림 {len(USED_FIGS)}개 삽입: "
        f"{sorted(USED_FIGS)}"
    )

removed_manifest, removed_files = (
    prune_unused_bindata(OUT_DIR, xml)
)

if removed_manifest or removed_files:
    print(
        "   미사용 BinData 정리: "
        f"manifest {removed_manifest}, "
        f"파일 {removed_files}"
    )
```

호출 순서는 반드시 새 그림 등록 뒤여야 합니다.

## 8. 5.6을 정규식이 아닌 XML·ZIP 전수 비교로 교체

교체 블록은 최소한 다음 항목을 모두 계산해야 합니다.

```python
print("\n### 5.6 BinData 정합")

try:
    import collections as _co56

    # ZIP 이름 중복을 set 변환 전에 확인한다.
    _infos56 = z.infolist()
    _names56 = [i.filename for i in _infos56]
    _counts56 = _co56.Counter(_names56)

    _bin_infos56 = [
        i for i in _infos56
        if i.filename.startswith("BinData/")
        and not i.filename.endswith("/")
    ]

    _dup_zip56 = sorted(
        name
        for name, count in _counts56.items()
        if name.startswith("BinData/")
        and count > 1
    )

    # manifest는 namespace prefix와 속성 순서에 독립적으로 파싱한다.
    _hpf_root56 = ET.fromstring(
        z.read("Contents/content.hpf")
    )

    _rows56 = []

    for _elem56 in _hpf_root56.iter():
        if _elem56.tag.rsplit("}", 1)[-1] != "item":
            continue

        _href56 = _elem56.attrib.get("href", "")
        if not _href56.startswith("BinData/"):
            continue

        _rows56.append((
            _elem56.attrib.get("id", ""),
            _href56,
            _elem56.attrib.get("media-type", ""),
            _elem56.attrib.get("isEmbeded", ""),
        ))

    _ids56 = [r[0] for r in _rows56]
    _hrefs56 = [r[1] for r in _rows56]

    _id_counts56 = _co56.Counter(
        value for value in _ids56 if value
    )
    _href_counts56 = _co56.Counter(_hrefs56)

    _dup_ids56 = sorted(
        value
        for value, count in _id_counts56.items()
        if count > 1
    )
    _dup_hrefs56 = sorted(
        value
        for value, count in _href_counts56.items()
        if count > 1
    )

    _bad_meta56 = [
        row
        for row in _rows56
        if (
            not row[0]
            or row[2] != "image/png"
            or row[3] != "1"
        )
    ]

    # 모든 section에서 실제 참조를 합친다.
    _section_names56 = sorted(
        name
        for name in _names56
        if re.fullmatch(
            r"Contents/section\d+\.xml",
            name,
        )
    )

    _used56 = set()
    _empty_refs56 = []

    for _section56 in _section_names56:
        _root56 = ET.fromstring(z.read(_section56))

        for _elem56 in _root56.iter():
            for _attr56, _value56 in _elem56.attrib.items():
                if (
                    _attr56.rsplit("}", 1)[-1]
                    != "binaryItemIDRef"
                ):
                    continue

                if _value56:
                    _used56.add(_value56)
                else:
                    _empty_refs56.append(_section56)

    _manifest_ids56 = {
        value for value in _ids56 if value
    }
    _manifest_hrefs56 = set(_hrefs56)
    _zip_bin56 = {
        info.filename for info in _bin_infos56
    }

    _orphan56 = sorted(
        (row[0], row[1])
        for row in _rows56
        if row[0] and row[0] not in _used56
    )
    _missing56 = sorted(
        _used56 - _manifest_ids56
    )
    _zip_missing56 = sorted(
        _manifest_hrefs56 - _zip_bin56
    )
    _zip_only56 = sorted(
        _zip_bin56 - _manifest_hrefs56
    )

    # 이름이 중복돼도 각 ZipInfo를 따로 읽는다.
    _bad_payload56 = []

    for _index56, _info56 in enumerate(
        _bin_infos56,
        1,
    ):
        try:
            IE.verified_png_bytes(
                z.read(_info56),
                f"{_info56.filename}#{_index56}",
            )
        except ValueError as _ex56:
            _bad_payload56.append(
                f"{_info56.filename}#{_index56}: "
                f"{_ex56}"
            )

    _issues56 = [
        ("BinData ZIP 엔트리명 중복", _dup_zip56),
        ("매니페스트 id 중복", _dup_ids56),
        ("매니페스트 href 중복", _dup_hrefs56),
        ("매니페스트 속성 이상", _bad_meta56),
        ("빈 binaryItemIDRef", _empty_refs56),
        ("고아 BinData", _orphan56),
        ("참조되나 매니페스트에 없음", _missing56),
        ("매니페스트에 있으나 ZIP에 없음", _zip_missing56),
        ("ZIP에만 있고 매니페스트에 없음", _zip_only56),
        ("정상 PNG가 아닌 BinData", _bad_payload56),
    ]

    _issues56 = [
        (label, value)
        for label, value in _issues56
        if value
    ]

    for _label56, _value56 in _issues56:
        errs += 1
        print(f"  [ERR] {_label56}: {_value56}")

    if not _issues56:
        print(
            "  고아 0건 / 참조 누락 0건 / ZIP 전용 0건 "
            f"(등록 {len(_rows56)}개, "
            f"참조 {len(_used56)}개, "
            f"ZIP BinData {len(_bin_infos56)}개)"
        )

except KeyError:
    errs += 1
    print(
        "  [ERR] Contents/content.hpf를 찾지 못함"
    )
except (ET.ParseError, UnicodeDecodeError) as _ex56:
    errs += 1
    print(
        "  [ERR] BinData 정합 검사 실패: "
        f"{_ex56}"
    )
```

현재 도구 계약이 PNG 전용이므로 모든 BinData를 PNG로 검증하는 형태입니다. 향후 BMP 등 다른 형식을 지원하려면 media type별 validator를 분기해야 합니다.

## 9. 원자적 출력과 동일 파일 잠금

`import fcntl`을 추가하고 기존 출력부를 다음으로 교체하십시오.

```python
out_path = os.path.abspath(OUT_PATH)
out_parent = os.path.dirname(out_path)
out_base = os.path.basename(out_path)

# lock 파일은 unlink하지 않고 고정 inode로 남긴다.
lock_path = os.path.join(
    out_parent,
    f".{out_base}.lock",
)

with open(lock_path, "a+b") as lock_fp:
    try:
        fcntl.flock(
            lock_fp.fileno(),
            fcntl.LOCK_EX | fcntl.LOCK_NB,
        )
    except BlockingIOError:
        raise SystemExit(
            f"동일 산출 파일을 다른 빌드가 사용 중: "
            f"{out_path}"
        )

    fd, staged_path = tempfile.mkstemp(
        prefix=f".{out_base}.",
        suffix=".tmp",
        dir=out_parent,
    )
    os.close(fd)

    try:
        with zipfile.ZipFile(staged_path, "w") as zf:
            zf.write(
                os.path.join(OUT_DIR, "mimetype"),
                "mimetype",
                compress_type=zipfile.ZIP_STORED,
            )

            for root, dirs, files in os.walk(OUT_DIR):
                dirs.sort()

                for filename in sorted(files):
                    full = os.path.join(root, filename)
                    rel = os.path.relpath(full, OUT_DIR)

                    if rel == "mimetype":
                        continue

                    zf.write(
                        full,
                        rel,
                        compress_type=zipfile.ZIP_DEFLATED,
                    )

        # 완성된 ZIP만 최종 경로에 원자 공개한다.
        os.replace(staged_path, out_path)

    finally:
        try:
            os.remove(staged_path)
        except FileNotFoundError:
            pass
```

잠금 없이 staged ZIP과 `os.replace()`만 사용하면 손상 ZIP은 막지만, 두 정상 빌드 중 마지막 것이 조용히 이기는 문제는 남습니다. 따라서 둘 다 필요합니다.

---

# 수정 후 반드시 통과해야 할 회귀 기준

릴리스 승인 조건은 최소한 다음이어야 합니다.

1. 제공 JSON/PNG로 실제 디스크 build가 0.
2. 바로 이어진 final check가 0이고 마지막 줄이 `FINAL-PASS`.
3. 최종 HWPX에는 `fig1`, `fig5`, `fig6` 세 BinData만 있고 `image1`, `image2`가 없음.
4. 요청된 비정상 PNG 5종 중 다섯 모두 build와 check에서 거부.
5. 빈 IDAT, bad zlib, 중복 IHDR, nonzero IEND, invalid interlace, unknown critical, 비연속 IDAT도 거부.
6. 동봉 PNG, Adam7, PLTE, tEXt, 큰 이미지는 통과.
7. missing figure matrix:

   - build final → 1
   - build draft → 산출 성공
   - check final → 1
   - check draft → 2, `DRAFT-ONLY`

8. clean draft도 정책상 2를 내고 `FINAL-PASS`를 절대 출력하지 않음.
9. draft waiver와 다른 오류가 함께 있으면 1, `FAIL`.
10. 문장 시작·중간의 모든 미매핑 `[그림 N]`을 final에서 거부.
11. manifest-only, reference-only, missing ZIP, ZIP-only, duplicate ID/href/name, bad payload를 모두 거부.
12. 실제 파일시스템에서 100회 병렬 시험:

   - 서로 다른 출력명은 둘 다 성공
   - 같은 출력명은 정확히 하나만 성공하고 다른 하나는 “사용 중”으로 실패
   - final 파일은 성공한 프로세스의 JSON과 정확히 일치
   - `unzip -t`와 check 모두 통과

13. 사용자 `out2/sentinel`이 모든 성공·실패 시험 뒤 그대로 남음.
14. 일반 예외 및 SIGTERM 뒤 `.<stem>.out2-*`가 남지 않음.
15. SIGKILL 잔재를 위한 다음 실행 시 노후 임시폴더 청소 정책이 별도로 있음.

## 최종 업무 판정

**현재 상태: 실제 업무 사용 불가.**

초안 문서를 사람이 수동 검토하는 비권위적 용도로도 build/check draft 정책이 서로 달라 불편하며, 최종 제출·배포·승인 게이트로는 사용하면 안 됩니다.

특히 정상 입력으로 만든 문서가 현재 checker에서 green이 아니고, 반대로 일부 실제 손상 입력은 green이 되는 상황입니다. 이는 검증 도구에서 가장 위험한 조합입니다.

최소 승인 전제는 다음 세 가지입니다.

- PNG validator와 snapshot 복사 수정
- builder의 BinData 정리 및 checker 5.6 전수 비교
- 최종 출력 잠금·staged ZIP·원자적 교체

그 뒤 제공된 정상 입력이 실제 디스크 `build 0 → check 0 / FINAL-PASS`가 되는지, 그리고 위 회귀 행렬과 실제 동시성 시험까지 다시 확인해야 합니다.
