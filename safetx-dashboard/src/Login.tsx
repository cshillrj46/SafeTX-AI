// File: src/Login.tsx
import { useState } from "react";
import { ApiError, login, register } from "./api";

interface LoginProps {
  onLoggedIn: () => void;
}

export default function Login({ onLoggedIn }: LoginProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await register(username, email, password);
      }
      await login(username, password);
      onLoggedIn();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center text-white">
      <h2 className="text-2xl font-bold mb-4">
        {mode === "login" ? "Login" : "Create Account"}
      </h2>
      <div className="w-full max-w-xs">
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full p-2 mb-2 rounded bg-gray-800 text-white border border-gray-600"
        />
        {mode === "register" && (
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-2 mb-2 rounded bg-gray-800 text-white border border-gray-600"
          />
        )}
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-2 mb-4 rounded bg-gray-800 text-white border border-gray-600"
        />
        <button
          onClick={handleSubmit}
          disabled={loading || !username || !password || (mode === "register" && !email)}
          className="w-full p-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-bold disabled:opacity-50"
        >
          {loading ? "Please wait..." : mode === "login" ? "Log In" : "Register & Log In"}
        </button>
        {error && <p className="mt-2 text-red-500 text-sm text-center">{error}</p>}
        <p className="mt-4 text-sm text-center text-gray-400">
          {mode === "login" ? "No account yet?" : "Already have an account?"}{" "}
          <button
            onClick={() => {
              setError(null);
              setMode(mode === "login" ? "register" : "login");
            }}
            className="text-blue-400 hover:underline"
          >
            {mode === "login" ? "Register" : "Log in"}
          </button>
        </p>
      </div>
    </div>
  );
}
