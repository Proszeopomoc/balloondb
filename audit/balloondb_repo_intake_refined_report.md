# BalloonDB repo intake refined audit
## Input
- Source ZIP: balloondb_repo_intake_audit.zip
- Files indexed: 49,500
- Folders indexed: 29,605
- Total bytes: 5,049,482,488 (5.05 GB)

## Refined category summary

| Category | Files | MB | Decision |
|---|---:|---:|---|
| DROP_WORKSPACE_RUNS | 22,589 | 3.094 | Do not move to repo; generated run workspaces. |
| DROP_BUILD_ARTIFACTS | 15,079 | 30.300 | Do not move to repo; compiled artifacts. |
| DROP_TMP_CACHE | 3,307 | 33.593 | Do not move to repo; temp/cache. |
| FROZEN_SHADOW_ARCHIVE | 3,026 | 64.129 | Keep local/offline archive only. |
| LOCAL_ONLY_LOGS | 2,679 | 147.395 | Keep local evidence, do not repo. |
| EXTERNAL_PROJECTS_NOT_CORE | 1,697 | 12.531 | Not BalloonDB core. |
| FROZEN_AUTONOMY_DRIFT | 445 | 6.761 | Move only summary to _frozen; do not revive. |
| EVIDENCE_CORE_REFERENCE | 145 | 5.218 | Small evidence can go to docs/evidence. |
| EXAMPLE_CODE_GRAPH | 90 | 1.358 | Example/migration only, not core. |
| OPERATOR_SCRIPT_LATER | 80 | 0.094 | Client/operator repo later. |
| REPO_CORE_SOURCE | 70 | 0.221 | Candidate source for balloondb repo. |
| MEMORY_REVIEW | 63 | 0.033 | Manual review under memory. |
| OPERATOR_CLIENT_LATER | 56 | 1.200 | Client/operator repo later. |
| MANUAL_REVIEW | 43 | 1.152 | Manual review; mostly old operator/core transition scripts. |
| SPEC_CONFIG_REVIEW | 33 | 0.066 | Spec/config seed material; review into docs/specs. |
| EVIDENCE_LOCAL_ONLY | 30 | 1.193 | Local evidence only. |
| MIGRATION_BPACK_EXAMPLES | 28 | 6.881 | Small migration examples, not runtime core. |
| REPO_CORE_SCRIPTS_REVIEW | 20 | 0.019 | Core scripts review; convert to tests/tools if useful. |
| REPO_CORE_EXAMPLES | 16 | 1.121 | Core binary/index/WAL examples. |
| RELEASE_ARTIFACT_LARGE_PACKS | 4 | 4733.124 | Do not commit; release/artifact/local archive only. |

## Core repo candidates

### REPO_CORE_SOURCE

