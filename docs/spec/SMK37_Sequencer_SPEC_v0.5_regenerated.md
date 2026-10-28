# SMK 37 Pro MIDI Step Sequencer — SPEC (Draft 0.5)

Status: discovery / not implementation-ready. Updated with questionnaire rounds 1–4 decisions on 2026-10-28. Platform: Windows. Language of requirements: Russian.

## 0. Rules for coding agent
- Do not implement assumptions marked OPEN or PROPOSED without confirmation.
- Preserve stock firmware; no Open firmware requirement.
- Do not conflate controller input MIDI channels, active instrument/track, and MIDI output channels.
- Keep MIDI handling deterministic and ensure Note Off / panic on transport stop, mode changes, and device disconnect.
- No DAW-specific API dependency is assumed. Validate target DAW's external MIDI Clock support.

## 1. Product goal [CONFIRMED]
Standalone Windows application controlled mainly by SMK 37 Pro (stock firmware) and PC keyboard. Rapid entry of percussion patterns (3–5 tracks) and melodic bass ostinatos. MIDI sync master: sequencer sets tempo, DAW is slave. Patterns up to 64 steps, optionally shorter; patterns and scenes are the same entity. Pattern change is queued and occurs after current pattern cycle ends.

## 2. Hardware mapping [CONFIRMED unless OPEN]
Pad bank 1, top row MIDI note numbers: 40 41 42 43 48 49 50 51; bottom row: 36 37 38 39 44 45 46 47.
Pad bank 2, top row: 56 57 58 59 64 65 66 67; bottom row: 52 53 54 55 60 61 62 63.
Knob bank 1: CC 48–55 on MIDI channel 6. Knob bank 2: CC 56–63, apparently also MIDI channel 6 [TO VERIFY].
Fader bank 1: CC 64–67 on MIDI channel 1. Fader bank 2: CC 68–71, apparently also MIDI channel 1 [TO VERIFY].
Input channels 1–9: instrument input contexts. Channel 10: step grid and edit commands. Channel 11: velocity/gate and groove tools. Channel 12: patterns. Channels 15–16: reserved for DAW MIDI mapping. Channels 13–14 [OPEN]. Pad banks and input channel selection mechanics [OPEN].

## 3. Step entry [CONFIRMED]
Instrument keyboard note selects the note/pitch to edit; pads place its steps. PC shortcut corresponding to `/ .` toggles audition (whether selected note is also sent to DAW). CH10 pad bank 1 provides 16 step pads; PC keyboard `<` and `>` (layout-independent physical keys, exact scancodes TBD) switch 1–16, 17–32, 33–48, 49–64. Selected-note versus all-notes edit scope toggle by double tap on designated pad, with pad color change [LED feedback capability TO VERIFY]; all-notes operations deferred for now.

## 4. Track modes [CONFIRMED intent, semantics OPEN]
Per instrument/track: Seq, Keyboard, Both. Mute is independent, not necessarily fourth mode. Live note routing, monitoring, and note ownership [OPEN].

## 5. CH10 pad bank 2 [PARTIALLY CONFIRMED]
Required actions: Undo, Redo; Duplicate ×2; Duplicate to Next Pattern; Rotate (hold pad + knob 1); Length (hold pad + knob 1); Clear Note; Clear Track; Clear Pattern (double press); Drone toggle; Legato; Non-legato. Exact pad assignments and tap/hold/double-tap priority [OPEN].
Duplicate ×2: operates on selected note only, determines next power-of-two length according to existing events, copies first half into second half only if target is empty; precise algorithm and pattern-length update [OPEN].
Clear Note: hold CLEAR and press keys to remove corresponding notes. Clear Track: hold CLEAR and press any one note three times consecutively to clear current instrument MIDI channel; disambiguation of the first/second presses versus immediate Clear Note [OPEN].
Copy to next pattern: entire pattern OR selected MIDI channel (mode selection [OPEN]).
Drone: toggle (not hold); while active, keyboard notes can be selected for sustained playback across the entire pattern and across loop boundary; ordinary steps on same pitch must coexist. Legato extends to next note, Non-legato has no separately configurable gap. Exact Note On/Off and overlap semantics [OPEN].

