# BB Fracture

A Blender extension for cutting objects with two named boolean cutters (`BoolA` and `BoolB`) in a single click. Originally built for fracture-style workflows where a single mesh needs to be split into two matching pieces using custom-shaped cutters.

Authors: **Blender Bob** and **Claude AI**

![Blender](https://img.shields.io/badge/Blender-4.2%2B-orange)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)

---

## What it does

Given one or more selected mesh objects and two cutter objects in the scene named `BoolA` and `BoolB`, pressing **Fracture** produces two live copies of each selected object:

- `<name>_A` with a Boolean Difference modifier using `BoolA`
- `<name>_B` with a Boolean Difference modifier using `BoolB`

Both modifiers use the **Exact** solver with **Hole Tolerant** enabled. Originals are moved to a hidden `Orig` collection so the scene stays clean but nothing is lost.

---

## Installation

1. Download the latest `bb_fracture.zip` from [Releases](../../releases).
2. In Blender: **Edit → Preferences → Get Extensions → ▼ (drop-down) → Install from Disk...**
3. Pick the zip.

Requires Blender 4.2 or newer.

---

## Usage

The panel lives in the **N-panel → Tool tab → BB Fracture**.

### Setup

Your scene needs two cutter objects named exactly `BoolA` and `BoolB`. The panel shows a checkmark next to each once it finds them.

### Fracture

Select the object(s) you want to fracture, then press **Fracture**. For each selected object you'll get two new live-boolean copies (`_A` and `_B`), and the original is moved into a hidden `Orig` collection.

Works on any number of selected mesh objects at once.

### Display A / Display B

These are **toggles**. Click **Display A** to show only the `_A` objects plus the cutters; click it again to show everything. Same for **Display B**. The active button stays depressed so you always know which mode you're in.

### Apply

Applies the `BB_Bool_A` / `BB_Bool_B` modifiers on the currently selected objects (makes the cut destructive).

### Apply All

Same thing but on every `_A` and `_B` object in the scene.

After applying, Display A / Display B still work — the add-on tags each object with a custom property (`bb_fracture_side`) at fracture time, so it doesn't rely on the modifier being present.

---

## How it works

Each fractured object is identified two ways:

1. A custom property `bb_fracture_side` set to `"A"` or `"B"`
2. A modifier named `BB_Bool_A` or `BB_Bool_B`

The Display and Apply operators look for either, so detection survives modifier apply, object renames, and most other edits.

Originals are preserved in a `Orig` collection (created automatically, hidden in the viewport) so the fracture is fully non-destructive until you choose to Apply.

---

## Notes and caveats

- If you delete `BoolA` or `BoolB`, the modifiers on existing `_A` / `_B` objects will stop cutting — recreate them with the same names to restore.
- Running Fracture on an object that's already a `_A` or `_B` will nest the boolean logic, which can get confusing. Start from originals when possible.
- Objects fractured with v1.0 or v1.1 don't have the `bb_fracture_side` property. Display will still work *before* applying, but re-fracturing is the cleanest fix if you've already applied those.

---

## Changelog

- **1.2.1** — Boolean modifiers now use Exact solver with Hole Tolerant
- **1.2.0** — Display A/B are toggle buttons; detection works after Apply
- **1.1.0** — Added Display A, Display B, Apply, Apply All
- **1.0.0** — Initial release

---

## License

GPL-3.0-or-later