- `balloondb_core\__init__.py` (55 bytes, 2026-06-15 10:09:44)
- `balloondb_core\bql_ast.py` (788 bytes, 2026-06-15 10:50:27)
- `balloondb_core\bql_contract_runner.py` (557 bytes, 2026-06-15 11:17:41)
- `balloondb_core\bql_daemon.py` (4832 bytes, 2026-06-15 11:34:00)
- `balloondb_core\bql_daemon_client.py` (3216 bytes, 2026-06-15 11:34:00)
- `balloondb_core\bql_error_contract.py` (2176 bytes, 2026-06-15 12:47:38)
- `balloondb_core\bql_executor.py` (7621 bytes, 2026-06-15 13:37:08)
- `balloondb_core\bql_memory_reader.py` (3948 bytes, 2026-06-15 08:30:08)
- `balloondb_core\bql_parser.py` (4611 bytes, 2026-06-15 12:47:37)
- `balloondb_core\bql_planner.py` (3289 bytes, 2026-06-15 13:37:08)
- `balloondb_core\bql_query_history.py` (11570 bytes, 2026-06-15 13:42:55)
- `balloondb_core\bql_time_filter.py` (3723 bytes, 2026-06-15 12:47:37)
- `balloondb_core\bql_ts_index.py` (7110 bytes, 2026-06-15 13:37:08)
- `balloondb_core\cli.py` (5869 bytes, 2026-06-15 10:50:27)
- `balloondb_core\config\README_ROLE_MAP_USAGE.md` (329 bytes, 2026-06-15 10:09:44)
- `balloondb_core\crash_recovery_v03h3.py` (5078 bytes, 2026-06-15 16:00:14)
- `balloondb_core\data\errors.jsonl` (300 bytes, 2026-06-15 18:16:35)
- `balloondb_core\data\explain_traces\153433369b66c33a644cac56fc581a63c0a835028e99911644646460494553da.json` (2865 bytes, 2026-06-15 18:16:38)
- `balloondb_core\data\explain_traces\7990c3900d2b3c6a449fb9273a319d79b1ba401d11c69197e25d2201f93f90cb.json` (1794 bytes, 2026-06-15 18:16:38)
- `balloondb_core\data\explain_traces\a6ec7a332eaeac88521ce32a8bc601e2d11d5404dc3569be5a534855ab505734.json` (1842 bytes, 2026-06-15 18:16:38)
- `balloondb_core\data\manual_query.bql` (159 bytes, 2026-06-15 10:18:26)
- `balloondb_core\data\query_history.jsonl` (5310 bytes, 2026-06-15 18:16:38)
- `balloondb_core\data\sample_outputs.jsonl` (4036 bytes, 2026-06-15 18:16:35)
- `balloondb_core\data\sample_queries.txt` (506 bytes, 2026-06-15 18:16:35)
- `balloondb_core\data\selftest_v03g9_memory.jsonl` (524 bytes, 2026-06-15 18:16:38)
- `balloondb_core\data\selftest_v03g9_memory\pack_selftest_v03g9.jsonl` (524 bytes, 2026-06-15 18:16:38)
- `balloondb_core\data\selftest_v03g9_rotation\query_history_rotation.jsonl` (1140 bytes, 2026-06-15 18:16:38)
- `balloondb_core\data\v03g1_manual_query.bql` (106 bytes, 2026-06-15 10:33:52)
- `balloondb_core\data\v03g1_selftest_output.jsonl` (1482 bytes, 2026-06-15 18:16:36)
- `balloondb_core\data\v03g2_selftest_output.jsonl` (3339 bytes, 2026-06-15 18:16:37)
- `balloondb_core\data\v03g2_test_exec_word.bql` (148 bytes, 2026-06-15 10:53:09)
- `balloondb_core\data\v03g3_selftest_output.jsonl` (18550 bytes, 2026-06-15 11:22:59)
- `balloondb_core\data\v03g4_bench_query.bql` (109 bytes, 2026-06-15 12:01:12)
- `balloondb_core\data\v03g4_selftest_output.json` (1442 bytes, 2026-06-15 11:34:01)
- `balloondb_core\data\v03g6_selftest_output.json` (1710 bytes, 2026-06-15 18:16:38)
- `balloondb_core\data\v03g6_time_filter_memory.balloondb\time_records.jsonl` (489 bytes, 2026-06-15 18:16:38)
- `balloondb_core\data\v03h1_selftest\partial_copy.bdb` (1299 bytes, 2026-06-15 18:16:30)
- `balloondb_core\data\v03h1_selftest\v03h1_selftest.bdb` (1306 bytes, 2026-06-15 18:16:30)
- `balloondb_core\data\v03h2_wal_selftest\partial_copy.wal` (1594 bytes, 2026-06-15 18:16:31)
- `balloondb_core\data\v03h2_wal_selftest\v03h2_recovered_store.bdb` (231 bytes, 2026-06-15 18:16:31)
- `balloondb_core\data\v03h2_wal_selftest\v03h2_selftest.wal` (1603 bytes, 2026-06-15 18:16:31)
- `balloondb_core\data\v03h3_crash_recovery_selftest\v03h3_partial_state.json` (630 bytes, 2026-06-15 18:16:31)
- `balloondb_core\data\v03h3_crash_recovery_selftest\v03h3_partial_store.bdb` (553 bytes, 2026-06-15 18:16:31)
- `balloondb_core\data\v03h3_crash_recovery_selftest\v03h3_partial_tail.wal` (2384 bytes, 2026-06-15 18:16:31)
- `balloondb_core\data\v03h3_crash_recovery_selftest\v03h3_recovered_store.bdb` (553 bytes, 2026-06-15 18:16:31)
- `balloondb_core\data\v03h3_crash_recovery_selftest\v03h3_recovery_state.json` (628 bytes, 2026-06-15 18:16:31)
- `balloondb_core\data\v03h3_crash_recovery_selftest\v03h3_selftest.wal` (2395 bytes, 2026-06-15 18:16:31)
- `balloondb_core\reports\selftest_v03g9_report.html` (2031 bytes, 2026-06-15 18:16:39)
- `balloondb_core\reports\v03g1_selftest_report.html` (341 bytes, 2026-06-15 10:30:45)
- `balloondb_core\reports\v03g2_selftest_report.html` (715 bytes, 2026-06-15 10:53:16)
- `balloondb_core\reports\v03g3_selftest_report.html` (1339 bytes, 2026-06-15 11:22:59)
- `balloondb_core\reports\validation_report.html` (1162 bytes, 2026-06-15 18:16:35)
- `balloondb_core\role_map_loader.py` (679 bytes, 2026-06-15 10:09:44)
- `balloondb_core\selftest\__init__.py` (0 bytes, 2026-06-15 10:09:44)
- `balloondb_core\selftest\bql_compat_fix_v03h4a.py` (774 bytes, 2026-06-15 16:24:46)
- `balloondb_core\selftest\run_core_regression_gate_v03h4.py` (6948 bytes, 2026-06-15 16:12:24)
- `balloondb_core\selftest\run_selftest.py` (3374 bytes, 2026-06-15 10:09:44)
- `balloondb_core\selftest\run_selftest_v03g1.py` (1445 bytes, 2026-06-15 08:30:08)
- `balloondb_core\selftest\run_selftest_v03g2.py` (2490 bytes, 2026-06-15 10:50:27)
- `balloondb_core\selftest\run_selftest_v03g3.py` (4423 bytes, 2026-06-15 11:17:41)
- `balloondb_core\selftest\run_selftest_v03g4.py` (4586 bytes, 2026-06-15 11:34:00)
- `balloondb_core\selftest\run_selftest_v03g6.py` (5014 bytes, 2026-06-15 12:47:38)
- `balloondb_core\selftest\run_selftest_v03g7_all.py` (12997 bytes, 2026-06-15 13:31:43)
- `balloondb_core\selftest\run_selftest_v03g8.py` (5034 bytes, 2026-06-15 13:37:08)
- `balloondb_core\selftest\run_selftest_v03g9.py` (12600 bytes, 2026-06-15 13:42:55)
- `balloondb_core\selftest\run_selftest_v03h1.py` (3343 bytes, 2026-06-15 15:46:24)
- `balloondb_core\selftest\run_selftest_v03h2.py` (4494 bytes, 2026-06-15 15:54:50)
- `balloondb_core\selftest\run_selftest_v03h3.py` (5223 bytes, 2026-06-15 16:00:14)
- `balloondb_core\storage_format_v03h1.py` (8370 bytes, 2026-06-15 15:46:24)
- `balloondb_core\wal_v03h2.py` (9358 bytes, 2026-06-15 15:54:50)

