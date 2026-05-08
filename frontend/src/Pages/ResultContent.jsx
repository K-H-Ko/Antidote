import React, { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useApp } from "../context/AppContext";
import "../css/ResultContent.css";

// 위험도 단계 정의
const RISK_LEVELS = [
  {
    label: "Extreme",
    range: "80-100",
    min: 80,
    color: "#dc2626",
    bg: "#fee2e2",
    desc: "심각한 법적 위험",
  },
  {
    label: "Danger",
    range: "60-79",
    min: 60,
    color: "#f97316",
    bg: "#ffedd5",
    desc: "독소조항 가능성 높음",
  },
  {
    label: "Warning",
    range: "40-59",
    min: 40,
    color: "#f59e0b",
    bg: "#fefce8",
    desc: "수정 검토 필요",
  },
  {
    label: "Caution",
    range: "20-39",
    min: 20,
    color: "#3b82f6",
    bg: "#dbeafe",
    desc: "일부 모호한 표현 있음",
  },
  {
    label: "Safe",
    range: "0-19",
    min: 0,
    color: "#22c55e",
    bg: "#dcfce7",
    desc: "법적으로 안전한 조항",
  },
];

const getRiskInfo = (score) => {
  if (score >= 80) return RISK_LEVELS[0];
  if (score >= 60) return RISK_LEVELS[1];
  if (score >= 40) return RISK_LEVELS[2];
  if (score >= 20) return RISK_LEVELS[3];
  return RISK_LEVELS[4];
};

// result.level 문자열 → 색상/라벨 매핑
const LEVEL_MAP = {
  EXTREME: { color: "#dc2626", label: "Extreme" },
  DANGER:  { color: "#f97316", label: "Danger"  },
  WARNING: { color: "#f59e0b", label: "Warning" },
  CAUTION: { color: "#3b82f6", label: "Caution" },
  SAFE:    { color: "#22c55e", label: "Safe"    },
};

// 바 색상 그라데이션 위치 계산
const getBarGradientPos = (score) => Math.min(100, Math.max(0, score));

