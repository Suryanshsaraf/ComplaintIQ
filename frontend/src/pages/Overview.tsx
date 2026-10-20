import { Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, BellRing, ChevronRight, Layers, Radio, ShieldCheck, Smile, Sparkles, TrendingUp, Users } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CategoryBars, SentimentDonut, SimpleBars, VolumeTrend } from "@/components/charts";
import { LivePredictBox } from "@/components/LivePredictBox";
import { Async, Badge, Card, CardContent, CardDescription, CardHeader, CardTitle, Empty, ErrorBox, Notice, SeverityBadge, Skeleton, Tabs } from "@/components/ui";
import { useApi } from "@/lib/api";
import { cn, fmtDate, fmtNum, fmtPct } from "@/lib/utils";

function Delta({ value, suffix = "%", goodWhenDown = false }: { value: number | null | undefined; suffix?: string; goodWhenDown?: boolean }) {
  if (value === null || value === undefined) return <span className="text-[11px] text-muted-foreground">benchmark starting</span>;
  const up = value > 0;
  const bad = goodWhenDown ? up : !up;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[11px] font-semibold",
        value === 0
          ? "bg-muted text-muted-foreground"
          : bad
          ? "bg-red-500/10 text-red-600 dark:text-red-400"
          : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
      )}
    >
      <Icon className="h-3 w-3" />
      {Math.abs(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}{suffix}
    </span>
  );
}

function Kpi({
  label,
  value,
  icon: Icon,
  iconColor,
  iconBg,
  subtext,
  children,
}: {
  label: string;
  value: string;
  icon: any;
  iconColor: string;
  iconBg: string;
  subtext?: string;
  children?: React.ReactNode;
}) {
  return (
    <Card className="relative overflow-hidden border-border/80 shadow-sm transition-all hover:shadow-md">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</span>
          <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg", iconBg)}>
            <Icon className={cn("h-4 w-4", iconColor)} />
          </div>
        </div>
        <div className="mt-2 flex items-baseline justify-between">
          <p className="text-2xl font-bold tracking-tight text-foreground">{value}</p>
          {children}
        </div>
        {subtext && <p className="mt-1 text-[11px] text-muted-foreground">{subtext}</p>}
      </CardContent>
    </Card>
  );
}

