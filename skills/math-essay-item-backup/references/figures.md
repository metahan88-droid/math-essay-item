문항 자료의 그림을 만드는 방법. 어떤 그림을 직접 작도하고 어떤 그림을 gpt-image-2에 맡길지 가르는 규칙, 두 경로의 실행법, HWPX에 넣는 절차.

## 1. 판단 규칙 — 먼저 이것부터 정한다

**그림 안의 글자가 문항 내용인가?**

| 답 | 경로 | 이유 |
|---|---|---|
| 그렇다 | `tools/figlib.py`로 **직접 작도** | AI 이미지 모델은 한글을 뭉갠다. 가격·치수·대사가 틀리면 문항이 무너진다 |
| 아니다 | **gpt-image-2** | 분위기·맥락 삽화는 사람이 그리는 것보다 낫고 빠르다 |

이번 개발에서 실제로 겪은 것 — 처음에는 가격표·대화방·쪽지를 AI로 그리려 했으나 한글이 깨져 쓸 수 없었다. 좌표로 직접 배치하니 정확하고 인쇄 품질도 나았다. 그래서 `tools/figlib.py` 머리에 이렇게 적어 두었다.

> 글자가 곧 문항 내용인 도해(가격표·대화방·쪽지·실측 도해·크기 비교)는 AI 이미지 모델이 한글을 뭉개므로 여기서 좌표로 직접 그린다. 글자가 없는 분위기 삽화만 gpt-image-2에 맡긴다.

### 경계 사례

- **가격표·안내판·쪽지·대화방·실측 도해·모눈 탐구** → 직접 작도. 예외 없다.
- **크기 비교도**(원·상자를 실제 비율로 나란히) → 직접 작도. 비율이 정확해야 하고 치수 글자가 붙는다.
- **표지 삽화, 상황을 떠올리게 하는 배경, 인물 없는 소품 그림** → gpt-image-2.
- **글자가 조금 들어가는 삽화** → 글자를 빼고 생성한 뒤, 필요하면 그 위에 SVG로 글자를 얹는다. 모델에게 한글을 그리게 하지 않는다.

## 2. 직접 작도 — `tools/figlib.py`

여섯 가지 도해를 함수 하나로 만든다. 모든 함수가 SVG를 쓰고 2배 해상도 PNG로 변환한 뒤 `(svg경로, png경로)`를 반환한다.

```python
import sys
sys.path.insert(0, "<스킬>/tools")
import figlib as F
F.OUT = "<작업폴더>/figs"        # 저장 위치. 없으면 자동 생성
```

**출력 폴더는 스킬 폴더가 아니다.** `figlib.OUT`의 기본값은 `FIGLIB_OUT` 환경변수이고, 없으면 **현재 작업 디렉터리 기준 `./figs`**다(`OUT = os.environ.get("FIGLIB_OUT") or os.path.join(os.getcwd(), "figs")`). 예전처럼 스킬 폴더 안에 산출물이 쌓이지 않는다. 셋 중 하나로 정하면 된다.

| 방법 | 쓸 때 |
|---|---|
| `F.OUT = "<작업폴더>/figs"` | 파이썬으로 부를 때. 절대경로로 못 박는 것이 가장 안전하다 |
| `FIGLIB_OUT=<작업폴더>/figs` | 셸에서 스크립트를 돌릴 때 |
| 아무것도 안 함 | 작업 폴더에서 실행할 때. `./figs`에 생긴다 |

빌더는 그림 상대경로를 **슬롯 JSON이 있는 폴더 기준**으로 여니, `figs/`는 content.json 옆에 두는 것이 맞다.

### 함수