### REPO_CORE_SCRIPTS_REVIEW

- `09_SCRIPTS\RUN_BALLOONDB_CORE_REGRESSION_GATE_V03H4.ps1` (539 bytes, 2026-06-15 16:12:24)
- `09_SCRIPTS\RUN_BQL_COMPAT_FIX_V03H4A.ps1` (297 bytes, 2026-06-15 16:24:46)
- `09_SCRIPTS\RUN_BQL_DAEMON_BENCH_V03G4.ps1` (596 bytes, 2026-06-15 11:34:00)
- `09_SCRIPTS\RUN_BQL_DAEMON_QUERY_V03G4.ps1` (581 bytes, 2026-06-15 11:34:00)
- `09_SCRIPTS\RUN_BQL_DAEMON_START_V03G4.ps1` (1651 bytes, 2026-06-15 11:58:39)
- `09_SCRIPTS\RUN_BQL_DAEMON_STOP_V03G4.ps1` (760 bytes, 2026-06-15 12:01:12)
- `09_SCRIPTS\RUN_BQL_QUERY_CONTRACT_V03G3.ps1` (1747 bytes, 2026-06-15 09:21:18)
- `09_SCRIPTS\RUN_BQL_QUERY_V03G1.ps1` (783 bytes, 2026-06-15 08:30:08)
- `09_SCRIPTS\RUN_BQL_REGRESSION_V03G7.ps1` (1253 bytes, 2026-06-15 13:31:43)
- `09_SCRIPTS\RUN_BQL_SELFTEST_V03G0.ps1` (860 bytes, 2026-06-15 10:09:44)
- `09_SCRIPTS\RUN_BQL_SELFTEST_V03G1.ps1` (801 bytes, 2026-06-15 08:30:08)
- `09_SCRIPTS\RUN_BQL_SELFTEST_V03G2.ps1` (935 bytes, 2026-06-15 10:50:27)
- `09_SCRIPTS\RUN_BQL_SELFTEST_V03G3.ps1` (1454 bytes, 2026-06-15 09:21:18)
- `09_SCRIPTS\RUN_BQL_SELFTEST_V03G4.ps1` (1253 bytes, 2026-06-15 11:34:00)
- `09_SCRIPTS\RUN_BQL_SELFTEST_V03G6.ps1` (2311 bytes, 2026-06-15 13:01:52)
- `09_SCRIPTS\RUN_BQL_SELFTEST_V03G8.ps1` (689 bytes, 2026-06-15 13:37:08)
- `09_SCRIPTS\RUN_BQL_SELFTEST_V03G9.ps1` (218 bytes, 2026-06-15 13:42:55)
- `09_SCRIPTS\RUN_CRASH_RECOVERY_SELFTEST_V03H3.ps1` (610 bytes, 2026-06-15 16:00:14)
- `09_SCRIPTS\RUN_STORAGE_SELFTEST_V03H1.ps1` (596 bytes, 2026-06-15 15:46:24)
- `09_SCRIPTS\RUN_WAL_SELFTEST_V03H2.ps1` (577 bytes, 2026-06-15 15:54:50)

