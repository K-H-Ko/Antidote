import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

// 앱 전역 공유 상태 컨텍스트
const AppContext = createContext(null);

export const AppProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [historyList, setHistoryList] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [alertMessage, setAlertMessage] = useState("");
  const [showAlertDropdown, setShowAlertDropdown] = useState(false);
  const [showGuideDropdown, setShowGuideDropdown] = useState(true);

  // 앱 시작 시 토큰 복원 및 히스토리 로드
  useEffect(() => {
    const token = localStorage.getItem("accessToken");
    const savedEmail = localStorage.getItem("userEmail");
    if (token && savedEmail) {
      setIsLoggedIn(true);
      setUserEmail(savedEmail);
      loadHistory(token);
    }
  }, []);

  // 히스토리 5개 조회
  const loadHistory = async (token) => {
    try {
      const res = await axios.get(
        `${process.env.REACT_APP_API_URL || "http://localhost:8000"}/history/recent`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      console.log("hist", res);
      // setHistoryList(res.data.histories || []);
      setHistoryList(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error("히스토리 로드 실패:", err);
    }
  };

  // 로그인 처리
  const handleLogin = (data) => {
    setIsLoggedIn(true);
    setUserEmail(data.user.email);
    localStorage.setItem("accessToken", data.access_token);
    localStorage.setItem("userEmail", data.user.email);
    loadHistory(data.access_token);
  };

  // 로그아웃 처리
  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserEmail("");
    setHistoryList([]);
    localStorage.removeItem("accessToken");
    localStorage.removeItem("userEmail");
  };

  // 히스토리 새로고침
  const refreshHistory = () => {
    const token = localStorage.getItem("accessToken");
    if (token) loadHistory(token);
  };

  // 히스토리 단건 삭제
  const deleteHistory = async (historyId) => {
    try {
      const token = localStorage.getItem("accessToken");
      await axios.delete(
        `${process.env.REACT_APP_API_URL || "http://localhost:8000"}/history/${historyId}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      // 로컬 목록에서 즉시 제거 (API 재호출 없이)
      setHistoryList((prev) => prev.filter((item) => item.id !== historyId));
      return true;
    } catch (err) {
      console.error("히스토리 삭제 실패:", err);
      return false;
    }
  };

  return (
    <AppContext.Provider
      value={{
        isDarkMode,
        setIsDarkMode,
        isLoggedIn,
        setIsLoggedIn,
        userEmail,
        setUserEmail,
        historyList,
        setHistoryList,
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
        refreshHistory,
        deleteHistory,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

// 훅으로 편하게 사용
export const useApp = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp은 AppProvider 내에서만 사용하세요.");
  return ctx;
};