```python
F.menu_board(name, title, headers, rows, note=None)
# 가격표·안내판. rows 안의 "?"는 자동으로 붉게 나온다(학생이 채울 자리).
F.menu_board("fig_menu", "○○피자 가격 안내",
             ["크기","지름","두께","한 판 가격","페퍼로니"],
             [["미디엄","24 cm","2 cm","16,000원","16개"],
              ["라지","30 cm","2.5 cm","26,000원","?"]],
             note="★ 이번 주 행사 : 미디엄 2판 묶음 30,000원")

F.chat(name, title, messages, footnote=None)
# 오개념을 심는 단체 대화방. 밑줄 친 줄이 ㉠·㉡ 표시 대상이 된다.
F.chat("fig_chat", "수학동아리 단체 대화방 (어젯밤)",
       [("민재", [("행사 봤어? 미디엄 2판이 30,000원이야.", 0)]),
        ("서연", [("자이언트는 지름이 1.5배니까 양도 1.5배야.", 1)])],
       footnote="※ ㉠은 서연의 발언에서 밑줄 친 부분 전체를 가리킨다.")

F.memo(name, title, lines, signer=None)
# 의뢰인의 쪽지. lines 원소는 문자열이거나 (문장, "bold", 색).
F.memo("fig_memo", "✉ 가게 사장님의 쪽지 (오늘 아침)",
       ["여쭙고 싶은 것이 두 가지 있습니다.",
        ("② 두께는 2 cm로 만들어야 합니다. 지름은 몇 cm일까요?", "bold", F.ACCENT)],
       signer="— ○○피자 사장")

F.circles_row(name, title, items, scale=3.0)
# 지름이 다른 원을 실제 비율로. items = [(라벨, 지름, 아래설명), ...]

F.boxes_row(name, title, items, scale=3.4)
# 아이소메트릭 직육면체 실측 도해. items = [(라벨, 가로, 세로, 높이, 비고), ...]
# 학생이 비를 직접 재는 자료이므로 비율을 정확히 유지한다.

F.grid_shape(name, title, cells=14, cell=22, shapes=(), caption=None)
# 모눈 위 도형. shapes = [("circle", cx, cy, r, 색), ("rect", x, y, w, h, 색)] — 단위는 칸.
```

### 데모 돌려 보기

새 도해를 만들기 전에 여섯 종의 데모를 한 번 뽑아 보고 어느 함수가 맞는지 고른다. **작업 폴더에서 스킬의 `figlib.py`를 절대경로로 부른다.**

```bash
cd "$WORK" && python3 "<스킬>/tools/figlib.py"
# 또는 출력 위치를 못 박아서
FIGLIB_OUT="$WORK/figs_demo" python3 "<스킬>/tools/figlib.py"
```

**스킬 폴더의 도구를 그대로 실행해도 스킬 폴더는 오염되지 않는다. 산출물은 작업 폴더에 생긴다** — 데모의 기본 출력은 `FIGLIB_OUT`이 없으면 `os.getcwd()/figs_demo`이므로, 현재 작업 디렉터리가 작업 폴더이기만 하면 스킬 폴더에는 아무것도 쓰이지 않는다(예전에는 `tools/figs_demo/`에 쌓여 스킬이 더러워졌다). 다만 `cd`로 스킬 폴더에 들어가서 돌리면 그 폴더가 곧 cwd가 되니 그러지 마라. 확실히 하려면 `FIGLIB_OUT`을 준다.

### 작도 원칙

- **정답을 그림에 흘리지 말 것.** 학생이 구해야 할 값은 `"?"`로 둔다. 비·배수·정답 수치를 도해에 적으면 문항이 죽는다.
- **비율을 지킬 것.** 크기 비교도와 실측 도해는 실제 비율로 그린다. 학생이 눈대중으로도 확인할 수 있어야 한다.
- **인쇄를 전제로.** 채도가 낮은 색만 쓴다(`figlib`의 기본 팔레트). 흑백 출력에서도 구분되도록 굵기·점선으로 층을 나눈다.
- **rsvg-convert가 필요하다.** 없으면 SVG만 생성되고 경고가 뜬다. `brew install librsvg`.

## 3. gpt-image-2 — 분위기 삽화

`gpt-image-2` 스킬의 브리지를 그대로 호출한다. 인증은 Codex CLI OAuth를 쓰므로 API 키가 필요 없다.

```bash
python3 "$HOME/.claude/skills/gpt-image-2/scripts/gptimage2_codex.py" \
  --prompt "<완성된 영어 프롬프트>" \
  --aspect landscape \
  --quality high \
  --output "<작업폴더>/figs/fig_scene.png"
```

인증 확인은 `--check-auth`. 실패하면 사용자에게 `codex login`을 안내하고, API 키를 요구하지 않는다.

### 프롬프트 규칙

- **한글을 넣지 않는다.** 넣으면 뭉개진다. 글자가 필요하면 SVG로 얹는다.
- 프롬프트에 `no text, no letters, no numbers, no signage`를 명시해 모델이 임의로 글자를 넣지 못하게 한다.
- 교실에서 쓸 자료이므로 `flat illustration, muted colors, clean white background, printable`처럼 인쇄 적합성을 지정한다.
- 사람 얼굴은 피한다. 특정 인물처럼 보이면 곤란하고, 학생이 소재보다 인물에 주의를 뺏긴다.
- 정확한 수량·비율을 그림에 요구하지 않는다. 모델은 "정확히 세 개"를 지키지 못한다. 수량과 비율이 중요하면 직접 작도로 간다.

