---
description: Show or switch the Oracle environment (dev | test | prod)
argument-hint: [dev|test|prod]
---
Argument: $ARGUMENTS

- No argument: call `env_info` and show env, pod URL, release, auth mode, agent user, mode.
- With an argument: call `switch_environment` with it, then `env_info`. If the new env is PROD, warn clearly that every change will require typing `CONFIRM PROD` and that the mode is forced to confirm.