## 6. CH11 [PARTIALLY CONFIRMED]
Pad bank 1 top 8 pads: velocity pages (8 steps each); bottom 8 pads: gate/length pages (8 steps each). 8 encoders edit the corresponding steps of the selected pitch only. Bank 2: modal popups and rhythm/velocity/gate formulas, Humanize, Scale Velocity (compression/expansion), accents, Apply/Cancel, possibly Undo/Redo. Exact layout [OPEN].
Groove Formula: lower 8 pads switch to formula input; choose formula length (2–8?) and offset; enter notes and rapidly repeat across pattern. Leftover steps that do not fit full formula cycle use softer repeats of first two formula notes, each twice; precise ordering, count and boundary rules [OPEN].
Velocity Formula and Gate Formula: repeat shape for repeating notes, without special remainder rule. Accents: strong every fourth step; above 50% knob adds weaker accents every second step. Humanize velocity; Scale Velocity compression/expansion. No quantize, invert, swing, shift timing.

## 7. CH12 [OPEN]
Pattern selection/creation/copy/queueing, with up to 64-step pattern lengths. Pattern change after completion of current cycle. Scope of instrument states copied with pattern [OPEN].

## 8. MIDI engine [OPEN details]
MIDI Clock 24 PPQN, Start/Stop/Continue and optional Song Position Pointer (DAW compatibility to verify). Tempo range, swing disabled, time signature, step resolution, latency handling, virtual MIDI port choice, MIDI loop prevention, panic, persistence and crash recovery [OPEN].

## 9. Questionnaire (answer by IDs)
### A. Timing and transport
A1. Default step subdivision: 1/16, 1/8, selectable? A2. BPM range and precision? A3. Start/Stop from PC keyboard, SMK pad, or both? A4. Clock always running or only during Play? A5. When switching patterns of different lengths, wait for old cycle or common bar? A6. DAW name/version and virtual MIDI port choice?
### B. Tracks and MIDI routing
B1. Exactly how are 1–9 instrument channels selected on the SMK? B2. Can one channel hold multiple pitches (drum kit), or one pitch per channel? B3. Separate output port/channel per track? B4. What should Keyboard mode do to stored sequence? B5. Should Mute silence live notes, sequenced notes, or both? B6. Are channels 13–14 free/reserved? B7. Can pads on channels 15–16 pass through directly to DAW?
### C. Step editing
C1. One pad press toggles a step or always inserts? C2. How do chords and simultaneous notes work? C3. Default velocity and gate source? C4. What happens to steps beyond shortened pattern length? C5. Should a page follow playhead? C6. What is exact physical PC shortcut for audition and pages? C7. Are note selection and live playback independent in Both mode?
### D. Duplication and clearing
D1. Exact ×2 examples for last occupied step 1, 2, 3, 4, 5, 8, 9, 32? D2. Does ×2 change pattern length? D3. Is empty target checked only for selected pitch, including overlapping note tails? D4. How should CLEAR + three taps avoid deleting note on first tap? D5. Clear Pattern: current instrument or entire pattern? D6. Clear Track: current pattern only? D7. Copy to Next Pattern: overwrite, merge, or refuse if occupied? D8. What if next pattern does not exist? D9. Undo stack depth and whether it spans pattern changes?
### E. Drone, legato, gate
E1. Does Drone survive pattern changes? E2. Can Drone pitch be removed by pressing same key again while Drone mode active? E3. When Drone and regular notes share pitch, should rearticulation occur? E4. Legato: next onset on same pitch or any pitch? E5. Non-legato: fixed default gate percentage, existing gate, or simply disable Legato? E6. Are legato/non-legato per pitch, per note, or global?
### F. Formula editor
F1. Formula length range 2–8 confirmed? F2. Formula offset in steps, and range? F3. Does groove formula generate step on/off, velocity, or both? F4. Explain remainder rule with formula length 5 on 16-step pattern. F5. Can formula preview be heard without Apply? F6. Does Apply overwrite or merge? F7. Are velocity/gate formula values absolute or relative? F8. Should Humanize be deterministic per pattern? F9. Accent counted by step number or note event number? F10. Which fader controls which formula parameter?
### G. Controller interaction and UI
G1. Does stock SMK report Note Off for pad release? G2. Can pad LEDs be controlled by software and via which protocol? G3. How to distinguish short/double/hold timing? G4. When holding a pad, should knobs use soft takeover? G5. Do banks change physical MIDI notes or just channel? G6. UI should be always visible, small overlay, or minimize to tray? G7. Popup closed by physical pad or PC Escape? G8. Preferred UI framework/language, if any?
### H. Patterns and persistence
H1. Max number of patterns per project? H2. CH12 pad layout? H3. Pattern duplication: auto-queue next pattern? H4. Save/load project format and autosave? H5. Should BPM be global or per pattern? H6. Do track modes and mutes persist per pattern? H7. What happens at end of last pattern?
### I. Delivery and testing
I1. Target DAW and Windows version? I2. Acceptable install footprint and portable EXE requirement? I3. Is a simulated MIDI input/test mode needed? I4. Which 3 end-to-end workflows define MVP acceptance? I5. What features are explicitly deferred to v2?

