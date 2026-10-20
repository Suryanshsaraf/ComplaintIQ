import { AlertCircle, CheckCircle2, ChevronRight, HelpCircle, Loader2, Sparkles, Tag, ThumbsDown, ThumbsUp, X } from "lucide-react";
import { useState } from "react";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { post } from "@/lib/api";
import { cn, SENTIMENT_COLORS } from "@/lib/utils";

interface PredictResponse {
  category: string;
  category_prob: number;
  category_probabilities: Record<string, number>;
  sentiment: string;
  sentiment_score: number;
  keywords: string[];
  explanation: {
    category_terms: { term: string; weight: number }[];
    sentiment_terms: { term: string; weight: number }[];
  };
}

const PRESET_COMPLAINTS = [
  {
    label: "💳 Double charge",
    text: "I was charged twice on my credit card for my monthly renewal and support has not responded to my email.",
  },
  {
    label: "🚚 Lost package",
    text: "The delivery status shows package was delivered yesterday, but no package arrived at my door or mailbox.",
  },
  {
    label: "📱 App crash on login",
    text: "After installing the latest app version, I get stuck in a login loop and the app crashes with token expired.",
  },
  {
    label: "💸 Refund delay",
    text: "I returned the defective item two weeks ago as instructed, but still no refund credited to my bank account.",
  },
];

export function LivePredictBox({ className }: { className?: string }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictResponse | null>(null);

  const handlePredict = async (complaintText?: string) => {
    const query = (complaintText ?? text).trim();
    if (!query) return;
    if (complaintText) setText(complaintText);
    setLoading(true);
    setError(null);
    try {
      const data = await post<PredictResponse>("/api/predict", { text: query });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to analyze complaint");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className={cn("border-primary/30 shadow-md", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">Test Your Own Complaint (Live AI Classifier)</CardTitle>
              <CardDescription className="text-xs">
                Type or paste any real text to test NLP category and sentiment classification in real time
              </CardDescription>
            </div>
          </div>
          {result && (
            <Button variant="ghost" size="sm" onClick={() => { setResult(null); setText(""); }}>
              <X className="h-3.5 w-3.5" /> Clear
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Quick sample chips */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="font-medium text-muted-foreground">Try samples:</span>
          {PRESET_COMPLAINTS.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => handlePredict(item.text)}
              className="rounded-full border bg-muted/60 px-2.5 py-1 text-xs font-medium transition-colors hover:border-primary/50 hover:bg-accent hover:text-accent-foreground"
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Input box and submit */}
        <div className="space-y-2">
          <textarea
            rows={3}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                handlePredict();
              }
            }}
            placeholder="Type customer complaint here... (e.g. 'I was charged twice on my card and nobody answered the call!')"
            className="w-full resize-none rounded-md border border-input bg-card p-3 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-muted-foreground">Press Cmd+Enter or click Analyze</span>
            <Button size="sm" onClick={() => handlePredict()} loading={loading} disabled={!text.trim()}>
              <Sparkles className="h-3.5 w-3.5" /> Analyze Complaint
            </Button>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-xs text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Prediction Results */}
        {result && (
          <div className="space-y-3.5 rounded-lg border bg-muted/30 p-3.5 transition-all max-h-[310px] overflow-y-auto">
            {/* Top result badges */}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-md border bg-card p-3">
                <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Predicted Category</span>
                <div className="mt-1 flex items-baseline justify-between">
                  <span className="text-lg font-bold text-foreground">{result.category}</span>
                  <Badge className="border-primary/40 bg-primary/10 text-primary font-semibold">
                    {(result.category_prob * 100).toFixed(1)}% confidence
                  </Badge>
                </div>
                {/* Confidence bar */}
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full bg-primary transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(5, result.category_prob * 100))}%` }}
                  />
                </div>
              </div>

              <div className="rounded-md border bg-card p-3">
                <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Predicted Sentiment</span>
                <div className="mt-1 flex items-baseline justify-between">
                  <div className="flex items-center gap-1.5">
                    {result.sentiment === "positive" ? (
                      <ThumbsUp className="h-4 w-4 text-emerald-600" />
                    ) : result.sentiment === "negative" ? (
                      <ThumbsDown className="h-4 w-4 text-red-600" />
                    ) : (
                      <HelpCircle className="h-4 w-4 text-amber-500" />
                    )}
                    <span className="text-lg font-bold capitalize text-foreground">{result.sentiment}</span>
                  </div>
                  <Badge
                    style={{
                      borderColor: SENTIMENT_COLORS[result.sentiment],
                      color: SENTIMENT_COLORS[result.sentiment],
                    }}
                  >
                    Score: {result.sentiment_score > 0 ? "+" : ""}{result.sentiment_score.toFixed(2)}
                  </Badge>
                </div>
                {/* Sentiment balance meter */}
                <div className="mt-2 flex h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full bg-red-500 transition-all duration-500"
                    style={{ width: `${Math.max(0, -result.sentiment_score) * 50}%` }}
                  />
                  <div
                    className="h-full bg-emerald-500 transition-all duration-500 ml-auto"
                    style={{ width: `${Math.max(0, result.sentiment_score) * 50}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Extracted keywords */}
            {result.keywords && result.keywords.length > 0 && (
              <div>
                <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5 mb-1.5">
                  <Tag className="h-3.5 w-3.5" /> Extracted Key Phrases:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {result.keywords.map((kw, i) => (
                    <Badge key={i} className="bg-accent text-accent-foreground text-xs py-0.5 font-normal">
                      {kw}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Decision explanation terms */}
            {result.explanation?.category_terms?.length > 0 && (
              <div>
                <span className="text-xs font-medium text-muted-foreground block mb-1.5">
                  Terms Influencing Classification (Linear SVM weights):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {result.explanation.category_terms.slice(0, 6).map((term, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 rounded bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
                    >
                      <span className="font-medium">{term.term}</span>
                      <span className="text-[10px] text-muted-foreground">+{term.weight.toFixed(2)}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Top 3 Alternative Categories */}
            {result.category_probabilities && (
              <div className="pt-1">
                <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide block mb-2">
                  Category Probability Breakdown
                </span>
                <div className="space-y-1.5">
                  {Object.entries(result.category_probabilities)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 4)
                    .map(([cat, prob]) => (
                      <div key={cat} className="flex items-center gap-2 text-xs">
                        <span className="w-28 truncate font-medium">{cat}</span>
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-secondary">
                          <div
                            className={cn("h-full rounded-full", cat === result.category ? "bg-primary" : "bg-muted-foreground/40")}
                            style={{ width: `${Math.max(2, prob * 100)}%` }}
                          />
                        </div>
                        <span className="w-12 text-right text-[11px] text-muted-foreground">{(prob * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
