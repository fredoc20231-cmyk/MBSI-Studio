import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LinkedSpatialAtlas } from "@/components/mbsi/LinkedSpatialAtlas";
import { mbsi, type DatasetSummary } from "@/lib/mbsi-api";

vi.mock("@/lib/mbsi-api", () => ({
  mbsi: {
    features: vi.fn(async () => ({
      dataset_id: "sample-a", genes: ["GENE1"], annotations: ["cluster"], total_genes: 1,
    })),
    spatial: vi.fn(async (id: string, selection: { gene?: string; annotation?: string }) => ({
      dataset_id: id,
      feature: selection.gene || selection.annotation || "",
      categorical: Boolean(selection.annotation),
      source_layer: selection.annotation ? "obs" : "X",
      total_observations: 3,
      returned_observations: 3,
      downsampled: false,
      coordinate_system: "source_obsm_spatial",
      points: [
        { barcode: "spot1", x: 10, y: 10, value: selection.annotation ? "immune" : 1 },
        { barcode: "spot2", x: 20, y: 20, value: selection.annotation ? "tumor" : 3 },
        { barcode: "spot3", x: 30, y: 30, value: selection.annotation ? "immune" : 5 },
      ],
    })),
    selectRegion: vi.fn(async (id: string) => ({
      dataset_id: id, feature: "GENE1", categorical: false,
      source_layer: "X", coordinate_system: "source_obsm_spatial",
      total_observations: 3, selected_observations: 2,
      barcodes: ["spot1", "spot2"], barcodes_truncated: false,
      statistics: { mean: 2, median: 2, fraction_detected: 1 },
      inference: false, warnings: [],
    })),
  },
}));

const datasets: DatasetSummary[] = ["sample-a", "sample-b"].map((dataset_id) => ({
  dataset_id, sample_id: dataset_id, project_id: "project-1",
  platform: "visium", readiness: {}, summary: {}, has_spatial_data: true,
}));

function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <LinkedSpatialAtlas selectedIds={["sample-a", "sample-b"]} datasets={datasets} />
    </QueryClientProvider>,
  );
}

beforeEach(() => vi.clearAllMocks());

describe("Lovable linked spatial atlas", () => {
  it("renders two observed samples under the same gene selection", async () => {
    mount();
    expect(await screen.findByRole("img", { name: "Spatial atlas for sample-a" })).toBeInTheDocument();
    expect(await screen.findByRole("img", { name: "Spatial atlas for sample-b" })).toBeInTheDocument();
    expect(mbsi.spatial).toHaveBeenCalledWith("sample-a", { gene: "GENE1", limit: 5000 });
    expect(mbsi.spatial).toHaveBeenCalledWith("sample-b", { gene: "GENE1", limit: 5000 });
    expect(screen.getByText(/Shared displayed range across loaded panels/)).toBeInTheDocument();
  });

  it("submits a drawn polygon to the exact backend ROI endpoint", async () => {
    mount();
    const svg = await screen.findByRole("img", { name: "Spatial atlas for sample-a" });
    Object.defineProperty(svg, "getScreenCTM", {
      configurable: true, value: () => ({ inverse: () => ({}) }),
    });
    Object.defineProperty(svg, "createSVGPoint", {
      configurable: true,
      value: () => ({
        x: 0, y: 0,
        matrixTransform(this: { x: number; y: number }) { return { x: this.x, y: this.y }; },
      }),
    });
    fireEvent.click(screen.getAllByRole("button", { name: "Draw ROI" })[0]);
    fireEvent.click(svg, { clientX: 8, clientY: 8 });
    fireEvent.click(svg, { clientX: 28, clientY: 8 });
    fireEvent.click(svg, { clientX: 28, clientY: 28 });
    fireEvent.click(screen.getAllByRole("button", { name: "Analyze exact ROI" })[0]);
    await waitFor(() => expect(mbsi.selectRegion).toHaveBeenCalledWith(
      "sample-a",
      expect.objectContaining({ gene: "GENE1", polygon: [[8, 8], [28, 8], [28, 28]] }),
    ));
    expect(await screen.findByText(/Exact selected cells\/spots: 2/)).toBeInTheDocument();
  });
});