## 10. Implementation plan [NOT YET APPROVED]
1. Verify SMK MIDI mapping, LEDs, pad release behavior, and DAW sync.
2. Implement headless MIDI clock/transport and deterministic note scheduling.
3. Implement track/pattern state, step edit, undo and persistence.
4. Implement CH10 bank 1 and CH11 bank 1 control mapping.
5. Implement CH10 bank 2 actions and CH12 pattern queue.
6. Add formula modal and CH11 bank 2, then optional refinements.
7. Run hardware integration and DAW sync tests.

## 11. Decision log — questionnaire round 1 (2026-10-28) [CONFIRMED]
These decisions supersede any contradictory OPEN items above.
- A1: Each step is fixed at 1/16 note.
- A2: BPM 30–240, integer values.
- A3: Start/Stop via both PC keyboard and controller pads.
- A4: Reducing pattern length preserves steps outside the active range (hidden, not deleted).
- B1: Each instrument channel 1–9 supports multiple pitches.
- B2: Mute silences only sequenced playback, not live keyboard input.
- B3: MIDI channels 15–16 use direct MIDI passthrough to DAW (routing and loop protection remain to specify).
- B4: Output instrument MIDI channels are 1–9 and match instrument channel numbers.
- C1: Duplicate to Next Pattern creates the destination if absent.
- C2: Duplicate to Next Pattern refuses to overwrite an occupied destination.
- C3: After successful duplication, queue the destination to play after current cycle.
- C4: Double-press Clear Pattern clears ONLY the current instrument MIDI channel in the current pattern, not all instruments.
- D1: Non-legato extends almost to next note onset, without configurable gap parameter.
- D2: Drone continues across a pattern change if that same drone pitch exists in the destination pattern; otherwise stop appropriately.
- D3: Formula Apply REPLACES notes in the selected range; precise definition of selection/range still OPEN.
- D4: Accents count grid steps, not note-on events; a free knob can shift accent phase/offset.

### Consistency / unresolved semantics
- The previous label 'Clear Pattern' is potentially misleading because it only clears the active instrument channel. UI naming TBD; do not silently reinterpret its scope.
- 'Non-legato almost until next note' needs a deterministic note-off rule even though no user-facing gap setting is desired.
- 'Occupied destination' needs an exact test: any notes on any of channels 1–9, or other stored pattern state?
- Direct passthrough on channels 15–16 must avoid echo and MIDI feedback loops.
- Earlier confirmed `Duplicate ×2` is selected-pitch-only, distinct from `Duplicate to Next Pattern`.

## 12. Questionnaire round 2 [OPEN]
### Controller ergonomics
R2-01. How are MIDI input channels 1–12 switched on SMK stock firmware (hardware control sequence)?
R2-02. Are pad LEDs software-addressable? If not, use screen feedback instead?
R2-03. Can a physical pad bank change while holding another pad, and how should held modifiers behave?
R2-04. Are knob banks 1/2 selectable independently of pad banks? What is expected default bank?
R2-05. Which PC key(s) are Play/Stop, Panic, Audition, page prev/next?
### CH10 bank 2
R2-06. Exact 16-pad placement of Undo, Redo, ×2, Duplicate-to-next, Rotate, Length, Clear, Drone, Legato, Non-legato, Note/All.
R2-07. Should Clear+keyboard first/second taps remove individual notes immediately or wait for third tap to distinguish Clear Track?
R2-08. Should Clear Track remove all notes of current channel only in current pattern, or across all patterns?
R2-09. What is 'empty destination' for Duplicate-to-next (any note in destination pattern or only selected channel)?
R2-10. How do users choose entire-pattern vs current-channel copy (hold pad, knob, or modal choice)?
R2-11. What should ×2 do if active pattern is shorter than target length, or already 64 steps?
### CH11 bank 2 and formulas
R2-12. Groove formula exact length choices, offset, and handling of remaining 1–7 steps: show 5-in-16 example.
R2-13. Do Velocity/Gate formulas operate on existing notes only, or create notes?
R2-14. Are formula knob values absolute, relative, or selectable?
R2-15. Which physical control adjusts accent offset and how does it wrap at pattern boundary?
R2-16. Is Humanize applied once on Apply (baked), or randomized each loop?
R2-17. How does formula modal capture and release pads, keyboard notes, knobs, and faders?
### Patterns and transport
R2-18. Maximum number of patterns and CH12 bank layout?
R2-19. When current pattern is 16 steps and queued next is 64, switch at step 16, correct?
R2-20. Does selecting a queued pattern twice cancel queue or restart it?
R2-21. Does 'occupied destination' include drone-only patterns?
R2-22. Do BPM, track modes, and mute states belong to project or individual pattern?
### Implementation environment
R2-23. Target DAW and Windows version?
R2-24. Preferred MIDI loopback solution (e.g. loopMIDI) and number of virtual ports?
R2-25. Should the app be portable and work offline without installation?
R2-26. UI preference: compact always-on-top editor, full window, or both?
R2-27. What must be in v1 versus deferred (hardware LED feedback, formulas, humanize, per-step gate)?

