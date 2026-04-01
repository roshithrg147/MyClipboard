# Release Notes: MyClipboard Enterprise v2.0-alpha

## Overview
This release marks the transition from MVP to a production-ready Enterprise solution. Key focus areas include security hardening, cross-platform stability, and a functional E2EE sync architecture.

## Key Features

### 🔐 Security & Privacy
- **E2EE Sync:** Implemented Zero-Knowledge Relay (ZK-Relay) architecture. All clipboard data is encrypted locally with a PBKDF2-derived key before transmission.
- **Unique Per-User Salts:** Automated salt generation and storage in `~/.config/myclipboard/config.json` to prevent rainbow table attacks.
- **Entropy-Based Detection:** Advanced heuristic detection of sensitive data (API keys, tokens) using Shannon entropy analysis, preventing accidental leaks of high-entropy strings.
- **RAM Cleansing:** Enhanced memory management to zero-out keys and clear encrypted buffers upon service termination.

### 🔄 Synchronization
- **Pull/Merge Logic:** Integrated timestamp-based conflict resolution for remote sync.
- **Real-time Updates:** Asynchronous push/pull mechanism with ZK-Relay.
- **Sync Conflict Monitoring:** UI notifications for superseded remote updates.

### 💻 Platform Compatibility
- **Linux Wayland Support:** Robust active-window detection for GNOME (gdbus) and KDE (qdbus) to pause recording in sensitive apps.
- **macOS Stability:** Refined `osascript` integration for frontmost application monitoring.
- **Windows Fallback:** Lightweight active-window detection using `pygetwindow` and `ctypes`.

### 🎨 UI/UX Enhancements
- **Sync Status:** Real-time connection status and "Last Synced" timestamp in the [SYNC] tab.
- **Conflict Notifications:** Integrated visual alerts for synchronization events.
- **Theme:** Polished Cyberpunk/Terminal aesthetic for power users.

## QA & Audit
- **Integration Tests:** Expanded `test_security.py` covering entropy detection and platform fallbacks.
- **Stress Testing:** `test_concurrency.py` verified stability under 100+ rapid concurrent clipboard operations.
- **Audit Compliance:** 100% compliance with CTO-mandated security and stability fixes.

---
*Ghost-EM (Engineering Manager)*
*2026-04-02*
