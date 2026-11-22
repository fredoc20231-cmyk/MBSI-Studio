<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.

## What Lovable manages

Rules outside this block are the project's own. Change the pieces below in
Lovable, not by hand. With the [Lovable MCP](https://mcp.lovable.dev)
connected, `send_message` asks Lovable to do it; otherwise ask the user to
use the editor.

- **Database.** Do not add or edit `supabase/migrations/` or `drizzle/`.
  Ask Lovable to change the schema.
- **Generated files.** Do not edit a file whose header says it is automatically
  generated.
- **AI gateway.** Keep model calls on Lovable's gateway, and keep
  `LOVABLE_API_KEY` out of browser code.
- **Connectors.** Lovable provides native connectors. `list_connectors` shows
  which are enabled; `add_connector` only returns the dashboard link. When a
  connector is enabled, calls go through the connector gateway and need
  `LOVABLE_API_KEY`. When Lovable does not provide one, users can bring their
  own key and store it in Secrets.
- **Secrets.** Lovable manages them. Do not put secret values in the repo.
<!-- LOVABLE:END -->

## MBSI Studio
- All scientific computation lives in the external MBSI FastAPI backend; this app only calls it via `src/lib/mbsi-api.ts` (base URL from `VITE_MBSI_API_URL`). Why: single API source of truth.
- Never render fabricated results; show empty/unavailable states until the API returns observed data. Why: biomedical data integrity.
- Map the Lovable working root to `frontend/` in the existing source repository; publish changes through explicit GitHub API commits and separate pull requests without modifying backend files or claiming automatic Git sync. Why: preserve the source backend and review boundary despite the existing-repository sync limitation.
- Resolve scientific service addresses in `mbsi-connection.ts` at request time; validate health before a tab-scoped override and clear query data on service changes. Why: avoid hosted localhost requests and mixing identifiers across scientific services.

- Never modify scientific Python from Lovable; frontend consumes backend contracts only and shows blocked states. Why: audit instruction.
- Keep Loupe function descriptions and capability schemas in `src/lib/loupe.ts`, with all execution and artifacts through the optional v1 adapter in `mbsi-api.ts`; do not bundle R sources or the converter. Why: preserve the external scientific boundary and vendor redistribution restrictions.
- Gate Loupe actions by live capabilities and scope runs/artifacts to service plus dataset; setup is administrator-managed and images require a separate renderer. Why: prevent unsupported conversions and cross-service data mixing.
- Subscribe service-aware UI through `useMbsiConnection` with an SSR-safe external store snapshot. Why: changing the scientific service must update query keys immediately rather than leaving mounted views on an old address.
- Keep the public hosted-service fallback in the connection resolver and reject upload responses marked unsupported before caching datasets. Why: environment omissions must not disconnect hosted builds, and receipt of bytes is not evidence of a parsed scientific dataset.
- Submit .cloupe files only through the external upload contract; do not equate LoupeR export support with a reader. Why: interactive views require actual decoded observations from an authorized service reader.