## 13. Decision log — questionnaire round 2 (2026-10-28) [CONFIRMED]
These answers supersede contradictory OPEN questions in previous sections. Do not infer unmentioned behavior.

### Hardware and control
- GLOBAL + one of the first 16 hardware keyboard keys changes the keyboard's MIDI channel; GLOBAL + any of the 16 pads changes the pads' MIDI channel. Keyboard and pad channel selection are independent. User accepts that changing pad channel away from the expected app control context may disrupt app logic; no automatic remapping is assumed.
- Software-to-pad LED color messages appear possible, but transport rate/latency is still under diagnosis. LED color feedback must remain an optional hardware capability until tested.
- There are 8 physical knobs, 2 banks = 16 logical CCs, only 8 physically available at a time. Both banks transmit on MIDI channel 6. There are 2 fader banks transmitting on MIDI channel 1.
- While a pad modifier is held, knobs temporarily change function and ideally revert on release. Value jumps, soft takeover, relative/absolute CC behavior and modifier interaction require prototype tests; no silent assumption of reliable pickup.

### Clearing, duplication, scope
- CLEAR + pressing a keyboard pitch removes that pitch immediately on first press; pressing the *same* pitch three times consecutively while CLEAR remains held clears the whole current instrument MIDI channel. This deliberate destructive action needs Undo; exact timing and how to count intervening key presses remain OPEN.
- Duplicate ×2: selected pitch only. Find the highest occupied step `h`; use the smallest power-of-two span `S` with `h <= S` (examples: h=3 -> S=4, h=5..8 -> S=8), and duplicate the span into the next `S` steps (3 -> 4→8; 5..8 -> 8→16). Only perform if destination steps for that pitch are empty. Behavior at 64 steps and active length updates OPEN.
- For commands with a scope choice (especially Duplicate to Next Pattern), use three pads on the opposite physical row: first selects NOTE, second CHANNEL, third PATTERN. If the action is on the lower row, scope pads are on the upper row; if action is on the upper row, scope pads are on the lower row. The precise chord/tap interaction is OPEN.
- Duplicate to Next Pattern supports NOTE / CHANNEL / PATTERN scope. Normal press must not overwrite existing content in target scope; double-tap corresponding scope pad enables adding selected note (merge), overwriting selected channel, or overwriting entire destination pattern, respectively. Previous 'no overwrite' rule is the DEFAULT, with explicitly requested double-tap exceptions. Destination is auto-created if absent and successfully copied pattern is queued for playback at end of current cycle. Exact conflict resolution for NOTE merge (same pitch, same step) OPEN.
- Rotate wraps cyclically across pattern boundary.
- LENGTH held + separate knobs should expose three adjustment granularities: +/-1 step, +/-4 steps, and power-of-two choices (4/8/16/32/64). Which knobs and whether power-of-two is snap/step OPEN.

