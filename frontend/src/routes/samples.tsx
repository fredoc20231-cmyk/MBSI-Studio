import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Check, FolderUp, LoaderCircle, Plus, Trash2, Upload, Users, X } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { EmptyState, PageHeader, Workspace } from "@/components/mbsi/Workspace";
import { mbsi, type DatasetUploadResponse } from "@/lib/mbsi-api";
import {
  assignGroup,
  bulkAssign,
  FILE_STEPS,
  GROUP_KINDS,
  missingSteps,
  samplesInGroup,
  type FileRole,
  type Group,
  type GroupKind,
  type Sample,
  type StudyFile,
} from "@/lib/study-design";

export const Route = createFileRoute("/samples")({
  head: () => ({
    meta: [
      { title: "Samples and groups — MBSI Studio" },
      {
        name: "description",
        content:
          "Upload FASTQ, CytAssist, slide and processed files, organise samples and assign them to conditions, timepoints and donors.",
      },
      { property: "og:title", content: "Samples and groups — MBSI Studio" },
      {
        property: "og:description",
        content: "Study design for spatial omics: multi-file uploads, sample groups and guided file steps.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SamplesPage,
});

const STORE_KEY = "mbsi-study-design";
const uid = () => Math.random().toString(36).slice(2, 10);
const roleTitle = (r: FileRole) => FILE_STEPS.find((s) => s.role === r)!.title;
const fmtSize = (b: number) =>
  b > 1e9 ? `${(b / 1e9).toFixed(1)} GB` : b > 1e6 ? `${(b / 1e6).toFixed(1)} MB` : `${Math.ceil(b / 1e3)} KB`;

function SamplesPage() {
  const queryClient = useQueryClient();
  const [groups, setGroups] = useState<Group[]>([]);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [newGroup, setNewGroup] = useState("");
  const [newKind, setNewKind] = useState<GroupKind>("condition");
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (raw) {
        const d = JSON.parse(raw) as { groups: Group[]; samples: Sample[] };
        setGroups(d.groups ?? []);
        // Files themselves are not kept between visits; only their record.
        setSamples(
          (d.samples ?? []).map((s) => ({
            ...s,
            files: s.files.map((f) => (f.status === "uploading" ? { ...f, status: "rejected", message: "Interrupted" } : f)),
          })),
        );
      }
    } catch {
      /* ignore */
    }
    setLoaded(true);
  }, []);
  useEffect(() => {
    if (loaded) localStorage.setItem(STORE_KEY, JSON.stringify({ groups, samples }));
  }, [groups, samples, loaded]);

  const updateFile = (sampleId: string, fileId: string, patch: Partial<StudyFile>) =>
    setSamples((cur) =>
      cur.map((s) =>
        s.id === sampleId ? { ...s, files: s.files.map((f) => (f.id === fileId ? { ...f, ...patch } : f)) } : s,
      ),
    );

  async function sendFile(sample: Sample, file: File, role: FileRole) {
    const rec: StudyFile = { id: uid(), name: file.name, size: file.size, role, status: "uploading" };
    setSamples((cur) => cur.map((s) => (s.id === sample.id ? { ...s, files: [...s.files, rec] } : s)));
    const groupParams = Object.fromEntries(
      GROUP_KINDS.map((k) => [k.id, groups.find((g) => g.kind === k.id && sample.groupIds.includes(g.id))?.name ?? ""]).filter(
        ([, v]) => v,
      ),
    );
    try {
      const result = await mbsi.upload(file, { sample_id: sample.name, file_role: role, ...groupParams });
      updateFile(sample.id, rec.id, { status: "accepted", datasetId: result.dataset_id });
      queryClient.setQueryData<DatasetUploadResponse[]>(["uploaded-datasets"], (cur = []) => [
        ...cur.filter((d) => d.dataset_id !== result.dataset_id),
        result,
      ]);
    } catch (error) {
      updateFile(sample.id, rec.id, { status: "rejected", message: (error as Error).message });
    }
  }

  function addSample(name?: string): Sample {
    const s: Sample = { id: uid(), name: name ?? `Sample ${samples.length + 1}`, groupIds: [], files: [] };
    setSamples((cur) => [...cur, s]);
    return s;
  }

  function bulkDrop(files: FileList | null) {
    if (!files?.length) return;
    const list = Array.from(files);
    const rows = bulkAssign(list.map((f) => f.name));
    const byName = new Map(samples.map((s) => [s.name, s]));
    const created: Sample[] = [];
    rows.forEach((row, i) => {
      let s = byName.get(row.sample);
      if (!s) {
        s = { id: uid(), name: row.sample, groupIds: [], files: [] };
        byName.set(row.sample, s);
        created.push(s);
      }
      const target = s;
      const role = row.role;
      queueMicrotask(() => void sendFile(target, list[i]!, role));
    });
    if (created.length) setSamples((cur) => [...cur, ...created]);
    const others = rows.filter((r) => r.role === "other").length;
    toast.success(`${list.length} file(s) sorted into ${byName.size} sample(s)`, {
      description: others
        ? `${others} file(s) had an unrecognised type and were kept as "other".`
        : undefined,
    });
  }

  const activeSample = samples.find((s) => s.id === active) ?? null;

  return (
    <Workspace>
      <PageHeader
        title="Samples and groups"
        description="Add many files at once or follow the guided steps per sample, then assign samples to conditions, timepoints, donors or your own labels."
        action={
          <Button asChild size="sm">
            <label className="cursor-pointer">
              <FolderUp /> Upload many files
              <input type="file" multiple className="sr-only" onChange={(e) => { bulkDrop(e.target.files); e.target.value = ""; }} />
            </label>
          </Button>
        }
      />

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          bulkDrop(e.dataTransfer.files);
        }}
        className="mb-4 rounded-xl border-2 border-dashed border-border bg-card p-5 text-center text-xs text-muted-foreground"
      >
        <Upload className="mx-auto mb-2 h-5 w-5 text-primary" />
        Drop FASTQ, CytAssist, slide or processed files here. Files sharing a name prefix (e.g. <span className="font-mono">TumorA_…</span>) are grouped into one sample.
      </div>

      <div className="grid gap-4 2xl:grid-cols-[300px_minmax(0,1fr)]">
        <section className="rounded-xl border border-border bg-card p-4 shadow-panel">
          <h2 className="flex items-center gap-2 text-sm font-semibold"><Users className="h-4 w-4 text-primary" /> Groups</h2>
          <form
            className="mt-3 flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!newGroup.trim()) return;
              setGroups((g) => [...g, { id: uid(), name: newGroup.trim(), kind: newKind }]);
              setNewGroup("");
            }}
          >
            <select aria-label="Group type" value={newKind} onChange={(e) => setNewKind(e.target.value as GroupKind)} className="h-8 rounded-md border border-input bg-background px-2 text-xs">
              {GROUP_KINDS.map((k) => <option key={k.id} value={k.id}>{k.label}</option>)}
            </select>
            <input aria-label="Group name" value={newGroup} onChange={(e) => setNewGroup(e.target.value)} placeholder="e.g. Treated" className="h-8 min-w-0 flex-1 rounded-md border border-input bg-background px-2 text-xs" />
            <Button type="submit" size="sm" variant="outline" aria-label="Add group"><Plus /></Button>
          </form>
          <div className="mt-4 space-y-4">
            {GROUP_KINDS.map((k) => {
              const list = groups.filter((g) => g.kind === k.id);
              if (!list.length) return null;
              return (
                <div key={k.id}>
                  <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{k.label}</div>
                  {list.map((g) => (
                    <div key={g.id} className="flex items-center justify-between rounded-md px-2 py-1.5 text-xs hover:bg-muted">
                      <span>{g.name} <span className="text-muted-foreground">· {samplesInGroup(samples, g.id).length} samples</span></span>
                      <button type="button" aria-label={`Delete ${g.name}`} onClick={() => { setGroups((c) => c.filter((x) => x.id !== g.id)); setSamples((c) => c.map((s) => ({ ...s, groupIds: s.groupIds.filter((id) => id !== g.id) }))); }} className="text-muted-foreground hover:text-destructive"><X className="h-3.5 w-3.5" /></button>
                    </div>
                  ))}
                </div>
              );
            })}
            {!groups.length && <p className="text-xs text-muted-foreground">No groups yet. Add a condition, timepoint, donor or label.</p>}
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card shadow-panel">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <h2 className="text-sm font-semibold">Samples ({samples.length})</h2>
            <Button size="sm" variant="outline" onClick={() => setActive(addSample().id)}><Plus /> Add sample (guided)</Button>
          </div>
          {!samples.length ? (
            <div className="h-56 p-3"><EmptyState title="No samples yet" body="Upload many files at once, or add a sample and follow the guided steps." icon={<FolderUp className="h-6 w-6" />} /></div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="text-left text-muted-foreground">
                  <tr className="border-b border-border">
                    <th className="px-4 py-2 font-medium">Sample</th>
                    {GROUP_KINDS.map((k) => <th key={k.id} className="px-2 py-2 font-medium">{k.label}</th>)}
                    <th className="px-2 py-2 font-medium">Files</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {samples.map((s) => {
                    const missing = missingSteps(s);
                    return (
                      <tr key={s.id} className={`border-b border-border last:border-0 ${active === s.id ? "bg-accent/50" : ""}`}>
                        <td className="px-4 py-2">
                          <input aria-label="Sample name" value={s.name} onChange={(e) => setSamples((c) => c.map((x) => (x.id === s.id ? { ...x, name: e.target.value } : x)))} className="w-32 rounded border border-transparent bg-transparent px-1 py-0.5 hover:border-input focus:border-input" />
                        </td>
                        {GROUP_KINDS.map((k) => {
                          const options = groups.filter((g) => g.kind === k.id);
                          const current = options.find((g) => s.groupIds.includes(g.id))?.id ?? "";
                          return (
                            <td key={k.id} className="px-2 py-2">
                              <select aria-label={`${k.label} for ${s.name}`} disabled={!options.length} value={current} onChange={(e) => {
                                const g = groups.find((x) => x.id === e.target.value);
                                setSamples((c) => c.map((x) => x.id !== s.id ? x : g ? assignGroup(x, g, groups) : { ...x, groupIds: x.groupIds.filter((id) => !options.some((o) => o.id === id)) }));
                              }} className="h-7 max-w-[120px] rounded border border-input bg-background px-1 disabled:opacity-40">
                                <option value="">—</option>
                                {options.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
                              </select>
                            </td>
                          );
                        })}
                        <td className="px-2 py-2 whitespace-nowrap">
                          {s.files.length} {missing.length ? <span className="text-muted-foreground">· needs {roleTitle(missing[0]!)}</span> : <span className="text-primary">· complete</span>}
                        </td>
                        <td className="px-2 py-2 whitespace-nowrap text-right">
                          <Button size="sm" variant="ghost" aria-label={`Files for ${s.name}`} onClick={() => setActive(s.id)}>Files</Button>
                          <button type="button" aria-label={`Remove ${s.name}`} onClick={() => { setSamples((c) => c.filter((x) => x.id !== s.id)); if (active === s.id) setActive(null); }} className="p-1 text-muted-foreground hover:text-destructive"><Trash2 className="h-3.5 w-3.5" /></button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {activeSample && (
            <div className="border-t border-border p-4">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold">Guided files for {activeSample.name}</h3>
                <button type="button" aria-label="Close guided files" onClick={() => setActive(null)} className="text-muted-foreground"><X className="h-4 w-4" /></button>
              </div>
              <ol className="grid gap-3 lg:grid-cols-2">
                {FILE_STEPS.map((step, i) => {
                  const files = activeSample.files.filter((f) => f.role === step.role);
                  const next = missingSteps(activeSample)[0] === step.role;
                  return (
                    <li key={step.role} className={`rounded-lg border p-3 ${next ? "border-primary" : "border-border"}`}>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="text-xs font-semibold">{i + 1}. {step.title} {step.role === "processed" && <span className="font-normal text-muted-foreground">(optional shortcut)</span>}</div>
                          <p className="mt-0.5 text-[11px] text-muted-foreground">{step.hint}</p>
                        </div>
                        <Button asChild size="sm" variant={next ? "default" : "outline"}>
                          <label className="cursor-pointer">
                            <Upload /> Add
                            <input type="file" multiple={step.role === "fastq" || step.role === "other"} accept={step.accept || undefined} className="sr-only" onChange={(e) => { Array.from(e.target.files ?? []).forEach((f) => void sendFile(activeSample, f, step.role)); e.target.value = ""; }} />
                          </label>
                        </Button>
                      </div>
                      {files.length > 0 && (
                        <ul className="mt-2 space-y-1">
                          {files.map((f) => (
                            <li key={f.id} className="flex items-center gap-2 text-[11px]">
                              {f.status === "uploading" ? <LoaderCircle className="h-3 w-3 animate-spin" /> : f.status === "accepted" ? <Check className="h-3 w-3 text-primary" /> : <X className="h-3 w-3 text-destructive" />}
                              <span className="truncate">{f.name}</span>
                              <span className="text-muted-foreground">{fmtSize(f.size)}</span>
                              {f.status === "rejected" && <span className="truncate text-destructive" title={f.message}>Not accepted by backend</span>}
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  );
                })}
              </ol>
              <p className="mt-3 text-[11px] text-muted-foreground">Raw files are sent to the scientific backend with their sample, group and file-type labels. If the backend cannot process a file type yet, it is marked “Not accepted by backend”.</p>
            </div>
          )}
        </section>
      </div>
    </Workspace>
  );
}
