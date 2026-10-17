import { RefreshCw } from "lucide-react";
import { useState } from "react";
import { Button, Notice } from "@/components/ui";
import { post } from "@/lib/api";

export function RetrainButton({ onDone }: { onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const run = async () => {
    setBusy(true);
    setMsg(null);
    try {
      const r = await post("/api/models/retrain");
      if (r.status === "empty") setMsg({ ok: false, text: r.message });
      else {
        const t = r.tasks || {};
        setMsg({
          ok: true,
          text: `Retrained on ${r.n_rows.toLocaleString()} complaints. Category: ${t.category?.status === "ok" ? `${t.category.selected}, acc ${(t.category.accuracy * 100).toFixed(1)}%` : t.category?.reason ?? "skipped"}.`,
        });
        onDone();
      }
    } catch (e: any) {
      setMsg({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flex flex-col items-end gap-2">
      <Button variant="outline" onClick={run} loading={busy}>
        <RefreshCw className="h-4 w-4" /> Retrain models
      </Button>
      {msg && <Notice tone={msg.ok ? "info" : "warn"}>{msg.text}</Notice>}
    </div>
  );
}
