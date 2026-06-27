// File: src/TransactionAnalyzer.tsx
import { useState } from "react";
import { ApiError, analyzeTransaction } from "./api";

export default function TransactionAnalyzer() {
  const [sender, setSender] = useState("");
  const [recipient, setRecipient] = useState("");
  const [amount, setAmount] = useState("");
  const [risk, setRisk] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setRisk(null);

    try {
      // O backend retorna o risco como string simples (ex: "high-risk"),
      // não como { risk: "..." } — antes este bug fazia o resultado nunca
      // aparecer na tela.
      const result = await analyzeTransaction({
        sender,
        recipient,
        amount_eth: parseFloat(amount),
      });
      setRisk(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to analyze transaction");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center text-white">
      <h2 className="text-2xl font-bold mb-4">Transaction Analyzer</h2>
      <div className="w-full max-w-xs">
        <input
          type="text"
          placeholder="Sender Address"
          value={sender}
          onChange={(e) => setSender(e.target.value)}
          className="w-full p-2 mb-2 rounded bg-gray-800 text-white border border-gray-600"
        />
        <input
          type="text"
          placeholder="Recipient Address"
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
          className="w-full p-2 mb-2 rounded bg-gray-800 text-white border border-gray-600"
        />
        <input
          type="number"
          placeholder="Amount (ETH)"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full p-2 mb-4 rounded bg-gray-800 text-white border border-gray-600"
        />
        <button
          onClick={handleAnalyze}
          className="w-full p-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-bold disabled:opacity-50"
          disabled={loading || !sender || !recipient || !amount}
        >
          {loading ? "Analyzing..." : "Analyze Transaction"}
        </button>
        {risk && (
          <p className="mt-4 text-lg font-semibold text-center">
            Risk Level: <span className="capitalize text-yellow-400">{risk}</span>
          </p>
        )}
        {error && <p className="mt-2 text-red-500 text-sm text-center">{error}</p>}
      </div>
    </div>
  );
}