### REPO_CORE_EXAMPLES

- `memory\balloon_memory.balloondb\BINARY\programming_concepts.bindex.json` (637800 bytes, 2026-06-15 08:57:33)
- `memory\balloon_memory.balloondb\BINARY\programming_rules.bbridge` (72 bytes, 2026-06-15 00:12:20)
- `memory\balloon_memory.balloondb\BINARY\programming_rules.bindex.json` (1417 bytes, 2026-06-15 00:50:59)
- `memory\balloon_memory.balloondb\BINARY\programming_rules.bseed` (670 bytes, 2026-06-15 00:12:20)
- `memory\balloon_memory.balloondb\BINARY\syllabus.bindex.json` (6293 bytes, 2026-06-15 08:31:07)
- `memory\balloon_memory.balloondb\MANIFEST.bdbm` (562 bytes, 2026-06-15 13:56:44)
- `memory\balloon_memory.balloondb\WAL\00000001.bwal` (28150 bytes, 2026-06-15 13:56:44)
- `memory\balloon_memory.balloondb\WAL\00000002_autofix.bwal` (16089 bytes, 2026-06-15 13:56:44)
- `memory\balloon_memory.balloondb\WAL\00000003_lessons.bwal` (369456 bytes, 2026-06-15 13:56:45)
- `memory\balloon_memory.balloondb\WAL\00000004_code_graph.bwal` (37175 bytes, 2026-06-15 15:35:13)
- `memory\balloon_memory.balloondb\WAL\00000005_graph_gpt_runner.bwal` (8772 bytes, 2026-06-15 13:56:36)
- `memory\balloon_memory.balloondb\WAL\00000008_v02l0_source_sanitizer.bwal` (584 bytes, 2026-06-14 19:58:42)
- `memory\balloon_memory.balloondb\WAL\00000009_v02m0_existing_project_intake.bwal` (225 bytes, 2026-06-14 20:04:47)
- `memory\balloon_memory.balloondb\WAL\00000012_v03a_local_agent_command_center.bwal` (492 bytes, 2026-06-14 23:07:54)
- `memory\balloon_memory.balloondb\WAL\00000013_v03c_programming_learning_lab.bwal` (958 bytes, 2026-06-14 23:19:38)
- `memory\balloon_memory.balloondb\WAL\00000015_v03e_api_teacher_safe_source.bwal` (12284 bytes, 2026-06-15 09:52:24)

### SPEC_CONFIG_REVIEW

