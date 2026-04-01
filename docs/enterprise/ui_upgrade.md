# Theme Upgrade Plan: "Hacker" Aesthetic (Emerald/Neon)

## 1. Vision: "The Ghost Terminal"
The UI should feel like an active terminal on a high-end hacker's workstation. 
- **Core Color:** `#0A0A0A` (Midnight Black)
- **Primary Accent:** `#00FF41` (Emerald Green / Matrix Neon)
- **Secondary Accent:** `#FF0055` (Neon Pink - for alerts/sensitive data)
- **Font:** `JetBrains Mono` or `Fira Code` (Monospaced, high legibility)

## 2. Component Overhauls
### 2.1. Main Window (`tk.Tk`)
- Remove standard title bars (use custom window controls if possible).
- Set background to absolute black.
- Add a subtle glow/border in Emerald.

### 2.2. Search Bar (`tk.Entry`)
- Remove border.
- Bottom-border only in Emerald.
- Cursor color: Emerald.
- Text color: Emerald.

### 2.3. History & Templates (`tk.Listbox`)
- Transparent or black background.
- Selection highlight: Emerald background, Black text.
- Item labels: Monospaced green (`#00FF41`).
- Sensitive data masks: Neon Pink (`#FF0055`).

### 2.4. Details Panel (`tk.Text`)
- Syntax highlighting for AI Insights.
- Code blocks in faded grey or cyan.
- Content wrapping with margin padding for readability.

## 3. Implementation Plan (Tkinter/ttk)
1. **Style Initialization:** Create a custom `ttk.Style` instance.
2. **Color Constants:** Define a central `THEME` dictionary in `app/main.py`.
3. **Dynamic Updates:** Update the `_setup_ui` method to apply these styles.
4. **Transparency:** Enable `alpha` (0.9) to allow the desktop to bleed through.

## 4. Visual Reference (Mental Model)
Imagine a sleek, minimalist CLI that happens to have a GUI wrapper. No "Windows" buttons. Just data and neon.
