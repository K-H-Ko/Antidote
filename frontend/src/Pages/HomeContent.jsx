import React, { useRef, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  FiSearch,
  FiFileText,
  FiImage,
  FiX,
  FiAlertCircle,
} from "react-icons/fi";
import { PieChart, Pie, Cell } from "recharts";
import { useApp } from "../context/AppContext";
import "../css/HomeContent.css";

const PIPELINE_STEPS = [
  { icon: "📄", label: "분석 요청" },
  { icon: "🔍", label: "독소조항 분석" },
  { icon: "📚", label: "법령/판례 검색" },
  { icon: "⚖️", label: "AI 정밀검증" },
  { icon: "📋", label: "결과 리포트" },
];

const MAX_CHARS = 500;

const HomeContent = () => {
  const navigate = useNavigate();
  const pdfInputRef = useRef(null);
  const imageInputRef = useRef(null);

  const { isDarkMode, setAlertMessage, setShowAlertDropdown } = useApp();

  const [textInput, setTextInput] = useState("");
  const [uploadedFile, setUploadedFile] = useState(null);
  const [chartPct, setChartPct] = useState(0);
  const [isDragging, setIsDragging] = useState(false);

  // 카운터 애니메이션 (0 → 70.8%)
  useEffect(() => {
    const TARGET = 70.8;
    const DURATION = 1600;
    const startTime = performance.now();

    const tick = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / DURATION, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setChartPct(eased * TARGET);
      if (progress < 1) requestAnimationFrame(tick);
    };

    const raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  // 파이차트 데이터
  const riskData = [
    { name: "30인 미만 사업장", value: 70.8, fill: "#dc2626" },
    { name: "기타", value: 29.2, fill: "#e5e7eb" },
  ];

  // 파일 유효성 검사 및 등록 (버튼 + 드래그 공용)
  const applyFile = (file) => {
    if (!file) return;
    const allowed = [".pdf", ".png", ".jpg", ".jpeg", ".jfif"];
    const name = file.name.toLowerCase();
    if (!allowed.some((ext) => name.endsWith(ext))) {
      setAlertMessage("지원하는 파일 형식: PDF, PNG, JPG, JPEG, JFIF");
      setShowAlertDropdown(true);
      return;
    }
    setUploadedFile(file);
    setTextInput("");
  };

  // 버튼으로 파일 선택
  const handleFileUpload = (e) => {
    applyFile(e.target.files[0]);
    // 같은 파일 재선택 가능하도록 value 초기화
    e.target.value = "";
  };

  // 드래그 이벤트 핸들러
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!uploadedFile) setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (uploadedFile) return; // 이미 파일 있으면 무시
    const file = e.dataTransfer.files[0]; // 1개만 사용
    applyFile(file);
  };

  // 분석 시작
  const handleAnalyze = () => {
    if (!textInput.trim() && !uploadedFile) {
      setAlertMessage("분석할 내용을 입력하거나 파일을 업로드해주세요.");
      setShowAlertDropdown(true);
      return;
    }

    // 질문 내용 또는 파일명.확장자 10글자 까지 title 로 저장
    let docName;
    if (uploadedFile) {
      const fileName = uploadedFile.name;
      docName =
        fileName.length > 15 ? fileName.substring(0, 15) + "..." : fileName;
    } else {
      const text = textInput.substring(0, 15);
      docName = textInput.length > 15 ? text + "..." : text;
    }

    navigate("/loading", {
      state: {
        content: textInput,
        file: uploadedFile,
        docName: docName,
        mode: uploadedFile ? "file" : "text",
      },
    });
  };

  const dm = isDarkMode;

  return (
    <div className={`hc-wrap ${dm ? "dark-mode" : "light-mode"}`}>
      <div className="hc-content">
        {/* 타이틀 */}
        <div className="hc-title-section">
          <h1 className={`hc-main-title ${dm ? "dark-mode" : "light-mode"}`}>
            당신의 권리를 보호합니다.
          </h1>
          <p className={`hc-subtitle ${dm ? "dark-mode" : "light-mode"}`}>
            법률 전문가가 검토한 듯한 정밀도. 근로계약서 속 숨겨진 리스크를
            찾아드립니다.
          </p>
        </div>

        {/* 입력 영역 */}
        <div className="hc-input-section">
          <div
            className={`hc-input-card ${dm ? "dark-mode" : "light-mode"} ${isDragging ? "dragging" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {/* 드래그 오버레이 */}
            {isDragging && (
              <div
                className={`hc-drag-overlay ${dm ? "dark-mode" : "light-mode"}`}
              >
                <span className="hc-drag-icon">📂</span>
                <span className="hc-drag-text">파일을 여기에 놓으세요</span>
              </div>
            )}

            <textarea
              value={uploadedFile ? "" : textInput}
              onChange={(e) => {
                if (e.target.value.length <= MAX_CHARS) {
                  setTextInput(e.target.value);
                }
              }}
              disabled={!!uploadedFile}
              placeholder={
                uploadedFile
                  ? `📎 ${uploadedFile.name}`
                  : "계약서 조항이나 근로법 관련 질문을 입력하세요...\n\n(파일 첨부시 PDF/이미지 파일 해당 영역에 드래그로 첨부 가능합니다.)"
              }
              className={`hc-textarea ${dm ? "dark-mode" : "light-mode"}`}
            />
            <div className="hc-input-actions">
              <button
                onClick={() => pdfInputRef.current?.click()}
                disabled={!!textInput.trim() || !!uploadedFile}
                className={`hc-file-btn ${dm ? "dark-mode" : "light-mode"}`}
              >
                <FiFileText size={16} /> PDF
              </button>
              <button
                onClick={() => imageInputRef.current?.click()}
                disabled={!!textInput.trim() || !!uploadedFile}
                className={`hc-file-btn ${dm ? "dark-mode" : "light-mode"}`}
              >
                <FiImage size={16} /> Image
              </button>
              <input
                ref={pdfInputRef}
                type="file"
                onChange={handleFileUpload}
                accept=".pdf"
                style={{ display: "none" }}
              />
              <input
                ref={imageInputRef}
                type="file"
                onChange={handleFileUpload}
                accept=".png,.jpg,.jpeg,.jfif"
                style={{ display: "none" }}
              />
              {uploadedFile && (
                <>
                  <button
                    onClick={() => setUploadedFile(null)}
                    className={`hc-file-clear ${dm ? "dark-mode" : "light-mode"}`}
                  >
                    <FiX size={14} />
                  </button>
                  <span
                    className={`hc-file-limit-msg ${dm ? "dark-mode" : "light-mode"}`}
                  >
                    (정밀 분석을 위해 계약서 파일은 1개만 첨부 가능합니다.)
                  </span>
                </>
              )}
              {/* 카운터 + 분석 버튼을 묶어서 오른쪽 정렬 */}
              <div className="hc-right-actions">
                {!uploadedFile && (
                  <span
                    className={`hc-char-count ${
                      textInput.length >= 450
                        ? "danger"
                        : textInput.length >= 400
                          ? "near-danger"
                          : textInput.length >= 250
                            ? "warn"
                            : textInput.length > 0
                              ? dm ? "active-dark" : "active"
                              : dm ? "dark-mode" : "light-mode"
                    }`}
                  >
                    {textInput.length} / {MAX_CHARS}
                  </span>
                )}
                <button onClick={handleAnalyze} className="hc-analyze-btn">
                  <FiSearch size={16} />
                  분석
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 박스 4개 그리드 */}
        <div className="hc-grid">
          {/* Box 1: 서비스 강점 */}
          <div className={`hc-box ${dm ? "dark-mode" : "light-mode"}`}>
            <div className="hc-box-badge blue">서비스 핵심 강점</div>
            <h3 className="hc-box-title">
              보이지 않는 독소조항, AI가 당신의 권리를 보호합니다.
            </h3>
            <p className={`hc-box-desc ${dm ? "dark-mode" : "light-mode"}`}>
              국가법령정보센터의 근로기준법 위반{" "}
              <strong>실제 판례 약 2,400건과 근로기준법</strong>의
              <br /> 정확한 근거자료를 통해 근로계약서 속 숨겨진 리스크를 찾아
              최적의 솔루션을 제공해 드립니다.
            </p>
            <div className="hc-tags">
              {["#정보비대칭해소", "#사전방어", "#협상력강화"].map((t) => (
                <span key={t} className="hc-tag blue">
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* Box 2: 보안 */}
          <div className={`hc-box hc-box-blue ${dm ? "dark-mode" : ""}`}>
            <div className="hc-security-icon">🛡️</div>
            <h3 className="hc-box-title white">
              데이터는 오직 분석을 위해서만 존재합니다.
            </h3>
            <p className="hc-box-desc white">
              입력하신 모든 파일은 서버에 저장되지 않으며, 분석 완료 즉시
              <br />
              안전하게 메모리에서 소멸됩니다.
            </p>
            <div className="hc-tags">
              {["No Data Retention", "End-to-End Encryption"].map((b) => (
                <span key={b} className="hc-tag white">
                  ✓ {b}
                </span>
              ))}
            </div>
          </div>

          {/* Box 3: 리스크 현실 */}
          <div
            className={`hc-box hc-box-risk ${dm ? "dark-mode" : "light-mode"}`}
          >
            <h3 className="hc-box-title">
              현실의 위험도: <span className="hc-b3-point">70.8%</span> 사각지대
            </h3>
            <div className="hc-risk-spacer" />
            <div className="hc-chart-wrap">
              <PieChart width={130} height={130}>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={60}
                  dataKey="value"
                  startAngle={90}
                  endAngle={-270}
                >
                  {riskData.map((e, i) => (
                    <Cell key={i} fill={e.fill} />
                  ))}
                </Pie>
              </PieChart>
              <div className="hc-chart-label">
                <div className="hc-chart-pct">{chartPct.toFixed(1)}%</div>
                <div
                  className={`hc-chart-sub ${dm ? "dark-mode" : "light-mode"}`}
                >
                  30인 미만 사업장
                </div>
              </div>
            </div>
            <div className="hc-risk-spacer" />
            <p
              className={`hc-box-desc ${dm ? "dark-mode" : "light-mode"}`}
              style={{ margin: 0 }}
            >
              체불 상담의 <span className="hc-b3-point">70.8%</span>가 발생하는
              '사각지대'. 조항 하나가 당신의 생계와 직결됩니다.
            </p>
          </div>

          {/* Box 4: 기술 스택 */}
          <div className={`hc-box hc-box-dark ${dm ? "dark-mode" : ""}`}>
            <h3 className="hc-box-title white">기술 스택 &amp; 전문성</h3>
            <div className="hc-tech-list">
              {[
                {
                  label: "Detection",
                  desc: "Deep Learning 기반 독소조항 AI 정밀 스캐닝",
                },
                {
                  label: "Retrieval",
                  desc: "Semantic Search를 통한 관련 판례 및 법령 실시간 대조",
                },
                {
                  label: "Reasoning",
                  desc: "Multi-modal LLM 아키텍처를 통한 법률 논리 검증",
                },
              ].map((t) => (
                <div key={t.label} className="hc-tech-item">
                  <span className="hc-tech-label">{t.label}</span>
                  <span className="hc-tech-desc">{t.desc}</span>
                </div>
              ))}
            </div>

            {/* 분석 파이프라인 흐름 */}
            <div className="hc-pipeline">
              <p className="hc-pipeline-title">분석 과정</p>
              <div className="hc-pipeline-flow">
                {PIPELINE_STEPS.map((step, i) => (
                  <React.Fragment key={i}>
                    <div className="hc-pipe-step">
                      <div
                        className="hc-pipe-icon"
                        style={{ animationDelay: `${i * 0.45}s` }}
                      >
                        {step.icon}
                      </div>
                      <div className="hc-pipe-label">{step.label}</div>
                    </div>
                    {i < PIPELINE_STEPS.length - 1 && (
                      <div
                        className="hc-pipe-arrow"
                        style={{ animationDelay: `${i * 0.45 + 0.22}s` }}
                      >
                        ›
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomeContent;
