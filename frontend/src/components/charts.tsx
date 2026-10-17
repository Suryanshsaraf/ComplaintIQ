import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import { PALETTE, SENTIMENT_COLORS, cn, shortDate } from "@/lib/utils";

const axis = { fontSize: 11, fill: "currentColor", opacity: 0.7 };
const grid = <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.15} vertical={false} />;
const tip = {
  contentStyle: {
    fontSize: 12,
    borderRadius: 8,
    border: "1px solid hsl(var(--border))",
    backgroundColor: "hsl(var(--card))",
    color: "hsl(var(--card-foreground))",
    boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
  },
};

export function VolumeTrend({
  data,
  onDateClick,
}: {
  data: { date: string; total: number; negative: number }[];
  onDateClick?: (date: string) => void;
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart
        data={data}
        margin={{ left: -10, right: 8, top: 8 }}
        style={{ cursor: onDateClick ? "pointer" : "default" }}
        onClick={(e: any) => {
          if (e && e.activePayload && e.activePayload[0] && onDateClick) {
            onDateClick(e.activePayload[0].payload.date);
          }
        }}
      >
        {grid}
        <XAxis dataKey="date" tickFormatter={shortDate} tick={axis} minTickGap={32} />
        <YAxis tick={axis} />
        <Tooltip {...tip} labelFormatter={(l) => shortDate(String(l))} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area isAnimationActive={false} type="monotone" dataKey="total" name="All complaints" stroke="#4f46e5" fill="#4f46e5" fillOpacity={0.15} strokeWidth={2} />
        <Area isAnimationActive={false} type="monotone" dataKey="negative" name="Negative" stroke="#d55e00" fill="#d55e00" fillOpacity={0.15} strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function CategoryStack({ data, categories }: { data: any[]; categories: string[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ left: -10, right: 8, top: 8 }}>
        {grid}
        <XAxis dataKey="date" tickFormatter={shortDate} tick={axis} minTickGap={32} />
        <YAxis tick={axis} />
        <Tooltip {...tip} labelFormatter={(l) => shortDate(String(l))} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {categories.map((c, i) => (
          <Area isAnimationActive={false} key={c} type="monotone" stackId="1" dataKey={c} stroke={PALETTE[i % 8]} fill={PALETTE[i % 8]} fillOpacity={0.55} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function CategoryBars({
  data,
  onCategoryClick,
}: {
  data: { category: string; count: number }[];
  onCategoryClick?: (category: string) => void;
}) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 32)}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ left: 20, right: 16 }}
        style={{ cursor: onCategoryClick ? "pointer" : "default" }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.15} horizontal={false} />
        <XAxis type="number" tick={axis} />
        <YAxis type="category" dataKey="category" tick={axis} width={110} />
        <Tooltip {...tip} />
        <Bar
          isAnimationActive={false}
          dataKey="count"
          name="Complaints"
          radius={[0, 4, 4, 0]}
          onClick={(entry: any) => {
            if (entry && entry.category && onCategoryClick) {
              onCategoryClick(entry.category);
            }
          }}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % 8]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SentimentDonut({
  data,
  onSentimentClick,
}: {
  data: { sentiment: string; count: number }[];
  onSentimentClick?: (sentiment: string) => void;
}) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          isAnimationActive={false}
          data={data}
          dataKey="count"
          nameKey="sentiment"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={2}
          style={{ cursor: onSentimentClick ? "pointer" : "default" }}
          onClick={(entry: any) => {
            if (entry && entry.sentiment && onSentimentClick) {
              onSentimentClick(entry.sentiment);
            }
          }}
        >
          {data.map((d) => (
            <Cell key={d.sentiment} fill={SENTIMENT_COLORS[d.sentiment]} />
          ))}
        </Pie>
        <Tooltip {...tip} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function SimpleBars({ data, x, y, color = "#4f46e5", height = 220, domain }: { data: any[]; x: string; y: string; color?: string; height?: number; domain?: [number, number] }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ left: -10, right: 8 }}>
        {grid}
        <XAxis dataKey={x} tick={axis} interval={0} angle={-20} textAnchor="end" height={55} />
        <YAxis tick={axis} domain={domain} />
        <Tooltip {...tip} />
        <Bar isAnimationActive={false} dataKey={y} fill={color} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function StackedSentimentBars({ data }: { data: any[] }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 34)}>
      <BarChart data={data} layout="vertical" margin={{ left: 20, right: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.15} horizontal={false} />
        <XAxis type="number" tick={axis} />
        <YAxis type="category" dataKey="key" tick={axis} width={120} />
        <Tooltip {...tip} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {["negative", "neutral", "positive"].map((s) => (
          <Bar isAnimationActive={false} key={s} dataKey={s} stackId="a" fill={SENTIMENT_COLORS[s]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ForecastChart({ history, forecast, holdout, height = 300 }: { history: { day: string; n: number }[]; forecast: { day: string; yhat: number; lower: number; upper: number }[]; holdout?: any[]; height?: number }) {
  const rows: any[] = history.map((h) => ({ day: h.day, actual: h.n }));
  forecast.forEach((f) => rows.push({ day: f.day, yhat: f.yhat, band: [f.lower, f.upper] }));
  if (rows.length && forecast.length) {
    const last = rows[history.length - 1];
    last.yhat = last.actual; // connect lines
  }
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={rows} margin={{ left: -10, right: 8, top: 8 }}>
        {grid}
        <XAxis dataKey="day" tickFormatter={shortDate} tick={axis} minTickGap={32} />
        <YAxis tick={axis} />
        <Tooltip {...tip} labelFormatter={(l) => shortDate(String(l))} formatter={(v: any) => (Array.isArray(v) ? `${v[0]} – ${v[1]}` : v)} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area isAnimationActive={false} dataKey="band" name="80% interval" stroke="none" fill="#4f46e5" fillOpacity={0.15} />
        <Line isAnimationActive={false} type="monotone" dataKey="actual" name="Actual" stroke="currentColor" strokeOpacity={0.7} strokeWidth={2} dot={false} />
        <Line isAnimationActive={false} type="monotone" dataKey="yhat" name="Forecast" stroke="#4f46e5" strokeWidth={2} strokeDasharray="5 4" dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function HoldoutChart({ data, models }: { data: any[]; models: string[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ left: -10, right: 8 }}>
        {grid}
        <XAxis dataKey="day" tickFormatter={shortDate} tick={axis} minTickGap={24} />
        <YAxis tick={axis} />
        <Tooltip {...tip} labelFormatter={(l) => shortDate(String(l))} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Line isAnimationActive={false} dataKey="actual" name="Actual" stroke="currentColor" strokeOpacity={0.8} strokeWidth={2} dot={false} />
        {models.map((m, i) => (
          <Line isAnimationActive={false} key={m} dataKey={m} stroke={PALETTE[i + 1]} strokeWidth={1.5} strokeDasharray="4 3" dot={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function AnomalyChart({ daily, onDateClick }: { daily: any[]; onDateClick?: (date: string) => void }) {
  const rows = daily.map((d) => ({ ...d, stat: d.stat_flag ? d.n : null, iso: d.iso_flag ? d.n : null }));
  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart
        data={rows}
        margin={{ left: -10, right: 8, top: 8 }}
        style={{ cursor: onDateClick ? "pointer" : "default" }}
        onClick={(e: any) => {
          if (e && e.activePayload && e.activePayload[0] && onDateClick) {
            onDateClick(e.activePayload[0].payload.day);
          }
        }}
      >
        {grid}
        <XAxis dataKey="day" tickFormatter={shortDate} tick={axis} minTickGap={32} />
        <YAxis tick={axis} />
        <Tooltip {...tip} labelFormatter={(l) => shortDate(String(l))} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line isAnimationActive={false} dataKey="upper" name="Upper threshold" stroke="#9ca3af" strokeDasharray="4 3" dot={false} strokeWidth={1.2} />
        <Line isAnimationActive={false} dataKey="baseline" name="Baseline" stroke="currentColor" strokeOpacity={0.4} dot={false} strokeWidth={1.2} />
        <Line isAnimationActive={false} dataKey="n" name="Daily volume" stroke="#4f46e5" dot={false} strokeWidth={2} />
        <Scatter isAnimationActive={false} dataKey="stat" name="Rolling z-score flag" fill="#d55e00" shape="circle" />
        <Scatter isAnimationActive={false} dataKey="iso" name="Isolation Forest flag" fill="#009e73" shape="diamond" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function ClusterScatter({ points, k }: { points: { x: number; y: number; cluster: number }[]; k: number }) {
  return (
    <ResponsiveContainer width="100%" height={380}>
      <ScatterChart margin={{ left: -10, right: 8, top: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.15} />
        <XAxis type="number" dataKey="x" tick={axis} name="PC1" />
        <YAxis type="number" dataKey="y" tick={axis} name="PC2" />
        <ZAxis range={[22, 22]} />
        <Tooltip {...tip} cursor={{ strokeDasharray: "3 3" }} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {Array.from({ length: k }, (_, c) => (
          <Scatter isAnimationActive={false} key={c} name={`Cluster ${c}`} data={points.filter((p) => p.cluster === c)} fill={[...PALETTE, "#0e7490", "#be123c", "#4d7c0f", "#a16207"][c % 12]} fillOpacity={0.65} />
        ))}
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function ConfusionMatrix({ labels, matrix }: { labels: string[]; matrix: number[][] }) {
  const rowSums = matrix.map((r) => r.reduce((a, b) => a + b, 0));
  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-0.5 text-xs">
        <thead>
          <tr>
            <th className="p-1 text-right text-muted-foreground">true ↓ / predicted →</th>
            {labels.map((l) => (
              <th key={l} className="max-w-[72px] p-1 text-center font-medium leading-tight">{l}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <th className="whitespace-nowrap p-1 pr-2 text-right font-medium">{labels[i]}</th>
              {row.map((v, j) => {
                const frac = rowSums[i] ? v / rowSums[i] : 0;
                return (
                  <td
                    key={j}
                    title={`${labels[i]} → ${labels[j]}: ${v} (${(frac * 100).toFixed(0)}% of true class)`}
                    className={cn("h-10 w-14 rounded text-center font-medium", i === j ? "text-white" : "text-foreground")}
                    style={{ background: i === j ? `rgba(79,70,229,${0.25 + frac * 0.75})` : `rgba(213,94,0,${Math.min(frac * 3, 0.85)})` }}
                  >
                    {v}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
