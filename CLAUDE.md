# 중2-유리수-순환소수-서논술형 Wiki Schema

## Directory Layout
- raw/              -- immutable source drops. Never edit files here.
- raw/articles/     -- text source documents (articles, papers, transcripts).
- raw/attachments/  -- images and binary attachments.
- wiki/             -- LLM-owned pages. You have full write access here.
- wiki/index.md     -- catalog. Read this FIRST before opening any other page.
- wiki/queries/     -- filed query answers. Promote to wiki/ when durable.
- outputs/reports/  -- dated lint reports and other artifacts.
- hwpx/             -- 완성된 HWPX 산출물.
- log.md            -- append-only operation log. Never edit existing entries.

## Entity Types and Templates

### concept.md
---
date: YYYY-MM-DD
tags: [domain]
type: concept
status: active
---
# Concept Name
<one-paragraph summary>

## Details
...

## See Also
- [[related-concept]]

## Counter-Arguments and Gaps
...

### person.md
---
date: YYYY-MM-DD
tags: [domain, person]
type: person
status: active
---
# Person Name
Role / affiliation.

## Key Contributions
...

## See Also
- [[related-concept]]

### source-summary.md
---
date: YYYY-MM-DD
tags: [domain]
type: source-summary
source-url: https://...
---
# Source Title
One-paragraph summary.

## Key Points
...

## Entities Mentioned
- [[person-or-concept]]

### query-output.md
---
date: YYYY-MM-DD
tags: [domain]
type: query-output
question: "<original question>"
status: filed
---
# <Question as title>
<synthesized answer>

## Sources
- [[page-1]]
- [[page-2]]

## Naming Conventions
- All filenames: lowercase-kebab-case.md (한글 파일명은 하이픈 연결)
- Wikilinks: [[filename-without-extension]]
- Never use standard markdown links for internal links

## Log Format
Append to log.md after every operation. Format:
  ## [YYYY-MM-DD] <operation> | <title>
  <one-line description>

Operations: ingest | compile | query | lint | promote | remove

## Index Format
wiki/index.md is a human- and LLM-readable catalog. Format:
  ## Domain Name
  - [[page-name]] -- one-line description (YYYY-MM-DD)

## Cross-Reference Rules
- Every page must link to at least one other page when content warrants it
- When creating or updating a concept page, scan index.md for related entities and add [[wikilinks]]
- Flag contradictions inline: > [!WARNING] Contradiction with [[other-page]]

## Ingest Rules
1. Acquire the source (URL or file)
2. Classify the source type
3. Save to raw/articles/ with frontmatter (compiled: false)
4. Append to log.md
5. Commit
Ingest does NOT create wiki pages. Use compile for that.

## Compile Rules
1. Identify uncompiled raw sources (no matching source-summary in wiki/)
2. For each source: write source-summary, extract entities, create/update pages
3. Backlink audit: grep existing pages for mentions of new titles
4. Update wiki/index.md
5. Append to log.md
6. Commit

## 이 위키의 목적
전북 2026 서·논술형 평가 심화과정 직무연수 사전과제 — 중학교 2학년
[유리수와 순환소수] 단원의 서·논술형 평가 문항 개발. 핵심 평가 목표는
"유리수는 유한소수 또는 순환소수로만 표현되고, 모든 유한소수와 순환소수는
유리수"라는 수 체계와 소수 표현 사이의 동치 관계 인식.