export default function Overview() {
  const navigate = useNavigate();
  const [days, setDays] = useState(30);
  const [gran, setGran] = useState("day");
  const [distTab, setDistTab] = useState("categories");
  const [signalTab, setSignalTab] = useState("alerts");

  const summary = useApi<any>(`/api/dashboard/summary?days=${days}`);
  const trends = useApi<any>(`/api/dashboard/trends?days=${Math.max(days * 2, 60)}&granularity=${gran}`);

  return (
    <div className="space-y-5">
      {/* Top Header & Status Ribbon */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-extrabold tracking-tight">Overview</h1>
            <Badge className="border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium gap-1.5 px-2 py-0.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live Monitoring
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {summary.data?.as_of
              ? `Window through ${fmtDate(summary.data.as_of)} · Benchmark vs prior ${days} days`
              : "Customer complaint intelligence & early-warning anomaly signals"}
          </p>
        </div>

        {/* Time period filter pills */}
        <div className="flex items-center gap-2">
          <Tabs
            tabs={[
              { id: "7", label: "7D" },
              { id: "30", label: "30D" },
              { id: "90", label: "90D" },
            ]}
            value={String(days)}
            onChange={(v) => setDays(Number(v))}
          />
        </div>
      </div>

      <Async state={summary}>
        {(s) =>
          s.empty ? (
            <Card>
              <Empty
                title="No complaints yet"
                hint="Import a CSV in the Complaint Explorer, or re-generate the synthetic demo dataset."
              />
            </Card>
          ) : (
            <div className="space-y-5">
              {/* Demo Mode Notice */}
              {s.data.is_fully_synthetic && (
                <Notice>
                  <b>Demo Environment:</b> Bundled dataset includes injected incidents (Billing double-charges, carrier backlogs, and app login bug) to demonstrate statistical anomaly detection.
                </Notice>
              )}

              {/* Row 1: KPI Ribbon (4 concise cards) */}
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <Kpi
                  label="Inbound Volume"
                  value={fmtNum(s.kpis.total.value)}
                  icon={Users}
                  iconColor="text-indigo-600 dark:text-indigo-400"
                  iconBg="bg-indigo-500/10"
                  subtext="Complaints in active window"
                >
                  <Delta value={s.kpis.total.change_pct} goodWhenDown />
                </Kpi>

                <Kpi
                  label="Negative Sentiment"
                  value={fmtPct(s.kpis.negative_pct.value)}
                  icon={AlertTriangle}
                  iconColor="text-rose-600 dark:text-rose-400"
                  iconBg="bg-rose-500/10"
                  subtext="Model-classified negative polarity"
                >
                  <Delta value={s.kpis.negative_pct.change_pts} suffix=" pts" goodWhenDown />
                </Kpi>

                <Kpi
                  label="Avg Sentiment Score"
                  value={s.kpis.avg_sentiment.value.toFixed(2)}
                  icon={Smile}
                  iconColor="text-emerald-600 dark:text-emerald-400"
                  iconBg="bg-emerald-500/10"
                  subtext="Bounded in [-1.0 to +1.0]"
                >
                  <Delta value={s.kpis.avg_sentiment.change} suffix="" />
                </Kpi>

                <Kpi
                  label="Active Warnings"
                  value={String(s.kpis.active_alerts.value)}
                  icon={BellRing}
                  iconColor="text-amber-600 dark:text-amber-400"
                  iconBg="bg-amber-500/10"
                  subtext={`${s.kpis.active_alerts.critical_high} High / Critical priority`}
                >
                  {s.kpis.active_alerts.critical_high > 0 && (
                    <Badge className="border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400 text-[10px] font-bold">
                      ACTION REQ
                    </Badge>
                  )}
                </Kpi>
              </div>

              {/* Row 2: Command Center (Volume Trend & Interactive Live AI Classifier) */}
              <div className="grid gap-5 lg:grid-cols-12 items-start">
                {/* Left (7 cols): Hero Volume Trend Chart */}
                <Card className="lg:col-span-7 flex flex-col border-border/80 shadow-sm">
                  <CardHeader className="flex-row items-center justify-between pb-2 border-b">
                    <div>
                      <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                        <TrendingUp className="h-4 w-4 text-primary" />
                        Inbound Volume & Negative Rate
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Daily complaint count vs negative volume · Click points to drill down
                      </CardDescription>
                    </div>
                    <Tabs
                      tabs={[
                        { id: "day", label: "Daily" },
                        { id: "week", label: "Weekly" },
                      ]}
                      value={gran}
                      onChange={setGran}
                    />
                  </CardHeader>
                  <CardContent className="pt-3">
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
                  <div className="border-t bg-muted/20 px-4 py-2 flex items-center justify-between text-xs text-muted-foreground rounded-b-lg">
                    <span>💡 Tip: Click any spike on the chart to filter Explorer</span>
                    <button
                      onClick={() => navigate("/explorer")}
                      className="text-primary font-medium hover:underline flex items-center gap-0.5"
                    >
                      Open Explorer →
                    </button>
                  </div>
                </Card>

                {/* Right (5 cols): Live AI Classifier Widget */}
                <div className="lg:col-span-5">
                  <LivePredictBox className="border-border/80 shadow-sm" />
                </div>
              </div>

              {/* Row 3: Analytical Breakdowns & Intelligence Signals */}
              <div className="grid gap-5 lg:grid-cols-12 items-start">
                {/* Left Card (6 cols): Operational Distributions */}
                <Card className="lg:col-span-6 flex flex-col border-border/80 shadow-sm">
                  <CardHeader className="flex-row items-center justify-between border-b pb-2.5">
                    <div>
                      <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                        <Layers className="h-4 w-4 text-primary" />
                        Operational Distributions
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Breakdown across categories, sentiment mix, and channels
                      </CardDescription>
                    </div>
                    <Tabs
                      tabs={[
                        { id: "categories", label: "Categories" },
                        { id: "sentiment", label: "Sentiment" },
                        { id: "channels", label: "Channels" },
                      ]}
                      value={distTab}
                      onChange={setDistTab}
                    />
                  </CardHeader>
                  <CardContent className="pt-3 min-h-[300px]">
                    {distTab === "categories" && (
                      <div className="space-y-1.5">
                        <CategoryBars
                          data={s.categories}
                          onCategoryClick={(c) => navigate(`/explorer?category=${encodeURIComponent(c)}`)}
                        />
                        <p className="text-[11px] text-muted-foreground text-center">
                          Click any bar to filter complaints by that category
                        </p>
                      </div>
                    )}
                    {distTab === "sentiment" && (
                      <div className="space-y-3 pt-2">
                        <SentimentDonut
                          data={s.sentiment}
                          onSentimentClick={(sent) => navigate(`/explorer?sentiment=${sent}`)}
                        />
                        <div className="grid grid-cols-3 gap-2 text-center text-xs pt-1">
                          <div
                            onClick={() => navigate("/explorer?sentiment=negative")}
                            className="cursor-pointer rounded-lg border p-2 transition-colors hover:border-red-500/50 hover:bg-red-500/5"
                          >
                            <span className="text-muted-foreground block text-[11px]">Negative</span>
                            <span className="font-bold text-red-600 dark:text-red-400">
                              {fmtNum(s.sentiment.find((x: any) => x.sentiment === "negative")?.count || 0)}
                            </span>
                          </div>
                          <div
                            onClick={() => navigate("/explorer?sentiment=neutral")}
                            className="cursor-pointer rounded-lg border p-2 transition-colors hover:border-amber-500/50 hover:bg-amber-500/5"
                          >
                            <span className="text-muted-foreground block text-[11px]">Neutral</span>
                            <span className="font-bold text-amber-500">
                              {fmtNum(s.sentiment.find((x: any) => x.sentiment === "neutral")?.count || 0)}
                            </span>
                          </div>
                          <div
                            onClick={() => navigate("/explorer?sentiment=positive")}
                            className="cursor-pointer rounded-lg border p-2 transition-colors hover:border-emerald-500/50 hover:bg-emerald-500/5"
                          >
                            <span className="text-muted-foreground block text-[11px]">Positive</span>
                            <span className="font-bold text-emerald-600 dark:text-emerald-400">
                              {fmtNum(s.sentiment.find((x: any) => x.sentiment === "positive")?.count || 0)}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                    {distTab === "channels" && (
                      <div className="space-y-1.5 pt-2">
                        <SimpleBars data={s.channels} x="channel" y="count" color="#009e73" />
                        <p className="text-[11px] text-muted-foreground text-center">
                          Distribution across customer contact points
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Right Card (6 cols): Early Warning & Incident Signals */}
                <Card className="lg:col-span-6 flex flex-col border-border/80 shadow-sm">
                  <CardHeader className="flex-row items-center justify-between border-b pb-2.5">
                    <div>
                      <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                        <Radio className="h-4 w-4 text-amber-500" />
                        Early Warning Signals
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Anomaly episodes, active alert rules & emerging surges
                      </CardDescription>
                    </div>
                    <Tabs
                      tabs={[
                        { id: "alerts", label: `Alerts (${s.priority_alerts.length})` },
                        { id: "spikes", label: `Spikes (${s.anomalies.length})` },
                        { id: "emerging", label: "Emerging" },
                      ]}
                      value={signalTab}
                      onChange={setSignalTab}
                    />
                  </CardHeader>
                  <CardContent className="pt-3 min-h-[300px] max-h-[330px] overflow-y-auto space-y-2">
                    {signalTab === "alerts" && (
                      <div className="space-y-2">
                        {s.priority_alerts.length ? (
                          s.priority_alerts.map((a: any) => (
                            <Link
                              to="/alerts"
                              key={a.id}
                              className="block rounded-lg border p-2.5 transition-colors hover:border-primary/50 hover:bg-muted/40"
                            >
                              <div className="flex items-center justify-between gap-2">
                                <div className="flex items-center gap-1.5">
                                  <SeverityBadge severity={a.severity} />
                                  <span className="text-xs font-semibold">{a.title}</span>
                                </div>
                                <span className="text-[11px] text-primary flex items-center">
                                  Review <ChevronRight className="h-3 w-3" />
                                </span>
                              </div>
                              <p className="mt-1 line-clamp-2 text-[11px] text-muted-foreground">
                                {a.explanation}
                              </p>
                            </Link>
                          ))
                        ) : (
                          <Empty title="No active alerts" hint="All metrics are within statistical baselines." />
                        )}
                      </div>
                    )}

                    {signalTab === "spikes" && (
                      <div className="space-y-1.5">
                        {s.anomalies.length ? (
                          s.anomalies.slice(0, 7).map((a: any) => (
                            <div
                              key={a.id}
                              onClick={() =>
                                navigate(
                                  `/explorer?date_from=${a.day}&date_to=${a.day}${
                                    a.category ? `&category=${encodeURIComponent(a.category)}` : ""
                                  }`
                                )
                              }
                              className="cursor-pointer rounded-lg border p-2 text-xs transition-colors hover:border-primary/50 hover:bg-muted/40 flex items-center justify-between"
                              title="Click to view complaints on this date"
                            >
                              <div className="min-w-0 pr-2">
                                <span className="font-semibold text-primary underline-offset-2 hover:underline">
                                  {fmtDate(a.day)}
                                </span>
                                {a.category && (
                                  <span className="ml-1.5 font-medium text-foreground">· {a.category}</span>
                                )}
                                <p className="mt-0.5 text-[11px] text-muted-foreground line-clamp-1 truncate">
                                  {a.explanation}
                                </p>
                              </div>
                              <Badge className="bg-secondary shrink-0 text-[10px]">
                                {a.method === "isolation_forest" ? "Isolation Forest" : "z-score"}
                              </Badge>
                            </div>
                          ))
                        ) : (
                          <Empty title="No anomalies in window" />
                        )}
                      </div>
                    )}

                    {signalTab === "emerging" && (
                      <div className="space-y-2">
                        {s.emerging.length ? (
                          s.emerging.map((e: any) => (
                            <div
                              key={e.category}
                              onClick={() => navigate(`/explorer?category=${encodeURIComponent(e.category)}`)}
                              className="cursor-pointer rounded-lg border p-2.5 transition-colors hover:border-primary/50 hover:bg-muted/40"
                              title={`Click to view ${e.category} complaints`}
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-semibold">{e.category}</span>
                                <span className="text-[11px] text-primary">Drill Down →</span>
                              </div>
                              <div className="mt-1.5 flex flex-wrap gap-1">
                                {e.terms.slice(0, 5).map((t: any) => (
                                  <Badge key={t.term} className="bg-accent text-accent-foreground text-[11px] py-0 font-normal">
                                    {t.term} <span className="opacity-70 ml-1">· {t.ratio}x</span>
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          ))
                        ) : (
                          <Empty title="Nothing emerging" hint="No terms surging beyond baseline threshold." />
                        )}
                      </div>
                    )}
                  </CardContent>
                  <div className="border-t bg-muted/20 px-4 py-2 flex items-center justify-between text-xs text-muted-foreground rounded-b-lg">
                    <span>Deep algorithms available in ML Intelligence</span>
                    <Link to="/alerts" className="text-primary font-medium hover:underline">
                      Alert Center →
                    </Link>
                  </div>
                </Card>
              </div>
            </div>
          )
        }
      </Async>
    </div>
  );
}
