-- The quiz's anonymous score tally (records/changes/CHG-019), D1 database
-- uncost-quiz (production) and uncost-quiz-preview (previews), bound to the
-- Pages project as QUIZ_DB. Separate from uncost-signups, which holds
-- personal data; nothing here is personal.
--
-- One row per completed quiz, and nothing else: no IP address, user agent,
-- cookie, fingerprint, email, name or id column. The rowid SQLite keeps is
-- internal and never read or returned.

CREATE TABLE score (
  -- The question set's version (_data/quiz.js): 12 hex characters.
  version TEXT NOT NULL CHECK (length(version) = 12 AND version NOT GLOB '*[^0-9a-f]*'),
  -- Number right, recomputed by the server from `answers`.
  correct INTEGER NOT NULL CHECK (correct >= 0 AND correct <= total),
  -- Number of questions.
  total INTEGER NOT NULL CHECK (total > 0 AND total <= 64),
  -- Right (1) or wrong (0) per question, in quiz order.
  answers TEXT NOT NULL CHECK (length(answers) = total AND answers NOT GLOB '*[^01]*'),
  -- The UTC date only, YYYY-MM-DD; no time.
  day TEXT NOT NULL CHECK (day GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
);
CREATE INDEX score_version ON score (version);

-- The question sets seen, in order, for retention: rows are kept for the
-- current set and the one before it only. When a score arrives for a new set,
-- every row of an older set is deleted (lib/quiz.js). Not per person.
CREATE TABLE question_set (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  version TEXT NOT NULL UNIQUE
);
