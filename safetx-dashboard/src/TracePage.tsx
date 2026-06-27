// File: src/TracePage.tsx
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, getTrace, type TraceDetail } from "./api";
import TraceCaseForm from "./TraceCaseForm";
import TraceGraph from "./TraceGraph";
import TraceTransactionTable from "./TraceTransactionTable";

const POLL_INTERVAL_MS = 2500;

const STATUS_LABEL: Record<string, string> = {
  pending: "Na fila",
  running: "Rastreando...",
  completed: "Concluído",
  failed: "Falhou",
};

export default function TracePage() {
  const [jobId, setJobId] = useState<number | null>(null);
  const [trace, setTrace] = useState<TraceDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (jobId === null) return;

    const poll = async () => {
      try {
        const data = await getTrace(jobId);
        setTrace(data);
        if (data.status === "completed" || data.status === "failed") {
          stopPolling();
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Falha ao consultar o rastreamento");
        stopPolling();
      }
    };

    poll(); // primeira chamada imediata, não espera o intervalo
    pollRef.current = window.setInterval(poll, POLL_INTERVAL_MS);

    return stopPolling;
  }, [jobId, stopPolling]);

  const handleNewCase = () => {
    stopPolling();
    setJobId(null);
    setTrace(null);
    setError(null);
  };

  if (jobId === null) {
    return <TraceCaseForm onCreated={setJobId} />;
  }

  return (
    <div className="text-white max-w-4xl mx-auto">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h2 className="text-2xl font-bold">Caso #{jobId}</h2>
          {trace?.case_reference && <p className="text-sm text-gray-400">{trace.case_reference}</p>}
        </div>
        <button onClick={handleNewCase} className="text-sm text-blue-400 hover:underline">
          + Novo rastreamento
        </button>
      </div>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {trace && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <StatCard label="Status" value={STATUS_LABEL[trace.status] ?? trace.status} />
            <StatCard label="Endereço alvo" value={shortAddr(trace.target_address)} mono />
            <StatCard label="Nós encontrados" value={String(trace.nodes_found)} />
            <StatCard label="Entidades sinalizadas" value={String(trace.flagged_entities)} />
          </div>

          {trace.status === "failed" && (
            <p className="text-red-500 text-sm mb-4">
              Falha no rastreamento: {trace.error_message ?? "erro desconhecido"}
            </p>
          )}

          {(trace.status === "pending" || trace.status === "running") && (
            <p className="text-gray-400 text-sm mb-4">
              Consultando a blockchain... isso pode levar alguns segundos a alguns minutos,
              dependendo da profundidade e do volume de transações dos endereços envolvidos.
            </p>
          )}

          {trace.status === "completed" && trace.nodes.length > 0 && (
            <>
              <Legend />
              <TraceGraph trace={trace} />
              <TraceTransactionTable trace={trace} />
            </>
          )}

          {trace.status === "completed" && trace.nodes.length === 0 && (
            <p className="text-gray-400 text-sm">
              Nenhuma movimentação relevante encontrada a partir deste endereço, dentro da
              profundidade e do período pesquisados.
            </p>
          )}
        </>
      )}
    </div>
  );
}

function shortAddr(addr: string): string {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

function StatCard({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="bg-gray-800 rounded p-3">
      <p className="text-xs text-gray-400">{label}</p>
      <p className={`text-sm font-semibold ${mono ? "font-mono" : ""}`}>{value}</p>
    </div>
  );
}

function Legend() {
  const items: [string, string][] = [
    ["#D85A30", "Endereço investigado"],
    ["#4B5563", "Sem rótulo público"],
    ["#378ADD", "Exchange conhecida"],
    ["#E24B4A", "Sinalizado (sanção/golpe)"],
  ];
  return (
    <div className="flex flex-wrap gap-4 mb-2 text-xs text-gray-400">
      {items.map(([color, text]) => (
        <span key={text} className="flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: color }} />
          {text}
        </span>
      ))}
    </div>
  );
}