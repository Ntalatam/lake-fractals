# Push timeline

GitHub's record of when each commit reached github.com/Ntalatam/lake-fractals, next to the commit date that git recorded. A commit date is set by the committer's machine; a push time is recorded by GitHub's server.

## Sources

- `gh api repos/Ntalatam/lake-fractals/events --paginate`, run 2026-11-01 at 22:27:55Z, returned an empty list (HTTP 200), so `docs/push_events.json` holds no PushEvent entries. GitHub's documentation for the events endpoints says a timeline holds up to 300 events, only events created within the past 30 days, and that event latency can be 30 s to 6 h (https://docs.github.com/en/rest/activity/events, read 2026-11-01).
- `gh api "repos/Ntalatam/lake-fractals/activity?per_page=100" --paginate`, run 2026-11-01 at 22:28:15Z, returned 19 records: 1 branch creation and 18 pushes, saved as returned in `docs/push_activity.json`. GitHub documents this endpoint as a history of pushes, merges, force pushes and branch changes (https://docs.github.com/en/rest/repos/repos#list-repository-activities); the page does not say how long records are kept. The table below comes from these records.
- Pushes after 22:28:15Z, including the one that added this file, are not listed.

Each record gives the branch tip before and after the push. Every push here moved `main` forward by exactly one commit (`git rev-list before..after`), and there are no force pushes.

## Commits and push times (UTC)

| commit | subject | commit date (git, as recorded) | commit date (UTC) | pushed (GitHub) | push minus commit date |
|---|---|---|---|---|---|
| f20606f | initial project setup | 2026-11-01T01:08:09-05:00 | 2026-11-01 06:08:09Z | 2026-11-01 06:08:27Z (branch created) | 18 s |
| a80a99d | Add box-counting dimension and logged lake filter | 2026-11-01T01:17:22-05:00 | 2026-11-01 06:17:22Z | 2026-11-01 06:17:26Z | 4 s |
| d5a7e1d | pilot: box-counting dimension under two scale windows | 2026-11-01T01:22:07-05:00 | 2026-11-01 06:22:07Z | 2026-11-01 06:22:08Z | 1 s |
| c4abc80 | pre-registered design; tests verified to fail on broken code | 2026-11-01T01:28:37-05:00 | 2026-11-01 06:28:37Z | 2026-11-01 06:28:38Z | 1 s |
| 5e041df | pre-registration: define decision rule (same sign of rho; area and shoreline length separately) | 2026-11-01T01:34:56-05:00 | 2026-11-01 06:34:56Z | 2026-11-01 06:34:57Z | 1 s |
| 7af119f | pre-registration: resolve source-group and missing-value decisions | 2026-11-01T01:44:11-05:00 | 2026-11-01 06:44:11Z | 2026-11-01 06:44:13Z | 2 s |
| 9ecfa25 | primary analysis: pre-registered design, three windows | 2026-11-01T01:59:02-05:00 | 2026-11-01 06:59:02Z | 2026-11-01 06:59:03Z | 1 s |
| ff3908c | pre-registration addendum: percentile bootstrap method note | 2026-11-01T01:06:00-06:00 | 2026-11-01 07:06:00Z | 2026-11-01 07:06:01Z | 1 s |
| 47f5fce | exploratory: outer-shore check (post-hoc, not pre-registered) | 2026-11-01T01:08:59-06:00 | 2026-11-01 07:08:59Z | 2026-11-01 07:09:00Z | 1 s |
| 6c24ab3 | audit cleanup: comments, strict count check, disclosures | 2026-11-01T01:39:06-06:00 | 2026-11-01 07:39:06Z | 2026-11-01 07:39:10Z | 4 s |
| e8cdbec | draft: methods, results, limitations, figures | 2026-11-01T01:51:45-06:00 | 2026-11-01 07:51:45Z | 2026-11-01 07:51:49Z | 4 s |
| d61206b | record rationale for 20-100 m window | 2026-11-01T01:57:25-06:00 | 2026-11-01 07:57:25Z | 2026-11-01 07:57:28Z | 3 s |
| 6ff2e1f | methods: note rationales recorded after results; cite every number | 2026-11-01T02:09:37-06:00 | 2026-11-01 08:09:37Z | 2026-11-01 09:09:41Z | 3,604 s |
| b53487f | cite map accuracy standard; note imagery-based sources | 2026-11-01T02:14:50-06:00 | 2026-11-01 08:14:50Z | 2026-11-01 09:14:53Z | 3,603 s |
| 3b85cc7 | correct digitizing accuracy in window disclosure | 2026-11-01T02:17:10-06:00 | 2026-11-01 08:17:10Z | 2026-11-01 09:17:14Z | 3,604 s |
| f9e2f28 | post-review validation: fix koch benchmark, calibrate estimator near 1 | 2026-11-01T06:17:01-06:00 | 2026-11-01 12:17:01Z | 2026-11-01 12:17:07Z | 6 s |
| d7de0da | methods, limitations: describe post-review validation; fix stale citations | 2026-11-01T06:26:46-06:00 | 2026-11-01 12:26:46Z | 2026-11-01 12:26:51Z | 5 s |
| 0befd9a | post-review checks: width, spatial bootstrap, digitizing density | 2026-11-01T07:43:43-06:00 | 2026-11-01 13:43:43Z | 2026-11-01 13:43:44Z | 1 s |
| b610563 | post-hoc: width-based exclusion check | 2026-11-01T16:22:58-06:00 | 2026-11-01 22:22:58Z | 2026-11-01 22:23:02Z | 4 s |

## Analysis plan and primary results

According to GitHub's activity records, the three analysis-plan commits were pushed before the primary analysis commit:

- c4abc80 (pre-registered design; tests verified to fail on broken code): pushed 2026-11-01 06:28:38Z
- 5e041df (pre-registration: define decision rule (same sign of rho; area and shoreline length separately)): pushed 2026-11-01 06:34:57Z
- 7af119f (pre-registration: resolve source-group and missing-value decisions): pushed 2026-11-01 06:44:13Z
- 9ecfa25 (primary analysis: pre-registered design, three windows): pushed 2026-11-01 06:59:03Z

Push minus commit date is under one minute for every commit except 6ff2e1f, b53487f, 3b85cc7, where it is 3,604 s, 3,603 s, 3,604 s.
