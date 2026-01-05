# Portfolio Analysis

Synthesize all clients into strategic insights across your customer base.

## Instructions

1. **First, analyze each client in parallel**: For each client folder, spawn a parallel agent using `analyze-client-history.md`. Run ALL client analyses concurrently.

2. **Then, aggregate**: Once all parallel client analyses complete, synthesize into portfolio-level insights below.

```
Example: Portfolio with 50 clients
├── client-a/     ──▶ [Agent 1]  ──┐
├── client-b/     ──▶ [Agent 2]  ──┤
├── client-c/     ──▶ [Agent 3]  ──┤
├── ...           ──▶ [Agent ...] ─┼──▶ Wait for all ──▶ Aggregate below
└── client-n/     ──▶ [Agent 50] ──┘
     (all spawn in parallel)
```

Note: Each client agent will itself spawn parallel agents for its transcripts (see `analyze-client-history.md`), creating a two-level parallelization tree.

---

## Output Format

### Portfolio Health Overview
| Client | Health Score | Trend | Top Risk | Top Opportunity |
|--------|--------------|-------|----------|-----------------|
{from each Client Summary Card, sorted by health score}

At-risk accounts: {count}
Expanding accounts: {count}
Stable accounts: {count}

### Pain Points Heatmap
| Pain Point | Clients Affected | Client Names | Category |
|------------|------------------|--------------|----------|
{aggregated from client Recurring Pain Points, ranked by frequency}

Top 3 systemic issues:
1. {pain point} — Affects {n} clients — Impact: {description}
2. ...
3. ...

### Feature Demand
| Feature | Clients Requesting | Request Intensity | Segment |
|---------|-------------------|-------------------|---------|
{aggregated from client Feature Requests}

Priority matrix:
- High demand + High urgency: {list}
- High demand + Low urgency: {list}
- Low demand + High urgency: {list}

### Competitive Landscape
| Competitor | Clients Mentioning | Threat Trend | Primary Battleground |
|------------|-------------------|--------------|---------------------|
{aggregated from client Competitive Pressure}

Positioning gaps:
- We lose on: {themes}
- We win on: {themes}

### Common Objection Patterns
| Objection | Frequency | Avg Resolution Rate | Best Response |
|-----------|-----------|---------------------|---------------|
{aggregated from client Objection Patterns}

### Churn Risk Ranking
| Client | Risk Level | Primary Risk Factor | Days Since Last Call |
|--------|------------|---------------------|---------------------|
{clients sorted by churn risk, from client Churn Risk Factors}

Immediate attention needed: {list clients with high risk}

### Expansion Pipeline
| Client | Opportunity | Signal Strength | Estimated Value |
|--------|-------------|-----------------|-----------------|
{from client Expansion Opportunities, ranked by strength}

### Stakeholder Insights
Champions across portfolio: {count}
- Most engaged: {top 3 champions}
- At-risk champions: {champions at declining accounts}

Decision maker patterns:
- Common titles: {list}
- Avg stakeholders per deal: {n}

---

## Strategic Recommendations

### For Product
1. {recommendation} — Evidence: {n} clients, {specific examples}
2. ...
3. ...

### For Sales
1. {recommendation} — Evidence: {pattern observed}
2. ...
3. ...

### For Customer Success
1. {recommendation} — Evidence: {at-risk patterns}
2. ...
3. ...

### For Leadership
1. {strategic insight} — Implication: {what to do}
2. ...
3. ...

---

## Portfolio Summary

```yaml
total_clients: {count}
total_calls_analyzed: {sum}
date_range: {earliest} to {latest}
avg_health_score: {n}/10
at_risk_count: {n}
expansion_pipeline_count: {n}
top_product_gap: {feature/capability}
top_competitive_threat: {competitor}
most_urgent_action: {specific action}
```
