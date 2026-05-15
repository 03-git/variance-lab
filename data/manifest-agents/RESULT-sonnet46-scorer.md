============================================================
SONNET-4-6 AS 4TH SCORER — V2 MANIFEST-AGENTS
============================================================

--- Per-Arm Means (A1+A2+A3 composite) ---
Scorer          Arm M    Arm R      M-R   M wins
----------------------------------------------------
claude           7.13     7.67    -0.53    11/30
gemma           14.10    13.43    +0.67     9/30
qwen            10.03    10.53    -0.50     5/30
sonnet46         7.00     7.10    -0.10    10/30

--- Sonnet-4-6 Per-Dimension Breakdown ---
  A1 (Correctness): M=2.10 R=2.23 diff=-0.13
  A2 (Completeness): M=1.97 R=1.97 diff=+0.00
  A3 (Coherence): M=2.93 R=2.90 diff=+0.03

--- Pairwise Kendall Tau (item-level rankings) ---
  claude vs gemma: tau=-0.078 (n=30)
  claude vs qwen: tau=+0.205 (n=30)
  claude vs sonnet46: tau=+0.212 (n=30)
  gemma vs qwen: tau=+0.239 (n=30)
  gemma vs sonnet46: tau=+0.486 (n=30)
  qwen vs sonnet46: tau=+0.184 (n=30)

--- Arm Direction Agreement ---
  claude: R favored (-0.53)
  gemma: M favored (+0.67)
  qwen: R favored (-0.50)
  sonnet46: R favored (-0.10)

  1/4 scorers favor Arm M or tie

