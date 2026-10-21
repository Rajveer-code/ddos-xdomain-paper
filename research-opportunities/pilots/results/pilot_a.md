# Pilot A results

MAE and mean signed error in percentage points of cases, predicting the union over all K attacks from k of them.

### AgentDojo GPT-4o-2024-05-13, 10 integrity attacks: n=629, K=10, union over K = 59.6%, best single = 47.7%, mean single = 28.1%
| k | best_single MAE (bias) | observed_union MAE (bias) | chao2_extrap MAE (bias) | jack1_extrap MAE (bias) | betabinom MAE (bias) |
|---|---|---|---|---|---|
| 2 | 20.92 (-20.9; 100% under) | 18.97 (-19.0; 100% under) | 20.79 (+3.1; 67% under) | 11.56 (-6.4; 53% under) | 18.48 (+10.2; 24% under) |
| 3 | 16.25 (-16.2; 100% under) | 12.38 (-12.4; 100% under) | 9.49 (-0.2; 72% under) | 6.33 (+0.0; 36% under) | 13.49 (+10.1; 9% under) |
| 4 | 14.14 (-14.1; 100% under) | 8.53 (-8.5; 100% under) | 4.22 (-1.8; 72% under) | 3.48 (+1.0; 29% under) | 9.69 (+8.2; 7% under) |
| 5 | 13.16 (-13.2; 100% under) | 6.02 (-6.0; 100% under) | 2.48 (-1.5; 71% under) | 2.13 (+0.7; 34% under) | 7.40 (+6.9; 4% under) |
| 6 | 12.68 (-12.7; 100% under) | 4.24 (-4.2; 100% under) | 1.97 (-0.8; 59% under) | 1.65 (+0.4; 42% under) | 6.02 (+5.8; 3% under) |
| 7 | 12.43 (-12.4; 100% under) | 2.87 (-2.9; 98% under) | 1.52 (-0.4; 52% under) | 1.42 (+0.2; 39% under) | 5.05 (+5.0; 2% under) |
| 8 | 12.25 (-12.2; 100% under) | 1.77 (-1.8; 87% under) | 1.15 (-0.1; 56% under) | 1.11 (+0.0; 53% under) | 4.30 (+4.3; 0% under) |
| 9 | 12.08 (-12.1; 100% under) | 0.83 (-0.8; 60% under) | 0.86 (-0.0; 40% under) | 0.85 (+0.0; 40% under) | 3.74 (+3.7; 0% under) |

### AgentDojo GPT-4o, 5 distinct attack families: n=629, K=5, union over K = 53.1%, best single = 47.7%, mean single = 19.4%
| k | best_single MAE (bias) | observed_union MAE (bias) | chao2_extrap MAE (bias) | jack1_extrap MAE (bias) | betabinom MAE (bias) |
|---|---|---|---|---|---|
| 2 | 21.99 (-22.0; 100% under) | 20.79 (-20.8; 100% under) | 28.20 (+1.8; 30% under) | 20.06 (-9.5; 60% under) | 24.32 (-1.1; 30% under) |
| 3 | 13.56 (-13.6; 100% under) | 11.41 (-11.4; 70% under) | 13.00 (+1.9; 40% under) | 12.64 (-1.0; 40% under) | 13.82 (+1.2; 40% under) |
| 4 | 8.04 (-8.0; 100% under) | 4.61 (-4.6; 40% under) | 5.55 (+0.6; 20% under) | 5.90 (+0.5; 20% under) | 7.07 (+1.0; 40% under) |

