// File: src/TransactionHistory.tsx
import { useEffect, useState } from "react";
import { ApiError, getHistory, type Transaction } from "./api";

export default function TransactionHistory() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    getHistory(page, 10)
      .then((data) => {
        setTransactions(data.items);
        setTotalPages(Math.max(1, data.total_pages));
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load history"));
  }, [page]);

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return isNaN(date.getTime()) ? "Invalid Date" : date.toLocaleString();
  };

  return (
    <div className="text-white p-4">
      <h2 className="text-2xl font-bold text-center mb-4">Transaction History</h2>

      {error && <p className="text-red-500 text-sm text-center mb-4">{error}</p>}

      <div className="max-h-[400px] overflow-y-auto rounded shadow-inner">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-700 text-white sticky top-0 z-10">
            <tr>
              <th className="p-2">ID</th>
              <th className="p-2">Sender</th>
              <th className="p-2">Recipient</th>
              <th className="p-2">Amount (ETH)</th>
              <th className="p-2">Risk</th>
              <th className="p-2">Timestamp</th>
            </tr>
          </thead>
          <tbody className="bg-slate-800">
            {transactions.map((tx) => (
              <tr key={tx.id} className="border-t border-gray-700 hover:bg-slate-700 transition-colors">
                <td className="p-2">{tx.id}</td>
                <td className="p-2 truncate max-w-xs">{tx.sender}</td>
                <td className="p-2 truncate max-w-xs">{tx.recipient}</td>
                <td className="p-2">{tx.amount_eth.toFixed(5)}</td>
                <td
                  className={`p-2 font-semibold ${
                    tx.risk === "high-risk"
                      ? "text-red-500"
                      : tx.risk === "suspicious"
                      ? "text-yellow-400"
                      : "text-green-500"
                  }`}
                >
                  {tx.risk.toUpperCase()}
                </td>
                <td className="p-2">{formatDate(tx.timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center mt-4">
        <button
          className="bg-slate-700 hover:bg-slate-600 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
        >
          Previous
        </button>
        <span className="text-white">
          Page {page} of {totalPages}
        </span>
        <button
          className="bg-slate-700 hover:bg-slate-600 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
}