const ResultContent = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams();

  const { isDarkMode, refreshHistory, setAlertMessage, setShowAlertDropdown } =
    useApp();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  // PDF 저장용 refs
  const headerRef = useRef(null);
  const rightPanelRef = useRef(null);
  const sectionRefs = useRef([]);

  const dm = isDarkMode;
  // 파일 첨부 여부:
  //  - 방금 분석한 경우 → location.state.mode
  //  - 히스토리에서 불러온 경우 → report.mode (DB에 저장된 값)
  const isFileMode =
    (location.state?.mode ?? report?.mode ?? "text") === "file";

  // 데이터 로드: URL state 또는 API
  useEffect(() => {
    if (id) {
      // 히스토리에서 로드
      fetchHistoryDetail(id);
    } else if (location.state?.report) {
      // 방금 분석한 결과
      setReport(location.state.report);
      refreshHistory(); // 사이드바 히스토리 갱신
    }
  }, [id]);

  const fetchHistoryDetail = async (historyId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem("accessToken");
      const res = await axios.get(
        `${process.env.REACT_APP_API_URL || "http://localhost:8000"}/history/${historyId}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setReport(res.data);
    } catch (err) {
      console.error("히스토리 조회 실패:", err);
      setAlertMessage("이전 결과를 불러오는 데 실패했습니다.");
      setShowAlertDropdown(true);
    } finally {
      setLoading(false);
    }
  };

  // 추천 조항 복사
  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 1500);
    });
  };

  // PDF 저장
  const handleDownloadPdf = async () => {
    if (pdfLoading) return;
    setPdfLoading(true);
    try {
      const [{ default: jsPDF }, { default: html2canvas }] = await Promise.all([
        import("jspdf"),
        import("html2canvas"),
      ]);

      const pdf = new jsPDF("p", "mm", "a4");
      const A4_W = 210;
      const A4_H = 297;
      const MARGIN = 10;
      const usableW = A4_W - MARGIN * 2;
      const usableH = A4_H - MARGIN * 2;

      const captureOpts = {
        scale: 2,
        useCORS: true,
        backgroundColor: dm ? "#0f172a" : "#ffffff",
        logging: false,
      };

      // ── 1페이지: 헤더 ──
      let yOffset = MARGIN;

      if (headerRef.current) {
        const canvas = await html2canvas(headerRef.current, captureOpts);
        const imgH = (canvas.height * usableW) / canvas.width;
        pdf.addImage(canvas.toDataURL("image/png"), "PNG", MARGIN, yOffset, usableW, imgH);
        yOffset += imgH + 6;
      }

      // ── 1페이지: 위험도 패널 ──
      if (rightPanelRef.current) {
        const panelEl = rightPanelRef.current;

        const prevMaxH     = panelEl.style.maxHeight;
        const prevOverflow = panelEl.style.overflowY;
        const prevPosition = panelEl.style.position;
        panelEl.style.maxHeight  = "none";
        panelEl.style.overflowY  = "visible";
        panelEl.style.position   = "static";

        const fullScrollH = panelEl.scrollHeight;
        const canvas = await html2canvas(panelEl, {
          ...captureOpts,
          height: fullScrollH,
          windowHeight: fullScrollH,
        });

        panelEl.style.maxHeight  = prevMaxH;
        panelEl.style.overflowY  = prevOverflow;
        panelEl.style.position   = prevPosition;

        const availH     = A4_H - MARGIN - yOffset;
        const ratio      = canvas.height / canvas.width;
        const hasMissing = !!report?.missing_clause_report;
        const hasChart   = analysisResults.length > 1;

        let finalW, finalH;
        if (hasMissing || hasChart) {
          const fullH = usableW * ratio;
          if (fullH <= availH) { finalW = usableW;  finalH = fullH; }
          else                 { finalH = availH;   finalW = finalH / ratio; }
        } else {
          finalW = usableW * 0.8;
          finalH = finalW * ratio;
        }

        const xOff = MARGIN + (usableW - finalW) / 2;
        pdf.addImage(canvas.toDataURL("image/png"), "PNG", xOff, yOffset, finalW, finalH);
      }

      // ── 2페이지~: 조항별 섹션 카드 ──
      const sections = sectionRefs.current.filter(Boolean);

      for (const section of sections) {
        pdf.addPage();

        const savedWidth    = section.style.width;
        const savedMaxWidth = section.style.maxWidth;
        const savedMinWidth = section.style.minWidth;
        section.style.width    = "700px";
        section.style.maxWidth = "700px";
        section.style.minWidth = "unset";

        await new Promise((r) =>
          requestAnimationFrame(() => requestAnimationFrame(r))
        );

        const fullH = section.scrollHeight;
        const canvas = await html2canvas(section, {
          ...captureOpts,
          height: fullH,
          windowHeight: fullH,
        });

        section.style.width    = savedWidth;
        section.style.maxWidth = savedMaxWidth;
        section.style.minWidth = savedMinWidth;

        const imgH = (canvas.height / canvas.width) * usableW;
        let finalW, finalH;
        if (imgH <= usableH) {
          finalW = usableW;
          finalH = imgH;
        } else {
          finalH = usableH;
          finalW = usableW * (usableH / imgH);
        }

        const xOffset = MARGIN + (usableW - finalW) / 2;
        pdf.addImage(
          canvas.toDataURL("image/png"), "PNG",
          xOffset, MARGIN, finalW, finalH,
        );
      }

      const fileName = (report?.doc_name || "분석리포트").replace(
        /[^a-zA-Z0-9가-힣_\-]/g,
        "_",
      );
      pdf.save(`${fileName}.pdf`);
    } catch (err) {
      console.error("PDF 저장 오류:", err);
    } finally {
      setPdfLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`rc-loading ${dm ? "dark-mode" : "light-mode"}`}>
        <div className="rc-loading-dots">
          <div></div>
          <div></div>
          <div></div>
        </div>
        <p>결과를 불러오는 중입니다...</p>
      </div>
    );
  }

  // 서비스 범위 벗어난 쿼리 처리
  if (report?.status === "invalid_query") {
    return (
      <div className={`rc-empty ${dm ? "dark-mode" : "light-mode"}`}>
        <div className="rc-empty-icon">⚠️</div>
        <p className="rc-empty-text">
          {report.message || "분석할 수 없습니다."}
        </p>
        <p className={`rc-empty-subtitle ${dm ? "dark-mode" : "light-mode"}`}>
          근로계약서 조항이나 노동법 관련 질문만 분석 가능합니다.
        </p>
        <button className="rc-empty-btn" onClick={() => navigate("/")}>
          새 분석 시작
        </button>
      </div>
    );
  }

  if (!report) {
    return (
      <div className={`rc-empty ${dm ? "dark-mode" : "light-mode"}`}>
        <div className="rc-empty-icon">📄</div>
        <p className="rc-empty-text">분석 결과가 없습니다.</p>
        <button className="rc-empty-btn" onClick={() => navigate("/")}>
          새 분석 시작
        </button>
      </div>
    );
  }

  const score = report.total_risk_score ?? 0;
  const riskInfo = getRiskInfo(score);
  const results = report.results || [];
  const analysisResults = results.filter((r) => r.result_type === "ANALYSIS");
  const generalResults = results.filter((r) => r.result_type === "GENERAL");

  return (
    <div className={`rc-wrap ${dm ? "dark-mode" : "light-mode"}`}>
      {/* 메인 + 우측 패널 레이아웃 */}
      <div className="rc-layout">
        {/* 좌측 메인 */}
        <div className="rc-main">
          {/* 리포트 제목 */}
          <div className="rc-report-header" ref={headerRef}>
            <div className="rc-report-logo">
              <div className="rc-logo-dot"></div>
            </div>
            <div style={{ flex: 1 }}>
              <h2
                className={`rc-report-title ${dm ? "dark-mode" : "light-mode"}`}
              >
                계약 조항 분석 리포트
              </h2>
              {report.analyzed_at && (
                <p
                  className={`rc-report-date ${dm ? "dark-mode" : "light-mode"}`}
                >
                  {new Date(
                    report.analyzed_at.replace(" ", "T") + "Z",
                  ).toLocaleString("ko-KR")}
                </p>
              )}
            </div>
            {/* PDF 저장 버튼 */}
            {analysisResults.length > 0 && (
              <button
                onClick={handleDownloadPdf}
                disabled={pdfLoading}
                className={`rc-pdf-btn ${dm ? "dark-mode" : "light-mode"}`}
              >
                {pdfLoading ? <>⏳ 저장 중...</> : <>📄 PDF 저장</>}
              </button>
            )}
          </div>

          {/* 일반 질문 답변 영역 */}
          {generalResults.map((result, idx) => (
            <div
              key={idx}
              ref={(el) => (sectionRefs.current[idx] = el)}
              className={`rc-section ${dm ? "dark-mode" : "light-mode"}`}
            >
              <div className="rc-section-label general">
                <span>💬</span> 질문 답변
              </div>
              <div
                className={`rc-clause-box ${dm ? "dark-mode" : "light-mode"}`}
              >
                <p
                  className={`rc-clause-text ${dm ? "dark-mode" : "light-mode"}`}
                >
                  "{result.clause}"
                </p>
              </div>
              <div
                className={`rc-answer-box ${dm ? "dark-mode" : "light-mode"}`}
              >
                <p
                  className={`rc-answer-text ${dm ? "dark-mode" : "light-mode"}`}
                >
                  {result.proposed_text || result.reason}
                </p>
              </div>
              {result.tags?.length > 0 && (
                <div className="rc-tags">
                  {result.tags.map((t, i) => (
                    <span
                      key={i}
                      className={`rc-tag ${dm ? "dark-mode" : "light-mode"}`}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* 분석 결과 영역 */}
          {analysisResults.map((result, idx) => {
            const isSafe = result.level === "SAFE";
            const sectionIdx = generalResults.length + idx;
            const lvl = LEVEL_MAP[result.level] || LEVEL_MAP.SAFE;
            return (
              <div
                key={idx}
                ref={(el) => (sectionRefs.current[sectionIdx] = el)}
                className={`rc-section ${dm ? "dark-mode" : "light-mode"}`}
              >
                {/* 섹션 헤더: 번호 + 위험 레벨 뱃지 */}
                <div className="rc-section-header">
                  <div className="rc-section-num">🔍검토 요청 질문</div>
                  <div className="rc-level-badge-wrap">
                    <span
                      className="rc-level-badge"
                      style={{ background: lvl.color }}
                    >
                      {lvl.label}
                    </span>
                    <span
                      className="rc-level-score"
                      style={{ color: lvl.color }}
                    >
                      {result.score?.toFixed(1)}점
                    </span>
                  </div>
                </div>
                <div
                  className={`rc-clause-box ${dm ? "dark-mode" : "light-mode"}`}
                >
                  <p
                    className={`rc-clause-label ${dm ? "dark-mode" : "light-mode"}`}
                  ></p>
                  <p
                    className={`rc-clause-text ${dm ? "dark-mode" : "light-mode"}`}
                  >
                    "{result.clause}"
                  </p>
                </div>

                {/* ② 분석 리포트 */}
                <div className="rc-section-num">⚖️ 분석 리포트 </div>

                {!isSafe ? (
                  /* 위험 조항 */
                  <div
                    className={`rc-danger-box ${dm ? "dark-mode" : "light-mode"}`}
                  >
                    <div className="rc-danger-header">
                      <span className="rc-danger-icon">⚠️</span>
                      <span className="rc-danger-label">
                        [주의] 위험 요소 발견
                      </span>
                    </div>
                    <p
                      className={`rc-reason-text ${dm ? "dark-mode" : "light-mode"}`}
                    >
                      {result.reason}
                    </p>

                    {/* 관련 법령 및 판례 */}
                    {(result.legal_basis?.length > 0 ||
                      result.precedents?.length > 0) && (
                      <div
                        className={`rc-evidence-box ${dm ? "dark-mode" : "light-mode"}`}
                      >
                        <div className="rc-evidence-label">
                          📖 관련 법령 및 판례 근거
                        </div>
                        {result.legal_basis?.map((law, i) => (
                          <div
                            key={i}
                            className={`rc-evidence-item ${dm ? "dark-mode" : "light-mode"}`}
                          >
                            <p className="rc-evidence-title">
                              [{law.title || law.keyword}]
                            </p>
                            <p
                              className={`rc-evidence-content ${dm ? "dark-mode" : "light-mode"}`}
                            >
                              {law.summary || law.content}
                            </p>
                          </div>
                        ))}
                        {result.precedents?.map((pre, i) => (
                          <div
                            key={i}
                            className={`rc-evidence-item ${dm ? "dark-mode" : "light-mode"}`}
                          >
                            <p className="rc-evidence-title">
                              [관련 판례: {pre.case_number || pre.title}]
                            </p>
                            <p
                              className={`rc-evidence-content ${dm ? "dark-mode" : "light-mode"}`}
                            >
                              {pre.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* 추천 표준 조항 */}
                    {result.proposed_text && (
                      <div
                        className={`rc-proposed-box ${dm ? "dark-mode" : "light-mode"}`}
                      >
                        <div className="rc-proposed-header">
                          <span>✅ 추천 표준 조항 (수정안)</span>
                          <button
                            className={`rc-copy-btn ${dm ? "dark-mode" : "light-mode"}`}
                            onClick={() =>
                              handleCopy(result.proposed_text, idx)
                            }
                          >
                            {copiedIdx === idx ? "✓ 복사됨" : "📋 복사하기"}
                          </button>
                        </div>
                        <p
                          className={`rc-proposed-text ${dm ? "dark-mode" : "light-mode"}`}
                        >
                          "{result.proposed_text}"
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  /* 안전 조항 */
                  <div
                    className={`rc-safe-box ${dm ? "dark-mode" : "light-mode"}`}
                  >
                    <div className="rc-safe-header">
                      <span className="rc-safe-icon">✅</span>
                      <span className="rc-safe-label">
                        안전 조항으로 판별되었습니다.
                      </span>
                    </div>
                    <p
                      className={`rc-reason-text ${dm ? "dark-mode" : "light-mode"}`}
                    >
                      {result.reason}
                    </p>
                    {result.proposed_text && report.missing_clause_report && (
                      <p
                        className={`rc-reason-text ${dm ? "dark-mode" : "light-mode"}`}
                        style={{ marginTop: "0.75rem" }}
                      >
                        {result.proposed_text}
                      </p>
                    )}
                  </div>
                )}

                {/* ⑤ 태그 */}
                {result.tags?.length > 0 && (
                  <div className="rc-tags">
                    {result.tags.map((t, i) => (
                      <span
                        key={i}
                        className={`rc-tag ${dm ? "dark-mode" : "light-mode"}`}
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* 우측 고정 패널: ANALYSIS 결과 있을 때만 표시 */}
        {analysisResults.length > 0 && (
          <aside
            ref={rightPanelRef}
            className={`rc-right-panel ${dm ? "dark-mode" : "light-mode"}`}
          >
            {/* ③ 위험도 시각화 */}
            <div className="rc-risk-card">
              {/* SAFE ↔ DANGER 바 */}
              <div className="rc-risk-bar-wrap">
                <span
                  className={`rc-bar-label ${dm ? "dark-mode" : "light-mode"}`}
                >
                  SAFE
                </span>
                <div className="rc-risk-bar">
                  <div
                    className="rc-risk-bar-fill"
                    style={{
                      width: `${getBarGradientPos(score)}%`,
                      backgroundColor: riskInfo.color,
                    }}
                  ></div>
                </div>
                <span
                  className={`rc-bar-label ${dm ? "dark-mode" : "light-mode"}`}
                >
                  DANGER
                </span>
              </div>

              {/* 점수 */}
              <div className="rc-score-wrap">
                {/* 다수 조항일 때 평균 뱃지 생성 */}
                {analysisResults.length > 1 && (
                  <div className="rc-avg-badge">
                    📊 전체 {analysisResults.length}개 조항 평균 점수
                  </div>
                )}
                <span
                  className="rc-score-value"
                  style={{ color: riskInfo.color }}
                >
                  {score.toFixed(2)}
                </span>
                <p
                  className={`rc-score-desc ${dm ? "dark-mode" : "light-mode"}`}
                >
                  {isFileMode ? "현재 계약서는" : "현재 조항은"}{" "}
                  <strong style={{ color: riskInfo.color }}>
                    {riskInfo.label}
                  </strong>{" "}
                  단계입니다.
                  {analysisResults.length > 1 && (
                    <span
                      className={`rc-avg-note ${dm ? "dark-mode" : "light-mode"}`}
                    >
                      전체 조항의 종합 위험도 기준
                    </span>
                  )}
                </p>
              </div>

              {/* 위험도 가이드 */}
              {analysisResults.length >= 2 ? (
                /* 2개 이상: 세그먼트 바 + 현재 단계 카드 */
                <div className={`rc-risk-guide ${dm ? "dark-mode" : "light-mode"}`}>
                  <p className="rc-guide-title">위험도 가이드 영역</p>
                  {/* 세그먼트 칩 5단계 */}
                  <div className="rc-segment-bar">
                    {RISK_LEVELS.map((lvl) => {
                      const active = riskInfo.label === lvl.label;
                      return (
                        <div
                          key={lvl.label}
                          className={`rc-segment-chip ${active ? "active" : ""} ${dm ? "dark-mode" : "light-mode"}`}
                          style={active ? { backgroundColor: lvl.color } : {}}
                        >
                          {lvl.label}
                        </div>
                      );
                    })}
                  </div>
                  {/* 현재 단계 상세 카드 */}
                  <div
                    className={`rc-segment-card ${dm ? "dark-mode" : "light-mode"}`}
                    style={{ borderLeftColor: riskInfo.color }}
                  >
                    <div className="rc-segment-card-header">
                      <span
                        className="rc-segment-card-dot"
                        style={{ background: riskInfo.color }}
                      ></span>
                      <span
                        className="rc-segment-card-label"
                        style={{ color: riskInfo.color }}
                      >
                        {riskInfo.label}
                      </span>
                      <span className={`rc-segment-card-range ${dm ? "dark-mode" : "light-mode"}`}>
                        {riskInfo.range}
                      </span>
                    </div>
                    <p className={`rc-segment-card-desc ${dm ? "dark-mode" : "light-mode"}`}>
                      {riskInfo.desc}
                    </p>
                  </div>
                </div>
              ) : (
                /* 1개: 기존 세로 가이드 유지 */
                <div className={`rc-risk-guide ${dm ? "dark-mode" : "light-mode"}`}>
                  <p className="rc-guide-title">위험도 가이드 영역</p>
                  {RISK_LEVELS.map((lvl) => {
                    const active = riskInfo.label === lvl.label;
                    return (
                      <div
                        key={lvl.label}
                        className={`rc-guide-row ${active ? "active" : ""}`}
                      >
                        {active && (
                          <span
                            className="rc-guide-dot"
                            style={{ background: lvl.color }}
                          ></span>
                        )}
                        <div className="rc-guide-label-wrap">
                          <span
                            className={`rc-guide-label ${active ? "active" : ""} ${dm ? "dark-mode" : "light-mode"}`}
                            style={active ? { color: lvl.color, fontWeight: 700 } : {}}
                          >
                            {lvl.label}
                          </span>
                          <span
                            className={`rc-guide-desc ${active ? "active" : ""} ${dm ? "dark-mode" : "light-mode"}`}
                            style={active ? { color: lvl.color } : {}}
                          >
                            {lvl.desc}
                          </span>
                        </div>
                        <span className={`rc-guide-range ${dm ? "dark-mode" : "light-mode"}`}>
                          {lvl.range}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* ④ 조항별 위험도 차트 (2개 이상일 때만) */}
            {analysisResults.length > 1 && (
              <div className={`rc-chart-card ${dm ? "dark-mode" : "light-mode"}`}>
                <p className="rc-chart-title">📊 조항별 위험도</p>
                <ResponsiveContainer width="100%" height={130}>
                  <BarChart
                    data={analysisResults.map((r, i) => ({
                      name: `조항 ${i + 1}`,
                      score: Math.round(r.score),
                      color: (LEVEL_MAP[r.level] || LEVEL_MAP.SAFE).color,
                    }))}
                    margin={{ top: 18, right: 4, left: -24, bottom: 0 }}
                    barCategoryGap="30%"
                  >
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 10, fill: dm ? "#94a3b8" : "#64748b" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      domain={[0, 100]}
                      tick={{ fontSize: 10, fill: dm ? "#94a3b8" : "#64748b" }}
                      axisLine={false}
                      tickLine={false}
                      tickCount={3}
                    />
                    <Tooltip
                      cursor={{ fill: dm ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)" }}
                      contentStyle={{
                        background: dm ? "#1e293b" : "#fff",
                        border: `1px solid ${dm ? "rgba(255,255,255,0.08)" : "#e2e8f0"}`,
                        borderRadius: "0.5rem",
                        fontSize: "0.75rem",
                      }}
                      formatter={(value) => [`${value}점`, "위험도"]}
                    />
                    <Bar
                      dataKey="score"
                      radius={[4, 4, 0, 0]}
                      label={(props) => {
                        const { x, y, width, value, index } = props;
                        const color = (LEVEL_MAP[analysisResults[index]?.level] || LEVEL_MAP.SAFE).color;
                        return (
                          <text
                            x={x + width / 2}
                            y={y - 4}
                            textAnchor="middle"
                            fill={color}
                            fontSize={10}
                            fontWeight={700}
                          >
                            {value}
                          </text>
                        );
                      }}
                    >
                      {analysisResults.map((r, i) => (
                        <Cell
                          key={i}
                          fill={(LEVEL_MAP[r.level] || LEVEL_MAP.SAFE).color}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* ⑤ 계약서 누락항목 */}
            {report.missing_clause_report && (
              <div
                className={`rc-missing-card ${dm ? "dark-mode" : "light-mode"}`}
              >
                <div className="rc-missing-body">
                  <p className="rc-missing-warning">⚠️ 계약서 누락 항목 주의</p>
                  <p
                    className={`rc-missing-text ${dm ? "dark-mode" : "light-mode"}`}
                  >
                    {report.missing_clause_report}
                  </p>
                </div>
              </div>
            )}
          </aside>
        )}
      </div>
    </div>
  );
};

export default ResultContent;
