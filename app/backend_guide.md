## 1. 프로젝트 인증 흐름 (Google OAuth2)

구글 인증을 통해 유저를 식별하며, 백엔드에서 자체 발급한 **JWT(JSON Web Token)**를 사용해 권한을 관리합니다.

### 🔄 인증 시퀀스

1. **구글 로그인**: 프론트엔드에서 구글 SDK를 사용하여 유저 인증 후 `ID Token`을 획득합니다.
2. **백엔드 검증**: 획득한 `ID Token`을 백엔드의 `/auth/google` 엔드포인트로 전송합니다.
3. **자체 토큰 발급**: 백엔드는 구글 토큰을 검증한 뒤, 우리 서버 전용 (JWT자체발급)한 `access_token`을 응답합니다.
4. **권한 인가**: 이후 모든 API 호출 시 헤더에 `Authorization: Bearer <access_token>`을 포함합니다.

---

## 2. 인증 관련 API 명세

### [POST] 구글 로그인 연동

- **URL**: `/auth/google`
- **Request Body**:
  ```json
  {
    "token": "string (구글에서 발급받은 ID Token)"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "string (우리 서버 전용 JWT)",
    "token_type": "bearer",
    "user": {
      "email": "user@gmail.com",
      "name": "이민혁"
    }
  }
  ```

---

## 3. 토큰 유효성 및 세션 만료 가이드 (중요)

### ⏱️ 토큰 생명 주기

- **유효 기간**: 발급 시점으로부터 **24시간**.
- **알고리즘**: HS256.

### 🛠️ 프론트엔드 필수 처리 사항

1. **토큰 저장**: 응답받은 `access_token`을 `localStorage` 또는 보안 쿠키에 저장하세요.
2. **자동 로그아웃 로직**:
   - `jwt-decode` 라이브러리를 사용하여 토큰의 `exp`(만료시간)를 체크하세요.
   - 현재 시간 기준 `exp`가 지났다면 프론트엔드에서 즉시 `localStorage.removeItem()`을 실행하고 UI를 비로그인 상태로 전환해야 합니다.
3. **401 Unauthorized 대응**:
   - 만료된 토큰으로 API 호출 시 서버는 `401` 에러 또는 `None`을 반환할 수 있습니다.
   - Axios Interceptor 등을 활용해 401 에러 발생 시 로그인 페이지로 리다이렉트하는 로직을 권장합니다.

---

## 4. 히스토리(History) 관리 기능

로그인한 유저는 자신이 분석한 계약서 리포트를 다시 볼 수 있습니다.

### 📂 주요 API 목록

| 기능                 | 엔드포인트             | 설명                              |
| :------------------- | :--------------------- | :-------------------------------- |
| **최근 목록 조회**   | `GET /history/recent`  | 사이드바용 최근 5개 요약 목록     |
| **상세 데이터 조회** | `GET /history/{id}`    | 특정 분석 기록의 전체 JSON 데이터 |
| **기록 삭제**        | `DELETE /history/{id}` | 히스토리 삭제                     |

---

## 5. UI/UX 구현 가이드

### 🚩 누락 조항 리포트 (Missing Clause)

분석 결과 데이터 중 `missing_clause_report` 필드를 확인해 주세요.

- **데이터가 있는 경우**: "이 계약서에서 누락된 위험 독소 조항이 있습니다"라는 경고 배너와 함께 해당 내용을 리포트 최상단에 노출해 주세요.
- **`null`인 경우**: 해당 섹션을 아예 렌더링하지 마세요.

### 🕒 타임존 처리

백엔드의 모든 시간 데이터는 **UTC** 기준입니다. 프론트엔드에서 `Intl.DateTimeFormat` 등을 이용해 사용자 로컬 시간(KST)으로 변환하여 표기해 주세요.

---

### 🔑 환경 변수 (.env)

프론트엔드 로컬 환경에 아래 설정이 필요합니다.
REACT_APP_GOOGLE_CLIENT_ID -> 해당 ID로 구글 토큰 받아옴

```env
REACT_APP_GOOGLE_CLIENT_ID=551271866202-lo73lgp94pcag3hiafnq1glolgcqbv8m.apps.googleusercontent.com
REACT_APP_API_URL=http://localhost:8000
```
