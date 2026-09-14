# 프론트 BACKEND_URL 주입 방식 (배포용 정리)

## 현재 동작
- frontend/index.html 내부 스크립트:
  ```
  const BACKEND_URL = (window.__BACKEND_URL__ || "").replace(/\/+$/, "") || "http://localhost:8000";
  ```
- window.__BACKEND_URL__ 가 있으면 그 값을 사용
- 없으면 http://localhost:8000 를 기본값으로 사용

## 배포 시 필요한 변경
- 백엔드가 HTTPS 도메인으로 배포되면, 프론트는 그 도메인을 BACKEND_URL로 받아야 함
- 현재는 정적 호스팅(Vercel) + 순수 JS라서, 빌드 시점에 환경변수를 넣는 구조가 아님
- 따라서 배포 시에는 아래 방식 중 하나로 BACKEND_URL을 주입

### 방식 A: 인라인 환경변수 삽입 (권장, 정적 호스팅과 잘 맞음)
- 프론트 배포 파이프라인에서 index.html 을 배포하기 직전, 플레이스홀더를 백엔드 URL로 치환
  - 예: `window.__BACKEND_URL__ = "__BACKEND_URL__"` 형태를 실제 도메인으로 치환
- 또는 빌드 스크립트에서 환경변수 BACKEND_URL을 받아 인라인 스크립트의 상수를 직접 교체
- 결과는 외부 스크립트·키 없이 순수 JS로 동작

### 방식 B: 데이터 속성/메타 태그로 백엔드 URL 전달
- index.html 에 <meta> 또는 data 속성으로 백엔드 URL를 넣고, 스크립트가 그걸 읽게 변경
- 예: <meta name="backend-url" content="https://backend.example.com">
- 배포 파이프라인에서 content 값만 채움

### 방식 C: 쿼리/해시로 전달 (간편하지만 덜 깔끔함)
- 프론트 URL 에 ?backend=https://... 형태로 넘기고 JS가 읽음
- 편의용으로는 쓸 수 있으나, 배포 방식에 따라 권장도는 낮음

## 현재 코드 유지 시 권장
- 방식 A 또는 B 중 배포 도구에 맞는 쪽으로 백엔드 URL를 주입
- 로컬 개발 환경에서는 값이 없어도 http://localhost:8000 로 동작하도록 기본값을 유지
- 배포 환경에서도 ALLOWED_ORIGINS에 프론트 도메인이 포함돼 있어야 CORS가 허용됨

## 관련 확인 항목
- 백엔드 환경변수: BACKEND_URL, FRONTEND_URL, ALLOWED_ORIGINS
- 프론트 배포 후 BACKEND_URL이 백엔드 HTTPS 도메인을 가리키는지 확인
- 백엔드 CORS가 프론트 도메인을 허용하는지 확인
