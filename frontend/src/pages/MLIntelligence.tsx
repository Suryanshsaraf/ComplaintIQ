import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnomalyChart, ClusterScatter, ForecastChart, HoldoutChart } from "@/components/charts";
import { RetrainButton } from "@/components/Retrain";
import { Async, Badge, Card, CardContent, CardDescription, CardHeader, CardTitle, Empty, Notice, PageHeader, Select, Tabs } from "@/components/ui";
import { useApi } from "@/lib/api";
import { cn, fmtDate, fmtNum } from "@/lib/utils";

function Clusters() {
  const c = useApi<any>("/api/ml/clusters");
  return (
    <Async state={c}>
      {(d) => d.status !== "ok" ? <Card><Empty title="Clustering unavailable" /></Card> : (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader><CardTitle>Cluster map</CardTitle><CardDescription>{d.algorithm} · 2-D PCA projection of a 1,500-complaint sample · k chosen by silhouette ({d.silhouette.toFixed(3)})</CardDescription></CardHeader>
              <CardContent><ClusterScatter points={d.points} k={d.k} /></CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Evaluation</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm">
                <table className="w-full text-xs"><thead className="text-muted-foreground"><tr><th className="text-left">k</th><th className="text-left">Silhouette</th></tr></thead>
                  <tbody>{d.k_scan.map((s: any) => <tr key={s.k} className={cn(s.k === d.k && "font-semibold text-primary")}><td>{s.k}</td><td>{s.silhouette.toFixed(4)}</td></tr>)}</tbody></table>
                {d.vs_ground_truth && <p className="text-xs text-muted-foreground">Agreement with known categories (labelled rows only, not used for fitting): ARI {d.vs_ground_truth.adjusted_rand.toFixed(2)}, NMI {d.vs_ground_truth.nmi.toFixed(2)}.</p>}
                <p className="text-xs text-muted-foreground">Silhouette is low for short, templated text; clusters are exploratory groupings, not ground truth.</p>
              </CardContent>
            </Card>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            {d.clusters.map((cl: any) => (
              <Card key={cl.cluster_id}>
                <CardHeader><CardTitle>Cluster {cl.cluster_id} · {fmtNum(cl.size)} complaints ({(cl.share * 100).toFixed(1)}%)</CardTitle>
                  <CardDescription>avg sentiment {cl.avg_sentiment.toFixed(2)} · {cl.sentiment.negative} neg / {cl.sentiment.neutral} neu / {cl.sentiment.positive} pos</CardDescription></CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex flex-wrap gap-1">{cl.terms.map((t: string) => <Badge key={t} className="bg-accent text-accent-foreground">{t}</Badge>)}</div>
                  <p className="text-xs text-muted-foreground">Predicted categories: {cl.categories.map(([k, n]: any) => `${k} (${n})`).join(", ")}</p>
                  {cl.representatives.slice(0, 2).map((r: any) => <p key={r.id} className="rounded bg-muted px-2 py-1.5 text-xs">“{r.text}”</p>)}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </Async>
  );
}

function Anomalies() {
  const navigate = useNavigate();
  const [method, setMethod] = useState("");
  const [days, setDays] = useState(365);
  const a = useApi<any>(`/api/ml/anomalies?days=${days}${method ? `&method=${method}` : ""}`);
  return (
    <Async state={a}>
      {(d) => d.status !== "ok" ? <Card><Empty title="Not enough data for anomaly detection" hint={d.reason} /></Card> : (
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <div><CardTitle>Daily volume with anomaly flags</CardTitle>
                <CardDescription>Baseline and threshold: weekday-adjusted trailing 28-day median/MAD (z ≥ {d.summary.z_threshold}). Isolation Forest: contamination {d.summary.contamination}. · Click point to inspect in Explorer</CardDescription></div>
              <div className="flex gap-2">
                <Select aria-label="Window" value={days} onChange={(e) => setDays(Number(e.target.value))}><option value={60}>Last 60 days</option><option value={120}>Last 120 days</option><option value={365}>Last year</option></Select>
                <Select aria-label="Method" value={method} onChange={(e) => setMethod(e.target.value)}><option value="">Both methods</option><option value="rolling_zscore">Rolling z-score</option><option value="isolation_forest">Isolation Forest</option></Select>
              </div>
            </CardHeader>
            <CardContent>
              <AnomalyChart
                daily={d.daily}
                onDateClick={(date) => navigate(`/explorer?date_from=${date}&date_to=${date}`)}
              />
              <p className="mt-2 text-xs text-muted-foreground">{d.summary.statistical_days} days flagged statistically (overall or per-category), {d.summary.isolation_forest_days} by Isolation Forest, {d.summary.both_methods} by both. Thresholds trade false alarms for sensitivity; some flags will be chance.</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Anomaly log ({d.anomalies.length})</CardTitle></CardHeader>
            <CardContent className="max-h-[28rem] space-y-2 overflow-y-auto">
              {d.anomalies.map((x: any) => (
                <div
                  key={x.id}
                  onClick={() => navigate(`/explorer?date_from=${x.day}&date_to=${x.day}${x.category ? `&category=${encodeURIComponent(x.category)}` : ""}`)}
                  className="cursor-pointer rounded-md border p-3 text-sm transition-colors hover:border-primary/50 hover:bg-muted/40"
                  title="Click to view complaints on this date in Explorer"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <b className="text-primary underline-offset-2 hover:underline">{fmtDate(x.day)}</b>
                    <Badge className="bg-secondary">{x.method === "isolation_forest" ? "Isolation Forest" : "Rolling z-score"}</Badge>
                    {x.category && <Badge className="bg-accent text-accent-foreground">{x.category}</Badge>}
                    {x.triggers.map((t: string) => <Badge key={t} className="bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-200">{t.replace(/_/g, " ")}</Badge>)}
                    <span className="ml-auto text-xs text-muted-foreground">score {x.score}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{x.explanation}</p>
                </div>
              ))}
              {!d.anomalies.length && <Empty title="No anomalies in this window" />}
            </CardContent>
          </Card>
        </div>
      )}
    </Async>
  );
}

function Forecast() {
  const [h, setH] = useState(14);
  const f = useApi<any>(`/api/ml/forecast?horizon=${h}`);
  return (
    <Async state={f}>
      {(d) => d.status !== "ok" ? <Card><Empty title="Not enough history to forecast" hint={d.reason} /></Card> : (
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <div><CardTitle>Volume forecast — {d.selected_model}</CardTitle><CardDescription>Interval: {d.interval}</CardDescription></div>
              <Tabs value={String(h)} onChange={(v) => setH(Number(v))} tabs={[{ id: "7", label: "7 days" }, { id: "14", label: "14 days" }, { id: "30", label: "30 days" }]} />
            </CardHeader>
            <CardContent><ForecastChart history={d.history} forecast={d.forecast} height={320} /></CardContent>
          </Card>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Model comparison (last {d.holdout_days} days held out)</CardTitle><CardDescription>Models are fitted on earlier data only, then scored chronologically.</CardDescription></CardHeader>
              <CardContent>
                <table className="w-full text-sm"><thead className="text-xs text-muted-foreground"><tr className="border-b"><th className="py-1 text-left">Model</th><th className="text-left">MAE</th><th className="text-left">RMSE</th><th className="text-left">Bias</th></tr></thead>
                  <tbody>{d.evaluation.map((e: any) => <tr key={e.model} className={cn("border-b last:border-0", e.is_selected && "bg-accent/60")}><td className="py-1.5">{e.model} {e.is_baseline && <Badge className="ml-1 bg-secondary">baseline</Badge>} {e.is_selected && <Badge className="ml-1 bg-emerald-50 text-emerald-700">selected</Badge>}</td><td>{e.mae?.toFixed(2)}</td><td>{e.rmse?.toFixed(2)}</td><td>{e.bias?.toFixed(2)}</td></tr>)}</tbody></table>
                {d.improvement_vs_baseline_rmse !== null && <p className="mt-2 text-xs">RMSE change vs. baseline: <b>{(d.improvement_vs_baseline_rmse * 100).toFixed(1)}%</b> {d.improvement_vs_baseline_rmse <= 0 && "(no improvement)"}</p>}
                <p className="mt-2 text-xs text-muted-foreground">{d.caveat}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Hold-out period: actual vs predicted</CardTitle></CardHeader>
              <CardContent><HoldoutChart data={d.holdout} models={d.evaluation.map((e: any) => e.model)} /></CardContent>
            </Card>
          </div>
        </div>
      )}
    </Async>
  );
}

export default function MLIntelligence() {
  const [tab, setTab] = useState("clusters");
  const runs = useApi<any[]>("/api/models/runs");
  return (
    <div>
      <PageHeader title="ML Intelligence" subtitle="Clustering, anomaly detection and forecasting." actions={<RetrainButton onDone={() => window.location.reload()} />} />
      <div className="mb-5"><Tabs value={tab} onChange={setTab} tabs={[{ id: "clusters", label: "Clustering" }, { id: "anomalies", label: "Anomalies" }, { id: "forecast", label: "Forecasting" }, { id: "runs", label: "Model runs" }]} /></div>
      {tab === "clusters" && <Clusters />}
      {tab === "anomalies" && <Anomalies />}
      {tab === "forecast" && <Forecast />}
      {tab === "runs" && (
        <Card><CardHeader><CardTitle>Model run history</CardTitle><CardDescription>Every training / analytics refresh is stored in the database.</CardDescription></CardHeader>
          <CardContent><Async state={runs}>{(r) => <table className="w-full text-sm"><thead className="text-xs text-muted-foreground"><tr className="border-b"><th className="py-1 text-left">#</th><th className="text-left">Kind</th><th className="text-left">Model</th><th className="text-left">Rows</th><th className="text-left">Active</th><th className="text-left">Created</th></tr></thead>
            <tbody>{r.map((x) => <tr key={x.id} className="border-b last:border-0"><td className="py-1">{x.id}</td><td>{x.kind}</td><td>{x.name}</td><td>{fmtNum(x.n_rows)}</td><td>{x.is_active ? "✓" : ""}</td><td>{new Date(x.created_at).toLocaleString()}</td></tr>)}</tbody></table>}</Async></CardContent></Card>
      )}
      <div className="mt-6"><Notice>Forecasts and anomaly scores describe statistical patterns in complaint counts; they do not identify causes.</Notice></div>
    </div>
  );
}
