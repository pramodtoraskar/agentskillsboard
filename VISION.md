# Vision — Agent Skills Board

## Why this matters

Machine-learning artifacts converged on a small set of common patterns (weights, config, model cards) and a few well-known hubs where **authors publish** and **consumers discover** with a shared mental model.

Agent extensibility is still fragmented: capabilities show up as **different shapes** (for example, long-lived MCP servers, repo-based `SKILL.md` skill folders, and product-specific tools or functions), and as **several parallel indexes** and lists that do not share one schema, one trust model, or one definition of “official.”

That fragmentation creates real cost: duplicated effort, unclear maintenance, weak supply-chain visibility, and no reliable first stop for questions like “where is the maintained entry for this vendor integration?”

**Agent Skills Board** exists to reduce that cost for one important slice of the ecosystem—public, file-based skills centered on `SKILL.md`—by making discovery, scoring, and browsing **repeatable and local-first**.

## What we are building (today)

**Agent Skills Board** is a **crawler-first registry** and **open-source dashboard**:

- Discover `SKILL.md` paths across GitHub with minimal API usage (search, trees, raw fetches).
- Normalize front matter and metadata into a **single JSON index** with transparent **scoring signals** (org allowlists, stars, recency, CI/tests heuristics, and similar).
- Serve **search, filters, stats, and detail views** via a small API and static UI—no registration wall, no opaque curation.

The goal of this phase is **evidence-backed discovery**: one place *you* run that answers “what exists?” and “how stale or credible does it look?” for folder-based skills—not a claim to be the universal hub for every agent technology.

## North star (where this could go)

The harder, largely unsolved problem is a **governed, publisher-authoritative registry** for enterprise-grade agent capabilities: strong identity for who published a skill, how updates are announced, how consumers pin versions, and how security and support expectations are expressed.

**Agent Skills Board** aims to grow **toward** that class of problem without pretending the current codebase already solves it:

- **Provenance** — clearer publisher identity and linkage to source repos and releases.
- **Trust tiers** — move from heuristic “official org” lists toward attestable signals where possible.
- **Operations** — freshness SLAs, diffable index versions, and audit-friendly exports for downstream systems.
- **Federation or mapping** — honest handling of adjacent formats (for example MCP listings) as *related* indexes, not as a second undocumented scraper, unless scope and schema are explicitly defined.

## What we are not claiming (yet)

- **Agent Skills Board** does **not** unify MCP, `SKILL.md`, and proprietary tool formats into one standard; it **indexes one family** well.
- Heuristic scores are **not** security reviews or vendor warranties.
- A local index is **not** a global canonical hub until publishers and consumers agree it should be—governance is a product and community problem as much as an engineering one.

## Who benefits

- **Platform and agent builders** who need a grounded inventory of public folder skills.
- **Security and platform engineering** teams who want indexes they can **run, diff, and air-gap** instead of only SaaS directories.
- **Authors** who want discoverability without each team re-solving GitHub search and scoring.

## How to use this document

Treat `VISION.md` as the **intent** behind `README.md` (how to run things). When trade-offs appear—scope creep, new formats, “official” badges—check whether the change moves **Agent Skills Board** **toward** transparent discovery and publisher clarity, or only **toward** more undifferentiated listings.

---

*This vision is meant to evolve with the project; open issues or pull requests when the implementation and the narrative drift apart.*