### JailbreakBench llama-2-7b-chat-hf, attacks ['DSN', 'GCG', 'JBC', 'PAIR', 'prompt_with_random_search']: n=100, K=5, union over K = 96.0%, best single = 94.0%, mean single = 37.4%
| k | best_single MAE (bias) | observed_union MAE (bias) | chao2_extrap MAE (bias) | jack1_extrap MAE (bias) | betabinom MAE (bias) |
|---|---|---|---|---|---|
| 2 | 30.80 (-30.8; 100% under) | 30.60 (-30.6; 90% under) | 30.36 (-25.5; 30% under) | 30.69 (-25.2; 30% under) | 27.91 (-27.3; 80% under) |
| 3 | 12.30 (-12.3; 100% under) | 11.70 (-11.7; 70% under) | 11.66 (-6.7; 10% under) | 12.48 (-5.9; 10% under) | 16.84 (-14.9; 70% under) |
| 4 | 2.80 (-2.8; 100% under) | 1.60 (-1.6; 40% under) | 1.75 (+1.7; 0% under) | 2.50 (+2.5; 0% under) | 8.95 (-9.0; 100% under) |

### JailbreakBench vicuna-13b-v1.5, attacks ['DSN', 'GCG', 'JBC', 'PAIR', 'prompt_with_random_search']: n=100, K=5, union over K = 96.0%, best single = 95.0%, mean single = 84.6%
| k | best_single MAE (bias) | observed_union MAE (bias) | chao2_extrap MAE (bias) | jack1_extrap MAE (bias) | betabinom MAE (bias) |
|---|---|---|---|---|---|
| 2 | 5.20 (-5.2; 100% under) | 2.40 (-2.4; 90% under) | 2.08 (-0.7; 70% under) | 2.74 (+2.4; 10% under) | 2.23 (+1.8; 20% under) |
| 3 | 3.10 (-3.1; 100% under) | 1.00 (-1.0; 70% under) | 0.79 (-0.7; 70% under) | 0.86 (+0.6; 10% under) | 2.31 (+2.2; 10% under) |
| 4 | 2.00 (-2.0; 100% under) | 0.40 (-0.4; 40% under) | 0.44 (-0.1; 40% under) | 0.47 (+0.1; 40% under) | 2.56 (+2.6; 0% under) |

### JailbreakBench gpt-3.5-turbo-1106, attacks ['GCG', 'JBC', 'PAIR', 'prompt_with_random_search']: n=100, K=4, union over K = 95.0%, best single = 93.0%, mean single = 52.8%
| k | best_single MAE (bias) | observed_union MAE (bias) | chao2_extrap MAE (bias) | jack1_extrap MAE (bias) | betabinom MAE (bias) |
|---|---|---|---|---|---|
| 2 | 17.00 (-17.0; 100% under) | 14.83 (-14.8; 83% under) | 4.00 (+1.8; 33% under) | 8.42 (-1.7; 17% under) | 8.93 (-6.1; 67% under) |
| 3 | 7.50 (-7.5; 100% under) | 3.75 (-3.8; 50% under) | 3.67 (+0.7; 25% under) | 4.39 (+2.3; 25% under) | 3.99 (-1.8; 50% under) |

### JailbreakBench gpt-4-0125-preview, attacks ['GCG', 'JBC', 'PAIR', 'prompt_with_random_search']: n=100, K=4, union over K = 86.0%, best single = 78.0%, mean single = 29.0%
| k | best_single MAE (bias) | observed_union MAE (bias) | chao2_extrap MAE (bias) | jack1_extrap MAE (bias) | betabinom MAE (bias) |
|---|---|---|---|---|---|
| 2 | 35.00 (-35.0; 100% under) | 33.33 (-33.3; 83% under) | 27.35 (-13.4; 50% under) | 33.17 (-19.2; 50% under) | 25.50 (-21.4; 50% under) |
| 3 | 19.00 (-19.0; 100% under) | 14.50 (-14.5; 50% under) | 20.15 (+0.5; 25% under) | 19.28 (-1.9; 25% under) | 14.98 (-15.0; 100% under) |

