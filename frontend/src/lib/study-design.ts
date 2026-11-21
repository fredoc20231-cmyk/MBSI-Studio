// Study design: groups, samples and the files expected for each sample.
// Pure helpers only; nothing here produces scientific results.

export type GroupKind = "condition" | "timepoint" | "donor" | "label";

export const GROUP_KINDS: { id: GroupKind; label: string }[] = [
  { id: "condition", label: "Condition" },
  { id: "timepoint", label: "Timepoint" },
  { id: "donor", label: "Patient / donor" },
  { id: "label", label: "Custom label" },
];

export type FileRole = "fastq" | "cytassist" | "slide" | "processed" | "other";

export const FILE_STEPS: {
  role: FileRole;
  title: string;
  hint: string;
  accept: string;
  raw: boolean;
}[] = [
  {
    role: "fastq",
    title: "FASTQ reads",
    hint: "Raw sequencing reads (R1, R2, index). Several files allowed.",
    accept: ".fastq,.fq,.gz",
    raw: true,
  },
  {
    role: "cytassist",
    title: "CytAssist image",
    hint: "CytAssist capture image (.tif / .tiff).",
    accept: ".tif,.tiff,.png,.jpg,.jpeg",
    raw: true,
  },
  {
    role: "slide",
    title: "Slide image",
    hint: "High-resolution H&E or immunofluorescence slide.",
    accept: ".tif,.tiff,.svs,.ndpi,.png,.jpg,.jpeg,.btf",
    raw: true,
  },
  {
    role: "processed",
    title: "Processed output",
    hint: "Space Ranger / Xenium output or .h5ad, if already processed.",
    accept: ".h5ad,.h5,.zip,.tar,.gz,.zarr,.parquet,.csv",
    raw: false,
  },
  {
    role: "other",
    title: "Any other file",
    hint: "Any other dataset or supporting file. The backend decides if it can use it.",
    accept: "",
    raw: false,
  },
];

export type FileStatus = "pending" | "uploading" | "accepted" | "rejected";

export type StudyFile = {
  id: string;
  name: string;
  size: number;
  role: FileRole;
  status: FileStatus;
  message?: string;
  datasetId?: string;
};

export type Group = { id: string; name: string; kind: GroupKind };
export type Sample = { id: string; name: string; groupIds: string[]; files: StudyFile[] };

/** Guess what a file is from its name. Unrecognised files are kept as "other". */
export function classifyFile(name: string): FileRole {
  const n = name.toLowerCase();
  if (/\.(fastq|fq)(\.gz)?$/.test(n)) return "fastq";
  if (/\.(h5ad|h5|zarr|parquet)$/.test(n) || /(outs|xenium|spaceranger).*\.(zip|tar|tar\.gz)$/.test(n))
    return "processed";
  if (/\.(svs|ndpi|btf)$/.test(n)) return "slide";
  if (/\.(tif|tiff|png|jpe?g)$/.test(n)) return /cytassist|cyt_?assist/.test(n) ? "cytassist" : "slide";
  if (/\.(zip|tar|tar\.gz)$/.test(n)) return "processed";
  return "other";
}

/** Derive a sample name from a file name, e.g. "S1_L001_R1_001.fastq.gz" -> "S1". */
export function sampleKeyFromName(name: string): string {
  const base = name.replace(/\.(fastq|fq|tiff?|png|jpe?g|svs|ndpi|btf|h5ad|h5|zip|tar|gz|zarr|parquet|csv)/gi, "");
  const stripped = base
    .replace(/_S\d+(_L\d{3})?(_[RI]\d)?(_\d{3})?$/i, "")
    .replace(/_L\d{3}(_[RI]\d)?(_\d{3})?$/i, "")
    .replace(/[_-]?(R1|R2|I1|I2)([_-]\d{3})?$/i, "")
    .replace(/[_-]?(cytassist|cyt_?assist|he|h&e|slide|image|outs)$/i, "");
  return stripped || base || name;
}

/** Group dropped files into samples by shared name prefix. */
export function bulkAssign(names: string[]): { sample: string; name: string; role: FileRole }[] {
  return names.map((name) => ({ sample: sampleKeyFromName(name), name, role: classifyFile(name) }));
}

/** Which guided steps a sample still lacks. Processed output alone is enough to analyse. */
export function missingSteps(sample: Sample): FileRole[] {
  const has = new Set(sample.files.filter((f) => f.status !== "rejected").map((f) => f.role));
  if (has.has("processed")) return [];
  return (["fastq", "cytassist", "slide"] as FileRole[]).filter((r) => !has.has(r));
}

export function samplesInGroup(samples: Sample[], groupId: string): Sample[] {
  return samples.filter((s) => s.groupIds.includes(groupId));
}

/** A sample can hold one group per kind (one condition, one timepoint ...). */
export function assignGroup(sample: Sample, group: Group, groups: Group[]): Sample {
  const sameKind = new Set(groups.filter((g) => g.kind === group.kind).map((g) => g.id));
  return { ...sample, groupIds: [...sample.groupIds.filter((id) => !sameKind.has(id)), group.id] };
}
