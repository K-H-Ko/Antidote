import React, { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import "../css/LoadingPage.css";

const steps = [
  { id: "step_1", label: "📄 조항 분석중", progress: 20 },
  { id: "step_2", label: "🔍 독소조항 감지", progress: 40 },
  { id: "step_3", label: "📚 법령/판례(벡터 검색)", progress: 60 },
  { id: "step_4", label: "⚖️  AI 정밀 검증", progress: 80 },
  { id: "step_5", label: "📋 최종 리포트 생성중", progress: 95 },
];

const LoadingPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isDarkMode } = useApp();
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("");
  const [message, setMessage] = useState("");

  // WebSocket ref: useEffect 밖에서도 접근 가능
  const wsRef = useRef(null);
  // 취소 여부 플래그: 취소 후 WebSocket 메시지로 navigate 방지
  const cancelledRef = useRef(false);

  useEffect(() => {
    let ws = null;

    const connectWebSocket = async () => {
      try {
        const token = localStorage.getItem("accessToken") || "";
        const state = location.state || {};
        const analysisData = {
          token,
          content: state.content || "",
          doc_name: state.docName || "Document",
          mode: state.mode || "text",
        };

        if (state.file && state.mode === "file") {
          const reader = new FileReader();
          reader.onload = (e) => {
            analysisData.raw_bytes = e.target.result;
            connectToWebSocket(analysisData);
          };
          reader.readAsDataURL(state.file);
        } else {
          connectToWebSocket(analysisData);
        }
      } catch (error) {
        console.error("분석 준비 오류:", error);
        setMessage("분석 중 오류가 발생했습니다.");
      }
    };

    const connectToWebSocket = (analysisData) => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const websocketUrl = `${protocol}//localhost:8000/analysis/ws/analyze`;

      ws = new WebSocket(websocketUrl);
      wsRef.current = ws; // ref에 저장 → 취소 버튼에서 접근 가능

      ws.onopen = () => {
        console.log("WebSocket 연결됨");
        ws.send(JSON.stringify(analysisData));
      };

      ws.onmessage = (event) => {
        if (cancelledRef.current) return; // 취소 후 수신 메시지 무시

        const response = JSON.parse(event.data);
        console.log("WebSocket 메시지:", response);

        // [추가] 서비스 범위 벗어난 쿼리 처리
        if (response.status === "invalid_query") {
          setProgress(100);
          setCurrentStep("분석 불가");
          setMessage(
            response.message || "Antidote는 근로계약 전문 분석 서비스입니다.",
          );

          setTimeout(() => {
            navigate("/result", {
              state: {
                report: {
                  status: "invalid_query",
                  message:
                    response.message ||
                    "Antidote는 근로계약 전문 분석 서비스입니다.",
                  results: [],
                },
              },
            });
          }, 1500);
          return;
        }

        if (response.step === "complete") {
          setProgress(100);
          setCurrentStep("완료");
          setMessage("분석이 완료되었습니다.");

          setTimeout(() => {
            navigate("/result", {
              state: {
                report: response.data,
                mode: analysisData.mode,   // "file" | "text"
              },
            });
          }, 500);
        } else if (response.step && response.step !== "error") {
          setProgress(response.progress || 0);
          const stepInfo = steps.find((s) => s.id === response.step);
          if (stepInfo) {
            setCurrentStep(stepInfo.label);
          }
          setMessage(response.message || "분석 중입니다.");
        } else if (response.error) {
          console.error("WebSocket 오류:", response.error);
          setMessage(`오류: ${response.error}`);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket 오류:", error);
        setMessage("연결 오류가 발생했습니다.");
      };

      ws.onclose = () => {
        console.log("WebSocket 연결 종료");
      };
    };

    connectWebSocket();

    // 페이지 떠날 때 WebSocket 종료
    return () => {
      // CONNECTING(0) 또는 OPEN(1) 상태 모두 종료
      if (
        ws &&
        ws.readyState !== WebSocket.CLOSED &&
        ws.readyState !== WebSocket.CLOSING
      ) {
        ws.close();
      }
    };
  }, [location.state, navigate]);

  // 분석 취소: WebSocket 닫고 홈으로 이동
  const handleCancel = () => {
    cancelledRef.current = true;
    if (
      wsRef.current &&
      wsRef.current.readyState !== WebSocket.CLOSED &&
      wsRef.current.readyState !== WebSocket.CLOSING
    ) {
      wsRef.current.close();
    }
    navigate("/");
  };

  return (
    <div
      className={`lp-loading-wrap ${isDarkMode ? "dark-mode" : "light-mode"}`}
    >
      <main className="lp-main">
        <div className="lp-content">
          {/* Progress Bar Section */}
          <div className="lp-progress-section">
            <div className="lp-bar-container">
              {/* Background bar */}
              <div
                className={`lp-bar-background ${isDarkMode ? "dark-mode" : "light-mode"}`}
              >
                {/* Progress bar */}
                <div
                  className="lp-bar-fill"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>

              {/* Progress percentage */}
              <div
                className={`lp-progress-text ${progress === 100 ? "complete" : "in-progress"}`}
              >
                {progress}%
              </div>
            </div>

            {/* Current Step */}
            <div className="lp-current-step">
              <h2 className="lp-step-title">{currentStep}</h2>
              <p
                className={`lp-step-message ${isDarkMode ? "dark-mode" : "light-mode"}`}
              >
                {message}
              </p>
            </div>

            {/* Step Timeline */}
            <div className="lp-timeline">
              {steps.map((step, idx) => (
                <div key={step.id} className="lp-step-item">
                  {/* Step Indicator */}
                  <div
                    className={`lp-step-indicator ${
                      progress >= step.progress
                        ? "completed"
                        : `pending ${isDarkMode ? "dark-mode" : "light-mode"}`
                    }`}
                  >
                    {progress >= step.progress ? "✓" : idx + 1}
                  </div>

                  {/* Step Label */}
                  <div className="lp-step-label-section">
                    <p
                      className={`lp-step-label ${
                        progress >= step.progress
                          ? "completed"
                          : `pending ${isDarkMode ? "dark-mode" : "light-mode"}`
                      }`}
                    >
                      {step.label}
                    </p>
                  </div>

                  {/* Step Progress */}
                  <div
                    className={`lp-step-progress ${
                      progress >= step.progress
                        ? "completed"
                        : `pending ${isDarkMode ? "dark-mode" : "light-mode"}`
                    }`}
                  >
                    {step.progress}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Loading Animation */}
          <div className="lp-animation">
            {[0, 1, 2].map((idx) => (
              <div key={idx} className="lp-dot"></div>
            ))}
          </div>

          {/* 취소 버튼: 분석 완료 전까지만 표시 */}
          {progress < 100 && (
            <button
              onClick={handleCancel}
              className={`lp-cancel-btn ${isDarkMode ? "dark-mode" : "light-mode"}`}
            >
              ✕ 분석 취소
            </button>
          )}
        </div>
      </main>
    </div>
  );
};

export default LoadingPage;
