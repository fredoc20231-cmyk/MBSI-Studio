import { describe, expect, it } from "vitest";
import { assignGroup, bulkAssign, classifyFile, missingSteps, type Group, type Sample } from "@/lib/study-design";

describe("study design", () => {
  it("recognises FASTQ, CytAssist, slide and processed files", () => {
    expect(classifyFile("S1_L001_R1_001.fastq.gz")).toBe("fastq");
    expect(classifyFile("S1_CytAssist.tif")).toBe("cytassist");
    expect(classifyFile("S1_HE.svs")).toBe("slide");
    expect(classifyFile("S1.h5ad")).toBe("processed");
    expect(classifyFile("notes.docx")).toBe("other");
  });

  it("groups bulk files of the same sample together", () => {
    const rows = bulkAssign(["TumorA_S1_L001_R1_001.fastq.gz", "TumorA_S1_L001_R2_001.fastq.gz", "TumorA_cytassist.tif"]);
    expect(new Set(rows.map((r) => r.sample))).toEqual(new Set(["TumorA"]));
  });

  it("asks for FASTQ, CytAssist and slide in order until processed output exists", () => {
    const s: Sample = { id: "s", name: "s", groupIds: [], files: [] };
    expect(missingSteps(s)).toEqual(["fastq", "cytassist", "slide"]);
    s.files.push({ id: "f", name: "a.h5ad", size: 1, role: "processed", status: "accepted" });
    expect(missingSteps(s)).toEqual([]);
  });

  it("keeps one group per kind but allows groups of different kinds", () => {
    const groups: Group[] = [
      { id: "ctl", name: "Control", kind: "condition" },
      { id: "trt", name: "Treated", kind: "condition" },
      { id: "d1", name: "Day 1", kind: "timepoint" },
    ];
    let s: Sample = { id: "s", name: "s", groupIds: [], files: [] };
    s = assignGroup(s, groups[0]!, groups);
    s = assignGroup(s, groups[2]!, groups);
    s = assignGroup(s, groups[1]!, groups);
    expect(s.groupIds.sort()).toEqual(["d1", "trt"]);
  });
});
