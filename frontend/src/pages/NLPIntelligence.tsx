import { Line, LineChart, ResponsiveContainer } from "recharts";
import { useState } from "react";
import { ConfusionMatrix, SimpleBars, StackedSentimentBars } from "@/components/charts";
import { RetrainButton } from "@/components/Retrain";
import { Async, Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Empty, ErrorBox, Notice, PageHeader, Select, Tabs } from "@/components/ui";
import { post, useApi } from "@/lib/api";
import { cn, fmtNum, SENTIMENT_COLORS } from "@/lib/utils";

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

function EvaluationPanel({ task }: { task: "category" | "sentiment" }) {
  const ev = useApi<any>(`/api/nlp/evaluation?task=${task}`);
  const [pick, setPick] = useState<string | null>(null);
  return (
    <Async state={ev}>
      {(e) => {
        if (e.status !== "ok") return <Card><Empty title="No supervised model available" hint={e.reason} /></Card>;
        const active = e.models.find((m: any) => m.model_name === (pick ?? e.selected)) ?? e.models[0];
        const terms = e.influential_terms ?? {};
        return (
          <div className="space-y-6">
            <Notice>{e.protocol}</Notice>
            <Card>
              <CardHeader><CardTitle>Model comparison (held-out test set)</CardTitle><CardDescription>Macro-averaged. “CV F1” is 5-fold cross-validation on the training split and drives model selection.</CardDescription></CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-xs text-muted-foreground"><tr className="border-b">{["Model", "Accuracy", "Precision", "Recall", "F1", "CV F1", "ECE", "Test n"].map((h) => <th key={h} className="px-2 py-2 text-left font-medium">{h}</th>)}</tr></thead>
                  <tbody>
                    {e.models.map((m: any) => (
                      <tr key={m.model_name} className={cn("cursor-pointer border-b last:border-0 hover:bg-muted/40", active.model_name === m.model_name && "bg-accent/60")} onClick={() => setPick(m.model_name)}>
                        <td className="px-2 py-2 font-medium">{m.model_name} {m.is_selected && <Badge className="ml-1 bg-emerald-50 text-emerald-700">deployed</Badge>}</td>
                        <td className="px-2">{pct(m.accuracy)}</td><td className="px-2">{pct(m.precision_macro)}</td><td className="px-2">{pct(m.recall_macro)}</td>
                        <td className="px-2 font-semibold">{pct(m.f1_macro)}</td><td className="px-2">{m.cv_f1_macro != null ? pct(m.cv_f1_macro) : "—"}</td>
                        <td className="px-2">{m.calibration ? m.calibration.ece.toFixed(3) : "—"}</td><td className="px-2">{m.n_test}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-2 text-xs text-muted-foreground">ECE = expected calibration error of predicted confidence (lower is better). The majority-class baseline shows what “no skill” looks like.</p>
              </CardContent>
            </Card>
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader><CardTitle>Confusion matrix — {active.model_name}</CardTitle><CardDescription>Rows = true label, columns = prediction (test set)</CardDescription></CardHeader>
                <CardContent><ConfusionMatrix labels={active.labels} matrix={active.confusion} /></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Per-class metrics — {active.model_name}</CardTitle></CardHeader>
                <CardContent>
                  <table className="w-full text-sm"><thead className="text-xs text-muted-foreground"><tr className="border-b">{["Class", "Precision", "Recall", "F1", "Support"].map((h) => <th key={h} className="px-2 py-1 text-left font-medium">{h}</th>)}</tr></thead>
                    <tbody>{Object.entries(active.per_class).map(([c, m]: any) => <tr key={c} className="border-b last:border-0"><td className="px-2 py-1.5 font-medium">{c}</td><td className="px-2">{pct(m.precision)}</td><td className="px-2">{pct(m.recall)}</td><td className="px-2">{pct(m.f1)}</td><td className="px-2">{m.support}</td></tr>)}</tbody>
                  </table>
                </CardContent>
              </Card>
            </div>
            <Card>
              <CardHeader><CardTitle>Most influential terms per class (deployed model)</CardTitle><CardDescription>Largest positive coefficients. They describe what the model learned, not what causes complaints.</CardDescription></CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {Object.entries(terms).map(([cls, list]: any) => (
                  <div key={cls}><p className="mb-1 text-sm font-medium capitalize">{cls}</p><div className="flex flex-wrap gap-1">{list.slice(0, 8).map((t: any) => <Badge key={t.term} className="bg-muted">{t.term}</Badge>)}</div></div>
                ))}
              </CardContent>
            </Card>
          </div>
        );
      }}
    </Async>
  );
}

function SentimentPanel() {
  const s = useApi<any>("/api/nlp/sentiment");
  return (
    <div className="space-y-6">
      <Async state={s}>
        {(d) => (
          <div className="grid gap-6 lg:grid-cols-2">
            <Card><CardHeader><CardTitle>Sentiment by category</CardTitle><CardDescription>Predicted sentiment counts</CardDescription></CardHeader><CardContent><StackedSentimentBars data={d.by_category} /></CardContent></Card>
            <Card><CardHeader><CardTitle>Sentiment by channel</CardTitle></CardHeader><CardContent><StackedSentimentBars data={d.by_channel} /></CardContent></Card>
            <Card className="lg:col-span-2"><CardHeader><CardTitle>Average sentiment score by product</CardTitle><CardDescription>Score = P(positive) − P(negative); lower is more negative</CardDescription></CardHeader>
              <CardContent><SimpleBars data={d.by_product} x="key" y="avg_sentiment" color={SENTIMENT_COLORS.negative} domain={[-1, 1]} /></CardContent></Card>
          </div>
        )}
      </Async>
      <h2 className="text-lg font-semibold">Sentiment model evaluation</h2>
      <EvaluationPanel task="sentiment" />
    </div>
  );
}

function TopicsPanel() {
  const t = useApi<any>("/api/nlp/topics");
  return (
    <Async state={t}>
      {(d) => d.status !== "ok" ? <Card><Empty title="Topic model unavailable" /></Card> : (
        <div className="space-y-4">
          <Notice>{d.algorithm} · {d.topics.length} topics. Topics are unsupervised — labels are the top terms, not curated names.</Notice>
          <div className="grid gap-4 lg:grid-cols-2">
            {d.topics.map((tp: any) => (
              <Card key={tp.topic_id}>
                <CardHeader className="flex-row items-start justify-between">
                  <div><CardTitle>Topic {tp.topic_id}: {tp.label}</CardTitle><CardDescription>{fmtNum(tp.count)} complaints · {(tp.share * 100).toFixed(1)}% · avg sentiment {tp.avg_sentiment.toFixed(2)}</CardDescription></div>
                  <div className="h-10 w-28">
                    <ResponsiveContainer><LineChart data={tp.weekly}><Line dataKey="count" stroke="#4f46e5" dot={false} strokeWidth={2} /></LineChart></ResponsiveContainer>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap gap-1">{tp.terms.map((x: string) => <Badge key={x} className="bg-accent text-accent-foreground">{x}</Badge>)}</div>
                  <p className="text-xs text-muted-foreground">Mostly: {tp.top_categories.map(([c, n]: any) => `${c} (${n})`).join(", ")}</p>
                  <div className="space-y-1.5">{tp.representatives.slice(0, 2).map((r: any) => <p key={r.id} className="rounded bg-muted px-2 py-1.5 text-xs">“{r.text}”</p>)}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </Async>
  );
}

function KeywordsPanel() {
  const [cat, setCat] = useState("");
  const opts = useApi<any>("/api/complaints/filter-options");
  const k = useApi<any>(`/api/nlp/keywords${cat ? `?category=${encodeURIComponent(cat)}` : ""}`);
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div><CardTitle>Key terms & phrases</CardTitle><CardDescription>{cat ? `Most frequent per-complaint TF-IDF keywords in ${cat}` : "Highest mean TF-IDF weight across all complaints"}</CardDescription></div>
        <Select aria-label="Category" value={cat} onChange={(e) => setCat(e.target.value)}><option value="">All complaints</option>{opts.data?.categories.map((c: string) => <option key={c}>{c}</option>)}</Select>
      </CardHeader>
      <CardContent>
        <Async state={k}>{(d) => <div className="flex flex-wrap gap-2">{d.keywords.map((x: any) => <Badge key={x.term} className="bg-accent px-3 py-1 text-sm text-accent-foreground">{x.term}<span className="ml-2 text-xs opacity-60">{x.docs}</span></Badge>)}{!d.keywords.length && <Empty title="No keywords" />}</div>}</Async>
      </CardContent>
    </Card>
  );
}

function TryIt() {
  const [text, setText] = useState("I was charged twice for my subscription and nobody has replied to my emails. This is unacceptable.");
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const go = async () => {
    setBusy(true); setErr(null);
    try { setRes(await post("/api/predict", { text })); } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };
  return (
    <Card>
      <CardHeader><CardTitle>Classify a new complaint</CardTitle><CardDescription>Runs the deployed classifiers; nothing is saved.</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <textarea aria-label="Complaint text" className="min-h-28 w-full rounded-md border border-input bg-card p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" value={text} onChange={(e) => setText(e.target.value)} />
        <Button onClick={go} loading={busy} disabled={text.trim().length < 3}>Analyze</Button>
        {err && <ErrorBox message={err} />}
        {res && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2"><Badge className="bg-accent text-accent-foreground">{res.category} · {(res.category_prob * 100).toFixed(0)}%</Badge><Badge className="capitalize" style={{ color: SENTIMENT_COLORS[res.sentiment], borderColor: SENTIMENT_COLORS[res.sentiment] }}>{res.sentiment} ({res.sentiment_score.toFixed(2)})</Badge></div>
            <div className="space-y-1">{Object.entries(res.category_probabilities).sort((a: any, b: any) => b[1] - a[1]).slice(0, 4).map(([c, p]: any) => (
              <div key={c} className="flex items-center gap-2 text-xs"><span className="w-32">{c}</span><div className="h-2 flex-1 rounded bg-muted"><div className="h-2 rounded bg-primary" style={{ width: `${p * 100}%` }} /></div><span>{(p * 100).toFixed(1)}%</span></div>))}</div>
            <p className="text-xs">Keywords: {res.keywords.join(", ") || "—"}</p>
            <p className="text-xs text-muted-foreground">Influential terms: {res.explanation.category_terms.map((t: any) => t.term).join(", ") || "—"} (model weights, not causes)</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function NLPIntelligence() {
  const [tab, setTab] = useState("sentiment");
  return (
    <div>
      <PageHeader title="NLP Intelligence" subtitle="Sentiment, category classification, topics and keywords." actions={<RetrainButton onDone={() => window.location.reload()} />} />
      <div className="mb-5"><Tabs value={tab} onChange={setTab} tabs={[{ id: "sentiment", label: "Sentiment" }, { id: "category", label: "Classification" }, { id: "topics", label: "Topics" }, { id: "keywords", label: "Keywords" }, { id: "try", label: "Try it" }]} /></div>
      {tab === "sentiment" && <SentimentPanel />}
      {tab === "category" && <EvaluationPanel task="category" />}
      {tab === "topics" && <TopicsPanel />}
      {tab === "keywords" && <KeywordsPanel />}
      {tab === "try" && <TryIt />}
    </div>
  );
}
