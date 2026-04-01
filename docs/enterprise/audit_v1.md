# Audit Report: MyClipboard Enterprise (v1.0) - Architectural Gaps

## 1. Overview
The current codebase (`app/main.py` and `app/service.py`) provides a functional prototype for an enterprise clipboard manager. However, critical architectural gaps exist that must be addressed for v2.0 "Enterprise" stability.

## 2. Key Gaps & Vulnerabilities
### 2.1. Concurrency & Data Consistency
- **Race Condition:** `self.history` is a `deque` modified by `_observe_clipboard` (background thread) and read by `_push_update_to_ui` (via `_render_listbox` in the UI thread).
- **Risk:** Potential for `RuntimeError` or inconsistent state when multiple updates occur rapidly.
- **Fix:** Implement a threading `Lock` around `self.history` operations.

### 2.2. Error Handling & Resilience
- **Issue:** Several `try-except: pass` blocks in `_ipc_listener` and `_observe_clipboard`.
- **Risk:** Silent failures. If the clipboard listener crashes, the app appears functional but stops recording.
- **Fix:** Replace with robust logging and automatic thread restart mechanisms.

### 2.3. Platform Compatibility
- **Issue:** `_is_terminal_or_vault_active` relies on `xdotool` (Linux) or `osascript` (macOS).
- **Risk:** No Windows support; assumes `xdotool` is installed on Linux (not always true on Wayland/Gnome).
- **Fix:** Use a cross-platform library like `pygetwindow` or handle Wayland-specific protocols.

### 2.4. Memory Management
- **Issue:** Sensitive plaintext is stored in `plaintext` variables in `_on_listbox_select` and `transform_item`.
- **Risk:** Plaintext remnants stay in the Python process heap even after the variable goes out of scope.
- **Fix:** Use bytearrays or manually overwrite sensitive strings with null bytes where possible (limited in Python but achievable for short-lived buffers).

### 2.5. IPC Protocol
- **Issue:** Socket-based IPC is purely "Send-Only" (One-way).
- **Risk:** The CLI cannot query the service for status or current history.
- **Fix:** Implement a Request-Response protocol over the Unix Domain Socket (JSON-RPC style).

## 3. Summary
The core logic is sound, but the foundation needs hardening. Address threading and IPC robustness before adding "Sync" or "Shared Snippets" to avoid a fragile distributed system.
