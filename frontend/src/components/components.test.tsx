import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

import { SourceList } from "./SourceList";
import { StatusBadge, EmptyState } from "./ui";
import { FileDropzone } from "./FileDropzone";
import type { SourceCitation } from "../lib/types";

function renderWithProviders(node: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{node}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("StatusBadge", () => {
  it("renders indexed status", () => {
    render(<StatusBadge status="indexed" />);
    expect(screen.getByText("indexed")).toBeInTheDocument();
  });

  it("renders failed status", () => {
    render(<StatusBadge status="failed" />);
    expect(screen.getByText("failed")).toBeInTheDocument();
  });
});

describe("EmptyState", () => {
  it("renders title and children", () => {
    renderWithProviders(
      <EmptyState title="Nothing here">
        <p>Add something.</p>
      </EmptyState>,
    );
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.getByText("Add something.")).toBeInTheDocument();
  });
});

describe("SourceList", () => {
  const sources: SourceCitation[] = [
    {
      chunk_id: "c1",
      document_id: "d1",
      filename: "network-security.pdf",
      score: 0.9,
      page_start: 12,
      page_end: 12,
      excerpt: "Zero trust assumes nothing is trusted.",
    },
  ];

  it("renders empty message", () => {
    renderWithProviders(<SourceList sources={[]} />);
    expect(screen.getByText(/could not be grounded/i)).toBeInTheDocument();
  });

  it("renders sources and calls onSelect", async () => {
    const onSelect = vi.fn();
    renderWithProviders(<SourceList sources={sources} onSelect={onSelect} />);
    expect(screen.getByText("network-security.pdf")).toBeInTheDocument();
    await userEvent.click(screen.getByText("network-security.pdf"));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });
});

describe("FileDropzone", () => {
  it("renders dropzone label", () => {
    renderWithProviders(<FileDropzone />);
    expect(screen.getByText(/Drag & drop files here/i)).toBeInTheDocument();
  });

  it("shows error toast on failed upload", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { message: "boom" } }), { status: 500 })));
    renderWithProviders(<FileDropzone />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["content"], "notes.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(await screen.findByText("boom")).toBeInTheDocument();
  });
});