### Synthetic, 20 replicates, near-duplicate rate rho=0.0: n=1000, K=10, union over K = 43.6%, best single = 24.1%, mean single = 17.1%
| k | best_single MAE (bias) | observed_union MAE (bias) | chao2_extrap MAE (bias) | jack1_extrap MAE (bias) | betabinom MAE (bias) |
|---|---|---|---|---|---|
| 2 | 23.82 (-23.8; 100% under) | 18.00 (-18.0; 100% under) | 8.11 (-8.0; 98% under) | 9.49 (-9.5; 100% under) | 4.83 (+4.5; 11% under) |
| 3 | 22.40 (-22.4; 100% under) | 12.79 (-12.8; 100% under) | 5.10 (-5.1; 99% under) | 3.22 (-3.1; 94% under) | 3.80 (+3.7; 6% under) |
| 4 | 21.66 (-21.7; 100% under) | 9.43 (-9.4; 100% under) | 2.83 (-2.8; 96% under) | 1.44 (-0.8; 68% under) | 3.09 (+3.0; 4% under) |
| 5 | 20.98 (-21.0; 100% under) | 6.83 (-6.8; 100% under) | 1.53 (-1.3; 82% under) | 1.04 (+0.0; 46% under) | 2.62 (+2.6; 3% under) |
| 6 | 20.52 (-20.5; 100% under) | 4.89 (-4.9; 100% under) | 1.03 (-0.6; 69% under) | 0.87 (+0.2; 40% under) | 2.19 (+2.2; 3% under) |
| 7 | 20.21 (-20.2; 100% under) | 3.34 (-3.3; 100% under) | 0.71 (-0.3; 61% under) | 0.67 (+0.1; 40% under) | 1.85 (+1.8; 2% under) |
| 8 | 19.93 (-19.9; 100% under) | 2.03 (-2.0; 100% under) | 0.51 (-0.1; 53% under) | 0.51 (+0.1; 42% under) | 1.56 (+1.5; 2% under) |
| 9 | 19.71 (-19.7; 100% under) | 0.94 (-0.9; 100% under) | 0.33 (-0.0; 46% under) | 0.34 (+0.0; 42% under) | 1.28 (+1.3; 1% under) |

### Synthetic, 20 replicates, near-duplicate rate rho=0.5: n=1000, K=10, union over K = 37.1%, best single = 21.0%, mean single = 17.4%
| k | best_single MAE (bias) | observed_union MAE (bias) | chao2_extrap MAE (bias) | jack1_extrap MAE (bias) | betabinom MAE (bias) |
|---|---|---|---|---|---|
| 2 | 18.33 (-18.3; 100% under) | 13.73 (-13.7; 100% under) | 10.18 (-10.2; 100% under) | 7.77 (-7.8; 100% under) | 3.16 (-0.1; 41% under) |
| 3 | 17.61 (-17.6; 100% under) | 10.33 (-10.3; 100% under) | 5.90 (-5.9; 99% under) | 4.09 (-4.0; 97% under) | 2.46 (-0.3; 44% under) |
| 4 | 17.23 (-17.2; 100% under) | 8.08 (-8.1; 100% under) | 2.92 (-2.8; 91% under) | 2.47 (-2.2; 85% under) | 2.02 (-0.5; 52% under) |
| 5 | 16.89 (-16.9; 100% under) | 6.12 (-6.1; 100% under) | 1.51 (-0.9; 72% under) | 1.56 (-1.0; 71% under) | 1.56 (-0.3; 54% under) |
| 6 | 16.64 (-16.6; 100% under) | 4.53 (-4.5; 100% under) | 1.06 (-0.3; 58% under) | 1.12 (-0.4; 60% under) | 1.29 (-0.3; 54% under) |
| 7 | 16.47 (-16.5; 100% under) | 3.18 (-3.2; 100% under) | 0.83 (-0.1; 52% under) | 0.86 (-0.1; 53% under) | 1.00 (-0.2; 54% under) |
| 8 | 16.32 (-16.3; 100% under) | 1.99 (-2.0; 100% under) | 0.62 (-0.0; 54% under) | 0.62 (-0.0; 53% under) | 0.74 (-0.1; 53% under) |
| 9 | 16.21 (-16.2; 100% under) | 0.93 (-0.9; 90% under) | 0.39 (-0.0; 53% under) | 0.39 (+0.0; 52% under) | 0.51 (-0.0; 54% under) |
