export type RepoSummaryMock = {
  repo: string;
  current_health: number;
  avg_score: number;
  total_prs: number;
  cumulative_score: number;
  updated_at: string;
  recent: Array<{
    pr_number: number;
    score: number;
    timestamp: string;
    author: string;
    overall_health: number;
  }>;
};

export const repoHealthMocks: RepoSummaryMock[] = [
  {
    repo: "owner/repo",
    current_health: 90,
    avg_score: 5,
    total_prs: 4,
    cumulative_score: 20,
    updated_at: "2026-01-17T22:46:12.817200",
    recent: [
      {
        pr_number: 3,
        score: 0,
        timestamp: "2026-01-17T22:46:12.817189",
        author: "carol",
        overall_health: 90,
      },
      {
        pr_number: 2,
        score: 10,
        timestamp: "2026-01-17T22:12:48.205190",
        author: "amogh",
        overall_health: 95,
      },
      {
        pr_number: 1,
        score: 10,
        timestamp: "2026-01-17T21:55:01.016220",
        author: "alex",
        overall_health: 100,
      },
    ],
  },
  {
    repo: "frontend/app",
    current_health: 84,
    avg_score: 7,
    total_prs: 6,
    cumulative_score: 42,
    updated_at: "2026-01-17T20:11:44.100000",
    recent: [
      {
        pr_number: 24,
        score: 8,
        timestamp: "2026-01-17T20:11:44.100000",
        author: "ravi",
        overall_health: 84,
      },
      {
        pr_number: 23,
        score: 6,
        timestamp: "2026-01-17T18:05:02.112000",
        author: "mila",
        overall_health: 82,
      },
      {
        pr_number: 22,
        score: 9,
        timestamp: "2026-01-17T16:44:08.772000",
        author: "zoe",
        overall_health: 80,
      },
    ],
  },
  {
    repo: "infra/pipelines",
    current_health: 62,
    avg_score: 3,
    total_prs: 9,
    cumulative_score: 27,
    updated_at: "2026-01-17T19:37:20.900000",
    recent: [
      {
        pr_number: 91,
        score: 2,
        timestamp: "2026-01-17T19:37:20.900000",
        author: "devin",
        overall_health: 62,
      },
      {
        pr_number: 90,
        score: 3,
        timestamp: "2026-01-17T18:13:44.382000",
        author: "sam",
        overall_health: 60,
      },
      {
        pr_number: 89,
        score: 5,
        timestamp: "2026-01-17T16:59:11.540000",
        author: "jin",
        overall_health: 58,
      },
    ],
  },
];
