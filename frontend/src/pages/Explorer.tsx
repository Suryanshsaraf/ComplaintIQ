import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Download, FilterX, Search, Sparkles, Upload } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Async, Badge, Button, Card, CardContent, ErrorBox, Input, Notice, PageHeader, Select, Sheet, Spinner } from "@/components/ui";
import { API_BASE, api, qs, useApi } from "@/lib/api";
import { cn, fmtDate, SENTIMENT_COLORS } from "@/lib/utils";

const PAGE_SIZES = [10, 25, 50, 100];

const DEMO_PRESETS = [
  {
    name: "💳 Overdraft / Double-Debit",
    desc: "March 29 - April 03, 2026: 3.2x spike in Billing & Fee penalties",
    filters: { q: "penalty", date_from: "2026-03-29", date_to: "2026-04-03", category: "Billing & Fees", sentiment: "", channel: "", product: "" },
  },
  {
    name: "📱 Mobile App 5.2 Login Loop",
    desc: "Sep 28 - Oct 15, 2026: Account & KYC surge with 'session expired' / login loop",
    filters: { q: "login", date_from: "2026-09-28", date_to: "2026-10-15", category: "Account & KYC", sentiment: "", channel: "", product: "" },
  },
  {
    name: "⚡ UPI & Transaction Outage",
    desc: "July 12 - July 17, 2026: 3.5x surge in failed UPI transfers & ATM timeouts",
    filters: { q: "", date_from: "2026-07-12", date_to: "2026-07-17", category: "Transaction Failure", sentiment: "", channel: "", product: "" },
  },
  {
    name: "🚨 ATM Skimming & Fraud",
    desc: "Oct 10 - Oct 15, 2026: Critical surge in unauthorized debit card withdrawals",
    filters: { q: "unauthorized", date_from: "2026-10-10", date_to: "2026-10-15", category: "Unauthorized Fraud", sentiment: "negative", channel: "", product: "" },
  },
];

function useDebounced<T>(v: T, ms = 350) {
  const [d, setD] = useState(v);
  useEffect(() => {
    const t = setTimeout(() => setD(v), ms);
    return () => clearTimeout(t);
  }, [v, ms]);
  return d;
}

const SentimentPill = ({ s, score }: { s: string; score?: number }) => (
  <Badge className="gap-1 capitalize" style={{ borderColor: SENTIMENT_COLORS[s], color: SENTIMENT_COLORS[s] }}>
    {s}
    {score !== undefined && <span className="opacity-70">{score.toFixed(2)}</span>}
  </Badge>
);

