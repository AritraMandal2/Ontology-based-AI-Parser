# My agent: ChromatographyOntologyAgent
One-liner: A GxP-compliant AI assistant for Ontology-Triggered Chromatography Extraction, Quality Assurance, and Video Visualization.

Tool coverage:
- Memory: Remembers instrument runs, GxP audit events, and quarantine records.
- Tools: Instrument telemetry extraction, QA approval, knowledge graph query, video generation for chromatography analytes and instruments using Google's Omni model (gemini-omni-flash-preview).
- Catalog/UI: Catalog of chromatogram runs, analytes, detectors, columns, and equipment classes.
- Image/Video gen: Generate short video visualizations for chromatography analytes, columns, and analytical instruments using Google's Omni model (gemini-omni-flash-preview) in the global region.
- Sandbox: Analytical calculation of retention time % RSD and USP theoretical plate counts.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch: video generation with Omni model (gemini-omni-flash-preview) in global region, GCS public bucket hosting, ALCOA++ audit trail.
