"""Exploratory follow-up to Pilot A (not pre-specified; run after seeing Pilot A's results).

Question: do the richness estimators work when the attacks are near-exchangeable draws from one
family (the six name-variants of AgentDojo's `important_instructions`), as opposed to a menu of
different attack algorithms (JailbreakBench) where Pilot A found no gain?
"""
import json
import sys
from pathlib import Path

from pilot_a import agentdojo_matrix, evaluate, summarise

VARIANTS = ["important_instructions", "important_instructions_no_model_name", "important_instructions_no_names",
            "important_instructions_no_user_name", "important_instructions_wrong_model_name",
            "important_instructions_wrong_user_name"]

data = Path(sys.argv[1] if len(sys.argv) > 1 else "./data")
Y = agentdojo_matrix(data / "agentdojo" / "runs")
res = {"variants6": evaluate(Y[VARIANTS].values),
       "distinct_without_variants": evaluate(Y[["direct", "ignore_previous", "injecagent", "tool_knowledge", "important_instructions"]].values)}
Path("results/pilot_a_exploratory.json").write_text(json.dumps(res, indent=1))
text = "# Pilot A, exploratory (post hoc)\n" + summarise(res["variants6"], "AgentDojo GPT-4o, six name-variants of one template")
Path("results/pilot_a_exploratory.md").write_text(text + "\n")
print(text)
