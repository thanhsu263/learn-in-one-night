---
name: learn-in-one-night
description: Build a concise, exam-focused study guide ("tài liệu ôn tập") for any course or subject — software engineering, math, economics, law, political theory, languages, medicine, anything. It first interviews the user (which course, which field, exam language and format) and collects ALL their sources (lecture slides, textbooks, past exams, question banks, Quizlet links, cheat sheets, notes), then extracts them, mines the exam question patterns, and writes one chapter-by-chapter HTML guide: original-language terms + short Vietnamese explanations + the cue phrases exams use + exam traps + formulas + a self-quiz mode. Use this whenever the user wants to ôn thi / ôn tập / review for an exam, asks for a tóm tắt môn, đề cương ôn tập, cheat sheet, summary of slides, flashcard-style notes, or says earlier summaries were too long — even if they don't say "study guide".
---

# Learn in one night (tài liệu ôn tập)

The user is a university student reviewing for exams across many subjects. What works for them — learned the hard way — is a **short, exam-shaped** document, not a faithful summary of the slides. Long, faithful bilingual summaries were tried before and failed: "quá dài dòng, khó hiểu". Their real problem is *recognition*: an exam question describes a concept by its features ("led by the author", "simulates the environment"), and they can't map the description back to the term. Every design choice below serves that: keep the term in the exam's language, explain it in one short Vietnamese line, and list the phrases exams use to describe it.

A finished example (software testing course, SWT301) is in `assets/example-swt301.html`. It's ~85 KB, so don't read it whole — skim one chapter (e.g. `grep -n "CHƯƠNG 3" -A 80`) when you want a concrete quality bar.

## Workflow

### 1. Interview first — collect everything before synthesizing

Don't start reading files or writing until you know what the exam is and have every source. A guide built from slides alone misses what the exam actually tests; a guide built before the user mentions their past-exam folder has to be redone.

The user prefers **popup questions** (the `AskUserQuestion` tool) over a wall of text questions — clicking is faster than typing, and every popup also has an "Other" field for free text. Write all questions and options in Vietnamese. Skip any question the user already answered (in the invocation arguments, e.g. `/learn-in-one-night MLN111`, or earlier in the chat).

**Before the first popup, look around (a few seconds, no deep reading):** list the working directory and obvious subfolders (`Slides`, `Exam`, `De`, `Quizlet`, `Downloads` only if the user mentions it) to guess the course code from folder/file names and to find candidate source files. Those guesses become popup options, so the user mostly clicks instead of typing paths.

**Popup 1 — môn & kỳ thi** (one `AskUserQuestion` call, 4 questions):

| header | question | options (2–4; user can always type "Other") |
|---|---|---|
| Môn học | Bạn cần ôn môn nào? | course codes guessed from folder/file names, labelled "(từ thư mục hiện tại)"; if nothing to guess, 2 generic options such as "Môn chuyên ngành" / "Môn đại cương" and rely on "Other" for the name |
| Ngôn ngữ đề | Đề thi viết bằng tiếng gì? | Tiếng Anh · Tiếng Việt · Tiếng Nhật |
| Hình thức | Đề thi có những dạng nào? (multiSelect) | Trắc nghiệm · Tự luận · Bài tập tính toán · Thực hành / code |
| Thời gian | Còn bao lâu nữa thi? | Tối nay / ngày mai · 2–4 ngày · 1 tuần trở lên |

The field (lĩnh vực) usually follows from the course; only ask it (as a popup) if it doesn't.

**Popup 2 — nguồn tài liệu & ưu tiên** (one call, up to 4 questions):

| header | question | options |
|---|---|---|
| Tài liệu | Chọn các nguồn sẽ dùng (multiSelect) | the candidate folders/files you found, each with a short description ("Slides/ – 8 file .ppt"); always include an option for **đề cũ / ngân hàng câu hỏi** even if none was found, since it's the most valuable source |
| Link | Có link Quizlet / flashcard / đề online không? | "Có, mình dán link" · "Không có" |
| Độ gọn | Muốn tài liệu gọn cỡ nào? | "Siêu gọn – chỉ ô Nhớ + Bẫy đề" · "Gọn – mỗi chương ~5 phút đọc (Recommended)" · "Chi tiết hơn" |
| Ưu tiên | Phần nào bạn chưa chắc nhất? (multiSelect) | chapter names if you could read them from file names; otherwise "Định nghĩa / thuật ngữ" · "Công thức / bài tập" · "Quy trình / thứ tự các bước" |

Links and paths not among the options arrive through "Other" text; if the user chose "Có, mình dán link", ask for the links in one short chat line.

**Popup 3 — xác nhận** (one question): summarize the source list in the question text and ask "Còn nguồn nào nữa không?" with options "Đủ rồi, bắt đầu làm (Recommended)" · "Thêm nguồn" (they type it in Other). Ask this once, then proceed without further questions unless something is blocking.

If `AskUserQuestion` isn't available (e.g. outside Claude Code), ask the same things as one compact numbered message in chat instead.