- `00_GOALS\AGENT_QUEUE\SELFTEST_REPAIR_REVIEW_1781519217677.json` (451 bytes, 2026-06-15 12:26:57)
- `00_GOALS\AGENT_QUEUE\V03G6_BQL_TIME_FILTER_REPAIR_REVIEW_1781519224940.json` (514 bytes, 2026-06-15 12:27:04)
- `00_GOALS\AGENT_QUEUE\V03G6_BQL_TIME_FILTER_REPAIR_REVIEW_1781519260709.json` (514 bytes, 2026-06-15 12:27:40)
- `00_GOALS\AGENT_QUEUE\V03G6_BQL_TIME_FILTER_REPAIR_REVIEW_1781521267230.json` (514 bytes, 2026-06-15 13:01:07)
- `00_GOALS\AGENT_QUEUE\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_REPAIR_REVIEW_1781523037445.json` (562 bytes, 2026-06-15 13:30:37)
- `00_GOALS\AGENT_QUEUE\V03G8_TS_INDEX_FOR_TIME_FILTER_REPAIR_REVIEW_1781523260828.json` (541 bytes, 2026-06-15 13:34:20)
- `00_GOALS\AGENT_QUEUE\V03G9_QUERY_HISTORY_AND_EXPLAIN_TRACE_REPAIR_REVIEW_1781523620444.json` (562 bytes, 2026-06-15 13:40:20)
- `00_GOALS\AGENT_QUEUE\V03H0_BINARY_GRAPH_PACKING_INTAKE_REPAIR_REVIEW_1781524363921.json` (550 bytes, 2026-06-15 13:52:43)
- `00_GOALS\AGENT_QUEUE\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_REPAIR_REVIEW_1781524688626.json` (568 bytes, 2026-06-15 13:58:08)
- `00_GOALS\BALLOONDB_BINARY_GRAPH_PACKING_INTAKE_V03H0_GOAL.json` (1430 bytes, 2026-06-15 10:58:14)
- `00_GOALS\BALLOONDB_BQL_CORE_V03G0_GOAL.json` (2282 bytes, 2026-06-15 09:35:18)
- `00_GOALS\BALLOONDB_BQL_CORE_V03G1_GOAL.json` (1265 bytes, 2026-06-15 10:21:41)
- `00_GOALS\BALLOONDB_BQL_CORE_V03G2_GOAL.json` (1317 bytes, 2026-06-15 10:41:12)
- `00_GOALS\BALLOONDB_BQL_CORE_V03G3_GOAL.json` (1146 bytes, 2026-06-15 11:09:51)
- `00_GOALS\BALLOONDB_BQL_CORE_V03G4_GOAL.json` (1266 bytes, 2026-06-15 11:26:29)
- `00_GOALS\V03G6_BQL_TIME_FILTER_JOB.json` (743 bytes, 2026-06-15 12:01:15)
- `README.md` (1281 bytes, 2026-06-14 14:24:02)
- `config\API_EXECUTOR_V03E.BACKUP_BEFORE_V03E4A_TEMP_FIX_20260615_014147.json` (2415 bytes, 2026-06-15 01:36:36)
- `config\API_EXECUTOR_V03E.BACKUP_BEFORE_V03E4_GPT55_20260615_013636.json` (2017 bytes, 2026-06-14 23:39:10)
- `config\API_EXECUTOR_V03E.json` (2742 bytes, 2026-06-15 01:41:47)
- `config\BALLOONDB_CONCEPT_GENERALIZATION_STRATEGY_V03F2.json` (1940 bytes, 2026-06-14 22:52:48)
- `config\BALLOONDB_V03G0_SCRIPT_ROLE_MAP.json` (5712 bytes, 2026-06-15 09:46:15)
- `config\BALLOON_ECOSYSTEM_STATE_V02F.json` (1438 bytes, 2026-06-14 18:14:05)
- `config\BALLOON_OPERATOR_CONTRACT_V02.json` (1160 bytes, 2026-06-14 14:24:02)
- `config\BUILD_QUEUE_V02H.json` (3162 bytes, 2026-06-14 19:18:55)
- `config\LESSON_RULES_V02E.json` (1951 bytes, 2026-06-15 13:56:45)
- `config\MODEL_ROUTER_V03D.json` (3648 bytes, 2026-06-14 23:28:37)
- `config\V02K1_DASHBOARD_TOKEN.txt` (32 bytes, 2026-06-14 19:41:02)
- `config\V02K2_DASHBOARD_TOKEN.txt` (32 bytes, 2026-06-14 20:58:55)
- `config\V03A_AGENT_TOKEN.txt` (32 bytes, 2026-06-14 21:00:28)
- `config\operator_config.json` (422 bytes, 2026-06-14 16:59:52)
- `data\v03g7_bql_regression_report.json` (12392 bytes, 2026-06-15 18:16:38)
- `reports\v03g7_bql_regression_summary.html` (10908 bytes, 2026-06-15 18:16:38)