### Formula and expression
- Groove Formula length 2–8 steps, adjustable with knob. For leftover steps fewer than 2, copy events from step 2 of formula; precise meaning of remainder of 2+ and softer velocity remains OPEN. Formula entry uses pads in modal state.
- Velocity Formula applies RELATIVE values to existing notes, not absolute velocity values. Exact coefficient range, zero behavior and cumulative/reapply semantics OPEN.
- Gate Formula range 14%–300% of a step, with intentionally nonlinear response above 150% (user describes 100–128 CC region as curved); exact mapping/curve OPEN.
- Humanize is applied once, immediately (no Apply confirmation); random velocity noise is baked into pattern and should be undoable. Seed/reproducibility not required by user.
- Accent offset knob has positions 1–4, where 1 is base downbeat and subsequent values shift accent phase; accents count grid steps. Accent processing is used to polish Velocity Formula with square/periodic emphasis.
- No Quantize, Invert Steps, Swing or Shift Timing.

### Patterns and testing
- Exactly 16 patterns per project.
- Seq/Keyboard/Both modes and Mute are stored separately in each pattern for each instrument channel.
- Initial integration targets: Ableton Live and MorningDAW. A preexisting prototype without velocity handling reportedly already worked with both. Windows version and virtual MIDI port implementation OPEN.

### Clarifications requiring explicit decision
- The sentence describing full-pattern overwrite used 'channel pad' a second time; interpret as PATTERN scope pad only provisionally and confirm.
- Does Duplicate ×2 change the active pattern length? How should 32→64 work when the source note has h=32, and what happens if h>32?
- What constitutes an occupied target for NOTE merge, and whether double-tap is detected on scope pad or action pad?
- Can a scope pad simultaneously act as a normal command when held/tapped as a modifier? Define event priority and avoid accidental command execution.
- Soft takeover for absolute knobs, no jumping on modifier release, and bank switching during modifier hold.
- Exact Groove Formula tail behavior: provide examples for lengths 3,5,7 on 16 steps, and what 'copy from step 2' means when the second formula step is silent.


## 14. Decision log — questionnaire round 3 (2026-10-28) [CONFIRMED]
This section supersedes earlier OPEN/PROPOSED statements when inconsistent. Do not treat tentative control assignments below as confirmed.

- E1: Hold command pad, then press a scope pad (NOTE / CHANNEL / PATTERN) in the opposite row. Exact timing and scope-pad collision resolution remain OPEN.
- E2: Absolute knob parameters use soft takeover (pickup): no value change until physical CC crosses/approaches stored parameter value. Define pickup tolerance and feedback in hardware tests.
- E3: Double-tap the SCOPE pad (not command pad) to request merge/overwrite according to scope. Confirm action dispatch timing to avoid accidental first single-tap operation before double-tap.
- E4: Return to previous knob assignment on modifier release is EXPERIMENTAL. Test pickup and release interactions before freezing behavior.
- E5: Duplicate ×2 only writes notes into previously hidden steps; it does NOT change active playback pattern length. Provide clear UI indicator for hidden edits.
- E6: If selected pitch has events in steps 33–64 (highest occupied step >32), Duplicate ×2 does nothing; no wrapping or truncation. Destination must also be empty for selected pitch.
- E7: CLEAR + three consecutive presses of same keyboard pitch clears current instrument MIDI channel in CURRENT PATTERN only; first press still clears that pitch immediately.
- E8: At pattern 16, Duplicate to Next Pattern is unavailable; do not wrap to 1.
- E9: CH12 uses 16 pads to select 16 patterns. Exact bank and transport controls OPEN.
- E10: Velocity Formula scales existing velocity multiplicatively using relative coefficients. Define range, rounding, clipping and repeated application OPEN.
- E11: Gate Formula CREATES notes and sets gate; it is not merely an effect on preexisting notes. Pitch selection and step occupancy conflict rules OPEN.
- E12: On repeated Humanize operations, restore baseline velocities before generating new randomized variation; store a stable baseline per affected note/operation and make each gesture undoable.
- E13: Groove Formula with exactly one leftover step takes the state of the SECOND formula step (even if silent). Softer tail velocity details OPEN.
- E14: Formula edits provide LIVE audible preview while knobs move, before committing. Modal cancel must restore original notes; MIDI note scheduling and preview timing must not produce stuck notes.

## 15. Candidate CH10 Bank 2 layout [PROPOSED — requires user approval]
Physical layout top row: MIDI 56,57,58,59,64,65,66,67; bottom row: 52,53,54,55,60,61,62,63. These are incoming note numbers; actual behavior depends on pad MIDI channel 10.

