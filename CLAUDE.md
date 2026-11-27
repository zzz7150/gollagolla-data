# 골라골라 (gollagolla.kr) — Claude Code 작업 안내

코스트코 주간 할인 전단 사이트. 사용자는 한국어·반말 섞인 편한 말투, 쉽고 짧게 설명 선호. 추정 수치는 "추정" 표시.

## 구조
- 호스팅: GitHub Pages (이 저장소 main 루트) + 도메인 gollagolla.kr (Cafe24 DNS: A 185.199.108.153, www CNAME zzz7150.github.io). `git push` = 배포.
- `index.html` 메인. `deals.json`을 같은 출처에서 불러와 렌더. TOP20은 빌드 때 미리 그려둠(SEO).
- `this-week/`, `ending/`, `c/{food,living,kitchen,health,fashion,digital}/`, `sitemap.xml` — `tools/gen_pages.py`가 생성(직접 고치지 말 것).
- `admin/` 관리자(noindex, robots Disallow): 방문자 현황 + 가격비교 입력(보류 중).
- `compare.js` / `compare.json` 가격비교 1차 구현. **보류 중**(사용자: 방문자 많아지면 다시 검토). compare.json은 비어 있음.
- 방문자 통계: GoatCounter (`gollagolla.goatcounter.com`). 쿠팡/네이버 버튼 클릭은 이벤트 `click/coupang`, `click/coupang/<상품코드>`.

## 매주 작업 (월요일 시트 받으면)
```
python3 tools/build.py data/sheets/sheet_YYYY-MM-DD.csv YYYY-MM-DD   # deals.json 생성(이전 쿠팡 링크 상품코드로 이어붙임)
python3 tools/coupang_links.py --max-calls 10                        # 링크 없는 새 상품만 딥링크 (키는 .env)
python3 tools/gen_pages.py                                           # 주제 페이지·TOP20·sitemap
git add -A && git commit -m "week YYYY-MM-DD" && git push
```
- 순위: 기본 점수 + 식품·생활용품 가산점(build.py `s_life`). 신호 데이터는 `tools/data/`.
- 날짜: deals.json은 ISO(YYYY-MM-DD)와 예전 MM-DD 둘 다 읽힘.
- 배포 후 https://gollagolla.kr 열어 확인(모바일 폭 포함).

## 꼭 지킬 것
- 쿠팡 파트너스 키는 절대 커밋·웹페이지에 넣지 말 것. 원본은 사용자 집 PC `golla` 폴더. 로컬에서 `.env`에 `COUPANG_ACCESS_KEY=`, `COUPANG_SECRET_KEY=` (gitignore됨).
- 쿠팡 API 호출 최소화: 1시간 10~20회 이하(30회+면 정지 위험 자료 있음, 추정). 캐시 `tools/data/link_cache.json` 활용.
- 비밀번호·토큰·결제 정보는 사용자가 직접 입력.
- 사용자가 발행할 글(블로그·인스타 등)엔 AI/Claude 작성 흔적 금지. 링크는 원문 URL 말고 짧은 글자에 하이퍼링크.
- 쿠팡 링크 근처엔 파트너스 대가성 문구 유지.

## 연결된 것들
- 네이버 블로그 3번 '골라골라'(ljhljh7150) 자동 발행 예약작업: 매일 10:00/17:00, 글 끝에 쿠팡 링크 1~3개 + 대가성 문구 + "이번 주 할인 품목 더 보기"(홈페이지 링크). Aside 프로필 '골라골라' 사용.
- 예약작업 문구 수정(gollagolla.kr 링크·상품코드 반영)은 집 PC(JY-20190909IAIS)에서 승인 대기 중.

## 남은 일
- [사용자] GoatCounter 가입(코드 `gollagolla`) → Settings에서 "Allow adding visitor counts on your website" 켜기
- [사용자] 네이버 서치어드바이저·구글 서치콘솔 등록 (sitemap: https://gollagolla.kr/sitemap.xml)
- [사용자] 네이버 블로그 이름 '다라온파파' → '골라골라', 인스타 계정 만들기(카드뉴스는 수동 게시부터)
- [나중] 애드센스, 가격비교 재개(그때 GitHub fine-grained 토큰 필요), 유튜브 영상픽(영상 생기면 노출)
