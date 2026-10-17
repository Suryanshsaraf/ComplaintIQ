import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const fmtNum = (n: number | null | undefined, digits = 0) =>
  n === null || n === undefined || Number.isNaN(n) ? "—" : n.toLocaleString(undefined, { maximumFractionDigits: digits });

export const fmtPct = (n: number | null | undefined, digits = 1) =>
  n === null || n === undefined || Number.isNaN(n) ? "—" : `${n.toFixed(digits)}%`;

export const fmtDate = (d: string | null | undefined) =>
  d ? new Date(d + (d.length === 10 ? "T00:00:00" : "")).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "2-digit" }) : "—";

export const shortDate = (d: string) =>
  new Date(d + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" });

/** Okabe-Ito based categorical palette (colour-blind safe) */
export const PALETTE = ["#4f46e5", "#e69f00", "#009e73", "#d55e00", "#56b4e9", "#cc79a7", "#7a7a2e", "#6b7280"];
export const SENTIMENT_COLORS: Record<string, string> = { negative: "#d55e00", neutral: "#9ca3af", positive: "#009e73" };
export const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-800 border-red-200",
  high: "bg-orange-100 text-orange-800 border-orange-200",
  medium: "bg-amber-100 text-amber-800 border-amber-200",
  low: "bg-slate-100 text-slate-700 border-slate-200",
};
export const STATUS_STYLES: Record<string, string> = {
  open: "bg-red-50 text-red-700 border-red-200",
  investigating: "bg-blue-50 text-blue-700 border-blue-200",
  acknowledged: "bg-amber-50 text-amber-700 border-amber-200",
  resolved: "bg-emerald-50 text-emerald-700 border-emerald-200",
};