좋은 프롬프트 예:

```
A flat vector illustration of a school club room table with pizza boxes of three
different sizes stacked, seen from a slight top-down angle. Muted warm colors,
clean white background, printable textbook style, no text, no letters, no numbers,
no signage, no people.
```

### 결과 처리

1. 파일이 존재하고 비어 있지 않은 PNG인지 확인한다.
2. **Read로 열어 눈으로 확인한다.** 글자가 섞여 들어갔거나 수량이 어긋났으면 다시 생성하거나 직접 작도로 바꾼다.
3. 보고할 때 절대 경로와 실제 크기를 함께 적는다.

## 4. HWPX에 넣기

빌더는 자료 본문의 `[그림 N]` 자리표시를 그림으로 바꾼다. 슬롯 JSON에 `_figs`로 매핑을 준다.

```json
{
  "item_intro": ["〔자료 1〕 ○○피자 가격표와 안내",
                 "[그림 1] 세 가지 크기의 피자 (실제 지름 비율)",
                 "[그림 2] ○○피자 가격 안내"],
  "_figs": {
    "[그림 1]": ["fig1", "figs/fig1_sizes.png"],
    "[그림 2]": ["fig2", "figs/fig2_menu.png"]
  }
}
```

- 값은 `[BinData 식별자, 슬롯 JSON이 있는 폴더 기준 상대경로]`다. 식별자는 문서 안에서 유일해야 한다.
- 그림 줄의 텍스트는 **캡션으로 함께 남는다.** 그림 아래 설명이 되도록 문장을 쓴다.
- 빌드 뒤 고아 BinData 제거를 반드시 한다(`references/hwpx-build.md`). 제거를 건너뛰면 `check_tpl2.py` **§5.6 BinData 정합**이 고아를 잡아 FAIL을 내므로 조판이 통과되지 않는다. 검증기가 자동으로 막아 준다는 뜻이지 제거 절차가 없어졌다는 뜻이 아니다 — 제거는 여전히 사람이 돌린다.

### 최종 모드와 초안 모드

`build_tpl2.py`는 **최종 모드가 기본**이다. 그림이 빠진 채 최종본이 나가는 것을 막는다.

| 모드 | 명령 | `_figs`가 가리키는 PNG가 없을 때 |
|---|---|---|
| 최종(기본) | `python3 build_tpl2.py out.hwpx content.json` | **`FileNotFoundError`로 즉시 중단** |
| 초안 | `python3 build_tpl2.py out.hwpx content.json --draft` | 그 줄을 자리표시 텍스트로 남기고 계속 |

중단 메시지는 없는 파일과 기준 폴더를 함께 알려 준다.

```
FileNotFoundError: 최종 조판에 필요한 그림 파일이 없음: figs/fig6_owner_memo.png
(기준 폴더 /…/work). 그림을 만들어 두거나, 초안이면 --draft를 붙여라.
```

그러므로 **그림을 만들기 전에 조판 결과를 미리 보고 싶으면 `--draft`를 쓴다.** 레이아웃·분량·줄바꿈을 먼저 확인하고 그림은 나중에 붙이는 경로다. 제출본은 반드시 플래그 없는 최종 모드로 다시 빌드한다. 플래그는 두 위치 인자 **뒤에만** 온다.

## 5. 순서

1. 문항 초안이 확정된 뒤에 그림을 만든다. 초안이 바뀌면 수치가 바뀌고 도해도 다시 그려야 한다.
2. 자료마다 **글자가 정보인지** 판단해 경로를 고른다.
3. 출력 폴더를 정한다 — `F.OUT` 또는 `FIGLIB_OUT`을 작업 폴더의 `figs/`로. 안 정하면 cwd 기준 `./figs`다.
4. 직접 작도는 `figlib`로, 분위기 삽화는 gpt-image-2로 만든다.
5. 생성한 그림을 **모두 Read로 열어 확인한다.** 특히 AI 생성물은 반드시 본다.
6. `_figs` 매핑을 슬롯 JSON에 넣고 **최종 모드**로 빌드한다.
7. 완성 HWPX에서 그림이 실제로 들어갔는지 확인한다(`binaryItemIDRef` 개수).

그림보다 조판을 먼저 보고 싶으면 순서를 뒤집어도 된다 — 1 → `_figs`를 적은 채 `--draft`로 초안 조판 → 3~5로 그림 생성 → 6에서 최종 모드 재빌드. 최종 모드가 그림 누락을 막아 주므로 초안을 최종본으로 착각할 위험이 없다.
