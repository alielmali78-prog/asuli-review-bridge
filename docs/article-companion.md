# Mapping code to the article

The original Turkish article concerns the running Asuli system, where three
advisers critiqued a Medium workflow incident. The reference project's example
is a **synthetic, reduced version**: manual document readback does not prove
that a scheduled writer can perform automatic delivery.

| Article idea | Portable source |
| --- | --- |
| A reply must identify its question | `store.py`: replies.request_id foreign key + UNIQUE |
| Adviser opinion is separate from operator decision | `store.py`: decisions table and decide |
| Concurrency must not duplicate calls | `store.py`: claim transaction |
| A failed or partial response is not success | `providers.py`: output/stop-reason checks |
| Demonstrate without external calls | `examples/offline_demo.py` |
| Test failure and restart behavior | `tests/test_bridge.py` |

Before putting a GitHub code link in the article, publish the reviewed project
and pin the link to its actual commit/tag. Do not invent a repository URL or
reuse original live-system PASS counts for this edition. The validation report
documents the checks that were actually run locally.