### Layout option A: put primary operations on bottom row; scopes on top row
Top: [NOTE scope 56] [CHANNEL scope 57] [PATTERN scope 58] [UNDO 59] [REDO 64] [DRONE toggle 65] [LEGATO 66] [NON-LEGATO 67]
Bottom: [COPY→ 52] [DUP×2 53] [ROTATE 54] [LENGTH 55] [CLEAR 60] [RESERVED 61] [RESERVED 62] [RESERVED 63]
- Scope pads are interpreted as scope only while a compatible command pad is held; otherwise their standalone functions are OPEN. To prevent ambiguous double taps, dispatch scope actions only after double-tap window expires or otherwise make the transaction reversible without audible glitch.
- COPY→ hold + top NOTE/CHANNEL/PATTERN single/double-tap uses previously confirmed safe/merge/overwrite rules.
- ROTATE hold + knob 1 = cyclic rotation; LENGTH hold + three knobs = +/-1, +/-4, power-of-two length selection (exact knobs OPEN).
- CLEAR hold + keyboard pitch = immediate clear pitch; third consecutive press of same pitch clears current channel in current pattern. Separate full-channel double-press action should NOT be assumed.
- DRONE toggles sticky selection mode; keyboard pitches toggle drone pitches. Legato/non-legato behavior needs exact rule for current selected pitch.
- DUP×2 selected pitch only; never extends active length, never overwrites, no operation if highest occupied step >32.
- UNDO/REDO should be available even when a formula modal is active; modal handling priority OPEN.

## 16. Candidate CH11 Bank 2 layout [PROPOSED — requires user approval]
Same physical note grid, but pads are on incoming channel 11. Proposed top row: [GROOVE 56] [VEL FORMULA 57] [GATE FORMULA 58] [HUMANIZE 59] [SCALE VEL 64] [ACCENT 65] [UNDO 66] [REDO 67]. Proposed bottom row: [OFFSET 52] [LENGTH 53] [PREVIEW 54] [APPLY 55] [CANCEL 60] [RESERVED 61] [RESERVED 62] [RESERVED 63].
- These are NOT finalized. In modal formula editor, bottom row can be repurposed to represent formula length 2–8 and pattern steps; design modal pad-state priority explicitly.
- Velocity Formula: multiply existing note velocity. Gate Formula: create notes with gate 14–300%, nonlinear control curve above 150%. Groove Formula: length 2–8; when one step remains, use second formula step.
- Humanize: immediate non-cumulative randomization from baseline; Undo required. Accent: 4-step main accents, optional 2-step microaccents above 50% knob; offset 1–4.
- Soft takeover applies on entering/leaving every knob context, including after switching physical knob bank.

## 17. Next questionnaire — finalize pad layouts and event semantics [OPEN]
F1. Should NOTE/CHANNEL/PATTERN top-row pads be dedicated scopes only while COPY→ is held, or available to other command pads as universal scope modifiers?
F2. Can CH10 top-row scope pads perform standalone actions when no command is held? If yes, which?
F3. Approve/rearrange CH10 candidate grid; are UNDO and REDO positions convenient?
F4. Should COPY→ also be a standalone short-tap action or only command+scope?
F5. Is DUP×2 strictly selected pitch, with no NOTE/CHANNEL/PATTERN scope selector?
F6. Should CLEAR remain a held modifier, and should clearing all notes in current channel have a second explicit shortcut?
F7. Are LEGATO and NON-LEGATO toggles, one-shot transforms, or mutually exclusive edit modes?
F8. Should DRONE toggle mode auto-exit on changing channel or pattern?
F9. What are the three exact knobs and ranges for LENGTH +/-1, +/-4, powers-of-two? How should soft takeover behave for discrete steps?
F10. How should ROTATE show displacement and commit/undo: live on knob move or only on release?
F11. Approve/rearrange CH11 candidate grid; which functions deserve a permanent pad?
F12. In Groove Formula modal, do lower 8 pads choose formula length, input steps, or switch between these submodes?
F13. For Velocity/Gate Formula, should 8 knobs represent 8 positions, and how do formula lengths <8 mask remaining knobs?
F14. What is the exact coefficient range for Velocity Formula (e.g. 0–200% or 0–400%)?
F15. For Gate Formula note creation, is a silent knob value possible and how does pitch get selected?
F16. Should formula live preview be audible immediately on every change, or applied at the next loop boundary to avoid cut notes?
F17. How are APPLY/CANCEL invoked in each formula modal (pads, PC keys, both)?
F18. Should CH11 bank 1 page selection always be 8 VEL pages top and 8 GATE pages bottom, even while formula modal is open?
F19. What does the app show when soft takeover has not yet latched (value, arrow, ghost knob)?
F20. Is hardware LED color feedback optional fallback to screen-only status until throughput is validated?


