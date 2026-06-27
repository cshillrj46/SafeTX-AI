// File: src/TraceTransactionTable.tsx
import type { TraceDetail } from "./api";

interface TraceTransactionTableProps {
  trace: TraceDetail;
}

function shortAddr(addr: string): string {
  return `${addr.slice(0, 8)}...${addr.slice(-6)}`;
}

function shortHash(hash: string): string {
  return `${hash.slice(0, 10)}...`;
}

export default function TraceTransactionTable({ trace }: TraceTransactionTableProps) {
  // Ordena por hop e depois por data — facilita acompanhar a sequência
  // cronológica da movimentação dentro de cada salto.
  const edges = [...trace.edges].sort((a, b) => {
    if (a.depth !== b.depth) return a.depth - b.depth;
    return a.timestamp.localeCompare(b.timestamp);
  });

  const explorerBase = trace.chain === "ethereum" ? "https://etherscan.io" : null;

  return (
    <div className="mt-6">
      <h3 className="text-lg font-semibold mb-2">Transações ({edges.length})</h3>
      <div className="max-h-[360px] overflow-y-auto rounded shadow-inner">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-700 text-white sticky top-0 z-10">
            <tr>
              <th className="p-2">Hop</th>
              <th className="p-2">De</th>
              <th className="p-2">Para</th>
              <th className="p-2">Valor</th>
              <th className="p-2">Token</th>
              <th className="p-2">Data/Hora</th>
              <th className="p-2">Tx</th>
            </tr>
          </thead>
          <tbody className="bg-slate-800">
            {edges.map((e, i) => (
              <tr key={`${e.tx_hash}-${i}`} className="border-t border-gray-700 hover:bg-slate-700 transition-colors">
                <td className="p-2">{e.depth}</td>
                <td className="p-2 font-mono text-xs" title={e.from}>
                  {shortAddr(e.from)}
                </td>
                <td className="p-2 font-mono text-xs" title={e.to}>
                  {shortAddr(e.to)}
                </td>
                <td className="p-2">{e.amount.toFixed(e.token_symbol ? 2 : 5)}</td>
                <td className="p-2">{e.token_symbol ?? "ETH"}</td>
                <td className="p-2 whitespace-nowrap">{e.timestamp}</td>
                <td className="p-2 font-mono text-xs">
                  {explorerBase ? (
                    <a
                      href={`${explorerBase}/tx/${e.tx_hash}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-400 hover:underline"
                      title={e.tx_hash}
                    >
                      {shortHash(e.tx_hash)} ↗
                    </a>
                  ) : (
                    shortHash(e.tx_hash)
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
