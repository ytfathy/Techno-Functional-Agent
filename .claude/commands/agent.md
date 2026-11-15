---
description: Turn the Oracle agent on (connect; backend by default) or off (disconnect + close the pane)
argument-hint: on | off
---
Argument: $ARGUMENTS

**on**
1. `preview_start` with name `oracle-setup` (connection form in the Claude browser pane). Ask the user to check the instance URL / username / password and press **Save & test** or **Keep current**, then tell you "done". Never ask for the password in chat; never read `.env*`.
2. When the user says done: `preview_logs` for `oracle-setup` → find the last `SAVED profile=<p> ok=<bool>` or `KEEP profile=<p> ok=<bool>`. If `ok=False`: show the message on the page and stop.
3. `switch_environment(<p>)` (this also reconnects after `/agent off`), then `env_info`.
4. `preview_stop` the `oracle-setup` server (the form is no longer needed). Do not open Fusion in the pane: the agent works on the backend; the pane opens later only if the user asks to watch.
5. Reply in 2 lines: env / release / user / mode, and "Agent is ON".

**off**
1. If a change is in progress, say so and ask before stopping.
2. Call `disconnect` (closes the Oracle connection; every Fusion tool now refuses until `/agent on`).
3. Browser: `tabs_context`, then `tabs_close` every tab (closing the last tab closes the pane). `preview_list` → `preview_stop` any running server (e.g. `oracle-setup`).
4. Do not sign out of Fusion (the pane keeps the sign-in for next time) and do not touch `.env*`.
5. Reply in 1 line: "Agent is OFF — connection closed, browser closed."

**anything else / empty**: call `env_info`; if it errors with "Agent is off", reply "Agent is OFF"; else reply "Agent is ON" + env / user / mode.
