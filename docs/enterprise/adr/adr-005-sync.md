# ADR-005: End-to-End Encrypted (E2EE) Sync Architecture

## Status
Proposed

## Context
Enterprise users frequently work across multiple machines (e.g., Laptop, Workstation, Cloud-IDE). Manually transferring snippets (via Slack/Email) is a security risk and productivity bottleneck. A unified clipboard sync is required, but it MUST maintain the "Zero Knowledge" principle where the central server (Relay) never sees the plaintext content.

## Decision
We will implement an E2EE Sync protocol using a "Relay-and-Salt" model.

### 1. Key Derivation
- Users set a "Sync Passphrase" locally.
- A strong key (AES-256) is derived using Argon2 with a local salt.
- This key (Master Key) never leaves the device.

### 2. Transport Security
- Clipboard items are encrypted with the Master Key *before* being sent to the Relay server.
- The Relay server stores only: `(DeviceID, EncryptedBlob, Timestamp, HMAC)`.
- Communication with the Relay occurs over TLS 1.3.

### 3. Conflict Resolution
- Last-Write-Wins (LWW) based on NTP-synchronized timestamps.
- A "Sync Queue" in `ClipboardService` will manage outgoing/incoming blobs to prevent UI blocking.

## Consequences
- **Positive:** Seamless cross-device productivity; No central server can leak user data.
- **Negative:** If a user loses their Sync Passphrase, existing synced data is unrecoverable.
- **Neutral:** Increases local CPU usage slightly due to encryption/decryption on every sync event.

## Alternatives Considered
- **Plain TLS Sync:** Rejected (Relay could see data).
- **P2P (WebRTC):** Rejected (Too complex for firewall traversal in enterprise environments).
