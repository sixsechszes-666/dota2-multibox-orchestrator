# Dota 2 Multibox Orchestrator

A multi-instance automation framework for orchestrating several Dota 2 clients in
parallel. It combines **computer-vision template matching**, **low-level hardware
input emulation**, a **YAML-driven scenario engine**, and **cross-instance
synchronization over Google Sheets** into a single command-line orchestrator.

> ⚠️ **Disclaimer.** This is a personal R&D / portfolio project built to explore
> Windows automation, OpenCV template matching and multi-process orchestration.
> It is **not** intended for use on online services where automation violates the
> Terms of Service. Run it only against private/sandboxed setups you own.

---

## Why it's interesting (engineering highlights)

- **Plugin-style action registry** - every high-level action is a small function
  decorated with `@register_action("name")` and auto-discovered at startup. Adding
  a behaviour means dropping one function into `actions/`; no central switchboard
  to edit.
- **Declarative scenario engine** - game flows (startup, draft, laning, farming,
  endgame) are described as ordered steps in `config/scenarios.yaml` with
  `repeat` / `interval` / per-step parameters, instead of being hardcoded.
- **Single-responsibility dispatcher** - `OptimizedHardwareManager` routes each
  action to one of three small runners (system-wide / cyclic / per-instance)
  instead of one large branching method, so each execution strategy is isolated
  and testable.
- **Hardware-level input** - input is emulated below the application layer so that
  multiple windows can be driven reliably, including fast window activation that
  works around Windows foreground-window restrictions.
- **Vision-based state detection** - OpenCV template matching against the assets in
  `imgs/` decides when the client has reached a given screen (loading, pick,
  reconnect, victory), instead of relying on fixed timers.
- **Cross-machine sync** - `features/hero_sync.py` and `core/connection_manager.py`
  use a pooled Google Sheets connection so instances on different machines can
  coordinate picks and readiness state.

## Architecture

```
main.py                     # CLI entry point: scenarios / ad-hoc actions / loop
│
├── core/                   # Orchestration & long-lived managers
│   ├── dota_manager.py        # Discovers windows, dispatches actions per instance
│   ├── prepare.py             # Per-instance facade (vision + input + logging)
│   ├── party_manager.py       # Party creation / invites / readiness
│   ├── sandbox_manager.py     # Launches isolated client instances
│   ├── sync_manager.py        # Cross-instance synchronization
│   └── connection_manager.py  # Pooled Google Sheets client (singleton)
│
├── actions/                # @register_action plugins (the "verbs")
│   ├── hero_actions.py        # picking / skilling / talents
│   ├── combat_actions.py      # fights, ward placement
│   ├── farming_actions.py     # jungle / lane farming
│   ├── support_actions.py     # shopping, consumables, items
│   ├── communication_actions.py  # chat, chat-wheel
│   ├── party_actions.py       # party lifecycle
│   ├── team_actions.py        # team checks
│   └── system_actions.py      # instance selection, ID collection, sandbox control
│
├── features/               # Higher-level capabilities
│   ├── gaming_actions.py      # composite in-game routines
│   ├── hero_sync.py           # Google-Sheets-backed hero sync
│   └── sheets_monitor.py      # sheet polling
│
├── input/                  # I/O layer
│   ├── hardware_input.py      # hardware-level mouse/keyboard emulation
│   └── hwnd_tracker.py        # window-handle registry per process
│
├── utils/
│   ├── actions_registry.py    # the @register_action decorator + lookup
│   ├── logging_setup.py       # single coloured logging config for all modules
│   └── dota_update_checker.py # detects client updates before launching
│
└── config/                 # YAML/JSON configuration (no secrets committed)
```

**Layering:** `main` → `core` (orchestration) → `actions`/`features` (behaviour)
→ `input` (OS I/O). The `actions_registry` decouples the orchestrator from the
concrete actions, so `core` never imports individual action modules directly.

## Tech stack

Python · OpenCV · NumPy · Pillow · PyAutoGUI · pywin32 · gspread (Google Sheets
API) · PyYAML · colorlog

## Getting started

```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

1. **Credentials** - copy `config/credentials.example.json` to
   `config/credentials.json` and fill in your own Google service-account key
   (only needed for the cross-instance sync features).
2. **Config** - adjust paths and instance counts in `config/sandbox_config.yaml`
   and tweak flows in `config/scenarios.yaml`. Replace the placeholder Steam IDs
   (`100000001`, …) with your own.
3. **Run:**

```bash
# Run a named scenario
python main.py --scenario standard_game

# Run individual actions ad-hoc
python main.py --actions hero_pick_sync team_check

# Continuous loop
python main.py --scenario game_loop
```

Available actions are printed at startup (`📋 Available actions: ...`) and are
also discoverable from the `@register_action` decorators in `actions/`.

## Configuration files

| File | Purpose |
|------|---------|
| `config/scenarios.yaml`      | Declarative step-by-step game flows |
| `config/sandbox_config.yaml` | Per-instance launch options & sandbox mapping |
| `config/hero_spell_config.json` | Per-hero ability exclusions for auto-skilling |
| `config/jungle_camps.yaml`   | Jungle camp coordinates for farming routines |
| `config/credentials.json`    | Google service-account key (**git-ignored**) |

## Notes & known limitations

- **Windows-only** - depends on `pywin32` and OS-level window handling.
- Vision templates in `imgs/` are resolution/theme specific and may need
  recapturing after a client UI update.
- This is a portfolio snapshot: runtime artifacts (logs, session state, captured
  window handles) and third-party binaries (`steamcmd/`) are intentionally
  excluded - see `.gitignore`.
