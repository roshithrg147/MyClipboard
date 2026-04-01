# PRD: MyClipboard Enterprise - Final Completion

## 1. Executive Summary
MyClipboard Enterprise is a high-security, productivity-focused clipboard manager for power users and developers. It moves beyond simple history tracking to offer secure-by-default architecture, automated DLP masking, and AI-driven insights.

## 2. Current Feature Set (v1.0)
- **RAM Encryption:** Clipboard history is stored in-memory using Fernet (AES-128) encryption. Keys are regenerated on restart and cleared on exit.
- **DLP Masking:** Automatic detection and masking of sensitive patterns (AWS Keys, SSH Private Keys, JWTs, Credit Cards) in the UI.
- **Multi-Paste:** Queue multiple items for sequential pasting via hotkey (`Ctrl+Alt+V`).
- **CLI Interface (`mcb`):** Seamless integration with terminal workflows.
- **Templates:** Rapid access to frequently used snippets (Email templates, meeting links).
- **AI Insights:** Optional Gemini-powered summaries and data extraction from clipboard content.
- **Smart Transforms:** Contextual code transformations (JSON formatting, Case conversion, Base64).

## 3. New Enterprise Features (v2.0)
### 3.1. Team Shared Snippets (RBAC)
- **Description:** Centralized snippet repository for teams.
- **Details:** Enterprise admins can push "Read-Only" templates to employee clients. Supports departmental tagging (e.g., "Support", "Engineering").
- **Benefit:** Standardizes communication and command usage across the organization.

### 3.2. End-to-End Encrypted (E2EE) Sync
- **Description:** Securely sync clipboard history between authorized devices.
- **Details:** Uses a Zero-Knowledge architecture. Encryption keys never leave the device. Sync happens via a secure relay or peer-to-peer.
- **Benefit:** Seamless transition between workstation and mobile/laptop without compromising security.

### 3.3. Smart Code Refactor Transforms
- **Description:** Advanced AI-driven code refactoring directly from the clipboard.
- **Details:** Beyond simple regex transforms, this uses LLMs to "Refactor to Pythonic", "Convert to TypeScript", or "Fix Bug" on the current clipboard item.
- **Benefit:** Drastically reduces context switching for developers.

## 4. Technical Requirements
- **Architecture:** Decoupled Service-Consumer model using Unix Domain Sockets for IPC.
- **Security:** Zero-disk-persistence policy for clipboard content.
- **Performance:** UI response time < 100ms; Background polling < 0.5s.
- **Platforms:** Linux (X11/Wayland), macOS, Windows.

## 5. Success Metrics
- 50% reduction in "Manual Copy-Paste" loops for common templates.
- Zero leakage of plain-text secrets in UI screenshots (verified by DLP).
- Successful adoption of shared snippets in team pilots.
