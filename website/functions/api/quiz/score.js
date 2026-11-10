// POST /api/quiz/score — one anonymous score per completed quiz (CHG-019).
// Body {version, answers}; see lib/quiz.js. 404 unless the tally is on.
import build from "../../_generated/build.json" with { type: "json" };
import { handleScore } from "../../../lib/quiz.js";

export const onRequestPost = (context) => handleScore(context, build.quiz);
