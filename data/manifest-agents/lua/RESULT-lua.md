============================================================
LUA CORPUS — MANIFEST vs BM25
============================================================

--- Cost Metrics ---
  Arm M: 5212 avg tokens, 34931ms avg wall
  Arm R: 4537 avg tokens, 35294ms avg wall

--- Per-Arm Means (A1+A2+A3 composite) ---
Scorer          Arm M    Arm R      M-R   M wins
----------------------------------------------------
claude           7.67     8.00    -0.33     6/15
gemma            9.40    10.13    -0.73     5/15
qwen            10.47    10.20    +0.27     5/15

--- claude Per-Dimension ---
  A1 (Correctness): M=2.20 R=2.47 diff=-0.27
  A2 (Completeness): M=2.33 R=2.33 diff=+0.00
  A3 (Coherence): M=3.13 R=3.20 diff=-0.07

--- gemma Per-Dimension ---
  A1 (Correctness): M=2.80 R=3.07 diff=-0.27
  A2 (Completeness): M=2.87 R=2.93 diff=-0.07
  A3 (Coherence): M=3.73 R=4.13 diff=-0.40

--- qwen Per-Dimension ---
  A1 (Correctness): M=3.93 R=4.00 diff=-0.07
  A2 (Completeness): M=3.33 R=3.27 diff=+0.07
  A3 (Coherence): M=3.20 R=2.93 diff=+0.27

--- Pairwise Kendall Tau ---
  claude vs gemma: tau=+0.729 (n=15)
  claude vs qwen: tau=+0.181 (n=15)
  gemma vs qwen: tau=+0.153 (n=15)

--- By Question Type ---

  traversal (n=5):
    claude: M=8.20 R=8.80 diff=-0.60
    gemma: M=11.40 R=11.60 diff=-0.20
    qwen: M=11.00 R=10.00 diff=+1.00

  synthesis (n=5):
    claude: M=7.80 R=9.40 diff=-1.60
    gemma: M=10.00 R=11.80 diff=-1.80
    qwen: M=10.60 R=10.40 diff=+0.20

  similarity (n=5):
    claude: M=7.00 R=5.80 diff=+1.20
    gemma: M=6.80 R=7.00 diff=-0.20
    qwen: M=9.80 R=10.20 diff=-0.40