export default function Explorer() {
  const [searchParams] = useSearchParams();
  const [filters, setFilters] = useState(() => ({
    q: searchParams.get("q") || "",
    date_from: searchParams.get("date_from") || "",
    date_to: searchParams.get("date_to") || "",
    category: searchParams.get("category") || "",
    sentiment: searchParams.get("sentiment") || "",
    channel: searchParams.get("channel") || "",
    product: searchParams.get("product") || "",
  }));

  useEffect(() => {
    const pQ = searchParams.get("q");
    const pDf = searchParams.get("date_from");
    const pDt = searchParams.get("date_to");
    const pCat = searchParams.get("category");
    const pSent = searchParams.get("sentiment");
    const pCh = searchParams.get("channel");
    const pPr = searchParams.get("product");
    if (pQ !== null || pDf !== null || pDt !== null || pCat !== null || pSent !== null || pCh !== null || pPr !== null) {
      setFilters({
        q: pQ || "",
        date_from: pDf || "",
        date_to: pDt || "",
        category: pCat || "",
        sentiment: pSent || "",
        channel: pCh || "",
        product: pPr || "",
      });
    }
  }, [searchParams]);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [sort, setSort] = useState("date");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [selected, setSelected] = useState<number | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const debouncedQ = useDebounced(filters.q);
  const opts = useApi<any>("/api/complaints/filter-options");

  const params = useMemo(() => ({ ...filters, q: debouncedQ }), [filters, debouncedQ]);
  const query = qs(params);
  const list = useApi<any>(`/api/complaints${query}${query ? "&" : "?"}page=${page}&page_size=${pageSize}&sort=${sort}&order=${order}`);

  useEffect(() => setPage(1), [query, pageSize]);
  const setF = (k: string, v: string) => setFilters((f) => ({ ...f, [k]: v }));
  const toggleSort = (col: string) => {
    if (sort === col) setOrder(order === "asc" ? "desc" : "asc");
    else { setSort(col); setOrder("desc"); }
  };
  const SortHead = ({ col, children, className }: { col: string; children: React.ReactNode; className?: string }) => (
    <th className={cn("cursor-pointer select-none px-3 py-2 text-left font-medium", className)} onClick={() => toggleSort(col)}>
      <span className="inline-flex items-center gap-1">
        {children}
        {sort === col && (order === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
      </span>
    </th>
  );
  const totalPages = list.data ? Math.max(1, Math.ceil(list.data.total / pageSize)) : 1;
  const anyFilter = Object.values(filters).some(Boolean);

  return (
    <div>
      <PageHeader
        title="Complaint Explorer"
        subtitle="Search, filter and inspect individual complaints with their model predictions."
        actions={
          <>
            <Button variant="outline" onClick={() => setImportOpen(true)}><Upload className="h-4 w-4" /> Import CSV</Button>
            <Button asChild variant="outline">
              <a href={`${API_BASE}/api/complaints/export${query}`} download><Download className="h-4 w-4" /> Export CSV</a>
            </Button>
          </>
        }
      />
      {/* Demo Incident Presets Toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-2 rounded-lg border bg-card p-3 shadow-sm">
        <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground mr-1">
          <Sparkles className="h-3.5 w-3.5 text-primary" /> Incident Presets:
        </span>
        {DEMO_PRESETS.map((p) => {
          const isActive = filters.category === p.filters.category && filters.date_from === p.filters.date_from;
          return (
            <button
              key={p.name}
              type="button"
              onClick={() => {
                setFilters(p.filters);
                setPage(1);
              }}
              title={p.desc}
              className={cn(
                "rounded-md border px-2.5 py-1 text-xs font-medium transition-colors hover:border-primary hover:bg-accent",
                isActive
                  ? "border-primary bg-primary/10 text-primary font-semibold"
                  : "border-border bg-muted/40 text-muted-foreground hover:text-foreground"
              )}
            >
              {p.name}
            </button>
          );
        })}
        {anyFilter && (
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto h-7 px-2 text-xs"
            onClick={() => setFilters({ q: "", date_from: "", date_to: "", category: "", sentiment: "", channel: "", product: "" })}
          >
            <FilterX className="h-3.5 w-3.5" /> Clear Filters
          </Button>
        )}
      </div>
      <Card className="mb-4">
        <CardContent className="grid gap-3 pt-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="relative sm:col-span-2">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input aria-label="Search complaints" className="pl-8" placeholder="Search complaint text or ID…" value={filters.q} onChange={(e) => setF("q", e.target.value)} />
          </div>
          <Input aria-label="From date" type="date" value={filters.date_from} min={opts.data?.date_min} max={opts.data?.date_max} onChange={(e) => setF("date_from", e.target.value)} />
          <Input aria-label="To date" type="date" value={filters.date_to} min={opts.data?.date_min} max={opts.data?.date_max} onChange={(e) => setF("date_to", e.target.value)} />
          <Select aria-label="Category" value={filters.category} onChange={(e) => setF("category", e.target.value)}>
            <option value="">All categories</option>
            {opts.data?.categories.map((c: string) => <option key={c}>{c}</option>)}
          </Select>
          <Select aria-label="Sentiment" value={filters.sentiment} onChange={(e) => setF("sentiment", e.target.value)}>
            <option value="">All sentiments</option>
            {["negative", "neutral", "positive"].map((c) => <option key={c}>{c}</option>)}
          </Select>
          <Select aria-label="Channel" value={filters.channel} onChange={(e) => setF("channel", e.target.value)}>
            <option value="">All channels</option>
            {opts.data?.channels.map((c: string) => <option key={c}>{c}</option>)}
          </Select>
          <Select aria-label="Product" value={filters.product} onChange={(e) => setF("product", e.target.value)}>
            <option value="">All products</option>
            {opts.data?.products.map((c: string) => <option key={c}>{c}</option>)}
          </Select>
          {anyFilter && (
            <Button variant="ghost" onClick={() => setFilters({ q: "", date_from: "", date_to: "", category: "", sentiment: "", channel: "", product: "" })}>
              <FilterX className="h-4 w-4" /> Clear filters
            </Button>
          )}
        </CardContent>
      </Card>

      {list.error ? <ErrorBox message={list.error} onRetry={list.reload} /> : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/50 text-xs text-muted-foreground">
                <tr>
                  <SortHead col="date">Date</SortHead>
                  <th className="px-3 py-2 text-left font-medium">Complaint</th>
                  <SortHead col="category">Predicted category</SortHead>
                  <SortHead col="sentiment">Sentiment</SortHead>
                  <SortHead col="channel">Channel</SortHead>
                  <SortHead col="product">Product</SortHead>
                </tr>
              </thead>
              <tbody className={cn(list.loading && "opacity-50")}>
                {list.data?.items.map((c: any) => (
                  <tr key={c.id} className="cursor-pointer border-b last:border-0 hover:bg-muted/40" onClick={() => setSelected(c.id)} tabIndex={0} onKeyDown={(e) => e.key === "Enter" && setSelected(c.id)}>
                    <td className="whitespace-nowrap px-3 py-2 text-muted-foreground">{fmtDate(c.created_at)}</td>
                    <td className="max-w-md px-3 py-2"><p className="line-clamp-2">{c.text}</p>
                      <div className="mt-1 flex flex-wrap gap-1">{c.prediction?.keywords.slice(0, 3).map((k: string) => <span key={k} className="rounded bg-muted px-1.5 text-[11px] text-muted-foreground">{k}</span>)}</div>
                    </td>
                    <td className="px-3 py-2">
                      {c.prediction ? <><span className="font-medium">{c.prediction.category}</span><span className="ml-1 text-xs text-muted-foreground">{Math.round(c.prediction.category_prob * 100)}%</span></> : "—"}
                      {c.true_category && c.prediction && c.true_category !== c.prediction.category && <div className="text-[11px] text-red-600">label: {c.true_category}</div>}
                    </td>
                    <td className="px-3 py-2">{c.prediction ? <SentimentPill s={c.prediction.sentiment} score={c.prediction.sentiment_score} /> : "—"}</td>
                    <td className="px-3 py-2">{c.channel ?? "—"}</td>
                    <td className="px-3 py-2">{c.product ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!list.data && <Spinner />}
            {list.data && list.data.items.length === 0 && (
              <p className="py-10 text-center text-sm text-muted-foreground">No complaints match these filters.</p>
            )}
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t px-4 py-3 text-sm">
            <span className="text-muted-foreground">{list.data ? `${list.data.total.toLocaleString()} complaints` : ""}</span>
            <div className="flex items-center gap-2">
              <Select aria-label="Rows per page" value={pageSize} onChange={(e) => setPageSize(Number(e.target.value))}>
                {PAGE_SIZES.map((n) => <option key={n} value={n}>{n} / page</option>)}
              </Select>
              <Button size="icon" variant="outline" aria-label="Previous page" disabled={page <= 1} onClick={() => setPage(page - 1)}><ChevronLeft className="h-4 w-4" /></Button>
              <span>Page {page} of {totalPages}</span>
              <Button size="icon" variant="outline" aria-label="Next page" disabled={page >= totalPages} onClick={() => setPage(page + 1)}><ChevronRight className="h-4 w-4" /></Button>
            </div>
          </div>
        </Card>
      )}

      <DetailSheet id={selected} onClose={() => setSelected(null)} />
      <ImportSheet open={importOpen} onClose={() => setImportOpen(false)} onDone={() => { list.reload(); opts.reload(); }} />
    </div>
  );
}

function DetailSheet({ id, onClose }: { id: number | null; onClose: () => void }) {
  const d = useApi<any>(id ? `/api/complaints/${id}` : null);
  return (
    <Sheet open={id !== null} onClose={onClose} title="Complaint details">
      {id !== null && (
        <Async state={d}>
          {(c) => (
            <div className="space-y-5 text-sm">
              <p className="rounded-md bg-muted p-3 leading-relaxed">{c.text}</p>
              <dl className="grid grid-cols-2 gap-3">
                <div><dt className="text-xs text-muted-foreground">Date</dt><dd>{fmtDate(c.created_at)}</dd></div>
                <div><dt className="text-xs text-muted-foreground">ID</dt><dd>{c.external_id ?? c.id}</dd></div>
                <div><dt className="text-xs text-muted-foreground">Channel</dt><dd>{c.channel ?? "—"}</dd></div>
                <div><dt className="text-xs text-muted-foreground">Product</dt><dd>{c.product ?? "—"}</dd></div>
              </dl>
              {c.prediction && (
                <div className="space-y-2">
                  <h4 className="font-semibold">Model predictions</h4>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge className="bg-accent text-accent-foreground">{c.prediction.category} · {(c.prediction.category_prob * 100).toFixed(0)}%</Badge>
                    <SentimentPill s={c.prediction.sentiment} score={c.prediction.sentiment_score} />
                    <Badge className="bg-secondary">{c.prediction.split === "external" ? "not in training" : `${c.prediction.split} split`}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">Probabilities are classifier outputs and may be over- or under-confident; see calibration in NLP Intelligence.</p>
                  <div className="flex flex-wrap gap-1">{c.prediction.keywords.map((k: string) => <Badge key={k} className="bg-muted">{k}</Badge>)}</div>
                </div>
              )}
              <div>
                <h4 className="mb-1 font-semibold">Ground truth (separate from predictions)</h4>
                {c.true_category || c.true_sentiment ? (
                  <p>Category: <b>{c.true_category ?? "—"}</b> · Sentiment: <b>{c.true_sentiment ?? "—"}</b></p>
                ) : <p className="text-muted-foreground">Unlabeled complaint.</p>}
              </div>
              <div className="space-y-3">
                <h4 className="font-semibold">Model explanation</h4>
                {c.explanation.warning && <Notice tone="warn">{c.explanation.warning}</Notice>}
                {[["Category", c.explanation.category_terms], ["Sentiment", c.explanation.sentiment_terms]].map(([label, terms]: any) => (
                  <div key={label}>
                    <p className="mb-1 text-xs font-medium text-muted-foreground">Terms pushing the {label.toLowerCase()} prediction</p>
                    <div className="flex flex-wrap gap-1">
                      {terms?.length ? terms.map((t: any) => <Badge key={t.term} className="bg-indigo-50 text-indigo-800">{t.term} <span className="ml-1 opacity-60">{t.weight}</span></Badge>) : <span className="text-xs text-muted-foreground">none</span>}
                    </div>
                  </div>
                ))}
                {c.explanation.topic && <p className="text-xs">Topic: {c.explanation.topic.terms.join(", ")}</p>}
                {c.explanation.cluster && <p className="text-xs">Cluster {c.explanation.cluster.id}: {c.explanation.cluster.terms.join(", ")}</p>}
                <p className="text-xs italic text-muted-foreground">{c.explanation.note}</p>
              </div>
            </div>
          )}
        </Async>
      )}
    </Sheet>
  );
}

const FIELDS: [string, string, boolean][] = [
  ["text", "Complaint text", true], ["date", "Date", false], ["category", "Category label (optional)", false],
  ["sentiment", "Sentiment label (optional)", false], ["product", "Product", false], ["channel", "Channel", false], ["external_id", "External ID", false],
];

function ImportSheet({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const reset = () => { setFile(null); setPreview(null); setMapping({}); setError(null); setResult(null); };

  const choose = async (f: File | null) => {
    reset();
    if (!f) return;
    setFile(f); setBusy(true);
    try {
      const fd = new FormData(); fd.append("file", f);
      const p = await api("/api/imports/preview", { method: "POST", body: fd });
      setPreview(p);
      setMapping(Object.fromEntries(Object.entries(p.suggested_mapping).filter(([, v]) => v) as [string, string][]));
    } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  };
  const run = async () => {
    if (!file) return;
    setBusy(true); setError(null);
    try {
      const fd = new FormData(); fd.append("file", file); fd.append("mapping", JSON.stringify(mapping));
      setResult(await api("/api/imports", { method: "POST", body: fd }));
      onDone();
    } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  };

  return (
    <Sheet open={open} onClose={() => { onClose(); reset(); }} title="Import complaints from CSV">
      <div className="space-y-4 text-sm">
        <p className="text-muted-foreground">Upload a CSV, map its columns, review the preview, then import. Labels are optional — unlabeled rows are scored by the existing models. Duplicates (same text + date) are skipped.</p>
        <Input type="file" accept=".csv,text/csv" aria-label="CSV file" onChange={(e) => choose(e.target.files?.[0] ?? null)} />
        <p className="text-xs text-muted-foreground">Try <code>backend/data/sample_unlabeled.csv</code>.</p>
        {error && <ErrorBox message={error} />}
        {busy && !result && <Spinner label="Working…" />}
        {preview && !result && (
          <>
            <div className="grid gap-2">
              {FIELDS.map(([key, label, required]) => (
                <label key={key} className="grid grid-cols-2 items-center gap-2">
                  <span>{label}{required && <span className="text-red-600"> *</span>}</span>
                  <Select value={mapping[key] ?? ""} onChange={(e) => setMapping((m) => ({ ...m, [key]: e.target.value }))}>
                    <option value="">— not mapped —</option>
                    {preview.columns.map((c: string) => <option key={c}>{c}</option>)}
                  </Select>
                </label>
              ))}
            </div>
            <div>
              <p className="mb-1 font-medium">Preview ({preview.n_rows.toLocaleString()} rows)</p>
              <div className="max-h-52 overflow-auto rounded-md border">
                <table className="w-full text-xs">
                  <thead className="bg-muted/60"><tr>{preview.columns.map((c: string) => <th key={c} className="px-2 py-1 text-left">{c}{preview.blank_counts[c] > 0 && <span className="ml-1 text-amber-600">({preview.blank_counts[c]} blank)</span>}</th>)}</tr></thead>
                  <tbody>{preview.sample.map((r: any, i: number) => <tr key={i} className="border-t">{preview.columns.map((c: string) => <td key={c} className="max-w-[200px] truncate px-2 py-1">{r[c]}</td>)}</tr>)}</tbody>
                </table>
              </div>
            </div>
            {!mapping.date && <Notice tone="warn">No date column mapped: complaints will be dated today, so trend analytics will not be meaningful.</Notice>}
            <Button onClick={run} loading={busy} disabled={!mapping.text}>Import {preview.n_rows.toLocaleString()} rows</Button>
          </>
        )}
        {result && (
          <div className="space-y-3">
            <Notice>Imported <b>{result.summary.rows_imported}</b> of {result.summary.rows_in_file} rows · scored {result.scored} · alerts refreshed.</Notice>
            <ul className="list-inside list-disc text-xs">
              {Object.entries(result.summary.skipped).map(([k, v]) => <li key={k}>Skipped {k.replace(/_/g, " ")}: {String(v)}</li>)}
              <li>Labelled category rows: {result.summary.labeled_category} · sentiment rows: {result.summary.labeled_sentiment}</li>
              {Object.entries(result.summary.missing_values).map(([k, v]) => <li key={k}>Missing {k}: {String(v)}</li>)}
            </ul>
            {result.summary.warnings.map((w: string) => <Notice key={w} tone="warn">{w}</Notice>)}
            {result.summary.labeled_category > 0 && <p className="text-xs text-muted-foreground">New labels are used the next time you retrain (ML Intelligence → Retrain models).</p>}
            <Button variant="outline" onClick={reset}>Import another file</Button>
          </div>
        )}
      </div>
    </Sheet>
  );
}
