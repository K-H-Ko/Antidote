# Antidote — Frontend 정의서

> **근로계약서 독소조항 AI 분석 서비스**의 React 프론트엔드 코드베이스 정의 문서입니다.  
> 이 문서는 코드 구조, 네이밍 컨벤션, 페이지별 기능, 백엔드 API 연동 방식을 설명 합니다.

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [기술 스택 및 설치](#2-기술-스택-및-설치)
3. [폴더 구조](#3-폴더-구조)
4. [환경 변수](#4-환경-변수)
5. [라우팅 구조](#5-라우팅-구조)
6. [네이밍 컨벤션](#6-네이밍-컨벤션)
7. [전역 상태 관리 (AppContext)](#7-전역-상태-관리-appcontext)
8. [페이지별 기능 정의](#8-페이지별-기능-정의)
   - [MainLayout — 앱 셸](#81-mainlayout--앱-셸)
   - [HomeContent — 입력 페이지](#82-homecontent--입력-페이지)
   - [LoadingPage — 분석 진행 페이지](#83-loadingpage--분석-진행-페이지)
   - [ResultContent — 결과 리포트 페이지](#84-resultcontent--결과-리포트-페이지)
9. [백엔드 API 연동 가이드](#9-백엔드-api-연동-가이드)
10. [CSS 클래스 네이밍 시스템](#10-css-클래스-네이밍-시스템)
11. [위험도 레벨 시스템](#11-위험도-레벨-시스템)

---

## 1. 프로젝트 개요

**Antidote**는 근로계약서 텍스트 또는 파일을 입력받아 독소조항을 AI로 분석하고, 위험도 점수와 수정 표준 조항을 제안하는 서비스입니다.

| 항목        | 내용                                                   |
| ----------- | ------------------------------------------------------ |
| 프레임워크  | React 19 (CRA 기반)                                    |
| 언어        | JavaScript (JSX)                                       |
| 스타일링    | 커스텀 CSS (컴포넌트별 분리), Tailwind CSS (부분 보조) |
| 라우팅      | React Router v7                                        |
| 상태 관리   | React Context API (`AppContext`)                       |
| 인증        | Google OAuth 2.0 → 서버 자체 JWT 발급                  |
| 실시간 통신 | WebSocket (`ws://localhost:8000/analysis/ws/analyze`)  |
| HTTP 통신   | Axios (대부분) + fetch (로그인 전용)                   |
| 차트        | Recharts (`PieChart`, `BarChart`)                      |
| PDF 저장    | html2canvas + jsPDF (동적 import)                      |

---

## 2. 기술 스택 및 설치

### 설치 및 실행

```bash
# 의존성 패키지 일괄 설치
npm install

# 개발 서버 실행 (기본: http://localhost:3000)
npm start

# 프로덕션 빌드
npm run build
```

### 주요 패키지 목록

| 패키지                | 버전    | 용도                                |
| --------------------- | ------- | ----------------------------------- |
| `react` / `react-dom` | ^19.2.5 | 코어 프레임워크                     |
| `react-router-dom`    | ^7.14.0 | 클라이언트 사이드 라우팅            |
| `axios`               | ^1.15.0 | HTTP 통신 (히스토리 API 등)         |
| `@react-oauth/google` | ^0.13.5 | Google OAuth 로그인                 |
| `react-icons`         | ^5.6.0  | 아이콘 (Feather Icons, `Fi` 접두사) |
| `recharts`            | ^3.8.1  | 데이터 시각화 (파이차트, 바차트)    |
| `html2canvas`         | ^1.4.1  | DOM → Canvas 변환 (PDF 생성용)      |
| `jspdf`               | ^4.2.1  | PDF 파일 생성                       |
| `tailwindcss`         | ^3.4.1  | 보조 유틸리티 CSS                   |

---

## 3. 폴더 구조

```
fron2/
├── public/                     # 정적 파일 (index.html 등)
├── src/
│   ├── App.js                  # 루트 컴포넌트: 라우터 설정 + 프로바이더 래핑
│   ├── App.css                 # CRA 기본 파일 (사용 안 함)
│   ├── index.js                # ReactDOM 진입점
│   ├── index.css               # Tailwind 디렉티브 + body 리셋
│   ├── assets/
│   │   └── profile.png         # 헤더 프로필 이미지 (정적 에셋)
│   ├── context/
│   │   └── AppContext.jsx      # 전역 상태 (인증, 히스토리, 다크모드 등)
│   ├── css/
│   │   ├── MainLayout.css      # 헤더·사이드바·레이아웃 스타일
│   │   ├── HomeContent.css     # 입력 페이지 스타일
│   │   ├── LoadingPage.css     # 로딩 진행 페이지 스타일
│   │   └── ResultContent.css   # 결과 리포트 페이지 스타일
│   └── Pages/
│       ├── MainLayout.jsx      # 앱 셸 (헤더 + 사이드바 + <Outlet />)
│       ├── HomeContent.jsx     # 입력 페이지 (라우트: /)
│       ├── LoadingPage.jsx     # 분석 진행 페이지 (라우트: /loading)
│       └── ResultContent.jsx   # 결과 리포트 페이지 (라우트: /result, /result/:id)
├── front_readme.md             # 현재 문서
├── package.json
├── .env                        # 환경 변수 (아래 섹션 참조)
└── .env.sample                 # 환경 변수 샘플
```

---

## 4. 환경 변수

프로젝트 루트(`frontend/`)에 `.env` 파일 생성 필요.

```env
REACT_APP_GOOGLE_CLIENT_ID=구글 클라우드 콘솔 플랫폼에서 부여받은 클라이언트 ID 값
REACT_APP_API_URL=http://localhost:8000
```

주의: 동일 컴퓨터에서 백엔드까지 실행하여 테스트시 백엔드 에도 동일 키 값이 적용되어야 함.<br>
(단, 백엔드가 다른 서버에서 동작중이고, IP 또는 http 주소로 접속시엔 상관없음)

클라이언트 ID 값 생성 방법: AIP 서비스 -> 사용자인증정보 -> OAuth 2.0 클라이언트 ID,<br>
키값\_예시: 551271234567-lo73lg..랜덤값..bv8m.apps.googleusercontent.com

| 변수                         | 용도                                                                  |
| ---------------------------- | --------------------------------------------------------------------- |
| `REACT_APP_GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID (구글 토큰 수신에 사용)                    |
| `REACT_APP_API_URL`          | 백엔드 REST API 베이스 URL (기본값 fallback: `http://localhost:8000`) |

> **코드 내 사용 예시:**
>
> ```javascript
> const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
> ```

---

## 5. 라우팅 구조

`App.js`에서 React Router v7 방식으로 중첩 라우팅 구성.  
모든 페이지는 `MainLayout`을 부모로 하며, `<Outlet />`을 통해 자식 컴포넌트가 렌더됨.

```
App.js
└── <BrowserRouter>
    └── <Routes>
        └── path="/"  → <MainLayout>         # 앱 셸 (항상 렌더됨)
            ├── index  → <HomeContent>         # 입력 페이지
            ├── path="loading" → <LoadingPage> # 분석 진행 중
            ├── path="result"  → <ResultContent> # 분석 결과
            └── path="result/:id" → <ResultContent> # 분석 결과 (히스토리)
```

| 경로          | 컴포넌트        | 진입 방식                                                                         |
| ------------- | --------------- | --------------------------------------------------------------------------------- |
| `/`           | `HomeContent`   | 직접 접근 또는 "New Question" 클릭                                                |
| `/loading`    | `LoadingPage`   | `HomeContent`에서 `navigate("/loading", { state: {...} })`                        |
| `/result`     | `ResultContent` | `LoadingPage`에서 분석 완료 시 `navigate("/result", { state: { report, mode } })` |
| `/result/:id` | `ResultContent` | 사이드바 히스토리 클릭 시 `navigate("/result/123")`                               |

### 라우터 state 전달 구조

**`/loading` 진입 시 전달값:**

```javascript
navigate("/loading", {
  state: {
    content: string, // 텍스트 입력값
    file: File | null, // 업로드된 파일 객체
    docName: string, // 문서명 (최대 15자 truncate)
    mode: "text" | "file",
  },
});
```

**`/result` 진입 시 전달값 (분석):**

```javascript
navigate("/result", {
  state: {
    report: object, // 백엔드 분석 결과 전체 JSON
    mode: "text" | "file",
  },
});
```

---

## 6. 네이밍 컨벤션

본 프로젝트에서 적용된 네이밍 규칙입니다.

```
[ 적용 대상 ]              [ 표기법 ]             [ 예시 ]
-----------------------------------------------------------------------
컴포넌트 (파일명·함수명)   PascalCase             MainLayout, HomeContent
일반 변수                  camelCase              textInput, uploadedFile
상태 변수                  camelCase              isDarkMode, historyList
상태 setter                camelCase + setX       setIsDarkMode, setReport
불리언 변수                is / show 접두사       isLoggedIn, showAlertDropdown
이벤트 핸들러 함수         handle 접두사          handleLogin, handleAnalyze
Ref 변수                   camelCase + Ref        wsRef, headerRef, sectionRefs
모듈 레벨 상수             SCREAMING_SNAKE_CASE   PIPELINE_STEPS, MAX_CHARS
커스텀 훅                  use 접두사             useApp
CSS 클래스명               kebab-case (접두사 포함) ml-sidebar, rc-section-header
-----------------------------------------------------------------------
```

### CSS 클래스 접두사 규칙

각 페이지·컴포넌트별로 고유한 2글자 접두사를 붙여 클래스 충돌을 방지합니다.

| 접두사 | 해당 파일           |
| ------ | ------------------- |
| `ml-`  | `MainLayout.css`    |
| `hc-`  | `HomeContent.css`   |
| `lp-`  | `LoadingPage.css`   |
| `rc-`  | `ResultContent.css` |

**상태 수식어(modifier)는 별도 클래스로 추가:**

```jsx
// 예시
<div className={`ml-history-item ${isDarkMode ? "dark-mode" : "light-mode"} ${active ? "active" : ""}`}>
```

---

## 7. 전역 상태 관리 (AppContext)

**파일:** `src/context/AppContext.jsx`  
**훅:** `useApp()` — 모든 페이지·컴포넌트에서 전역 상태 접근 시 사용

### 상태 변수

| 변수명              | 타입    | 초기값  | 역할                              |
| ------------------- | ------- | ------- | --------------------------------- |
| `isDarkMode`        | boolean | `false` | 라이트/다크 테마 전환             |
| `isLoggedIn`        | boolean | `false` | 로그인 여부                       |
| `userEmail`         | string  | `""`    | 로그인된 사용자 이메일            |
| `historyList`       | array   | `[]`    | 사이드바 히스토리 목록 (최근 N개) |
| `isSidebarOpen`     | boolean | `true`  | 사이드바 열림/닫힘                |
| `alertMessage`      | string  | `""`    | 상단 알림 드롭다운 메시지         |
| `showAlertDropdown` | boolean | `false` | 알림 드롭다운 표시 여부           |
| `showGuideDropdown` | boolean | `true`  | 도움말 드롭다운 표시 여부         |

### 주요 함수

| 함수명                     | 동작 설명                                                                                                                         |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `handleLogin(data)`        | 인증 성공 시 호출. `isLoggedIn=true`, `userEmail` 설정, `accessToken` + `userEmail`을 `localStorage`에 저장, `loadHistory()` 실행 |
| `handleLogout()`           | `isLoggedIn=false`, `userEmail=""`, `historyList=[]`, `localStorage` 초기화                                                       |
| `loadHistory(token)`       | `GET /history/recent` 호출 → `historyList` 업데이트                                                                               |
| `refreshHistory()`         | `localStorage`에서 토큰 꺼내 `loadHistory()` 재호출 (분석 완료 후 갱신 시 사용)                                                   |
| `deleteHistory(historyId)` | `DELETE /history/:historyId` 호출 → 성공 시 `historyList`에서 해당 항목 제거                                                      |

### localStorage 저장 키

| 키            | 저장 값                            |
| ------------- | ---------------------------------- |
| `accessToken` | 서버 발급 JWT (Bearer 인증에 사용) |
| `userEmail`   | 로그인된 구글 계정 이메일          |

---

## 8. 페이지별 기능 정의

---

### 8.1 MainLayout — 앱 셸

**파일:** `src/Pages/MainLayout.jsx`  
**백엔드 호출:** ✅ 사용  
**역할:** 모든 페이지에 공통으로 표시되는 헤더와 사이드바를 제공하는 레이아웃 컴포넌트.  
내부 컨텐츠는 `<Outlet />`을 통해 라우터가 삽입.

#### 백엔드 연동 상세

| 함수명                         | 메서드   | 엔드포인트        | 통신 방식 | 호출 시점                           |
| ------------------------------ | -------- | ----------------- | --------- | ----------------------------------- |
| `handleGoogleSuccess()`        | `POST`   | `/auth/google`    | `fetch()` | Google OAuth 로그인 성공 직후       |
| `AppContext > loadHistory()`   | `GET`    | `/history/recent` | `axios`   | 로그인 성공 후 사이드바 목록 초기화 |
| `AppContext > deleteHistory()` | `DELETE` | `/history/:id`    | `axios`   | 히스토리 삭제 버튼 클릭 시          |

```javascript
// 1. Google 로그인 → 서버 JWT 발급
handleGoogleSuccess(credentialResponse)
  → fetch POST /auth/google { body: { token: credentialResponse.credential } }
  → 응답: { access_token, email }
  → handleLogin(data) 호출 → localStorage 저장 + loadHistory() 실행

// 2. 히스토리 삭제
handleDeleteHistory(e, id)
  → e.stopPropagation()
  → AppContext.deleteHistory(id) → axios DELETE /history/:id
  → 성공 시 historyList에서 해당 항목 제거
  → 현재 보고 있던 결과가 삭제 대상이면 navigate("/")
```

#### 헤더 구성 요소

| 요소                 | 기능                                                       |
| -------------------- | ---------------------------------------------------------- |
| Dot AI 로고          | 클릭 시 홈(/) 이동                                         |
| 다크모드 토글 버튼   | `isDarkMode` 전환 (🌙 / ☀️)                                |
| 알림 벨(🔔)          | `showAlertDropdown` 토글, 알림 메시지 드롭다운 표시        |
| 도움말(?) 버튼       | `showGuideDropdown` 토글, 서비스 이용 가이드 드롭다운 표시 |
| 프로필 이미지        | `assets/profile.png` 정적 이미지                           |
| 이메일 표시          | `userEmail` 렌더 (로그인 상태 시)                          |
| 로그인/로그아웃 버튼 | 미로그인: Google OAuth 버튼 / 로그인: 로그아웃 버튼        |

#### 사이드바 구성 요소

| 요소            | 기능                                                            |
| --------------- | --------------------------------------------------------------- |
| 햄버거 메뉴(☰) | `isSidebarOpen` 토글                                            |
| + New Question  | `handleNewQuestion()` → `/`로 이동                              |
| 히스토리 목록   | `historyList` 렌더, 클릭 시 `/result/:id`로 이동                |
| 삭제(🗑) 버튼   | 각 히스토리 항목 hover 시 표시, 클릭 시 `handleDeleteHistory()` |

#### 주요 함수

```javascript
// Google OAuth 로그인 성공 콜백
handleGoogleSuccess(credentialResponse)
  → fetch POST /auth/google
  → 성공 시 handleLogin(data) 호출

// 새 질문 버튼
handleNewQuestion()
  → navigate("/") (이미 "/" 이면 스킵)

// 히스토리 항목 클릭
handleHistoryClick(id)
  → navigate(`/result/${id}`)

// 히스토리 삭제 (이벤트 버블링 차단 포함)
handleDeleteHistory(e, id)
  → e.stopPropagation()
  → deleteHistory(id)
  → 현재 보고 있던 결과가 삭제된 항목이면 navigate("/")
```

> **API 통신 방식:** 로그인(`/auth/google`)은 `fetch()` 사용.  
> 나머지(히스토리)는 `AppContext`의 axios 함수 위임.

---

### 8.2 HomeContent — 입력 페이지

**파일:** `src/Pages/HomeContent.jsx`  
**백엔드 호출:** ❌ 사용 안함  
**라우트:** `/` (index)  
**역할:** 사용자가 계약서 텍스트 또는 파일을 입력하고 분석을 시작하는 메인 입력 화면.  
분석 시작 버튼은 백엔드를 직접 호출하지 않고, `/loading`으로 `navigate()`만 수행하여 입력값을 `location.state`로 전달함.

#### 상태 변수

| 변수명         | 역할                                                                |
| -------------- | ------------------------------------------------------------------- |
| `textInput`    | 텍스트 입력값 (최대 `MAX_CHARS = 500`자)                            |
| `uploadedFile` | 업로드된 파일 객체 (File \| null)                                   |
| `chartPct`     | 파이차트 애니메이션 숫자 (0 → 70.8, 마운트 시 1600ms 동안 ease-out) |
| `isDragging`   | 드래그 중 여부 (true일 때 입력 카드에 파란 테두리 오버레이 표시)    |

#### 상수

```javascript
MAX_CHARS = 500; // 텍스트 입력 최대 글자 수

PIPELINE_STEPS = [
  { icon: "📄", label: "조항 분석" },
  { icon: "🔍", label: "독소조항 감지" },
  { icon: "📚", label: "법령/판례 검색" },
  { icon: "⚖️", label: "AI 정밀 검증" },
  { icon: "📋", label: "리포트 생성" },
];
```

#### 주요 함수

```javascript
// 파일 유효성 검사 및 적용 (드래그·버튼 공용)
applyFile(file)
  → 확장자 검사: pdf, png, jpg, jpeg, jfif 허용
  → setUploadedFile(file)
  → setTextInput("") (파일 선택 시 텍스트 초기화)

// 파일 입력(<input type="file">) onChange 핸들러
handleFileUpload(e)
  → applyFile(e.target.files[0])
  → 입력값 리셋 (동일 파일 재선택 허용)

// 드래그앤드랍 이벤트 핸들러 (입력 카드에 장착)
handleDragOver(e)   → isDragging = true (파일 미첨부 상태에서만)
handleDragLeave(e)  → isDragging = false
handleDrop(e)       → applyFile(e.dataTransfer.files[0])

// 분석 시작
handleAnalyze()
  → 입력값 검증 (텍스트 또는 파일 필수)
  → docName = 텍스트 첫 15자 or 파일명
  → navigate("/loading", { state: { content, file, docName, mode } })
```

#### UI 구성

1. **입력 카드** — 텍스트 textarea (드래그앤드랍 지원), PDF / 이미지 업로드 버튼, 글자수 카운터(0/500), 분석 시작 버튼<br>
   (독소조항 분석 모델 글자수에 따른 분류 한계로, 각 조항별 256자 이내여야 함, 100자이내 조항은 5개 까지 한번에 분석 가능)
2. **글자수 카운터 색상 단계**
   - `0`: 연한 회색 (비활성)
   - `1~249`: 검정 (라이트) / 흰색 (다크)
   - `250~399`: 주황색 (`#f59e0b`)
   - `400~449`: 주황-레드 (`#f97316`)
   - `450~500`: 빨강 + 흔들림 애니메이션 (`#dc2626`)
3. **인포 그리드 (4칸)** — 서비스 강점 카드, 보안 카드, 위험도 통계 (파이차트 포함), 기술 스택 + 파이프라인 플로우

> **API 호출 없음.** 분석 시작은 `/loading`으로 navigate만 함.

---

### 8.3 LoadingPage — 분석 진행 페이지

**파일:** `src/Pages/LoadingPage.jsx`  
**백엔드 호출:** ✅ 사용 (WebSocket)  
**라우트:** `/loading`  
**역할:** 백엔드 WebSocket에 연결하여 실시간으로 분석 진행 상황을 표시. 완료 시 `/result`로 자동 이동.

#### 백엔드 연동 상세

| 함수명                 | 프로토콜    | 엔드포인트                                | 호출 시점                                 |
| ---------------------- | ----------- | ----------------------------------------- | ----------------------------------------- |
| `connectToWebSocket()` | `WebSocket` | `ws://localhost:8000/analysis/ws/analyze` | 페이지 마운트 시 `useEffect` 내 자동 실행 |

```javascript
// 페이지 진입 시 자동 연결 (useEffect)
connectToWebSocket(analysisData)
  → ws = new WebSocket("ws://localhost:8000/analysis/ws/analyze")
  → wsRef.current = ws  // 취소 버튼에서 ws.close() 호출 가능하도록 ref 저장

// 연결 수립 후 분석 요청 송신
ws.onopen
  → ws.send(JSON.stringify({
      token,       // localStorage의 accessToken
      content,     // 텍스트 입력값 (text 모드)
      doc_name,    // 문서명
      mode,        // "text" | "file"
      raw_bytes    // base64 파일 데이터 (file 모드에서만 포함)
    }))

// 서버 메시지 수신 처리
ws.onmessage
  → cancelledRef.current === true 이면 무시 (취소 후 수신 방지)
  → response.status === "invalid_query" → navigate("/result", 서비스 범위 외 결과)
  → response.step === "complete"        → navigate("/result", { report: response.data, mode })
  → 진행 중 step (step_1~step_5)        → setProgress / setCurrentStep / setMessage 업데이트
  → response.error                      → setMessage(에러 문구)
```

#### 상태 변수

| 변수명        | 역할                                  |
| ------------- | ------------------------------------- |
| `progress`    | 진행률 숫자 0~100                     |
| `currentStep` | 현재 단계 라벨 (예: "📄 조항 분석중") |
| `message`     | 백엔드에서 받은 상세 메시지           |

#### Ref 변수

| Ref            | 역할                                                                |
| -------------- | ------------------------------------------------------------------- |
| `wsRef`        | WebSocket 인스턴스 보관 (useEffect 외부에서 접근하기 위해 ref 사용) |
| `cancelledRef` | 취소 후 WebSocket 메시지 수신 시 navigate 방지용 boolean 플래그     |

#### 분석 단계 정의

```javascript
const steps = [
  { id: "step_1", label: "📄 조항 분석중", progress: 20 },
  { id: "step_2", label: "🔍 독소조항 감지", progress: 40 },
  { id: "step_3", label: "📚 법령/판례(벡터 검색)", progress: 60 },
  { id: "step_4", label: "⚖️  AI 정밀 검증", progress: 80 },
  { id: "step_5", label: "📋 최종 리포트 생성중", progress: 95 },
];
```

#### WebSocket 연결 흐름

```
1. useEffect 실행
   → location.state에서 { content, docName, mode, file } 추출
   → mode === "file" 이면 FileReader.readAsDataURL() 로 파일 base64 변환
   → connectToWebSocket(analysisData) 호출

2. connectToWebSocket(analysisData)
   → ws = new WebSocket("ws://localhost:8000/analysis/ws/analyze")
   → wsRef.current = ws (취소 버튼에서 접근 가능하도록 저장)

3. ws.onopen
   → ws.send(JSON.stringify({ token, content, doc_name, mode, raw_bytes? }))

4. ws.onmessage
   → cancelledRef.current === true 이면 무시
   → response.status === "invalid_query" → progress=100, navigate("/result", { report: {...} })
   → response.step === "complete" → navigate("/result", { report: response.data, mode })
   → 일반 step → setProgress, setCurrentStep, setMessage
   → response.error → setMessage(에러 문구)

5. useEffect cleanup
   → 페이지 떠날 때 ws.close()
```

#### 주요 함수

```javascript
handleCancel()
  → cancelledRef.current = true   // 이후 메시지 무시
  → wsRef.current.close()         // WebSocket 종료
  → navigate("/")                 // 홈으로 이동
```

#### UI 구성

- 진행률 바 (progress% 너비로 실시간 업데이트)
- 현재 단계 제목 + 메시지
- 5단계 타임라인 (완료 단계: ✓ 파란색, 미완료: 회색 번호)
- 로딩 점 애니메이션 (3개 bounce)
- 취소 버튼 (progress < 100 일 때만 표시)

---

### 8.4 ResultContent — 결과 리포트 페이지

**파일:** `src/Pages/ResultContent.jsx`  
**백엔드 호출:** ✅ 사용 (히스토리 조회 경로에서만)  
**라우트:** `/result` (신규 분석), `/result/:id` (히스토리 조회)  
**역할:** 분석 결과 전체를 시각화. 좌측에 조항별 카드, 우측 고정 패널에 위험도 종합 점수·차트·가이드 표시.

#### 백엔드 연동 상세

> `/result` (신규 분석) 진입 시에는 백엔드 호출 없음 — `LoadingPage`가 전달한 `location.state.report`를 그대로 사용.  
> `/result/:id` (히스토리) 진입 시에만 아래 API 호출.

| 함수명                 | 메서드 | 엔드포인트     | 통신 방식 | 호출 시점                                        |
| ---------------------- | ------ | -------------- | --------- | ------------------------------------------------ |
| `fetchHistoryDetail()` | `GET`  | `/history/:id` | `axios`   | URL에 `:id` 파라미터 있을 때 마운트 시 자동 호출 |

```javascript
// 히스토리 조회 진입 시 자동 실행 (useEffect)
fetchHistoryDetail(historyId)
  → axios.get(`/history/${historyId}`, { headers: { Authorization: "Bearer <token>" } })
  → 응답: 분석 결과 전체 JSON
  → setReport(res.data)  // 이후 신규 분석과 동일한 렌더 흐름 진행
```

#### 상태 변수

| 변수명       | 역할                                        |
| ------------ | ------------------------------------------- |
| `report`     | 분석 결과 전체 JSON 데이터                  |
| `loading`    | 히스토리 API 로딩 여부                      |
| `copiedIdx`  | 복사 버튼 클릭 인덱스 (1500ms 후 null 리셋) |
| `pdfLoading` | PDF 생성 진행 중 여부                       |

#### Ref 변수 (PDF 생성용)

| Ref             | 역할                                           |
| --------------- | ---------------------------------------------- |
| `headerRef`     | 리포트 헤더 영역 (PDF 1페이지 상단)            |
| `rightPanelRef` | 우측 위험도 패널 (PDF 1페이지 하단)            |
| `sectionRefs`   | 각 조항 섹션 카드 배열 (PDF 2페이지~ 각 1개씩) |

#### 주요 함수

```javascript
// 히스토리에서 결과 불러오기
fetchHistoryDetail(historyId)
  → GET /history/:historyId (axios, Bearer 토큰)
  → setReport(res.data)

// 추천 조항 클립보드 복사
handleCopy(text, idx)
  → navigator.clipboard.writeText(text)
  → setCopiedIdx(idx) → 1500ms 후 null

// PDF 저장 (동적 import)
handleDownloadPdf()
  → import("jspdf") + import("html2canvas")
  → 1페이지: headerRef + rightPanelRef 캡처
  → 2페이지~: sectionRefs 각 카드 캡처 (700px 너비 고정)
  → A4 비율 자동 맞춤 후 PDF 저장 (<docName>.pdf)
```

#### 결과 데이터 분류 로직

```javascript
// 백엔드 results 배열을 타입으로 분리
const analysisResults = results.filter((r) => r.result_type === "ANALYSIS");
const generalResults = results.filter((r) => r.result_type === "GENERAL");
```

| `result_type` | 렌더 방식                                              |
| ------------- | ------------------------------------------------------ |
| `ANALYSIS`    | 위험도 뱃지 + 위험/안전 박스 + 법령 + 추천 조항 + 태그 |
| `GENERAL`     | 질문 답변 형태 (answer-box 스타일)                     |

#### UI 구성

**좌측 메인 (스크롤):**

- 리포트 헤더 (로고, 제목, 날짜, PDF 저장 버튼)
- 조항별 섹션 카드 (각 카드마다 `sectionRefs`에 ref 할당)
  - 헤더: `🔍 검토 요청 질문` + 위험도 뱃지 + 점수
  - 원문 텍스트 박스
  - `⚖️ 분석 리포트` 레이블
  - 위험 조항: 위험 요소 발견 박스 → 법령/판례 → 추천 표준 조항
  - 안전 조항: 안전 판별 박스
  - 태그 목록

**우측 고정 패널 (sticky):**

- SAFE ↔ DANGER 진행 바
- 종합 위험도 점수 (숫자)
- 조항 2개 이상 시: 평균 뱃지 + 세그먼트 바 가이드 (단계별 칩 + 현재 단계 상세 카드)
- 조항 1개: 5단계 세로 목록 가이드
- 조항 2개 이상 시: 조항별 위험도 바차트 (Recharts)
- 파일 분석 시: 누락 항목 경고 카드

#### 특수 케이스 처리

| 조건                                    | 처리                                  |
| --------------------------------------- | ------------------------------------- |
| `report === null`                       | "분석 결과가 없습니다" 빈 상태 화면   |
| `loading === true`                      | 로딩 스피너 화면                      |
| `report.status === "invalid_query"`     | "서비스 범위 외" 안내 화면            |
| `analysisResults.length === 0`          | PDF 버튼 미표시                       |
| `report.missing_clause_report === null` | 누락 항목 카드 미렌더                 |
| `analysisResults.length < 2`            | 바차트 미표시, 세그먼트 가이드 미표시 |

---

## 9. 백엔드 API 연동 가이드

### 인증

모든 API 호출 시 헤더에 JWT 포함:

```
Authorization: Bearer <accessToken>
```

`accessToken`은 `localStorage.getItem("accessToken")`으로 획득.

### API 호출 일람

| 메서드   | 엔드포인트             | 호출 위치                                    | 통신 방식   | 설명                              |
| -------- | ---------------------- | -------------------------------------------- | ----------- | --------------------------------- |
| `POST`   | `/auth/google`         | `MainLayout.jsx` > `handleGoogleSuccess()`   | `fetch()`   | 구글 토큰 검증 → 자체 JWT 발급    |
| `GET`    | `/history/recent`      | `AppContext.jsx` > `loadHistory()`           | `axios`     | 사이드바 히스토리 최근 목록 조회  |
| `GET`    | `/history/:id`         | `ResultContent.jsx` > `fetchHistoryDetail()` | `axios`     | 특정 분석 기록 전체 데이터 조회   |
| `DELETE` | `/history/:id`         | `AppContext.jsx` > `deleteHistory()`         | `axios`     | 히스토리 항목 삭제                |
| `WS`     | `/analysis/ws/analyze` | `LoadingPage.jsx` > `connectToWebSocket()`   | `WebSocket` | 실시간 분석 진행 및 결과 스트리밍 |

### WebSocket 송수신 데이터 구조

**송신 (클라이언트 → 서버):**

```json
{
  "token": "Bearer JWT 토큰",
  "content": "분석할 텍스트 (text 모드)",
  "doc_name": "문서명",
  "mode": "text | file",
  "raw_bytes": "base64 인코딩된 파일 데이터 (file 모드)"
}
```

**수신 — 진행 중 (서버 → 클라이언트):**

```json
{
  "step": "step_1 ~ step_5",
  "progress": 20,
  "message": "분석 진행 중 설명 메시지"
}
```

**수신 — 완료:**

```json
{
  "step": "complete",
  "data": {
    /* 전체 분석 결과 JSON */
  }
}
```

**수신 — 서비스 범위 외 질문:**

```json
{
  "status": "invalid_query",
  "message": "Antidote는 근로계약 전문 분석 서비스입니다."
}
```

### 분석 결과 데이터 구조 (report JSON)

```json
{
  "total_risk_score": 60.21,
  "doc_name": "계약서명",
  "analyzed_at": "2026-05-04 07:03:44",
  "mode": "text | file",
  "missing_clause_report": "누락 항목 설명 텍스트 | null",
  "status": "invalid_query (해당 시에만)",
  "results": [
    {
      "result_type": "ANALYSIS | GENERAL",
      "clause": "원문 계약 조항 텍스트",
      "level": "EXTREME | DANGER | WARNING | CAUTION | SAFE",
      "score": 72.5,
      "reason": "위험 판단 근거 설명",
      "proposed_text": "수정 표준 조항 텍스트",
      "tags": ["#부당계약", "#검토필요"],
      "legal_basis": [{ "title": "법령명", "summary": "요약 내용" }],
      "precedents": [{ "case_number": "2006구합45852", "content": "판례 요약" }]
    }
  ]
}
```

---

## 10. CSS 클래스 네이밍 시스템

각 CSS 파일은 컴포넌트 접두사 + BEM-like 수식어 구조로 작성됩니다.

### 구조 패턴

```
[접두사]-[요소명]             기본 요소
[접두사]-[요소명]-[수식어]   하위 요소 또는 변형
light-mode / dark-mode       테마 수식어 (별도 클래스로 추가)
active / completed / pending 상태 수식어
```

### 예시

```css
/* MainLayout.css */
.ml-sidebar          /* 사이드바 컨테이너 */
.ml-history-row      /* 히스토리 행 (버튼 + 삭제 버튼 래퍼) */
.ml-history-item     /* 히스토리 이동 버튼 */
.ml-history-delete   /* 히스토리 삭제 버튼 (hover 시 표시) */

/* ResultContent.css */
.rc-section          /* 개별 조항 카드 */
.rc-section-header   /* 카드 헤더 (번호 + 뱃지) */
.rc-level-badge      /* 위험도 레벨 뱃지 (색상은 inline style) */
.rc-segment-bar      /* 세그먼트 칩 행 (2개+ 조항용 가이드) */
.rc-segment-card     /* 현재 단계 상세 카드 */
```

### CSS 변수 (커스텀 프로퍼티)

각 CSS 파일 상단 `:root`에 선언:

```css
/* LoadingPage.css / MainLayout.css 공통 팔레트 */
--color-blue-600: #2563eb;
--color-slate-900: #0f172a;
--color-slate-500: #64748b;
--color-white: #ffffff;
--transition-base: all 0.3s ease;
```

---

## 11. 위험도 레벨 시스템

`ResultContent.jsx`에 정의된 `RISK_LEVELS` 배열을 기준으로 전체 위험도 시각화가 동작합니다.

| 레벨      | 점수 범위 | 색상             | 한글 설명             |
| --------- | --------- | ---------------- | --------------------- |
| `Extreme` | 80 ~ 100  | `#dc2626` (빨강) | 심각한 법적 위험      |
| `Danger`  | 60 ~ 79   | `#f97316` (주황) | 독소조항 가능성 높음  |
| `Warning` | 40 ~ 59   | `#f59e0b` (황색) | 수정 검토 필요        |
| `Caution` | 20 ~ 39   | `#3b82f6` (파랑) | 일부 모호한 표현 있음 |
| `Safe`    | 0 ~ 19    | `#22c55e` (초록) | 법적으로 안전한 조항  |

### 레벨 판별 함수

```javascript
// 점수 → RISK_LEVELS 항목 반환
const getRiskInfo = (score) => {
  if (score >= 80) return RISK_LEVELS[0]; // Extreme
  if (score >= 60) return RISK_LEVELS[1]; // Danger
  if (score >= 40) return RISK_LEVELS[2]; // Warning
  if (score >= 20) return RISK_LEVELS[3]; // Caution
  return RISK_LEVELS[4]; // Safe
};
```

### result.level → 색상 매핑 (LEVEL_MAP)

```javascript
// 백엔드 level 문자열을 색상/라벨로 변환
const LEVEL_MAP = {
  EXTREME: { color: "#dc2626", label: "Extreme" },
  DANGER: { color: "#f97316", label: "Danger" },
  WARNING: { color: "#f59e0b", label: "Warning" },
  CAUTION: { color: "#3b82f6", label: "Caution" },
  SAFE: { color: "#22c55e", label: "Safe" },
};
```

---

_최종 업데이트: 2026-05-04_
