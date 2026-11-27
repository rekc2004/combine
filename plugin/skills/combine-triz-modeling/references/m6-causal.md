# M6. Evidence-backed Causal Analysis

This is an optional deepening stage, not a tax on every fixed defect. If an evidence-backed fix already passes its regression check, deliver that result and offer M6 separately for an unclear/recurring root cause. The owner chooses the extra depth unless the task already authorizes it.

1. **Undesired effect:** observable symptom, location, time, and evidence—not a guessed root cause.
2. **Causal graph:** ask "why?" and record alternative branches. Use AND when several conditions are jointly required and OR when each can independently produce the effect.
3. **Validate every important edge:** cite a test, log, code path, measurement, or direct observation. Mark unknown edges as hypotheses.
4. **Classify actions:** useful / insufficient / harmful. Find controllable causes with nearby resources.
5. **Stop rule:** stop at a cause the project can change and verify; do not stop merely at a convenient component or continue into untestable history.

Gate: choose 1–3 key causes and frame each with M1/A1. A fix for an unverified cause is an experiment, not a diagnosis. After implementation, rerun the observation that demonstrated the original defect.
