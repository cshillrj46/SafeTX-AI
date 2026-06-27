// src/App.tsx
import { useState } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  NavLink,
  Navigate
} from "react-router-dom";
import TransactionAnalyzer from "./TransactionAnalyzer";
import TransactionHistory from "./TransactionHistory";
import ReclassificationForm from "./ReclassificationForm";
import TracePage from "./TracePage";
import Login from "./Login";
import { clearToken, getToken } from "./api";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(() => Boolean(getToken()));

  const handleLogout = () => {
    clearToken();
    setIsLoggedIn(false);
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-black text-white p-4 flex items-center justify-center">
        <Login onLoggedIn={() => setIsLoggedIn(true)} />
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-black text-white p-4">
        <header className="text-center mb-8">
          <h1 className="text-5xl font-extrabold mb-4">
            <span className="text-white">$afe</span>
            <span className="text-blue-500">TX</span>
          </h1>
          <nav className="flex justify-center gap-4 items-center">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `text-white font-semibold ${isActive ? 'underline text-blue-400' : 'hover:text-blue-300'}`
              }
              end
            >
              Analyzer
            </NavLink>
            <NavLink
              to="/history"
              className={({ isActive }) =>
                `text-white font-semibold ${isActive ? 'underline text-blue-400' : 'hover:text-blue-300'}`
              }
            >
              History
            </NavLink>
            <NavLink
              to="/reclassify"
              className={({ isActive }) =>
                `text-white font-semibold ${isActive ? 'underline text-blue-400' : 'hover:text-blue-300'}`
              }
            >
              Manual Classification
            </NavLink>
            <NavLink
              to="/trace"
              className={({ isActive }) =>
                `text-white font-semibold ${isActive ? 'underline text-blue-400' : 'hover:text-blue-300'}`
              }
            >
              Rastreamento
            </NavLink>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-400 hover:text-red-400 ml-4"
            >
              Log out
            </button>
          </nav>
        </header>

        <main>
          <Routes>
            <Route path="/" element={<TransactionAnalyzer />} />
            <Route path="/history" element={<TransactionHistory />} />
            <Route path="/reclassify" element={<ReclassificationForm />} />
            <Route path="/trace" element={<TracePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
