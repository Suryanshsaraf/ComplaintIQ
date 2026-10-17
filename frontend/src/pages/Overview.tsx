import { AlertTriangle, ArrowDownRight, ArrowUpRight, BellRing, Smile, TrendingUp, Users } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CategoryBars, ForecastChart, SentimentDonut, SimpleBars, VolumeTrend } from "@/components/charts";
import { LivePredictBox } from "@/components/LivePredictBox";
import { Async, Badge, Card, CardContent, CardDescription, CardHeader, CardTitle, Empty, ErrorBox, Notice, PageHeader, Select, SeverityBadge, Skeleton, Tabs } from "@/components/ui";
import { useApi } from "@/lib/api";
import { cn, fmtDate, fmtNum, fmtPct } from "@/lib/utils";

function Delta({ value, suffix = "%", goodWhenDown = false }: { value: number | null | undefined; suffix?: string; goodWhenDown?: boolean }) {
  if (value === null || value === undefined) return <span className="text-xs text-muted-foreground">no prior period</span>;
  const up = value > 0;
  const bad = goodWhenDown ? up : !up;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return (
    <span className={cn("inline-flex items-center text-xs font-medium", value === 0 ? "text-muted-foreground" : bad ? "text-red-600" : "text-emerald-600")}>
      <Icon className="h-3 w-3" />
      {Math.abs(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}
      {suffix} vs prior period
    </span>
  );
}

function Kpi({ label, value, icon: Icon, children }: { label: string; value: string; icon: any; children: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex items-center justify-between text-muted-foreground">
          <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
          <Icon className="h-4 w-4" />
        </div>
        <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
        <div className="mt-1">{children}</div>
      </CardContent>
    </Card>
  );
}

export default function Overview() {
  const navigate = useNavigate();
  const [days, setDays] = useState(30);
  const [gran, setGran] = useState("day");
  const summary = useApi<any>(`/api/dashboard/summary?days=${days}`);
  const trends = useApi<any>(`/api/dashboard/trends?days=${Math.max(days * 2, 60)}&granularity=${gran}`);

  return (
    <div>
      <PageHeader
        title="Overview"
        subtitle={summary.data?.as_of ? `Data through ${fmtDate(summary.data.as_of)} · compared with the previous ${days} days` : "Complaint intelligence at a glance"}
        actions={
          <Select aria-label="Period" value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </Select>
        }
      />
      <Async state={summary}>
        {(s) =>
          s.empty ? (
            <Card>
              <Empty title="No complaints yet" hint="Import a CSV in the Complaint Explorer, or re-generate the synthetic demo dataset." />
            </Card>
          ) : (
            <div className="space-y-6">
              {s.data.is_fully_synthetic && (
                <Notice>Demo mode: all data shown is <b>synthetic</b> (template-generated with injected incident spikes). Import your own CSV in the Complaint Explorer to analyse real complaints.</Notice>
              )}
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <Kpi label="Total complaints" value={fmtNum(s.kpis.total.value)} icon={Users}>
                  <Delta value={s.kpis.total.change_pct} goodWhenDown />
                </Kpi>
                <Kpi label="Negative sentiment" value={fmtPct(s.kpis.negative_pct.value)} icon={AlertTriangle}>
                  <Delta value={s.kpis.negative_pct.change_pts} suffix=" pts" goodWhenDown />
                </Kpi>
                <Kpi label="Avg sentiment score" value={s.kpis.avg_sentiment.value.toFixed(2)} icon={Smile}>
                  <Delta value={s.kpis.avg_sentiment.change} suffix="" />
                </Kpi>
                <Kpi label="Active alerts" value={String(s.kpis.active_alerts.value)} icon={BellRing}>
                  <span className="text-xs text-muted-foreground">{s.kpis.active_alerts.critical_high} critical / high</span>
                </Kpi>
              </div>

              {/* Interactive Live Complaint Classifier */}
              <LivePredictBox />

              <div className="grid gap-6 lg:grid-cols-3">
                <Card className="lg:col-span-2">
                  <CardHeader className="flex-row items-center justify-between">
                    <div>
                      <CardTitle>Complaint volume</CardTitle>
                      <CardDescription>Total vs. negative complaints · Click a date point to drill down in Explorer</CardDescription>
                    </div>
                    <Tabs tabs={[{ id: "day", label: "Daily" }, { id: "week", label: "Weekly" }]} value={gran} onChange={setGran} />
                  </CardHeader>
                  <CardContent>
                    {trends.error ? (
                      <ErrorBox message={trends.error} onRetry={trends.reload} />
                    ) : trends.data ? (
                      <VolumeTrend
                        data={trends.data.series}
                        onDateClick={(d) => navigate(`/explorer?date_from=${d}&date_to=${d}`)}
                      />
                    ) : (
                      <Skeleton className="h-64" />
                    )}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Categories</CardTitle>
                    <CardDescription>Predicted category · Click bar to filter Explorer</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <CategoryBars
                      data={s.categories}
                      onCategoryClick={(c) => navigate(`/explorer?category=${encodeURIComponent(c)}`)}
                    />
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 lg:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle>Sentiment</CardTitle>
                    <CardDescription>Predicted mix · Click slice to filter</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <SentimentDonut
                      data={s.sentiment}
                      onSentimentClick={(sent) => navigate(`/explorer?sentiment=${sent}`)}
                    />
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Channels</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <SimpleBars data={s.channels} x="channel" y="count" color="#009e73" />
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Top recurring topics</CardTitle>
                    <CardDescription>NMF topics · change vs prior period</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {s.topics.slice(0, 6).map((t: any) => (
                      <div key={t.topic_id} className="flex items-center justify-between gap-2 text-sm">
                        <span className="truncate" title={t.terms.join(", ")}>{t.label}</span>
                        <span className="flex shrink-0 items-center gap-2">
                          <b>{fmtNum(t.count)}</b>
                          {t.change_pct !== null && <span className={cn("text-xs", t.change_pct > 15 ? "text-red-600" : "text-muted-foreground")}>{t.change_pct > 0 ? "+" : ""}{t.change_pct}%</span>}
                        </span>
                      </div>
                    ))}
                    {!s.topics.length && <Empty title="No topics" />}
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 lg:grid-cols-3">
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2"><TrendingUp className="h-4 w-4" /> Historical vs forecast volume</CardTitle>
                    <CardDescription>
                      {s.forecast?.status === "ok" ? `${s.forecast.selected_model} · next 14 days with 80% interval` : "Forecast unavailable"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {s.forecast?.status === "ok" ? <ForecastChart history={s.forecast.history} forecast={s.forecast.forecast} /> : <Empty title="Not enough history to forecast" hint={s.forecast?.reason} />}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Emerging issues</CardTitle>
                    <CardDescription>Terms surging vs. the prior 60-day baseline · Click to inspect</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {s.emerging.length ? s.emerging.map((e: any) => (
                      <div
                        key={e.category}
                        onClick={() => navigate(`/explorer?category=${encodeURIComponent(e.category)}`)}
                        className="cursor-pointer rounded-md border p-3 transition-colors hover:border-primary/50 hover:bg-muted/40"
                        title={`Click to view ${e.category} complaints`}
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium">{e.category}</p>
                          <span className="text-[11px] text-primary">View in Explorer →</span>
                        </div>
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {e.terms.slice(0, 5).map((t: any) => <Badge key={t.term} className="bg-accent text-accent-foreground">{t.term} · {t.ratio}x</Badge>)}
                        </div>
                      </div>
                    )) : <Empty title="Nothing emerging" hint="No terms are surging beyond the baseline." />}
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                  <CardHeader className="flex-row items-center justify-between">
                    <div><CardTitle>Priority alerts</CardTitle><CardDescription>Highest-severity active alerts</CardDescription></div>
                    <Link to="/alerts" className="text-xs font-medium text-primary hover:underline">Open Alert Center →</Link>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {s.priority_alerts.length ? s.priority_alerts.map((a: any) => (
                      <Link to="/alerts" key={a.id} className="block rounded-md border p-3 hover:bg-muted/50">
                        <div className="flex items-center gap-2"><SeverityBadge severity={a.severity} /><span className="text-sm font-medium">{a.title}</span></div>
                        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{a.explanation}</p>
                      </Link>
                    )) : <Empty title="No active alerts" />}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Unusual spikes (last 30 days)</CardTitle>
                    <CardDescription>Statistical + Isolation Forest anomalies · Click to inspect date</CardDescription>
                  </CardHeader>
                  <CardContent className="max-h-80 space-y-2 overflow-y-auto">
                    {s.anomalies.length ? s.anomalies.map((a: any) => (
                      <div
                        key={a.id}
                        onClick={() => navigate(`/explorer?date_from=${a.day}&date_to=${a.day}${a.category ? `&category=${encodeURIComponent(a.category)}` : ""}`)}
                        className="cursor-pointer rounded-md border p-3 text-sm transition-colors hover:border-primary/50 hover:bg-muted/40"
                        title="Click to view complaints on this date in Explorer"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-primary underline-offset-2 hover:underline">{fmtDate(a.day)}{a.category ? ` · ${a.category}` : ""}</span>
                          <Badge className="bg-secondary">{a.method === "isolation_forest" ? "Isolation Forest" : "Rolling z-score"}</Badge>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">{a.explanation}</p>
                      </div>
                    )) : <Empty title="No anomalies in the last 30 days" />}
                  </CardContent>
                </Card>
              </div>
            </div>
          )
        }
      </Async>
    </div>
  );
}
