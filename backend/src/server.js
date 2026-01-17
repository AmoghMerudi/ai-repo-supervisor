import express from "express";
import cors from "cors";
import { analyzePullRequest } from "./analyze-pr.js";

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_SECRET = process.env.BACKEND_SECRET || "dev-secret";

app.use(cors());
app.use(express.json());

function checkAuth(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth || auth !== `Bearer ${BACKEND_SECRET}`) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
}

app.get("/health", (_, res) => {
  res.json({ status: "ok" });
});

app.post("/analyze-pr", checkAuth, (req, res) => {
  try {
    const result = analyzePullRequest(req.body);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Analysis failed" });
  }
});

export function startServer() {
  app.listen(PORT, () => {
    console.log(`Backend running on http://localhost:${PORT}`);
  });
}

app.get("/", (_, res) => {
  res.send("AI Repo Supervisor backend running");
});