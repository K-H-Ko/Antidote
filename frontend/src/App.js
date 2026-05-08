import { BrowserRouter, Routes, Route } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AppProvider } from "./context/AppContext";
import MainLayout from "./Pages/MainLayout";
import HomeContent from "./Pages/HomeContent";
import LoadingPage from "./Pages/LoadingPage";
import ResultContent from "./Pages/ResultContent";

function App() {
  return (
    <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID || ""}>
      <AppProvider>
        <BrowserRouter>
          <Routes>
            {/* 공통 레이아웃 (헤더 + 사이드바) 안에서 중앙 콘텐츠만 교체 */}
            <Route path="/" element={<MainLayout />}>
              <Route index element={<HomeContent />} />
              <Route path="loading" element={<LoadingPage />} />
              <Route path="result" element={<ResultContent />} />
              <Route path="result/:id" element={<ResultContent />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AppProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
