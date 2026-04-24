# Audit Backlog

Items surfaced during the image/SEO audit that are out of scope for the current fix and need follow-up work.

## 1. Base64-encoded property listing images

**Where:** `index.html` lines ~1059 and ~1063 (the featured listings on the home page — `5 Lakeside Court, Hope Island` and `18 Canal Drive, Broadbeach Waters`).

**Problem:**
- Each `<img>` currently inlines the full JPEG as a `data:image/jpeg;base64,…` URL (~500 KB per image, ~1 MB of the HTML payload before any other content loads).
- Inlined base64 images:
  - Cannot be lazy-loaded (already in the HTML, already parsed by the time `loading="lazy"` could skip them).
  - Cannot be cached across pages — each page load re-downloads the bytes as part of the HTML.
  - Bloat the initial HTML response, hurting TTFB and LCP.
  - Are ~33% larger than the raw JPEG due to base64 encoding overhead.

**Recommended fix (needs asset management):**
1. Extract the two JPEGs to files (e.g. `listings/5-lakeside-court-hope-island.jpg`, `listings/18-canal-drive-broadbeach-waters.jpg`).
2. Replace the inline `src="data:..."` with `src="/listings/<name>.jpg"`.
3. Keep the existing `alt`, `loading="lazy"`, `decoding="async"`, `width`, and `height` attributes.
4. Consider serving AVIF/WebP with `<picture>` fallbacks for another ~30 % size cut.

**Why out of scope here:** Requires creating an asset folder and a naming convention that the admin panel (`/admin/`) will then need to respect when uploading new listings — that is a separate infra change.
