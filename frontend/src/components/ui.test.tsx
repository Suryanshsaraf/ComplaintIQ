import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Async, ErrorBox, SeverityBadge, Tabs } from "./ui";

describe("ui components", () => {
  it("renders severity badge text", () => {
    render(<SeverityBadge severity="critical" />);
    expect(screen.getByText("critical")).toBeInTheDocument();
  });
  it("Async shows error with retry", () => {
    const reload = vi.fn();
    render(<Async state={{ data: null, error: "boom", loading: false, reload }}>{() => <div>ok</div>}</Async>);
    expect(screen.getByRole("alert")).toHaveTextContent("boom");
    fireEvent.click(screen.getByText("Retry"));
    expect(reload).toHaveBeenCalled();
  });
  it("Async renders children when data present", () => {
    render(<Async state={{ data: { n: 3 }, error: null, loading: false, reload: () => {} }}>{(d) => <div>count {d.n}</div>}</Async>);
    expect(screen.getByText("count 3")).toBeInTheDocument();
  });
  it("Tabs call onChange", () => {
    const onChange = vi.fn();
    render(<Tabs value="a" onChange={onChange} tabs={[{ id: "a", label: "A" }, { id: "b", label: "B" }]} />);
    fireEvent.click(screen.getByText("B"));
    expect(onChange).toHaveBeenCalledWith("b");
  });
  it("ErrorBox without retry has no button", () => {
    render(<ErrorBox message="x" />);
    expect(screen.queryByText("Retry")).toBeNull();
  });
});
