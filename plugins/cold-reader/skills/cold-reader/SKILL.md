---
name: cold-reader
description: "A cold read of the writer's own writing: one chapter of a book, one piece (a story, a poem, an essay or any file by path) or a whole book, read in a fresh read-only agent that reports ranked findings in chat. Structural first, line-level second, never a rewrite, never a suggested sentence. Use for 'read this back', 'what is wrong with chapter 3', 'read the whole book', 'does the book hold', or any request to judge writing rather than produce it."
---

# Cold reader

One reader, one report in chat. This skill never edits: nothing is
written to disk, no sentence is proposed.

The reader judges the page, not the intent. That is why the read runs in
the `cold-reader:cold-reader` agent with only the files named here: a
reader who has watched the drafting knows what was meant and forgives the
page for it. The reader's standards live in that agent; this skill only
decides what it is given.

## Inputs

Each input is named by the user, then by the skill that invoked this one,
then by the project's `CLAUDE.md`, in that order. Any input may be
absent; an absent one is `none` in the dispatch, never guessed.

| Input | What it is |
|---|---|
| Chapters directory | The directory that holds a book's chapters. A numbered chapter is a file in it whose name starts with digits and a hyphen, such as `07-the-crossing.md`; that number orders it. |
| Outline | The book's plan, one file. |
| Lore | The world's settled facts: a file, or a directory. If the directory has an index (a `README.md`), chapter mode gives the reader the pages the chapter touches, chosen from that index; otherwise, and in book mode, the whole file or directory. |
| Running order | A file that maps chapters to acts. This skill reads it for act boundaries; the reader never gets it. |
| Voice file | A profile of the writer's prose voice, and the sections of it to read. Chapter and book mode only. |
| Never | Paths the reader must never see: a file, or a directory and everything under it. Name here the record's reasoning (open questions, the deliberation behind decisions), archives, other books, and a draft's own notes. |
| Root | The directory relative paths resolve against. Default: the session's working directory. |

Every path in a dispatch is absolute. Before dispatching, check every
path in it against the never list and leave out any path on or under a
never path. The never list itself goes on the dispatch's `never:` line.

`examples/` in this skill's directory holds an invented book to try it
on: `examples/chapters/` (three numbered chapters) and
`examples/outline.md`. It has no lore, so the lore input is `none`.

## Modes

Decide which from the invocation, in one line, then act.

- **Chapter**: one numbered chapter in the chapters directory.
- **Piece**: any other file: a poem, a story, an essay, anything.
- **Book**: every numbered chapter in a directory, in order. "Read the
  whole book", "does the book hold".

## Chapter mode

### 1. Resolve the piece: do not ask

| Named | Piece |
|---|---|
| nothing | the highest-numbered chapter in the chapters directory |
| a chapter number `NN` | the chapter in the chapters directory with that number |
| a file | that file; if no chapters directory is named and the file is a numbered chapter, its own directory becomes the chapters directory; a numbered chapter in the chapters directory is chapter mode, anything else is piece mode |

If there is still no chapters directory, or it has no numbered chapter,
or none with that number, say so in one line and stop; do not fall back to
another directory unasked.

Name the piece in the opening line. Then dispatch.

### 2. What the reader gets, and nothing else

- **The piece**, whole.
- **The outline**.
- **The lore**: the pages the chapter touches, per the lore's index, or
  the whole lore.
- **The two chapters before it** in the chapters directory, by number,
  whole: the voice reference and the continuity reference. One if only
  one exists; `none` for the first chapter.
- **The voice file**, and the sections to read.
- **The beat**: which beat of the outline the chapter should serve, if
  the outline makes that readable; otherwise "beat: not stated".

### 3. Dispatch

One `Agent` call, `subagent_type: cold-reader:cold-reader`. The message is exactly these lines, nothing else:

    mode: chapter
    piece: <absolute path>
    outline: <absolute path, or "none">
    lore: <absolute paths, one per line, or "none">
    preceding: <one or two absolute paths, or "none">
    beat: <the beat's words, or "not stated">
    voice: <absolute path, then the sections to read, or "none">
    never: <absolute paths, one per line, or "none">

## Piece mode

The piece alone. Nothing else: not the outline, not the lore, not the
voice file. A poem's `themes` frontmatter is in the file; the reader
reads it there.

One `Agent` call, `subagent_type: cold-reader:cold-reader`. The message is exactly these lines, nothing else:

    mode: piece
    piece: <absolute path>
    never: <absolute paths, one per line, or "none">

## Book mode

### 1. Resolve the book

The chapters directory, or the directory the user names. A directory
with no numbered chapters: say so, stop.

Say in the opening line which directory, how many chapters, and, if the
outline or the running order names acts, the act split by word count
(`wc -w`); computed now, never stored.

### 2. What the reader gets

- The outline and the lore, whole.
- Every numbered chapter in the directory, in order, whole. A
  100,000-word book is within one agent's reach; do not split the book
  across agents; the point of the mode is one reader holding all of it.
- The act boundaries, as chapter numbers, if the outline or the running
  order states them; otherwise "acts: not stated".
- The voice file, and the sections to read.

### 3. Dispatch

One `Agent` call, `subagent_type: cold-reader:cold-reader`. The message is exactly these lines, nothing else:

    mode: book
    directory: <absolute path>
    outline: <absolute path, or "none">
    lore: <absolute paths, one per line, or "none">
    chapters: <every numbered file, absolute, in order, one per line>
    acts: <act, chapter range, words; one per line, or "not stated">
    voice: <absolute path, then the sections to read, or "none">
    never: <absolute paths, one per line, or "none">

## Relay: all modes

Give the report back as the agent wrote it, unedited. Do not soften it,
add findings, or argue with it. If the agent broke the shape or proposed
a sentence, say so in one line above the report and leave the report as
is; the breach is itself a finding about the skill.

Then stop. No offer to fix, no commit, no file touched.
