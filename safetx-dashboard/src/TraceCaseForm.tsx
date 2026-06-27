// File: src/TraceCaseForm.tsx
import { useState } from "react";
import { ApiError, createTrace } from "./api";

interface TraceCaseFormProps {
  onCreated: (jobId: number) => void;
}

export default function TraceCaseForm({ onCreated }: TraceCaseFormProps) {
  const [address, setAddress] = useState("");
  const [maxHops, setMaxHops] = useState(2);
  const [caseReference, setCaseReference] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      const result = await createTrace({
        address: address.trim(),
        chain: "ethereum",
        max_hops: maxHops,
        case_reference: caseReference.trim() || undefined,
      });
      onCreated(result.job_id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Falha ao abrir o rastreamento");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="text-white max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-1 text-center">Novo Rastreamento</h2>
      <p className="text-sm text-gray-400 text-center mb-6">
        Hoje só Ethereum mainnet. Segue ETH nativo e stablecoins (USDT, USDC, DAI).
      </p>

      <label className="block text-sm text-gray-300 mb-1">Endereço investigado</label>
      <input
        type="text"
        placeholder="0x..."
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        className="w-full p-2 mb-4 rounded bg-gray-800 border border-gray-600 font-mono text-sm"
      />

      <label className="block text-sm text-gray-300 mb-1">Profundidade (hops)</label>
      <select
        value={maxHops}
        onChange={(e) => setMaxHops(Number(e.target.value))}
        className="w-full p-2 mb-4 rounded bg-gray-800 border border-gray-600"
      >
        <option value={1}>1 hop — mais rápido</option>
        <option value={2}>2 hops — recomendado</option>
        <option value={3}>3 hops</option>
        <option value={4}>4 hops — mais lento</option>
      </select>

      <label className="block text-sm text-gray-300 mb-1">Referência do caso (opcional)</label>
      <input
        type="text"
        placeholder="Ex: Inquérito 2026/0451 - golpe de investimento"
        value={caseReference}
        onChange={(e) => setCaseReference(e.target.value)}
        className="w-full p-2 mb-6 rounded bg-gray-800 border border-gray-600"
      />

      <button
        onClick={handleSubmit}
        disabled={loading || !address.trim()}
        className="w-full p-2 rounded bg-blue-600 hover:bg-blue-700 font-bold disabled:opacity-50"
      >
        {loading ? "Abrindo caso..." : "Iniciar Rastreamento"}
      </button>

      {error && <p className="mt-3 text-red-500 text-sm text-center">{error}</p>}
    </div>
  );
}
