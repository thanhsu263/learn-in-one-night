# Adapting the guide to the field

The SWT301 example is a term-heavy theory course with an English MCQ exam, so its main component is the 3-column term table. Other fields are tested differently; pick the main component from what the exam questions actually look like, and keep everything else from SKILL.md (key box, traps, quiz mode, brevity).

| Field / exam shape | Main component | Column 3 / extra |
|---|---|---|
| Theory with many terms (SE, networking, management, marketing, economics MCQ) | Term table | Cue phrases from questions; "A vs B" tables for confusable pairs |
| Math, statistics, physics, signal processing, finance calculations | **Formula cards**: formula · symbols · *when to use (how the question signals it)* · one worked exam problem | Lookup tables of special cases; "lỗi hay sai" (units, sign, off-by-one) |
| Programming / practical code exams (Java, C, SQL, web) | Syntax/API table: construct · what it does · gotcha; short code snippets with predicted output | Output-prediction traps; complexity table; common compile/runtime errors |
| Political theory, philosophy, law, history (often Vietnamese-language exams: MLN, HCM, PLĐC) | Concept table: khái niệm · **định nghĩa giữ nguyên từ khóa giáo trình** (exams quote it) · dấu hiệu nhận biết | Dates/articles/numbers table; timeline flow; for essay exams a **dàn ý trả lời** (answer skeleton) per likely question |
| Foreign language (Japanese, English, Korean…) | Pattern table: mẫu ngữ pháp / từ · nghĩa VI · ví dụ ngắn | "dễ nhầm với" column; kanji/vocab grouped by topic, not by lesson, if the exam mixes lessons |
| Biology, medicine, chemistry | Process flows (ordered steps) + comparison tables | Mnemonics for lists; normal values / numbers table |
| Essay-only exams (any field) | Per likely question: 3–6 bullet answer skeleton + key terms that must appear | Keep it outline-only — the user writes the prose in the exam |

Notes:
- **Exam language decides column 1.** If the exam is in Vietnamese, column 1 is the Vietnamese term as the textbook phrases it, with the English/original term in `<small>` only if it helps.
- **Calculation courses** need fewer tables and more worked examples; recompute every example yourself.
- **Mixed exams** (MCQ + essay + calc): build per-chapter boxes for each part rather than one giant table.
- If the user's question bank shows a recurring question shape (e.g. "which order", "how many test cases"), give it a dedicated quick-method box — that is often worth more than a dozen term rows.