### EVIDENCE_CORE_REFERENCE

- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781519541204\api_materialization_raw.json` (33079 bytes, 2026-06-15 12:34:07)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781520068979\STAGED_FILES\balloondb_core\bql_error_contract.py` (2176 bytes, 2026-06-15 12:43:52)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781520068979\STAGED_FILES\balloondb_core\bql_executor.py` (6859 bytes, 2026-06-15 12:43:52)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781520068979\STAGED_FILES\balloondb_core\bql_parser.py` (4611 bytes, 2026-06-15 12:43:52)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781520068979\STAGED_FILES\balloondb_core\bql_planner.py` (1799 bytes, 2026-06-15 12:43:52)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781520068979\STAGED_FILES\balloondb_core\bql_time_filter.py` (3723 bytes, 2026-06-15 12:43:52)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781520068979\STAGED_FILES\balloondb_core\selftest\run_selftest_v03g6.py` (5014 bytes, 2026-06-15 12:43:52)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781520068979\api_materialization_raw.json` (88310 bytes, 2026-06-15 12:43:52)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781520068979\materialization.json` (27173 bytes, 2026-06-15 12:43:52)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781521267651\STAGED_FILES\09_SCRIPTS\RUN_BQL_SELFTEST_V03G6.ps1` (2311 bytes, 2026-06-15 13:01:51)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781521267651\api_materialization_raw.json` (14909 bytes, 2026-06-15 13:01:51)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G6_BQL_TIME_FILTER_1781521267651\materialization.json` (4130 bytes, 2026-06-15 13:01:51)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_1781523037878\STAGED_FILES\09_SCRIPTS\RUN_BQL_REGRESSION_V03G7.ps1` (1253 bytes, 2026-06-15 13:31:43)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_1781523037878\STAGED_FILES\balloondb_core\selftest\run_selftest_v03g7_all.py` (12997 bytes, 2026-06-15 13:31:43)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_1781523037878\api_materialization_raw.json` (53345 bytes, 2026-06-15 13:31:43)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_1781523037878\materialization.json` (16101 bytes, 2026-06-15 13:31:43)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G8_TS_INDEX_FOR_TIME_FILTER_1781523261232\STAGED_FILES\09_SCRIPTS\RUN_BQL_SELFTEST_V03G8.ps1` (689 bytes, 2026-06-15 13:37:08)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G8_TS_INDEX_FOR_TIME_FILTER_1781523261232\STAGED_FILES\balloondb_core\bql_executor.py` (7621 bytes, 2026-06-15 13:37:08)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G8_TS_INDEX_FOR_TIME_FILTER_1781523261232\STAGED_FILES\balloondb_core\bql_planner.py` (3289 bytes, 2026-06-15 13:37:08)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G8_TS_INDEX_FOR_TIME_FILTER_1781523261232\STAGED_FILES\balloondb_core\bql_ts_index.py` (7110 bytes, 2026-06-15 13:37:08)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G8_TS_INDEX_FOR_TIME_FILTER_1781523261232\STAGED_FILES\balloondb_core\selftest\run_selftest_v03g8.py` (5034 bytes, 2026-06-15 13:37:08)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G9_QUERY_HISTORY_AND_EXPLAIN_TRACE_1781523620867\STAGED_FILES\09_SCRIPTS\RUN_BQL_SELFTEST_V03G9.ps1` (218 bytes, 2026-06-15 13:42:55)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G9_QUERY_HISTORY_AND_EXPLAIN_TRACE_1781523620867\STAGED_FILES\balloondb_core\bql_query_history.py` (11570 bytes, 2026-06-15 13:42:55)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03G9_QUERY_HISTORY_AND_EXPLAIN_TRACE_1781523620867\STAGED_FILES\balloondb_core\selftest\run_selftest_v03g9.py` (12600 bytes, 2026-06-15 13:42:55)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03H0_BINARY_GRAPH_PACKING_INTAKE_1781524364324\STAGED_FILES\09_SCRIPTS\RUN_BINARY_GRAPH_PACKING_INTAKE_V03H0.ps1` (1141 bytes, 2026-06-15 13:55:20)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03H0_BINARY_GRAPH_PACKING_INTAKE_1781524364324\STAGED_FILES\balloon_operator_tools\binary_graph_packing_intake_v03h0.py` (18885 bytes, 2026-06-15 13:55:20)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03H0_BINARY_GRAPH_PACKING_INTAKE_1781524364324\api_materialization_raw.json` (67090 bytes, 2026-06-15 13:55:20)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03H0_BINARY_GRAPH_PACKING_INTAKE_1781524364324\materialization.json` (21305 bytes, 2026-06-15 13:55:20)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781524689046\api_materialization_normalizer_raw.json` (434 bytes, 2026-06-15 13:58:11)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781524689046\api_materialization_raw.json` (434 bytes, 2026-06-15 13:58:10)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781524689046\api_materialization_unparsed.txt` (0 bytes, 2026-06-15 13:58:10)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS_CHUNKED\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781528394569\STAGED_FILES\balloondb_core\selftest\run_selftest_v03h1.py` (17896 bytes, 2026-06-15 15:03:47)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS_CHUNKED\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781528394569\STAGED_FILES\balloondb_core\storage_format_v03h1.py` (17843 bytes, 2026-06-15 15:01:26)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS_CHUNKED\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781528394569\gen_balloondb_core__selftest__run_selftest_v03h1.py.json` (480 bytes, 2026-06-15 15:03:47)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS_CHUNKED\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781528394569\gen_balloondb_core__storage_format_v03h1.py.json` (476 bytes, 2026-06-15 15:01:26)
- `06_EVIDENCE\API_REPAIR_MATERIALIZATIONS_CHUNKED_SAFE\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT\api_balloondb_core__storage_format_v03h1.py_1781534952281.json` (64 bytes, 2026-06-15 16:49:12)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781518940718\NO_GO_REPAIR_PLAN_REQUIRES_CONFIRMATION.json` (833 bytes, 2026-06-15 12:22:20)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781518940718\repair_context.json` (331587 bytes, 2026-06-15 12:22:20)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781518954536\api_raw_response.json` (14091 bytes, 2026-06-15 12:23:38)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781518954536\normalizer_api_raw.json` (13068 bytes, 2026-06-15 12:27:40)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781518954536\repair_context.json` (331587 bytes, 2026-06-15 12:22:34)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781518954536\repair_plan.normalized.json` (6614 bytes, 2026-06-15 12:27:40)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781518954536\repair_plan_unparsed.txt` (5745 bytes, 2026-06-15 12:23:38)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781521179633\api_raw_response.json` (18647 bytes, 2026-06-15 13:00:43)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781521179633\normalizer_api_raw.json` (13516 bytes, 2026-06-15 13:01:07)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781521179633\repair_context.json` (298524 bytes, 2026-06-15 12:59:39)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781521179633\repair_plan.normalized.json` (6796 bytes, 2026-06-15 13:01:07)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G6_BQL_TIME_FILTER_1781521179633\repair_plan_unparsed.txt` (7899 bytes, 2026-06-15 13:00:43)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_1781522962918\api_raw_response.json` (17895 bytes, 2026-06-15 13:30:17)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_1781522962918\normalizer_api_raw.json` (11938 bytes, 2026-06-15 13:30:37)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_1781522962918\repair_context.json` (334582 bytes, 2026-06-15 13:29:22)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_1781522962918\repair_plan.normalized.json` (6037 bytes, 2026-06-15 13:30:37)
- `06_EVIDENCE\API_REPAIR_PLANS\V03G7_REGRESSION_SUITE_ALL_BQL_LAYERS_1781522962918\repair_plan_unparsed.txt` (7577 bytes, 2026-06-15 13:30:17)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H0_BINARY_GRAPH_PACKING_INTAKE_1781524279748\api_raw_response.json` (15973 bytes, 2026-06-15 13:52:22)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H0_BINARY_GRAPH_PACKING_INTAKE_1781524279748\normalizer_api_raw.json` (15494 bytes, 2026-06-15 13:52:43)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H0_BINARY_GRAPH_PACKING_INTAKE_1781524279748\repair_context.json` (355454 bytes, 2026-06-15 13:51:19)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H0_BINARY_GRAPH_PACKING_INTAKE_1781524279748\repair_plan.normalized.json` (7807 bytes, 2026-06-15 13:52:43)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H0_BINARY_GRAPH_PACKING_INTAKE_1781524279748\repair_plan_unparsed.txt` (6758 bytes, 2026-06-15 13:52:22)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781524606186\api_raw_response.json` (23998 bytes, 2026-06-15 13:57:43)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781524606186\normalizer_api_raw.json` (18940 bytes, 2026-06-15 13:58:08)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781524606186\repair_context.json` (337291 bytes, 2026-06-15 13:56:46)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781524606186\repair_plan.normalized.json` (9570 bytes, 2026-06-15 13:58:08)
- `06_EVIDENCE\API_REPAIR_PLANS\V03H1_SEED_BRIDGE_NATIVE_STORAGE_FORMAT_1781524606186\repair_plan_unparsed.txt` (10590 bytes, 2026-06-15 13:57:43)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\T01_REMEMBER_V03G4_1781517001310.ps1` (1001 bytes, 2026-06-15 11:50:01)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\T01_REMEMBER_V03G4_1781517276636.ps1` (1001 bytes, 2026-06-15 11:54:36)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\T03_V03G4_DAEMON_BENCHMARK_BASELINE_1781517002210.ps1` (603 bytes, 2026-06-15 11:50:02)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\T03_V03G4_DAEMON_BENCHMARK_BASELINE_1781517277483.ps1` (603 bytes, 2026-06-15 11:54:37)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_BUILD_RUN_WITH_SCRIPT_MAP.txt` (152156 bytes, 2026-06-15 09:57:16)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_FORCE_BUILD_RUN.txt` (109300 bytes, 2026-06-15 10:00:52)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_GPT55_ARCHITECT_REVIEW.txt` (330 bytes, 2026-06-15 09:50:55)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_GPT55_ARCHITECT_REVIEW_MINI.txt` (8212 bytes, 2026-06-15 09:52:24)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_GPT55_PROMPT.txt` (6612 bytes, 2026-06-15 09:49:54)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_GPT55_PROMPT_MINI.txt` (484 bytes, 2026-06-15 09:52:02)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_GRAPH_GPT_PLAN_WITH_SCRIPT_MAP.txt` (46236 bytes, 2026-06-15 09:56:06)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_MATERIALIZE_REPORT.json` (587 bytes, 2026-06-15 10:09:44)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_MATERIALIZE_RUN.txt` (1180 bytes, 2026-06-15 10:09:44)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_SELFTEST_RUN.txt` (964 bytes, 2026-06-15 10:09:59)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_SELFTEST_RUN_FIX1.txt` (964 bytes, 2026-06-15 10:12:32)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G0_SELFTEST_RUN_FIX2.txt` (964 bytes, 2026-06-15 10:18:36)
- `06_EVIDENCE\BALLOONDB_BQL_CORE\V03G1_BUILD_RUN.txt` (112166 bytes, 2026-06-15 10:23:16)
- ... 65 more

## Large local-only artifacts

- `memory\balloon_memory.balloondb\PACKS\programming_concepts.bpack` (2232.16 MB, 2026-06-15 08:57:33) — keep outside git.
- `memory\balloon_memory.balloondb\PACKS\balloondb_audit.bpack` (2232.15 MB, 2026-06-15 07:24:40) — keep outside git.
- `memory\balloon_memory.balloondb\PACKS\multilang_compiler_harness.bpack` (254.45 MB, 2026-06-15 07:24:40) — keep outside git.
- `memory\balloon_memory.balloondb\PACKS\failure_signatures.bpack` (14.36 MB, 2026-06-15 13:56:45) — keep outside git.

## Immediate conclusion

Do not continue H before cutting a clean repository boundary. The current tree contains a small usable BalloonDB core, but most files are workspace runs, evidence, local logs, frozen autonomy, operator/client code, or large migration packs. Create the repository from a curated subset, not from the full C:\\BalloonOperator tree.
