import React, { useRef } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";
import { GoogleOAuthProvider } from "@react-oauth/google";
import {
  FiBell,
  FiHelpCircle,
  FiSun,
  FiMoon,
  FiLogOut,
  FiPlus,
  FiX,
  FiAlertCircle,
  FiTrash2,
} from "react-icons/fi";
import { useApp } from "../context/AppContext";
import profileImg from "../assets/profile.png";
import "../css/MainLayout.css";

const MainLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const alertRef = useRef(null);
  const guideRef = useRef(null);

  const {
    isDarkMode,
    setIsDarkMode,
    isLoggedIn,
    userEmail,
    historyList,
    isSidebarOpen,
    setIsSidebarOpen,
    alertMessage,
    setAlertMessage,
    showAlertDropdown,
    setShowAlertDropdown,
    showGuideDropdown,
    setShowGuideDropdown,
    handleLogin,
    handleLogout,
    deleteHistory,
  } = useApp();

  // 구글 로그인 성공 처리
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const token = credentialResponse.credential;
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || "http://localhost:8000"}/auth/google`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        },
      );
      const data = await response.json();
      if (data.user) {
        handleLogin(data);
      }
    } catch (err) {
      console.error("구글 로그인 오류:", err);
      setAlertMessage("로그인 중 오류가 발생했습니다.");
      setShowAlertDropdown(true);
    }
  };

  // 새 질문 버튼: 홈으로 이동
  const handleNewQuestion = () => {
    if (location.pathname !== "/") {
      navigate("/");
    }
  };

  // 히스토리 항목 클릭 → 결과 페이지
  const handleHistoryClick = (id) => {
    navigate(`/result/${id}`);
  };

  // 히스토리 삭제
  const handleDeleteHistory = async (e, id) => {
    e.stopPropagation(); // 상위 클릭 이벤트 차단
    const success = await deleteHistory(id);
    if (success && location.pathname === `/result/${id}`) {
      navigate("/"); // 현재 보고 있던 항목이 삭제되면 홈으로
    }
  };

  return (
    <div className={`ml-container ${isDarkMode ? "dark-mode" : "light-mode"}`}>
      {/* ─── 헤더 (모든 페이지 공통 고정) ─── */}
      <header
        className={`ml-header ${isDarkMode ? "dark-mode" : "light-mode"}`}
      >
        <div className="ml-header-inner">
          {/* 사이드바 토글 + 로고 */}
          <div className="ml-header-left">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className={`ml-toggle-btn ${isDarkMode ? "dark-mode" : "light-mode"}`}
              aria-label="사이드바 토글"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <div
              className="ml-logo"
              onClick={() => navigate("/")}
              style={{ cursor: "pointer" }}
            >
              <div className="ml-logo-dot-outer">
                <div className="ml-logo-dot-inner"></div>
              </div>
              <span className="ml-logo-text">Dot AI</span>
            </div>
          </div>

          {/* 우측 액션 버튼 */}
          <div className="ml-header-right">
            {/* 다크모드 토글 */}
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className={`ml-icon-btn ${isDarkMode ? "dark-mode" : "light-mode"}`}
              aria-label="다크모드 토글"
            >
              {isDarkMode ? <FiSun size={20} /> : <FiMoon size={20} />}
            </button>

            {/* 오류 알람 */}
            <div className="ml-dropdown-wrap" ref={alertRef}>
              <button
                onClick={() => setShowAlertDropdown(!showAlertDropdown)}
                className={`ml-icon-btn ${isDarkMode ? "dark-mode" : "light-mode"}`}
                aria-label="알람"
              >
                <FiBell size={20} />
                {alertMessage && <span className="ml-alert-dot"></span>}
              </button>
              {showAlertDropdown && (
                <div
                  className={`ml-dropdown ${isDarkMode ? "dark-mode" : "light-mode"}`}
                >
                  <div className="ml-dropdown-header">
                    {alertMessage ? (
                      <>
                        <FiAlertCircle size={16} />
                        <span>오류 알림</span>
                      </>
                    ) : (
                      <span>알림</span>
                    )}
                    <button
                      onClick={() => {
                        setShowAlertDropdown(false);
                        setAlertMessage("");
                      }}
                      className="ml-dropdown-close"
                    >
                      <FiX size={14} />
                    </button>
                  </div>
                  <div className="ml-dropdown-body">
                    <p>{alertMessage || "현재 오류 내용이 없습니다."}</p>
                  </div>
                </div>
              )}
            </div>

            {/* 도움말 가이드 */}
            <div className="ml-dropdown-wrap" ref={guideRef}>
              <button
                onClick={() => setShowGuideDropdown(!showGuideDropdown)}
                className={`ml-icon-btn ${isDarkMode ? "dark-mode" : "light-mode"}`}
                aria-label="도움말"
              >
                <FiHelpCircle size={20} />
              </button>
              {showGuideDropdown && (
                <div
                  className={`ml-dropdown ml-guide-dropdown ${isDarkMode ? "dark-mode" : "light-mode"}`}
                >
                  <div className="ml-dropdown-header">
                    <span>사용 가이드</span>
                    <button
                      onClick={() => setShowGuideDropdown(false)}
                      className="ml-dropdown-close"
                    >
                      <FiX size={14} />
                    </button>
                  </div>
                  <div className="ml-dropdown-body">
                    <div className="ml-guide-item">
                      <h4 className="ml-guide-title">1. 분석 방법 선택</h4>
                      <p
                        className={`ml-guide-text ${isDarkMode ? "dark-mode" : "light-mode"}`}
                      >
                        <strong>TEXT :</strong> 계약서 조항을 붙여넣거나 노동법
                        관련 질문을 하세요.
                        <br />
                        <strong>FILE :</strong> PDF 또는 이미지 파일을
                        업로드하세요.
                      </p>
                    </div>
                    <div className="ml-guide-item">
                      <h4 className="ml-guide-title">2. 지원 파일</h4>
                      <p
                        className={`ml-guide-text ${isDarkMode ? "dark-mode" : "light-mode"}`}
                      >
                        📄 PDF &nbsp;|&nbsp; 🖼️ JPG, PNG, JPEG, JFIF
                      </p>
                    </div>
                    <div className="ml-guide-item">
                      <h4 className="ml-guide-title">3. 분석 범위</h4>
                      <p
                        className={`ml-guide-text ${isDarkMode ? "dark-mode" : "light-mode"}`}
                      >
                        ✓ 근로계약, 노동법, 고용 관계
                        <br />✗ 일상 대화는 거절될 수 있습니다.
                      </p>
                    </div>
                    <div className="ml-guide-item">
                      <h4 className="ml-guide-title">4. 소요 시간</h4>
                      <p
                        className={`ml-guide-text ${isDarkMode ? "dark-mode" : "light-mode"}`}
                      >
                        텍스트: 30초~1분 &nbsp;|&nbsp; 파일: 1~3분
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 프로필 이미지 */}
            <img src={profileImg} alt="Profile" className="ml-profile-img" />

            {/* 로그인 / 로그아웃 */}
            <div className="ml-auth-section">
              {isLoggedIn ? (
                <>
                  <div
                    className={`ml-user-email ${isDarkMode ? "dark-mode" : "light-mode"}`}
                    title={userEmail}
                  >
                    {userEmail}
                  </div>
                  <button onClick={handleLogout} className="ml-logout-btn">
                    <FiLogOut size={16} />
                    로그아웃
                  </button>
                </>
              ) : (
                <GoogleOAuthProvider
                  clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID || ""}
                >
                  <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={() => console.log("Google Login Failed")}
                  />
                </GoogleOAuthProvider>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* ─── 바디: 사이드바 + 중앙 콘텐츠 ─── */}
      <div className="ml-body">
        {/* 사이드바 (모든 페이지 공통 고정) */}
        <aside
          className={`ml-sidebar ${isDarkMode ? "dark-mode" : "light-mode"} ${isSidebarOpen ? "open" : "closed"}`}
        >
          {/* 새 질문 버튼 */}
          <button onClick={handleNewQuestion} className="ml-new-btn">
            <FiPlus size={16} />
            New Question
          </button>

          {/* 분석 히스토리 (로그인 시에만) */}
          {isLoggedIn && (
            <div className="ml-history-section">
              <p
                className={`ml-history-label ${isDarkMode ? "dark-mode" : "light-mode"}`}
              >
                Result
              </p>
              <div className="ml-history-list">
                {historyList.length === 0 ? (
                  <p
                    className={`ml-no-history ${isDarkMode ? "dark-mode" : "light-mode"}`}
                  >
                    분석 이력이 없습니다.
                  </p>
                ) : (
                  historyList.map((item, idx) => (
                    <div key={idx} className="ml-history-row">
                      <button
                        onClick={() => handleHistoryClick(item.id)}
                        className={`ml-history-item ${isDarkMode ? "dark-mode" : "light-mode"} ${
                          location.pathname === `/result/${item.id}`
                            ? "active"
                            : ""
                        }`}
                      >
                        <span className="ml-history-icon">📄</span>
                        <span className="ml-history-title">
                          {item.doc_name || "분석 결과"}
                        </span>
                      </button>
                      <button
                        onClick={(e) => handleDeleteHistory(e, item.id)}
                        className={`ml-history-delete ${isDarkMode ? "dark-mode" : "light-mode"}`}
                        title="삭제"
                      >
                        <FiTrash2 size={13} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </aside>

        {/* 중앙 메인 콘텐츠 (라우트에 따라 교체) */}
        <main
          className={`ml-main ${isSidebarOpen ? "with-sidebar" : "full-width"}`}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
