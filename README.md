# gollagolla-data

골라골라(https://gollagolla.kr) 주간 코스트코 할인 데이터.

- `deals.json` : 이번 주 할인 상품(상품코드·가격·기간·인기순위·쿠팡 파트너스 링크)
- 매주 월요일 갱신. 사이트가 이 파일을 직접 불러와요.

## 가격 비교 (1차)
- 관리자 입력: https://gollagolla.kr/admin/ (검색 노출 안 됨)
- 저장 파일: `compare.json` — 상품코드(Item)로 묶어서 주간 `deals.json`을 다시 올려도 지워지지 않음
- 계산·표시: `compare.js` (사이트·관리자 공용). 추천 순위(`rk`)에는 반영하지 않음
