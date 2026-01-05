# Client History Analysis

Synthesize all call transcripts for one client into relationship-level insights.

## Instructions

1. **First, analyze each transcript in parallel**: For each transcript file in the client folder, spawn a parallel agent using `analyze-transcript.md`. Run ALL transcript analyses concurrently to minimize latency.

2. **Then, aggregate**: Once all parallel analyses complete, synthesize the structured outputs into the client-level analysis below.

```
Example: Client with 10 calls
├── call-1.md ──▶ [Agent 1] ──┐
├── call-2.md ──▶ [Agent 2] ──┤
├── call-3.md ──▶ [Agent 3] ──┼──▶ Wait for all ──▶ Aggregate below
├── ...       ──▶ [Agent ...] ┤
└── call-10.md ─▶ [Agent 10] ─┘
     (all spawn in parallel)
```

---

## Output Format

### Relationship Timeline
| Date | Call Title | Key Event | Sentiment |
|------|------------|-----------|-----------|
{table of calls with pivotal moments marked}

Turning points:
- {date}: {what changed and why}

### Recurring Pain Points
| Pain Point | Frequency | First Mentioned | Last Mentioned | Resolved? |
|------------|-----------|-----------------|----------------|-----------|
{aggregated from transcript Pain Points, ranked by frequency}

### Feature Requests (Aggregated)
| Feature | Times Requested | Urgency Trend | Status |
|---------|-----------------|---------------|--------|
{aggregated from transcript Feature Requests}

### Stakeholder Map
| Name | Role | First Seen | Last Seen | Type | Engagement Trend |
|------|------|------------|-----------|------|------------------|
{aggregated from transcript Stakeholders, showing evolution}

Key dynamics:
- Champion: {name and status}
- Decision maker: {name}
- Blocker/skeptic: {if any}

### Competitive Pressure
| Competitor | Mentions | Trend | Threat Level |
|------------|----------|-------|--------------|
{aggregated from transcript Competitive Mentions}

### Objection Patterns
| Objection Type | Occurrences | Resolution Rate | Notes |
|----------------|-------------|-----------------|-------|
{aggregated from transcript Objections}

### Health Trajectory
```
{sentiment over time: emoji or simple chart}
Call 1 (date): ⬆️ positive
Call 2 (date): ➡️ neutral
Call 3 (date): ⬇️ negative
...
```
Trend: {improving|stable|declining}

### Unmet Needs
{synthesized from unresolved pain points, implicit feature requests, and recurring themes}
1. {need} — Evidence: {which calls}
2. ...

### Expansion Opportunities
{synthesized from buying signals, new use cases mentioned, additional stakeholders}
1. {opportunity} — Signal strength: {high|medium|low}
2. ...

### Churn Risk Factors
{synthesized from risks, declining sentiment, competitor mentions}
1. {risk factor} — Severity: {high|medium|low}
2. ...

### Open Action Items
| Owner | Action | Committed Date | Status |
|-------|--------|----------------|--------|
{aggregated from transcript Action Items, tracking what's still open}

---

## Client Summary Card

```yaml
client: {name}
calls_analyzed: {count}
date_range: {first_call} to {last_call}
health_score: {1-10}
health_trend: {improving|stable|declining}
top_risk: {one-liner}
top_opportunity: {one-liner}
next_action: {specific recommended action}
```
