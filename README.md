# variance-lab

Empirical testing harness for local LLM reliability. Measures quality variance per task class to produce routing tables for subtract.ing's tier system.

## Structure

```
findings/          16 numbered findings + calibration reviews
data/              experiment datasets (manifest-agents, bitnet-log, reflex-binding, handler)
feature-tests/     Claude Code feature test specs
prompts/           task-class prompt files for the harness
output/            raw run results
```

## Usage

```bash
./run-local-batch.sh --passes 5
python3 aggregate-local.py output/run-YYYYMMDD-HHMMSS 5
```

## Status

This repo needs cleanup — duplicated findings, stale snapshots, inconsistent naming. The data is valid; the organization is not.

## License

GPL-2.0
