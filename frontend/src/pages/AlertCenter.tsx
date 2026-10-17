import { CheckCircle2, Eye, Search, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Card, CardContent, Empty, ErrorBox, Input, Notice, PageHeader, Select, SeverityBadge, Spinner, StatusBadge, Badge } from "@/components/ui";
import { patch, post, useApi } from "@/lib/api";
import { fmtDate } from "@/lib/utils";

const TYPE_LABEL: Record<string, string> = {
  volume_spike: "Volume spike", sentiment_decline: "Rising negative sentiment", emerging_topic: "Emerging topic", forecast_high: "High forecast",
};

function AlertCard({ a, onChanged }: { a: any; onChanged: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [open, setOpen] = useState(false);
  const act = async (status: string) => {
    setBusy(status); setErr(null);
    try { await patch(`/api/alerts/${a.id}`, { status, note: note || undefined }); setNote(""); onChanged(); } catch (e: any) { setErr(e.message); } finally { setBusy(null); }
  };
  return (
    <Card>
      <CardContent className="space-y-3 pt-5">
        <div className="flex flex-wrap items-center gap-2">
          <SeverityBadge severity={a.severity} /><StatusBadge status={a.status} />
          <Badge className="bg-secondary">{TYPE_LABEL[a.type] ?? a.type}</Badge>
          {a.categories.map((c: string) => <Badge key={c} className="bg-accent text-accent-foreground">{c}</Badge>)}
          <span className="ml-auto text-xs text-muted-foreground">detected for {fmtDate(a.detected_for)}</span>
        </div>
        <h3 className="text-base font-semibold">{a.title}</h3>
        <p className="text-sm text-muted-foreground">{a.explanation}</p>
        <div className="grid gap-3 rounded-md bg-muted/60 p-3 text-xs sm:grid-cols-2">
          <div><p className="mb-1 font-medium">Triggering metrics</p>{Object.entries(a.metrics).map(([k, v]: any) => <p key={k}>{k.replace(/_/g, " ")}: <b>{Array.isArray(v) ? v.map((t: any) => `${t.term} (${t.ratio}x)`).join(", ") : String(v)}</b></p>)}</div>
          <div><p className="mb-1 font-medium">Comparison baseline</p>{Object.entries(a.baseline).map(([k, v]: any) => <p key={k}>{k.replace(/_/g, " ")}: <b>{String(v)}</b></p>)}</div>
        </div>
        {a.categories.length > 0 && (
          <Link className="text-xs font-medium text-primary hover:underline" to="/explorer">Open Complaint Explorer to review affected complaints →</Link>
        )}
        {err && <ErrorBox message={err} />}
        <div className="flex flex-wrap items-center gap-2">
          {a.status === "open" && <Button size="sm" variant="outline" loading={busy === "investigating"} onClick={() => act("investigating")}><Search className="h-3.5 w-3.5" /> Investigate</Button>}
          {(a.status === "open" || a.status === "investigating") && <Button size="sm" variant="outline" loading={busy === "acknowledged"} onClick={() => act("acknowledged")}><Eye className="h-3.5 w-3.5" /> Acknowledge</Button>}
          {a.status !== "resolved" && <Button size="sm" loading={busy === "resolved"} onClick={() => act("resolved")}><CheckCircle2 className="h-3.5 w-3.5" /> Resolve</Button>}
          {a.status === "resolved" && <Button size="sm" variant="outline" loading={busy === "open"} onClick={() => act("open")}>Reopen</Button>}
          <Input aria-label="Note" className="h-8 max-w-xs text-xs" placeholder="Optional note for this change" value={note} onChange={(e) => setNote(e.target.value)} />
          {a.notes.length > 0 && <button className="text-xs text-primary hover:underline" onClick={() => setOpen(!open)}>{open ? "Hide" : "Show"} history ({a.notes.length})</button>}
        </div>
        {open && <ul className="space-y-1 text-xs text-muted-foreground">{a.notes.map((n: any, i: number) => <li key={i}>{new Date(n.at).toLocaleString()} — {n.from} → <b>{n.to}</b>{n.note && `: ${n.note}`}</li>)}</ul>}
      </CardContent>
    </Card>
  );
}

export default function AlertCenter() {
  const [status, setStatus] = useState("active");
  const [severity, setSeverity] = useState("");
  const [type, setType] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const q = new URLSearchParams({ status, ...(severity && { severity }), ...(type && { type }) }).toString();
  const list = useApi<any[]>(`/api/alerts?${q}`);
  const counts = useApi<Record<string, number>>("/api/alerts/counts");
  const changed = () => { list.reload(); counts.reload(); };
  const refresh = async () => {
    setRefreshing(true); setMsg(null);
    try { const r = await post("/api/alerts/refresh"); setMsg(r.status === "ok" ? `Re-analysed through ${fmtDate(r.as_of)}: ${r.alerts.created} new alert(s), ${r.alerts.updated} updated.` : "No data to analyse."); changed(); } catch (e: any) { setMsg(e.message); } finally { setRefreshing(false); }
  };
  return (
    <div>
      <PageHeader title="Alert Center" subtitle="Spikes, rising negativity, emerging topics and high forecasts. Status changes are stored in the database."
        actions={<Button variant="outline" onClick={refresh} loading={refreshing}><ShieldCheck className="h-4 w-4" /> Re-run detection</Button>} />
      {msg && <div className="mb-4"><Notice>{msg}</Notice></div>}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Select aria-label="Status" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="active">Active (not resolved)</option><option value="open">Open</option><option value="investigating">Investigating</option><option value="acknowledged">Acknowledged</option><option value="resolved">Resolved</option>
        </Select>
        <Select aria-label="Severity" value={severity} onChange={(e) => setSeverity(e.target.value)}><option value="">All severities</option>{["critical", "high", "medium", "low"].map((s) => <option key={s}>{s}</option>)}</Select>
        <Select aria-label="Type" value={type} onChange={(e) => setType(e.target.value)}><option value="">All types</option>{Object.entries(TYPE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</Select>
        {counts.data && <span className="ml-auto text-xs text-muted-foreground">{Object.entries(counts.data).map(([k, v]) => `${v} ${k}`).join(" · ")}</span>}
      </div>
      {list.error ? <ErrorBox message={list.error} onRetry={list.reload} /> : !list.data ? <Spinner /> : list.data.length === 0 ? <Card><Empty title="No alerts match" hint="Everything looks normal for this filter, or no alerts have been generated yet." /></Card> : (
        <div className="space-y-4">{list.data.map((a) => <AlertCard key={a.id} a={a} onChanged={changed} />)}</div>
      )}
    </div>
  );
}
