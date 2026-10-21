# Pilot B results

Noise floor (GPT-4o, no defense, `important_instructions` vs `_no_names`, 293 cases breached under neither): clean/stopped flip rate 16.0%, clean→stopped 18.6%.

Among cases the undefended agent let the attacker breach: share the defense moves to *clean* (user task done, no breach) vs *stopped* (neither). 95% cluster-bootstrap intervals over user tasks.

| model | defense | BU 0→1 | UA 0→1 | ASR 0→1 | breached₀ | resist | incapacitate | still breached | collateral clean→stopped |
|---|---|---|---|---|---:|---|---|---:|---:|
| gpt-4o-2024-05-13 | repeat_user_prompt | 0.691→0.845 | 0.501→0.672 | 0.477→0.278 | 300 | 0.37 [0.30, 0.45] | 0.10 [0.06, 0.15] | 0.53 | 0.10 |
| gpt-4o-2024-05-13 | spotlighting_with_delimiting | 0.691→0.722 | 0.501→0.556 | 0.477→0.417 | 300 | 0.13 [0.09, 0.17] | 0.07 [0.04, 0.10] | 0.81 | 0.11 |
| gpt-4o-2024-05-13 | tool_filter | 0.691→0.722 | 0.501→0.563 | 0.477→0.068 | 300 | 0.48 [0.39, 0.59] | 0.42 [0.31, 0.52] | 0.10 | 0.22 |
| gpt-4o-2024-05-13 | transformers_pi_detector | 0.691→0.412 | 0.501→0.211 | 0.477→0.079 | 300 | 0.19 [0.11, 0.28] | 0.65 [0.54, 0.75] | 0.16 | 0.74 |
| meta-llama_Llama-3.3-70B-Instruct | repeat_user_prompt | 0.577→0.588 | 0.465→0.460 | 0.103→0.058 | 278 | 0.30 [0.20, 0.41] | 0.29 [0.20, 0.38] | 0.41 | 0.21 |
| Meta-SecAlign-70B | repeat_user_prompt | 0.773→0.856 | 0.779→0.806 | 0.017→0.016 | 48 | 0.08 [0.00, 1.00] | 0.10 [0.00, 0.18] | 0.81 | 0.06 |
| meta-llama_Llama-3.3-70B-Instruct | Meta-SecAlign-70B (model swap) | 0.577→0.773 | 0.472→0.779 | 0.129→0.017 | 367 | 0.66 [0.51, 0.82] | 0.22 [0.13, 0.32] | 0.12 | 0.09 |
