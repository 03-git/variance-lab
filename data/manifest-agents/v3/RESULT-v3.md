============================================================
MODEL-SIZE PREDICTION TEST: V2 (qwen-7b) vs V3 (sonnet-4-6)
============================================================

--- V2 (qwen-7b) Arm Means ---
Scorer          Arm M    Arm R      M-R
----------------------------------------
claude           7.13     7.67    -0.53
gemma           14.10    13.43    +0.67
qwen            10.03    10.53    -0.50
sonnet46         7.00     7.10    -0.10

--- V3 (sonnet-4-6) Arm Means ---
Scorer          Arm M    Arm R      M-R
----------------------------------------
claude           8.97     9.53    -0.57
gemma           15.00    14.33    +0.67
qwen            11.10    11.03    +0.07

--- Cost Comparison ---
  V2 qwen-7b:    M=4613tok/17844ms  R=5726tok/23850ms
  V3 sonnet-4-6: M=4313tok/14502ms  R=5327tok/14040ms

--- Prediction: 'Gap narrows with larger models' ---
  claude: V2 gap=0.53 → V3 gap=0.57 (wider)
  gemma: V2 gap=0.67 → V3 gap=0.67 (wider)
  qwen: V2 gap=0.50 → V3 gap=0.07 (narrower)

  Average gap: V2=0.57 → V3=0.43
  PREDICTION CONFIRMED: gap narrows by 0.13

