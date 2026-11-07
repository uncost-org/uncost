// GET /api/quiz/stats?version=… — the tally for the current question set
// (CHG-019): {count, mean, perQuestion}, cached at the edge for 60 seconds;
// see lib/quiz.js. 404 unless the tally is on.
import build from "../../_generated/build.json" with { type: "json" };
import { handleStats } from "../../../lib/quiz.js";

export const onRequestGet = (context) => handleStats(context, build.quiz);