## 18. Decision log — questionnaire round 4 (2026-10-28) [CONFIRMED]
These decisions override contradictory PROPOSED or OPEN text above. F3 (approval of CH10 layout) was not answered: layout remains a proposal.

- F1: NOTE / CHANNEL / PATTERN scope modifiers are initially used only for COPY→ and CLEAR, not all commands.
- F2: Without a held command, scope pads switch the active editing scope. This is separate from their momentary scope selection while COPY→/CLEAR is held. Exact double-tap collision handling remains OPEN.
- F4: DUP×2 is a single press, selected pitch only.
- F5: LEGATO and NON-LEGATO are two toggleable modes. Whether mutually exclusive and how they transform stored notes is OPEN.
- F6: DRONE input mode remains enabled across pattern switches.
- F7: GROOVE / VELOCITY FORMULA / GATE FORMULA each have a dedicated launch pad.
- F8: Inside GROOVE FORMULA, lower 8 pads select formula length 2–8. There are seven valid lengths, so eighth pad is RESERVED until assigned. Step entry inside modal remains OPEN.
- F9: VELOCITY FORMULA relative multiplicative coefficients range 25–200%.
- F10: GATE FORMULA uses keyboard to select pitch and pads to choose note steps; gate range remains 14–300%.
- F11: PREVIEW, APPLY, CANCEL all have dedicated pads. PREVIEW's exact behavior given always-live next-cycle preview remains OPEN.
- F12: Audible formula preview takes effect at the NEXT pattern cycle boundary, not mid-cycle. Cancel restores baseline and prevents pending preview from applying.
- F13: Soft takeover blocks parameter jumps silently; no UI pickup indicator required for prototype.
- F14: On-screen state is authoritative; hardware pad LED color feedback is optional pending MIDI throughput diagnostics.
- F15: UNDO / REDO are DISABLED while formula modal is open; APPLY/CANCEL must be used. This supersedes section 15's earlier suggestion that Undo/Redo remain available inside modal.
- User notes: some questions were unclear; do not interpret unanswered layout choices as approval. Build only a subset at first, keep polish features in roadmap.

## 19. Refined CH10 Pad Bank 2 — PROPOSED, NOT APPROVED
Incoming MIDI channel 10. Physical TOP notes: 56 57 58 59 64 65 66 67; BOTTOM: 52 53 54 55 60 61 62 63.

| Row | Pad 1 | Pad 2 | Pad 3 | Pad 4 | Pad 5 | Pad 6 | Pad 7 | Pad 8 |
|---|---|---|---|---|---|---|---|---|
| TOP | NOTE (56) | CHANNEL (57) | PATTERN (58) | UNDO (59) | REDO (64) | DRONE (65) | LEGATO (66) | NON-LEGATO (67) |
| BOTTOM | COPY→ (52) | DUP×2 (53) | ROTATE (54) | LENGTH (55) | CLEAR (60) | reserve (61) | reserve (62) | reserve (63) |

Interaction priority proposal: with COPY→ or CLEAR held, top pads 1–3 choose operation scope; without compatible command held, top pads 1–3 select editing scope. A double-tap on a scope pad while COPY→ held requests the appropriate overwrite/merge behavior. Ensure single tap is not destructively dispatched before a potential double tap is resolved. Clear keyboard note on first keypress; third consecutive same note clears current channel in current pattern, with one Undo transaction. Define exactly what CLEAR + NOTE/CH/PAT scope pads do before implementing; avoid making up destructive shortcuts. DUP×2 single tap operates on selected pitch only, writes hidden steps without increasing active length, requires empty destination and highest source step <=32. ROTATE + knob 1 wraps; LENGTH + three separate knobs controls +/-1, +/-4 and power-of-two choices (specific CCs still OPEN). DRONE sticky across pattern change. LEGATO/NON-LEGATO toggles, mutual exclusion OPEN.

## 20. Refined CH11 Pad Bank 2 — PROPOSED, NOT APPROVED
Incoming MIDI channel 11. Top row: 56 57 58 59 64 65 66 67; bottom: 52 53 54 55 60 61 62 63.