### 2. Extract the sources

Run the bundled extractor on every local path the user gave (files or folders, any mix):

```bash
python "<skill-dir>/scripts/extract_sources.py" <path1> <path2> ... -o "<work-dir>/_extract"
```

It writes one UTF-8 `.txt` per source (with `### Slide N` / `### Page N` markers) plus `_index.md` listing what was extracted, char counts, and warnings. It handles .pptx, .ppt (old binary), .pdf, .docx, .xlsx, .svg (text + embedded images), .txt/.md/.html/.csv. Read `_index.md` first, then the texts.

- **Warnings matter**: a PDF with ~0 chars is scanned — read its pages as images with the Read tool (`pages` param). Images extracted from SVGs/slides: look only at the ones likely to hold diagrams or tables.
- **Quizlet / web question banks**: open the link in the browser and use `get_page_text`. Public Quizlet pages only show part of a large set; say how many cards you actually got, and offer that the user paste the rest (Quizlet's own export needs the set owner).
- Old `.doc` / `.xls` aren't supported — ask the user to resave as .docx/.xlsx or PDF.

### 3. Mine the exam patterns (before outlining)

From the past exams / question banks, build a scratch list (not part of the guide) of:

- **topics actually tested** and how often → this sets priority and length per chapter;
- **how each term is described** in questions — the exact cue phrases, in the exam's language;
- **question shapes**: "which is NOT…", ordering steps, pick the matching value, calculate X, match role → task;
- **traps**: plausible wrong options, near-synonyms, absolute words ("always", "prove").

If there are no exam sources, derive priority from the syllabus/learning outcomes and slide emphasis, and tell the user the guide is less exam-calibrated because of that.

### 4. Outline: decide what earns a place

Per chapter, keep only what an exam could ask or what is needed to understand that. Drop course logistics, history anecdotes, motivational slides, long examples. The user's own example of the right scope: "chap 1 chỉ tập trung vào 7 quy tắc kiểm thử". When a slide deck and a standard disagree (old vs. new syllabus wording), note both briefly — exams sometimes use either.

Rough budget: a chapter should be readable in ~5 minutes. If a chapter's table passes ~15 rows, you're probably including things the exam doesn't test.

### 5. Write the HTML from the template

Copy `assets/template.html` and fill it in. Read the comments in it — it demonstrates every component. Save as `<CODE>_On_Tap_Gon/<CODE>_On_Tap_Gon.html` next to the user's sources (or where they asked). For big courses, write the skeleton first, then fill one chapter per edit.

Each chapter, in this order:

1. **"Nhớ trong 30 giây"** box — ≤5 bullets: the must-know lists, orders, formulas. Add a mnemonic (`<span class="mn">`) for any ordered list or set the exam asks to recall (e.g. *Có – Hết – Sớm – Cụm – Sâu – Cảnh – Ảo* for the 7 principles).
2. **Term tables**, 3 columns: **Term (exam language)** | **Hiểu nhanh (VI)** | **Đề hay tả bằng cụm từ…** (cue phrases quoted in the exam language). Synonyms go in `<small>` under the term.
3. **Flows / ordered steps** (`.flow`), **comparison tables** for pairs that get confused, **formula boxes** (`.f`) with one worked example each.
4. **"Bẫy đề"** box — the traps from step 3, each phrased as the wrong belief → the right answer.

End with a **"Tổng hợp công thức và con số"** section and a short exam-tactics box suited to the exam format.

Writing rules, and why:
- **Never translate the term itself.** The exam shows "Pesticide paradox", not "nghịch lý thuốc trừ sâu"; the Vietnamese goes in column 2 to make it stick.
- **One idea per cell, short sentences.** The user skims; prose paragraphs are what made the previous guides fail.
- **Bold the distinguishing word** (who leads, before/after, valid/invalid) — that is what the MCQ options differ on.
- **Cue phrases come from real questions** when you have them; otherwise from the textbook's definitions. Don't invent exam phrasing.
- Keep the self-quiz button (it blurs column 2; click a cell to reveal). Active recall is the point.

Different fields need different main components (formula cards for math, answer outlines for essay exams, grammar-pattern tables for languages…). Read `references/domains.md` when the course isn't a term-heavy theory course like software engineering.

### 6. Verify before handing over

```bash
python "<skill-dir>/scripts/check_html.py" "<path-to-guide.html>"
```

It checks tag balance, that the quiz toggle and every chapter anchor exist, and counts terms/traps per chapter (flagging empty or bloated chapters). Then spot-check content yourself: recompute every worked example, compare every ordered list (process steps, phases) against the source, and make sure each exam pattern from step 3 is answerable from the guide. Anything you added from general knowledge rather than the sources should be correct and standard; if unsure, leave it out.

### 7. Report

Tell the user (in Vietnamese): where the file is, what each chapter focuses on in one line each, how to use the boxes + quiz mode, and any gaps (sources you couldn't read, partial Quizlet coverage, chapters with no exam data). Offer to add terms they meet later while practising.
