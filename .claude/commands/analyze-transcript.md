# Transcript Analysis

Analyze this call transcript and output structured insights.

## Instructions

Extract the following from the transcript. Be specific with quotes and timestamps. Output as structured sections that can be aggregated across multiple calls.

---

## Output Format

### Pain Points
- `[QUOTE]` "{exact quote}" `[TIMESTAMP]` — Category: {technical|operational|business|organizational}

### Feature Requests
- `[EXPLICIT]` {feature description} — "{supporting quote}"
- `[IMPLICIT]` {inferred need} — "{supporting quote}"

### Competitive Mentions
- `[COMPETITOR]` {name} — Sentiment: {positive|negative|neutral} — Context: {why mentioned}

### Objections
- `[OBJECTION]` {type: price|technical|timeline|resources|approval} — "{quote}" — Resolved: {yes|no|partial}

### Buying Signals
- `[SIGNAL]` {strength: strong|moderate|weak} — "{quote or behavior}"

### Stakeholders
- `[PERSON]` {name} — Role: {role} — Type: {decision-maker|influencer|champion|skeptic|technical|business}

### Timeline
- `[DEADLINE]` {date or timeframe} — Driver: {what's driving it} — Urgency: {high|medium|low}

### Technical Requirements
- `[REQUIREMENT]` {category: infrastructure|scale|integration|security|compliance} — {details}

### Success Metrics
- `[METRIC]` {what they'll measure} — Current: {baseline} — Target: {goal}

### Risks
- `[RISK]` {description} — Severity: {high|medium|low} — Mitigation: {if discussed}

### Action Items
- `[ACTION-US]` {what we committed to} — Due: {when}
- `[ACTION-THEM]` {what they committed to} — Due: {when}

### Sentiment
- Overall: {positive|neutral|negative}
- Engagement: {high|medium|low}
- Red flags: {list or "none"}

### Summary
{2-3 sentences: key insight, recommended action, risk level}

---

## Transcript

{paste transcript here}
