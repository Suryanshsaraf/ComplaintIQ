import { describe, expect, it } from "vitest";
import { fmtNum, fmtPct, SEVERITY_STYLES } from "./utils";
import { qs } from "./api";

describe("formatters", () => {
  it("formats numbers and handles missing values", () => {
    expect(fmtNum(1234)).toBe((1234).toLocaleString());
    expect(fmtNum(null)).toBe("—");
    expect(fmtPct(12.345)).toBe("12.3%");
  });
  it("has a style for every severity", () => {
    ["critical", "high", "medium", "low"].forEach((s) => expect(SEVERITY_STYLES[s]).toBeTruthy());
  });
});

describe("qs", () => {
  it("drops empty values and encodes the rest", () => {
    expect(qs({ a: "x y", b: "", c: undefined, d: 3 })).toBe("?a=x+y&d=3");
    expect(qs({})).toBe("");
  });
});