| Row | Pad 1 | Pad 2 | Pad 3 | Pad 4 | Pad 5 | Pad 6 | Pad 7 | Pad 8 |
|---|---|---|---|---|---|---|---|---|
| TOP | GROOVE (56) | VEL FORMULA (57) | GATE FORMULA (58) | HUMANIZE (59) | SCALE VEL (64) | ACCENT (65) | UNDO (66) | REDO (67) |
| BOTTOM outside modal | OFFSET (52) | LENGTH (53) | PREVIEW (54) | APPLY (55) | CANCEL (60) | reserve (61) | reserve (62) | reserve (63) |
| BOTTOM inside Groove modal | LEN 2 | LEN 3 | LEN 4 | LEN 5 | LEN 6 | LEN 7 | LEN 8 | reserve |

Conflict: modal lower row cannot simultaneously provide dedicated PREVIEW/APPLY/CANCEL and seven formula-length selections. Resolve by moving modal confirmation to TOP-row controls, PC keyboard, or an additional modal subpage. Do NOT implement both assignments on same pads. PREVIEW should not cause immediate playback; candidate semantics are preview enable/disable with updates scheduled on next loop. UNDO/REDO disabled during modal. The above outside-modal bottom assignments are tentative and may be replaced entirely.

## 21. Short development roadmap — TWO PHASES

### Phase 1 — working musical core / MVP
Goal: rapidly create, hear and switch percussion and bass patterns with no stuck MIDI notes. Do not wait for LED diagnostics or formula design.
1. MIDI I/O diagnostics: identify stock SMK37 input events, pad banks, MIDI channels, knob/fader CC and routing; verify virtual MIDI ports and MIDI Clock in Ableton Live and MorningDAW. Reserve channels 15–16 for DAW passthrough.
2. Deterministic engine: 30–240 BPM, 1/16 steps, max 64, 16 patterns, queued switch at current active cycle end; note-on/off and stop/panic; pattern length changes preserve hidden steps; save/load project. MIDI Clock master, DAW slave.
3. Fast step workflow: CH10 Bank1 16-step grid and four pages; pitch selection via SMK keyboard, audition toggle; channels 1–9 as independent instruments with multiple pitches, Seq/Keyboard/Both and sequencer-only Mute per pattern; CH12 16-pad pattern selection; basic on-screen status.
4. Basic edits: Undo/Redo; safe COPY→ next pattern (entire pattern or selected channel), auto-create target and queue it, refuse overwrite and refuse beyond pattern 16; CLEAR selected pitch and current channel (triple same-key gesture), DUP×2 selected pitch (hidden-step write only). Implement CH10 Bank2 only for commands actually needed; use temporary PC shortcuts for any unresolved pad collisions.
MVP acceptance: enter kick/snare/bass on separate channels, play DAW in sync, vary pattern 1→2 by copying and editing, change length without deleting hidden steps, stop cleanly, reopen saved project and reproduce notes. Check 15–16 passthrough if technically supported by routing setup.

### Phase 2 — musical expression and hardware polish
Only after Phase 1 is stable: complete CH10/CH11 Bank2 mappings and modifier precedence; soft takeover with testable behavior; ROTATE and LENGTH knob modifiers; Drone across loop/pattern changes; Legato/Non-legato; CH11 Bank1 per-pitch velocity/gate pages; modal GROOVE / VELOCITY / GATE formulas with next-cycle audible preview, Apply/Cancel and tail rules; Humanize from baseline, Scale Velocity, accents with 1–4 offset; LED feedback only if speed/reliability validated. Add scope-based overwrite/merge with double-tap after safe copy is proven.

### Explicitly deferred / not in scope
Quantize, swing, timing shift, invert steps, elaborate ALL NOTES editing, more than 16 patterns, DAW-specific automation, mandatory hardware LED feedback.

## 22. Agent implementation guardrails
- Do not infer that F3 approved either pad map. Both are design drafts.
- Prefer a thin vertical slice with working MIDI and a small control set over implementing every draft command.
- Keep controller MIDI decoding, editor command state machine, pattern data, clock scheduler and MIDI output routing separate.
- Use tests for note ownership, transport stop, queued switching, hidden-step duplication, non-overwrite copy, modifier release and modal preview cancellation.
- Do not silently substitute timing behavior or destructive overwrite semantics when specifications remain OPEN.
