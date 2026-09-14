# meeting-personal-todo 데모 진행 체크리스트

## 결정된 전원 상태 (이 세션 시작 시점)
- LLM: Solar Pro 4 mock 유지 (실호출 정보 확보 시 교체)
- 백엔드: Render/Railway 텍스트 전용 (VM 미확보 → STT/mp3 경로 제외)
- Notion·Google OAuth: mock (나중에 클라이언트 ID/Secret 입력)
- 쿠키 사용 금지, UUID Bearer 세션만 사용

---

## Day 1: LLM 추출 + 스키마 검증 + 날짜 변환

### 완료
- [x] `backend/`, `frontend/` 파일 구조 생성
- [x] `backend/.venv` 생성 + `requirements.txt` 의존성 설치
- [x] `python tests/test_extract.py` 통과 (7개 전부)
- [x] uvicorn 로컬 기동
- [x] `/api/session` → 세션 UUID 발급 확인
- [x] `/api/extract` → 샘플 기반 추출 확인
- [x] `/api/save` → Notion URL + Google Calendar URL mock 확인
- [x] OAuth mock 엔드포인트 4개 응답 확인
- [x] 프론트 저장 흐름 구조 확인

### 샘플 3개 기대 결과 (mock 기준)
- sample_1: 이름 직접 언급 → high
- sample_2: 부서만 언급 → mid
- sample_3: 업무 키워드만 겹침 → low

### 특이사항
- 처음에 `solar.py`에서 `Highlight` 임포트 누락으로 샘플 3개 실패 → 이후 수정
- `/api/extract`, `/api/save`가 초기에 422 오류 → `Request = Depends()`와 Pydantic body 충돌로 추정, `get_session_id` 의존성으로 분리 후 해결
- `/api/save`에서 `ExtractRequest` 미import로 NameError → 상단 import 추가로 해결

---

## Day 2: OAuth + 저장 + 링크 반환 + UUID 세션

### 완료 (mock 기준)
- [x] `/api/auth/notion/login` 응답 확인
- [x] `/api/auth/notion/callback` 응답 확인 (code/state 수신 구조)
- [x] `/api/auth/google/login` 응답 확인
- [x] `/api/auth/google/callback` 응답 확인 (code/state 수신 구조)
- [x] `/api/save` 응답에 notion_url + google_calendar_url 포함 확인
- [x] 프론트에서 추출 후 저장 버튼 활성화 → 저장 링크 표시 구조 확인

### 아직 남은 부분 (데모 이후)
- [ ] Notion OAuth 실제 클라이언트 ID/Secret 입력 → 실연동
- [ ] Google OAuth 실제 클라이언트 ID/Secret 입력 → 실연동 (테스트 사용자)
- [ ] `/api/save` 응답에 노션 페이지 URL + 캘린더 이벤트 URL이 실제로 반환되는지 실연동 확인

---

## Day 3: 프론트 Vercel 배포 + 백엔드 Render/Railway 배포 + 시크릿 창 리허설

### 사전 확인
- [ ] 프론트: `frontend/index.html` + `vercel.json` 존재
- [ ] 백엔드: `backend/Dockerfile`, `backend/app/main.py`, `backend/requirements.txt` 존재
- [ ] 백엔드 환경변수 준비:
  - `BACKEND_URL`
  - `FRONTEND_URL`
  - `ALLOWED_ORIGINS`
  - `LLM_USE_MOCK=true` (실호출 전까지)
  - Notion/Google OAuth 값은 아직 비어 있어도 됨 (mock 모드)

### 프론트 Vercel 배포
- [ ] `vercel --prod` 배포
- [ ] 배포 후 도메인 확인
- [ ] 프론트에서 `BACKEND_URL`이 백엔드 도메인을 가리키도록 설정
  - 현재는 프론트 코드가 `window.__BACKEND_URL__` 또는 `http://localhost:8000` 기본 사용
  - 배포 시에는 인라인 스크립트에서 백엔드 URL 주입 방식 확인

### 백엔드 Render/Railway 배포
- [ ] Dockerfile 기반 배포
- [ ] HTTPS 도메인 확보
- [ ] 환경변수 주입:
  - `BACKEND_URL`
  - `FRONTEND_URL`
  - `ALLOWED_ORIGINS` (프론트 도메인 포함)
  - `LLM_USE_MOCK=true`
- [ ] CORS 설정이 프론트 도메인을 허용하는지 확인
- [ ] `/health`, `/api/session`, `/api/extract`, `/api/save` 외부 접근 확인

### 시크릿 창 리허설
- [ ] 첫 방문 → 세션 UUID 발급
- [ ] 텍스트 붙여넣기 → 추출 → 결과 표시
- [ ] 저장 버튼 동작 → notion_url/calendar_url 표시
- [ ] (mock 상태이므로 "저장 링크가 없습니다. (OAuth 미설정 상태)" 표시도 정상 동작으로 간주)

### 데모 이후 (VM 확보 시)
- [ ] mp3 업로드 → faster-whisper STT → 잡 큐 폴링 추가

---

## 실연동 전환 시 필요한 정보 (나중에 입력)

### Solar Pro 4 실호출
- API 키
- 엔드포인트
- 모델명
- (무료 한도/과금 정보는 스크린샷에 없어 확인 필요)

### Notion OAuth
- `NOTION_CLIENT_ID`
- `NOTION_CLIENT_SECRET`
- `NOTION_REDIRECT_URI`

### Google OAuth
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- 테스트 사용자 목록

### 백엔드 배포
- Render/Railway 중 선택한 플랫폼
- HTTPS 도메인
- 환경변수 값

---

## 현재 파일 구성 (이 세션에서 생성)
backend/
  requirements.txt
  .env.example
  .env
  Dockerfile
  app/
    __init__.py
    config.py
    deps.py
    schemas.py
    solar.py
    extract.py
    notion_service.py
    google_service.py
    main.py
  tests/
    test_extract.py
frontend/
  index.html
  vercel.json
  README.md
