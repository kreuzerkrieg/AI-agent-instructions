# Total unique metrics: 647
# From 55 source files

##  (10 metrics)

| `scylla__stats_plugin_name_rx_bad_length_errors` | counter | seastar/src/net/dpdk.cc:437 | Counts a number of received packets with a bad length value. |
| `scylla__stats_plugin_name_rx_crc_errors` | counter | seastar/src/net/dpdk.cc:428 | Counts a number of received packets with a bad CRC value. |
| `scylla__stats_plugin_name_rx_dropped` | counter | seastar/src/net/dpdk.cc:432 | Counts a number of dropped received packets. |
| `scylla__stats_plugin_name_rx_errors` | counter | seastar/src/net/dpdk.cc:465 | Counts the total number of ingress errors: CRC errors, bad length errors, etc. |
| `scylla__stats_plugin_name_rx_multicast` | counter | seastar/src/net/dpdk.cc:425 | Counts a number of received multicast packets. |
| `scylla__stats_plugin_name_rx_pause_xoff` | counter | seastar/src/net/dpdk.cc:455 | Counts a number of received PAUSE XOFF frames. |
| `scylla__stats_plugin_name_rx_pause_xon` | counter | seastar/src/net/dpdk.cc:442 | Counts a number of received PAUSE XON frames (PAUSE frame with a quanta of zero). |
| `scylla__stats_plugin_name_tx_errors` | counter | seastar/src/net/dpdk.cc:468 | Counts a total number of egress errors. A non-zero value usually indicated a problem with a HW or a SW driver. |
| `scylla__stats_plugin_name_tx_pause_xoff` | counter | seastar/src/net/dpdk.cc:460 | Counts a number of sent PAUSE XOFF frames. |
| `scylla__stats_plugin_name_tx_pause_xon` | counter | seastar/src/net/dpdk.cc:449 | Counts a number of sent PAUSE XON frames (L2 flow control frames). |

## ? (9 metrics)

| `scylla_?_cql_pending_response_memory` | gauge | transport/server.cc:277 | Holds the total memory in bytes consumed by responses waiting to be sent. |
| `scylla_?_cql_request_bytes` | counter | transport/server.cc:251 | Counts the total number of received bytes in CQL messages of a specific kind. |
| `scylla_?_cql_request_histogram_bytes` | histogram | transport/server.cc:263 | A histogram of received bytes in CQL messages of a specific kind and specific scheduling group. |
| `scylla_?_cql_requests_count` | counter | transport/server.cc:245 | Counts the total number of CQL messages of a specific kind. |
| `scylla_?_cql_requests_serving` | gauge | transport/server.cc:283 | Holds the number of requests that are being processed right now. |
| `scylla_?_cql_response_bytes` | counter | transport/server.cc:257 | Counts the total number of sent response bytes for CQL requests of a specific kind. |
| `scylla_?_cql_response_histogram_bytes` | histogram | transport/server.cc:269 | A histogram of sent response bytes in CQL messages of a specific kind and specific scheduling group. |
| `scylla_?_queries` | counter | cql3/query_processor.cc:119 | Counts queries by consistency level. |
| `scylla_?_statements_prepared` | counter | cql3/query_processor.cc:113 | Counts the total number of parsed CQL requests. |

## aaaa (4 metrics)

| `scylla_aaaa_counter_test` | counter | seastar/tests/unit/prometheus_http_test.cc:49 | (no description) |
| `scylla_aaaa_double_test` | gauge | seastar/tests/unit/prometheus_http_test.cc:48 | (no description) |
| `scylla_aaaa_escaped_label_value_test` | gauge | seastar/tests/unit/prometheus_http_test.cc:46 | (no description) |
| `scylla_aaaa_int_test` | gauge | seastar/tests/unit/prometheus_http_test.cc:47 | (no description) |

## alien (2 metrics)

| `scylla_alien_total_received_messages` | counter | seastar/src/core/alien.cc:114 | Total number of received messages |
| `scylla_alien_total_sent_messages` | counter | seastar/src/core/alien.cc:116 | Total number of sent messages |

## alternator (2 metrics)

| `scylla_alternator_authentication_failures` | counter | alternator/stats.cc:181 | total number of authentication failures |
| `scylla_alternator_authorization_failures` | counter | alternator/stats.cc:183 | total number of authorization failures |

## auth (2 metrics)

| `scylla_auth_cache_permissions` | gauge | auth/cache.cc:40 | Total number of permission sets currently cached across all roles |
| `scylla_auth_cache_roles` | gauge | auth/cache.cc:38 | Number of roles currently cached |

## batchlog (1 metrics)

| `scylla_batchlog_manager_total_write_replay_attempts` | counter | db/batchlog_manager.cc:160 | Counts write operations issued in a batchlog replay flow. |

## cache (35 metrics)

| `scylla_cache_active_reads` | gauge | db/row_cache.cc:173 | number of currently active reads |
| `scylla_cache_bytes_total` | gauge | db/row_cache.cc:151 | total size of memory for the cache |
| `scylla_cache_bytes_used` | gauge | db/row_cache.cc:150 | current bytes used by the cache out of the total size of memory |
| `scylla_cache_concurrent_misses_same_key` | counter | db/row_cache.cc:164 | total number of operation with misses same key |
| `scylla_cache_dummy_row_hits` | counter | db/row_cache.cc:156 | total number of dummy rows touched by reads in cache |
| `scylla_cache_mispopulations` | counter | db/row_cache.cc:168 | number of entries not inserted by reads |
| `scylla_cache_partition_evictions` | counter | db/row_cache.cc:166 | total number of evicted partitions |
| `scylla_cache_partition_hits` | counter | db/row_cache.cc:152 | number of partitions needed by reads and found in cache |
| `scylla_cache_partition_insertions` | counter | db/row_cache.cc:154 | total number of partitions added to cache |
| `scylla_cache_partition_merges` | counter | db/row_cache.cc:165 | total number of partitions merged |
| `scylla_cache_partition_misses` | counter | db/row_cache.cc:153 | number of partitions needed by reads and missing in cache |
| `scylla_cache_partition_removals` | counter | db/row_cache.cc:167 | total number of invalidated partitions |
| `scylla_cache_partitions` | gauge | db/row_cache.cc:169 | total number of cached partitions |
| `scylla_cache_pinned_dirty_memory_overload` | counter | db/row_cache.cc:177 | amount of pinned bytes that we tried to unpin over the limit. This should sit constantly at 0, and any number different than 0 is indicative of a bug |
| `scylla_cache_range_tombstone_reads` | counter | db/row_cache.cc:184 | total amount of range tombstones processed during read |
| `scylla_cache_reads` | counter | db/row_cache.cc:171 | number of started reads |
| `scylla_cache_reads_with_misses` | counter | db/row_cache.cc:172 | number of reads which had to read from sstables |
| `scylla_cache_row_evictions` | counter | db/row_cache.cc:159 | total number of rows evicted from cache |
| `scylla_cache_row_hits` | counter | db/row_cache.cc:155 | total number of rows needed by reads and found in cache |
| `scylla_cache_row_insertions` | counter | db/row_cache.cc:158 | total number of rows added to cache |
| `scylla_cache_row_misses` | counter | db/row_cache.cc:157 | total number of rows needed by reads and missing in cache |
| `scylla_cache_row_removals` | counter | db/row_cache.cc:160 | total number of invalidated rows |
| `scylla_cache_row_tombstone_reads` | counter | db/row_cache.cc:186 | total amount of row tombstones processed during read |
| `scylla_cache_rows` | gauge | db/row_cache.cc:170 | total number of cached rows |
| `scylla_cache_rows_compacted` | counter | db/row_cache.cc:188 | total amount of attempts to compact expired rows during read |
| `scylla_cache_rows_compacted_away` | counter | db/row_cache.cc:190 | total amount of compacted and removed rows during read |
| `scylla_cache_rows_compacted_with_tombstones` | counter | db/row_cache.cc:162 | Number of rows scanned during write of a tombstone for the purpose of compaction in cache |
| `scylla_cache_rows_dropped_by_tombstones` | counter | db/row_cache.cc:161 | Number of rows dropped in cache by a tombstone write |
| `scylla_cache_rows_dropped_from_memtable` | counter | db/row_cache.cc:180 | total number of rows in memtables which were dropped during cache update on memtable flush |
| `scylla_cache_rows_merged_from_memtable` | counter | db/row_cache.cc:182 | total number of rows in memtables which were merged with existing rows during cache update on memtable flush |
| `scylla_cache_rows_processed_from_memtable` | counter | db/row_cache.cc:178 | total number of rows in memtables which were processed during cache update on memtable flush |
| `scylla_cache_sstable_partition_skips` | counter | db/row_cache.cc:175 | number of times sstable reader was fast forwarded across partitions |
| `scylla_cache_sstable_reader_recreations` | counter | db/row_cache.cc:174 | number of times sstable reader was recreated due to memtable flush |
| `scylla_cache_sstable_row_skips` | counter | db/row_cache.cc:176 | number of times sstable reader was fast forwarded within a partition |
| `scylla_cache_static_row_insertions` | counter | db/row_cache.cc:163 | total number of static rows added to cache |

## column (28 metrics)

| `scylla_column_family_cache_hit_rate` | gauge | replica/table.cc:2185 | Cache hit rate |
| `scylla_column_family_cas_commit_latency` | histogram | replica/table.cc:2184 | CAS learn round latency histogram |
| `scylla_column_family_cas_prepare_latency` | histogram | replica/table.cc:2182 | CAS prepare round latency histogram |
| `scylla_column_family_cas_propose_latency` | histogram | replica/table.cc:2183 | CAS accept round latency histogram |
| `scylla_column_family_live_disk_space` | gauge | replica/table.cc:2137 | Live disk space used |
| `scylla_column_family_live_sstable` | gauge | replica/table.cc:2140 | Live sstable count |
| `scylla_column_family_memtable_partition_hits` | counter | replica/table.cc:2129 | Number of times a write operation was issued on an existing partition in memtables |
| `scylla_column_family_memtable_partition_writes` | counter | replica/table.cc:2128 | Number of write operations performed on partitions in memtables |
| `scylla_column_family_memtable_range_tombstone_reads` | counter | replica/table.cc:2134 | Number of range tombstones read from memtables |
| `scylla_column_family_memtable_row_hits` | counter | replica/table.cc:2131 | Number of rows overwritten by write operations in memtables |
| `scylla_column_family_memtable_row_tombstone_reads` | counter | replica/table.cc:2135 | Number of row tombstones read from memtables |
| `scylla_column_family_memtable_row_writes` | counter | replica/table.cc:2130 | Number of row writes performed in memtables |
| `scylla_column_family_memtable_rows_compacted_with_tombstones` | counter | replica/table.cc:2133 | Number of rows scanned during write of a tombstone for the purpose of compaction in memtables |
| `scylla_column_family_memtable_rows_dropped_by_tombstones` | counter | replica/table.cc:2132 | Number of rows dropped in memtables by a tombstone write |
| `scylla_column_family_memtable_switch` | counter | replica/table.cc:2127 | Number of times flush has resulted in the memtable being switched out |
| `scylla_column_family_pending_compaction` | gauge | replica/table.cc:2141 | Estimated number of compactions pending for this column family |
| `scylla_column_family_pending_sstable_deletions` | gauge | replica/table.cc:2142 | Number of tasks waiting to delete sstables from a table |
| `scylla_column_family_pending_tasks` | gauge | replica/table.cc:2136 | Estimated number of tasks pending for this column family |
| `scylla_column_family_read_latency` | histogram | replica/table.cc:2180 | Read latency histogram |
| `scylla_column_family_tablet_count` | gauge | replica/table.cc:2168 | Tablet count |
| `scylla_column_family_total_disk_space` | gauge | replica/table.cc:2138 | Total disk space used |
| `scylla_column_family_total_disk_space_before_compression` | gauge | replica/table.cc:2139 | Hypothetical total disk space used if data files weren't compressed |
| `scylla_column_family_view_updates_failed_local` | counter | db/view/view.cc:249 | Number of updates (mutations) that failed to be pushed to local view replicas |
| `scylla_column_family_view_updates_failed_remote` | counter | db/view/view.cc:245 | Number of updates (mutations) that failed to be pushed to remote view replicas |
| `scylla_column_family_view_updates_pending` | gauge | db/view/view.cc:251 | Number of updates pushed to view and are still to be completed |
| `scylla_column_family_view_updates_pushed_local` | counter | db/view/view.cc:247 | Number of updates (mutations) pushed to local view replicas |
| `scylla_column_family_view_updates_pushed_remote` | counter | db/view/view.cc:243 | Number of updates (mutations) pushed to remote view replicas |
| `scylla_column_family_write_latency` | histogram | replica/table.cc:2181 | Write latency histogram |

## commitlog (20 metrics)

| `scylla_commitlog_active_allocations` | gauge | db/commitlog/commitlog.cc:2153 | Current number of active allocations. |
| `scylla_commitlog_alloc` | counter | db/commitlog/commitlog.cc:2095 | Counts number of times a new mutation has been added to a segment. |
| `scylla_commitlog_allocating_segments` | gauge | db/commitlog/commitlog.cc:2087 | Holds the number of not closed segments that still have some free space. |
| `scylla_commitlog_blocked_on_new_segment` | gauge | db/commitlog/commitlog.cc:2150 | Number of allocations blocked on acquiring new segment. |
| `scylla_commitlog_bytes_flush_requested` | counter | db/commitlog/commitlog.cc:2112 | Counts number of bytes requested to be flushed (persisted). |
| `scylla_commitlog_bytes_released` | counter | db/commitlog/commitlog.cc:2109 | Counts number of bytes released from disk. (Deleted/recycled) |
| `scylla_commitlog_bytes_written` | counter | db/commitlog/commitlog.cc:2105 | Counts number of bytes written to the disk. |
| `scylla_commitlog_cycle` | counter | db/commitlog/commitlog.cc:2099 | Counts number of commitlog write cycles - when the data is written from the internal memory buffer to the disk. |
| `scylla_commitlog_disk_active_bytes` | gauge | db/commitlog/commitlog.cc:2139 | Holds size of disk space in bytes used for data so far. |
| `scylla_commitlog_disk_slack_end_bytes` | gauge | db/commitlog/commitlog.cc:2143 | Holds size of disk space in bytes unused because of segment switching (end slack). |
| `scylla_commitlog_disk_total_bytes` | gauge | db/commitlog/commitlog.cc:2135 | Holds size of disk space in bytes reserved for data so far. |
| `scylla_commitlog_flush` | counter | db/commitlog/commitlog.cc:2102 | Counts number of times the flush() method was called for a file. |
| `scylla_commitlog_flush_limit_exceeded` | counter | db/commitlog/commitlog.cc:2129 | Holds size of disk space in bytes reserved for data so far. |
| `scylla_commitlog_memory_buffer_bytes` | gauge | db/commitlog/commitlog.cc:2147 | Holds the total number of bytes in internal memory buffers. |
| `scylla_commitlog_pending_allocations` | gauge | db/commitlog/commitlog.cc:2121 | Holds number of currently pending allocations. |
| `scylla_commitlog_pending_flushes` | gauge | db/commitlog/commitlog.cc:2118 | Holds number of currently pending flushes. See the related flush_limit_exceeded metric. |
| `scylla_commitlog_requests_blocked_memory` | counter | db/commitlog/commitlog.cc:2125 | Counts number of requests blocked due to memory pressure. |
| `scylla_commitlog_segments` | gauge | db/commitlog/commitlog.cc:2084 | Holds the current number of segments. |
| `scylla_commitlog_slack` | counter | db/commitlog/commitlog.cc:2115 | Counts number of unused bytes written to the disk due to disk segment alignment. |
| `scylla_commitlog_unused_segments` | gauge | db/commitlog/commitlog.cc:2091 | Holds the current number of unused segments. |

## compaction (8 metrics)

| `scylla_compaction_manager_backlog` | gauge | compaction/compaction_manager.cc:1086 | Holds the sum of compaction backlog for all tables in the system. |
| `scylla_compaction_manager_compactions` | gauge | compaction/compaction_manager.cc:1076 | Holds the number of currently active compactions. |
| `scylla_compaction_manager_completed_compactions` | counter | compaction/compaction_manager.cc:1080 | Holds the number of completed compaction tasks. |
| `scylla_compaction_manager_failed_compactions` | counter | compaction/compaction_manager.cc:1082 | Holds the number of failed compaction tasks. |
| `scylla_compaction_manager_normalized_backlog` | gauge | compaction/compaction_manager.cc:1088 | Holds the sum of normalized compaction backlog for all tables in the system. Backlog is normalized by dividing backlog by shard's available memory. |
| `scylla_compaction_manager_pending_compactions` | gauge | compaction/compaction_manager.cc:1078 | Holds the number of compaction tasks waiting for an opportunity to run. |
| `scylla_compaction_manager_postponed_compactions` | gauge | compaction/compaction_manager.cc:1084 | Holds the number of tables with postponed compaction. |
| `scylla_compaction_manager_validation_errors` | counter | compaction/compaction_manager.cc:1090 | Holds the number of encountered validation errors. |

## corrupt (1 metrics)

| `scylla_corrupt_data_entries_reported` | counter | db/corrupt_data_handler.cc:23 | Counts the number of corrupt data instances reported to the corrupt data handler. |

## cql (2 metrics)

| `scylla_cql_write_consistency_levels_disallowed_violations` | counter | cql3/query_processor.cc:534 | Counts the number of write_consistency_levels_disallowed guardrail violations, |
| `scylla_cql_write_consistency_levels_warned_violations` | counter | cql3/query_processor.cc:540 | Counts the number of write_consistency_levels_warned guardrail violations, |

## database (49 metrics)

| `scylla_database_active_reads` | gauge | reader_concurrency_semaphore.cc:1094 | Holds the number of currently active read operations. |
| `scylla_database_clustering_filter_count` | counter | replica/database.cc:626 | Counts bloom filter invocations. |
| `scylla_database_clustering_filter_fast_path_count` | counter | replica/database.cc:633 | Counts number of times bloom filtering short cut to include all sstables when only one full range was specified. |
| `scylla_database_clustering_filter_sstables_checked` | counter | replica/database.cc:629 | Counts sstables checked after applying the bloom filter. |
| `scylla_database_clustering_filter_surviving_sstables` | counter | replica/database.cc:636 | Counts sstables that survived the clustering key filtering. |
| `scylla_database_counter_cell_lock_acquisition` | counter | replica/database.cc:719 | The number of acquired counter cell locks. |
| `scylla_database_disk_reads` | gauge | reader_concurrency_semaphore.cc:1121 | Holds the number of currently active disk read operations. |
| `scylla_database_dropped_view_updates` | counter | replica/database.cc:642 | Counts the number of view updates that have been dropped due to cluster overload. |
| `scylla_database_large_partition_exceeding_threshold` | counter | replica/database.cc:725 | Number of large partitions exceeding compaction_large_partition_warning_threshold_mb. |
| `scylla_database_multishard_query_failed_reader_saves` | counter | replica/database.cc:716 | The number of times the saving of a shard reader failed. |
| `scylla_database_multishard_query_failed_reader_stops` | counter | replica/database.cc:713 | The number of times the stopping of a shard reader failed. |
| `scylla_database_multishard_query_unpopped_bytes` | counter | replica/database.cc:708 | The total number of bytes that were extracted from the shard reader but were unconsumed by the query and moved back into the reader. |
| `scylla_database_multishard_query_unpopped_fragments` | counter | replica/database.cc:705 | The total number of fragments that were extracted from the shard reader but were unconsumed by the query and moved back into the reader. |
| `scylla_database_paused_reads` | gauge | reader_concurrency_semaphore.cc:1106 | The number of currently active reads that are temporarily paused. |
| `scylla_database_paused_reads_permit_based_evictions` | counter | reader_concurrency_semaphore.cc:1110 | The number of paused reads evicted to free up permits. |
| `scylla_database_querier_cache_drops` | counter | replica/database.cc:676 | Counts querier cache lookups that found a cached querier but had to drop it |
| `scylla_database_querier_cache_lookups` | counter | replica/database.cc:670 | Counts querier cache lookups (paging queries) |
| `scylla_database_querier_cache_misses` | counter | replica/database.cc:673 | Counts querier cache lookups that failed to find a cached querier |
| `scylla_database_querier_cache_population` | gauge | replica/database.cc:689 | The number of entries currently in the querier cache. |
| `scylla_database_querier_cache_resource_based_evictions` | counter | replica/database.cc:685 | Counts querier cache entries that were evicted to free up resources |
| `scylla_database_querier_cache_scheduling_group_mismatches` | counter | replica/database.cc:679 | Counts querier cache lookups that found a cached querier but had to drop it due to scheduling group mismatch |
| `scylla_database_querier_cache_time_based_evictions` | counter | replica/database.cc:682 | Counts querier cache entries that timed out and were evicted. |
| `scylla_database_queued_reads` | gauge | reader_concurrency_semaphore.cc:1102 | Holds the number of currently queued read operations. |
| `scylla_database_reads_memory_consumption` | gauge | reader_concurrency_semaphore.cc:1098 | Holds the amount of memory consumed by current read operations. |
| `scylla_database_reads_shed_due_to_overload` | counter | reader_concurrency_semaphore.cc:1116 | The number of reads shed because the admission queue reached its max capacity. |
| `scylla_database_requests_blocked_memory` | counter | replica/database.cc:622 | Counts bloom filter invocations. |
| `scylla_database_requests_blocked_memory_current` | gauge | replica/database.cc:617 | (no description) |
| `scylla_database_schema_changed` | counter | replica/database.cc:754 | The number of times the schema changed |
| `scylla_database_short_data_queries` | counter | replica/database.cc:699 | The rate of data queries (data or digest reads) that returned less rows than requested due to result size limiting. |
| `scylla_database_short_mutation_queries` | counter | replica/database.cc:702 | The rate of mutation queries that returned less rows than requested due to result size limiting. |
| `scylla_database_sstable_read_queue_overloads` | counter | reader_concurrency_semaphore.cc:1089 | Counts the number of times the sstable read queue was overloaded. |
| `scylla_database_sstables_read` | gauge | reader_concurrency_semaphore.cc:1125 | Holds the number of currently read sstables. |
| `scylla_database_total_reads` | counter | reader_concurrency_semaphore.cc:1129 | Counts the total number of successful user reads on this shard. |
| `scylla_database_total_reads_failed` | counter | reader_concurrency_semaphore.cc:1133 | Counts the total number of failed user read operations. |
| `scylla_database_total_reads_rate_limited` | counter | replica/database.cc:664 | Counts read operations which were rejected on the replica side because the per-partition limit was reached. |
| `scylla_database_total_result_bytes` | gauge | replica/database.cc:696 | Holds the current amount of memory used for results. |
| `scylla_database_total_view_updates_due_to_replica_count_mismatch` | counter | replica/database.cc:747 | Total number of view updates for which there were more view replicas than base replicas |
| `scylla_database_total_view_updates_failed_local` | counter | replica/database.cc:735 | Total number of view updates generated for tables and failed to be applied locally. |
| `scylla_database_total_view_updates_failed_pairing` | counter | replica/database.cc:744 | Total number of view updates for which we failed base/view pairing. |
| `scylla_database_total_view_updates_failed_remote` | counter | replica/database.cc:738 | Total number of view updates generated for tables and failed to be sent to remote replicas. |
| `scylla_database_total_view_updates_on_wrong_node` | counter | replica/database.cc:741 | Total number of view updates which are computed on the wrong node. |
| `scylla_database_total_view_updates_pushed_local` | counter | replica/database.cc:729 | Total number of view updates generated for tables and applied locally. |
| `scylla_database_total_view_updates_pushed_remote` | counter | replica/database.cc:732 | Total number of view updates generated for tables and sent to remote replicas. |
| `scylla_database_total_writes` | counter | replica/database.cc:648 | Counts the total number of successful write operations performed by this shard. |
| `scylla_database_total_writes_failed` | counter | replica/database.cc:651 | Counts the total number of failed write operations. |
| `scylla_database_total_writes_rate_limited` | counter | replica/database.cc:658 | Counts write operations which were rejected on the replica side because the per-partition limit was reached. |
| `scylla_database_total_writes_rejected_due_to_out_of_space_prevention` | counter | replica/database.cc:661 | Counts write operations which were rejected due to disabled user tables writes. |
| `scylla_database_total_writes_timedout` | counter | replica/database.cc:655 | Counts write operations failed due to a timeout. A positive value is a sign of storage being overloaded. |
| `scylla_database_view_building_paused` | counter | replica/database.cc:645 | Counts the number of times view building process was paused (e.g. due to node unavailability). |

## gossip (3 metrics)

| `scylla_gossip_heart_beat` | counter | gms/gossiper.cc:105 | (no description) |
| `scylla_gossip_live` | gauge | gms/gossiper.cc:114 | How many live nodes the current node sees |
| `scylla_gossip_unreachable` | gauge | gms/gossiper.cc:118 | How many unreachable nodes the current node sees |

## group (41 metrics)

| `scylla_group_name_auto_repair_enabled_nr` | counter | service/tablet_allocator.cc:85 | number of tablets with auto repair enabled |
| `scylla_group_name_auto_repair_needs_repair_nr` | counter | service/tablet_allocator.cc:83 | number of tablets with auto repair enabled that currently needs repair |
| `scylla_group_name_batch_item_count` | counter | alternator/stats.cc:135 | The total number of items processed across all batches |
| `scylla_group_name_batch_item_count_histogram` | histogram | alternator/stats.cc:139 | Histogram of the number of items in a batch request |
| `scylla_group_name_calls` | counter | service/tablet_allocator.cc:52 | number of calls to the load balancer |
| `scylla_group_name_corrupted_files` | counter | db/hints/manager.cc:188 | Number of hints files that were discarded during sending because the file was corrupted. |
| `scylla_group_name_cross_rack_collocations` | counter | service/tablet_allocator.cc:58 | number of co-locating migrations which move replica across racks |
| `scylla_group_name_discarded` | counter | db/hints/manager.cc:182 | Number of hints that were discarded during sending (too old, schema changed, etc.). |
| `scylla_group_name_dropped` | counter | db/hints/manager.cc:173 | Number of dropped hints. |
| `scylla_group_name_errors` | counter | db/hints/manager.cc:170 | Number of errors during hints writes. |
| `scylla_group_name_expression_cache_evictions` | counter | alternator/stats.cc:159 | Counts number of entries evicted from expressions cache |
| `scylla_group_name_expression_cache_hits` | counter | alternator/stats.cc:162 | Counts number of hits of cached expressions |
| `scylla_group_name_expression_cache_misses` | counter | alternator/stats.cc:164 | Counts number of misses of cached expressions |
| `scylla_group_name_filtered_rows_dropped_total` | counter | alternator/stats.cc:133 | number of rows read and dropped during filtering operations |
| `scylla_group_name_filtered_rows_matched_total` | counter | alternator/stats.cc:121 | number of rows read and matched during filtering operations |
| `scylla_group_name_filtered_rows_read_total` | counter | alternator/stats.cc:119 | number of rows read during filtering operations |
| `scylla_group_name_load` | gauge | service/tablet_allocator.cc:68 | node load during last load balancing |
| `scylla_group_name_migrations_produced` | counter | service/tablet_allocator.cc:54 | number of migrations produced by the load balancer |
| `scylla_group_name_migrations_skipped` | counter | service/tablet_allocator.cc:56 | number of migrations skipped by the load balancer due to load limits |
| `scylla_group_name_op_latency` | histogram | alternator/stats.cc:41 | Latency histogram of an operation via Alternator API |
| `scylla_group_name_operation` | counter | alternator/stats.cc:37 | number of operations via Alternator API |
| `scylla_group_name_operation_size_kb` | histogram | alternator/stats.cc:143 | Histogram of item sizes involved in a request |
| `scylla_group_name_pending_drains` | gauge | db/hints/manager.cc:191 | Number of tasks waiting in the queue for draining hints |
| `scylla_group_name_pending_sends` | gauge | db/hints/manager.cc:195 | Number of tasks waiting in the queue for sending a hint |
| `scylla_group_name_rcu_total` | counter | alternator/stats.cc:123 | total number of consumed read units |
| `scylla_group_name_reads_before_write` | counter | alternator/stats.cc:109 | number of performed read-before-write operations |
| `scylla_group_name_requests_blocked_memory` | counter | alternator/stats.cc:115 | Counts a number of requests blocked due to memory pressure. |
| `scylla_group_name_requests_shed` | counter | alternator/stats.cc:117 | Counts a number of requests shed due to overload. |
| `scylla_group_name_resizes_emitted` | counter | service/tablet_allocator.cc:77 | number of resizes produced by the load balancer |
| `scylla_group_name_resizes_finalized` | counter | service/tablet_allocator.cc:81 | number of resizes finalized by the load balancer |
| `scylla_group_name_resizes_revoked` | counter | service/tablet_allocator.cc:79 | number of resizes revoked by the load balancer |
| `scylla_group_name_send_errors` | counter | db/hints/manager.cc:185 | Number of unexpected errors during sending, sending will be retried later |
| `scylla_group_name_sent_bytes_total` | counter | db/hints/manager.cc:179 | The total size of the sent hints (in bytes) |
| `scylla_group_name_sent_total` | counter | db/hints/manager.cc:176 | Number of sent hints. |
| `scylla_group_name_shard_bounce_for_lwt` | counter | alternator/stats.cc:113 | number writes that had to be bounced from this shard because of LWT requirements |
| `scylla_group_name_size_of_hints_in_progress` | gauge | db/hints/manager.cc:164 | Size of hinted mutations that are scheduled to be written. |
| `scylla_group_name_total_operations` | counter | alternator/stats.cc:107 | number of total operations via Alternator API |
| `scylla_group_name_unsupported_operations` | counter | alternator/stats.cc:105 | number of unsupported operations via Alternator API |
| `scylla_group_name_wcu_total` | counter | alternator/stats.cc:125 | total number of consumed write units |
| `scylla_group_name_write_using_lwt` | counter | alternator/stats.cc:111 | number of writes that used LWT |
| `scylla_group_name_written` | counter | db/hints/manager.cc:167 | Number of successfully written hints. |

## httpd (5 metrics)

| `scylla_httpd_connections_current` | gauge | seastar/src/http/httpd.cc:67 | The current number of open  connections |
| `scylla_httpd_connections_total` | counter | seastar/src/http/httpd.cc:66 | The total number of connections opened |
| `scylla_httpd_read_errors` | counter | seastar/src/http/httpd.cc:68 | The total number of errors while reading http requests |
| `scylla_httpd_reply_errors` | counter | seastar/src/http/httpd.cc:69 | The total number of errors while replying to http |
| `scylla_httpd_requests_served` | counter | seastar/src/http/httpd.cc:70 | The total number of http requests served |

## index (1 metrics)

| `scylla_index_query_latencies` | histogram | index/secondary_index_manager.cc:238 | Index query latencies |

## io (19 metrics)

| `scylla_io_queue_activations` | counter | seastar/src/core/io_queue.cc:1378 | The number of times the class was woken up from idle |
| `scylla_io_queue_adjusted_consumption` | counter | seastar/src/core/io_queue.cc:1375 | Consumed disk capacity units adjusted for class shares and idling preemption |
| `scylla_io_queue_consumption` | counter | seastar/src/core/io_queue.cc:1372 | Accumulated disk capacity units consumed by this class; an increment per-second rate indicates full utilization |
| `scylla_io_queue_delay` | gauge | seastar/src/core/io_queue.cc:831 | random delay time in the queue |
| `scylla_io_queue_flow_ratio` | gauge | seastar/src/core/io_queue.cc:677 | Ratio of dispatch rate to completion rate. Is expected to be 1.0+ growing larger on reactor stalls or (!) disk problems |
| `scylla_io_queue_integrated_disk_queue_length` | counter | seastar/src/core/io_queue.cc:837 | Integrated disk queue length |
| `scylla_io_queue_integrated_queue_length` | counter | seastar/src/core/io_queue.cc:836 | Integrated queue length |
| `scylla_io_queue_shares` | gauge | seastar/src/core/io_queue.cc:834 | current amount of shares |
| `scylla_io_queue_starvation_time_sec` | counter | seastar/src/core/io_queue.cc:812 | Total time spent starving for disk |
| `scylla_io_queue_total_bytes` | counter | seastar/src/core/io_queue.cc:788 | Total bytes passed in the queue |
| `scylla_io_queue_total_delay_sec` | counter | seastar/src/core/io_queue.cc:806 | Total time spent in the queue |
| `scylla_io_queue_total_exec_sec` | counter | seastar/src/core/io_queue.cc:809 | Total time spent in disk |
| `scylla_io_queue_total_operations` | counter | seastar/src/core/io_queue.cc:791 | Total operations passed in the queue |
| `scylla_io_queue_total_read_bytes` | counter | seastar/src/core/io_queue.cc:794 | Total read bytes passed in the queue |
| `scylla_io_queue_total_read_ops` | counter | seastar/src/core/io_queue.cc:796 | Total read operations passed in the queue |
| `scylla_io_queue_total_split_bytes` | counter | seastar/src/core/io_queue.cc:804 | Total number of bytes split |
| `scylla_io_queue_total_split_ops` | counter | seastar/src/core/io_queue.cc:802 | Total number of requests split |
| `scylla_io_queue_total_write_bytes` | counter | seastar/src/core/io_queue.cc:798 | Total write bytes passed in the queue |
| `scylla_io_queue_total_write_ops` | counter | seastar/src/core/io_queue.cc:800 | Total write operations passed in the queue |

## ipv4 (1 metrics)

| `scylla_ipv4_linearizations` | counter | seastar/src/net/ip.cc:70 | Counts a number of times a buffer linearization was invoked during buffers merge process. |

## logstor (26 metrics)

| `scylla_logstor_sm_bytes_freed` | counter | replica/logstor/segment_manager.cc:887 | Counts number of data bytes freed. |
| `scylla_logstor_sm_bytes_read` | counter | replica/logstor/segment_manager.cc:885 | Counts number of bytes read from the disk. |
| `scylla_logstor_sm_bytes_written` | counter | replica/logstor/segment_manager.cc:881 | Counts number of bytes written to the disk. |
| `scylla_logstor_sm_compaction_bytes_written` | counter | replica/logstor/segment_manager.cc:895 | Counts number of bytes written to the disk by compaction. |
| `scylla_logstor_sm_compaction_data_bytes_written` | counter | replica/logstor/segment_manager.cc:897 | Counts number of data bytes written to the disk by compaction. |
| `scylla_logstor_sm_compaction_records_rewritten` | counter | replica/logstor/segment_manager.cc:905 | Counts number of records rewritten during compaction. |
| `scylla_logstor_sm_compaction_records_skipped` | counter | replica/logstor/segment_manager.cc:903 | Counts number of records skipped during compaction. |
| `scylla_logstor_sm_compaction_segments_freed` | counter | replica/logstor/segment_manager.cc:901 | Counts number of segments freed by compaction. |
| `scylla_logstor_sm_data_bytes_written` | counter | replica/logstor/segment_manager.cc:883 | Counts number of data bytes written to the disk. |
| `scylla_logstor_sm_disk_usage` | gauge | replica/logstor/segment_manager.cc:893 | Total disk usage. |
| `scylla_logstor_sm_free_segments` | gauge | replica/logstor/segment_manager.cc:867 | Counts number of free segments currently available. |
| `scylla_logstor_sm_segment_pool_compaction_segments_get` | counter | replica/logstor/segment_manager.cc:875 | Counts number of segments taken from the segment pool for compaction. |
| `scylla_logstor_sm_segment_pool_normal_segments_get` | counter | replica/logstor/segment_manager.cc:873 | Counts number of segments taken from the segment pool for normal writes. |
| `scylla_logstor_sm_segment_pool_normal_segments_wait` | counter | replica/logstor/segment_manager.cc:879 | Counts number of times normal writes had to wait for a segment to become available in the segment pool. |
| `scylla_logstor_sm_segment_pool_segments_put` | counter | replica/logstor/segment_manager.cc:871 | Counts number of segments returned to the segment pool. |
| `scylla_logstor_sm_segment_pool_separator_segments_get` | counter | replica/logstor/segment_manager.cc:877 | Counts number of segments taken from the segment pool for separator writes. |
| `scylla_logstor_sm_segment_pool_size` | gauge | replica/logstor/segment_manager.cc:869 | Counts number of segments in the segment pool. |
| `scylla_logstor_sm_segments_allocated` | counter | replica/logstor/segment_manager.cc:889 | Counts number of segments allocated. |
| `scylla_logstor_sm_segments_compacted` | counter | replica/logstor/segment_manager.cc:899 | Counts number of segments compacted. |
| `scylla_logstor_sm_segments_freed` | counter | replica/logstor/segment_manager.cc:891 | Counts number of segments freed. |
| `scylla_logstor_sm_segments_in_use` | gauge | replica/logstor/segment_manager.cc:865 | Counts number of segments currently in use. |
| `scylla_logstor_sm_separator_buffer_flushed` | counter | replica/logstor/segment_manager.cc:911 | Counts number of times the separator buffer has been flushed. |
| `scylla_logstor_sm_separator_bytes_written` | counter | replica/logstor/segment_manager.cc:907 | Counts number of bytes written to the separator. |
| `scylla_logstor_sm_separator_data_bytes_written` | counter | replica/logstor/segment_manager.cc:909 | Counts number of data bytes written to the separator. |
| `scylla_logstor_sm_separator_flow_control_delay` | gauge | replica/logstor/segment_manager.cc:915 | Current delay applied to writes to control separator debt in microseconds. |
| `scylla_logstor_sm_separator_segments_freed` | counter | replica/logstor/segment_manager.cc:913 | Counts number of segments freed by the separator. |

## lsa (13 metrics)

| `scylla_lsa_compact_time_ms` | counter | utils/logalloc.cc:2892 | Total time spent in segment compaction, that was not accounted under reclaim_time_ms |
| `scylla_lsa_evict_time_ms` | counter | utils/logalloc.cc:2889 | Total time spent in evicting objects, that was not accounted under reclaim_time_ms |
| `scylla_lsa_free_space` | gauge | utils/logalloc.cc:2865 | Holds a current amount of free memory that is under lsa control. |
| `scylla_lsa_memory_allocated` | counter | utils/logalloc.cc:2877 | Counts number of bytes which were requested from LSA. |
| `scylla_lsa_memory_compacted` | counter | utils/logalloc.cc:2874 | Counts number of bytes which were copied as part of segment compaction. |
| `scylla_lsa_memory_evicted` | counter | utils/logalloc.cc:2880 | Counts number of bytes which were evicted. |
| `scylla_lsa_memory_freed` | counter | utils/logalloc.cc:2883 | Counts number of bytes which were requested to be freed in LSA. |
| `scylla_lsa_non_lsa_used_space_bytes` | gauge | utils/logalloc.cc:2862 | Holds a current amount of used non-LSA memory. |
| `scylla_lsa_occupancy` | gauge | utils/logalloc.cc:2868 | Holds a current portion (in percents) of the used memory. |
| `scylla_lsa_reclaim_time_ms` | counter | utils/logalloc.cc:2886 | Total time spent in reclaiming LSA memory back to std allocator. |
| `scylla_lsa_segments_compacted` | counter | utils/logalloc.cc:2871 | Counts a number of compacted segments. |
| `scylla_lsa_total_space_bytes` | gauge | utils/logalloc.cc:2856 | Holds a current size of allocated memory in bytes. |
| `scylla_lsa_used_space_bytes` | gauge | utils/logalloc.cc:2859 | Holds a current amount of used memory in bytes. |

## memory (9 metrics)

| `scylla_memory_cross_cpu_free_operations` | counter | seastar/src/core/reactor.cc:2606 | Total number of cross cpu free |
| `scylla_memory_dirty_bytes` | gauge | replica/database.cc:594 | Holds the current size of all ("regular" and "system") non-free memory in bytes: used memory + released memory that hasn't been returned to a free mem |
| `scylla_memory_free_operations` | counter | seastar/src/core/reactor.cc:2605 | Total number of free operations |
| `scylla_memory_malloc_failed` | counter | seastar/src/core/reactor.cc:2612 | Total count of failed memory allocations |
| `scylla_memory_malloc_live_objects` | gauge | seastar/src/core/reactor.cc:2607 | Number of live objects |
| `scylla_memory_malloc_operations` | counter | seastar/src/core/reactor.cc:2603 | Total number of malloc operations |
| `scylla_memory_oversized_allocs` | counter | seastar/src/core/reactor.cc:2613 | Total count of oversized memory allocations |
| `scylla_memory_reclaims_operations` | counter | seastar/src/core/reactor.cc:2611 | Total reclaims operations |
| `scylla_memory_unspooled_dirty_bytes` | gauge | replica/database.cc:599 | Holds the size of all ("regular" and "system") used memory in bytes. Compare it to "dirty_bytes" to see how many memory is wasted (neither used nor av |

## memtables (3 metrics)

| `scylla_memtables_failed_flushes` | gauge | replica/database.cc:611 | Holds the number of failed memtable flushes. |
| `scylla_memtables_pending_flushes` | gauge | replica/database.cc:604 | Holds the current number of memtables that are currently being flushed to sstables. |
| `scylla_memtables_pending_flushes_bytes` | gauge | replica/database.cc:608 | Holds the current number of bytes in memtables that are currently being flushed to sstables. |

## network (2 metrics)

| `scylla_network_bytes_received` | counter | seastar/src/net/stack.cc:295 | Counts the number of bytes received from network sockets. |
| `scylla_network_bytes_sent` | counter | seastar/src/net/stack.cc:293 | Counts the number of bytes written to network sockets. |

## node (2 metrics)

| `scylla_node_operation_mode` | gauge | service/storage_service.cc:324 | The operation mode of the current node. UNKNOWN = 0, STARTING = 1, JOINING = 2, NORMAL = 3, |
| `scylla_node_ops_finished_percentage` | gauge | repair/repair.cc:80 | Finished percentage of node operation on this shard |

## object (1 metrics)

| `scylla_object_storage_memory_usage` | gauge | sstables/sstables_manager.cc:96 | Total number of bytes consumed by object storage client |

## per (5 metrics)

| `scylla_per_partition_rate_limiter_allocations` | counter | db/rate_limiter.cc:202 | Number of times a entry was allocated over an empty/expired entry. |
| `scylla_per_partition_rate_limiter_failed_allocations` | counter | db/rate_limiter.cc:208 | Number of times the rate limiter gave up trying to allocate. |
| `scylla_per_partition_rate_limiter_load_factor` | gauge | db/rate_limiter.cc:214 | Current load factor of the hash table (upper bound, may be overestimated). |
| `scylla_per_partition_rate_limiter_probe_count` | counter | db/rate_limiter.cc:211 | Number of probes made during lookups. |
| `scylla_per_partition_rate_limiter_successful_lookups` | counter | db/rate_limiter.cc:205 | Number of times a lookup returned an already allocated entry. |

## query (47 metrics)

| `scylla_query_processor_authorized_prepared_statements_cache_evictions` | counter | cql3/query_processor.cc:435 | Counts the number of authenticated prepared statements cache entries evictions. |
| `scylla_query_processor_authorized_prepared_statements_cache_size` | gauge | cql3/query_processor.cc:450 | Number of entries in the authenticated prepared statements cache. |
| `scylla_query_processor_authorized_prepared_statements_privileged_entries_evictions_on_size` | counter | cql3/query_processor.cc:440 | Counts a number of evictions of prepared statements from the authorized prepared statements cache after they have been used more than once. |
| `scylla_query_processor_authorized_prepared_statements_unprivileged_entries_evictions_on_size` | counter | cql3/query_processor.cc:445 | Counts a number of evictions of prepared statements from the authorized prepared statements cache after they have been used only once. An increasing c |
| `scylla_query_processor_batches` | counter | cql3/query_processor.cc:296 | Counts the total number of CQL BATCH requests without conditions. |
| `scylla_query_processor_batches_pure_logged` | counter | cql3/query_processor.cc:320 | Counts the total number of LOGGED batches that were executed as LOGGED batches. |
| `scylla_query_processor_batches_pure_unlogged` | counter | cql3/query_processor.cc:326 | Counts the total number of UNLOGGED batches that were executed as UNLOGGED |
| `scylla_query_processor_batches_unlogged_from_logged` | counter | cql3/query_processor.cc:333 | Counts the total number of LOGGED batches that were executed as UNLOGGED |
| `scylla_query_processor_deletes` | counter | cql3/query_processor.cc:187 | Counts the total number of CQL DELETE requests with/without conditions. |
| `scylla_query_processor_deletes_per_ks` | counter | cql3/query_processor.cc:271 | Counts the number of CQL DELETE requests executed on particular keyspaces. |
| `scylla_query_processor_filtered_read_requests` | counter | cql3/query_processor.cc:387 | Counts the total number of CQL read requests that required ALLOW FILTERING. See filtered_rows_read_total to compare how many rows needed to be filtere |
| `scylla_query_processor_filtered_rows_dropped_total` | counter | cql3/query_processor.cc:405 | Counts the number of rows read during CQL requests that required ALLOW FILTERING and dropped by the filter. Number similar to filtered_rows_read_total |
| `scylla_query_processor_filtered_rows_matched_total` | counter | cql3/query_processor.cc:399 | Counts the number of rows read during CQL requests that required ALLOW FILTERING and accepted by the filter. Number similar to filtered_rows_read_tota |
| `scylla_query_processor_filtered_rows_read_total` | counter | cql3/query_processor.cc:393 | Counts the total number of rows read during CQL requests that required ALLOW FILTERING. See filtered_rows_matched_total and filtered_rows_dropped_tota |
| `scylla_query_processor_forwarded_requests` | counter | cql3/query_processor.cc:515 | Counts the total number of attempts to forward CQL requests to other nodes. One request may be forwarded multiple times, |
| `scylla_query_processor_inserts` | counter | cql3/query_processor.cc:145 | Counts the total number of CQL INSERT requests with/without conditions. |
| `scylla_query_processor_inserts_per_ks` | counter | cql3/query_processor.cc:222 | Counts the number of CQL INSERT requests executed on particular keyspaces. |
| `scylla_query_processor_maximum_replication_factor_fail_violations` | counter | cql3/query_processor.cc:497 | Counts the number of maximum_replication_factor_fail_threshold guardrail violations, |
| `scylla_query_processor_maximum_replication_factor_warn_violations` | counter | cql3/query_processor.cc:491 | Counts the number of maximum_replication_factor_warn_threshold guardrail violations, |
| `scylla_query_processor_minimum_replication_factor_fail_violations` | counter | cql3/query_processor.cc:479 | Counts the number of minimum_replication_factor_fail_threshold guardrail violations, |
| `scylla_query_processor_minimum_replication_factor_warn_violations` | counter | cql3/query_processor.cc:485 | Counts the number of minimum_replication_factor_warn_threshold guardrail violations, |
| `scylla_query_processor_prepared_cache_evictions` | counter | cql3/query_processor.cc:344 | Counts the number of prepared statements cache entries evictions. |
| `scylla_query_processor_prepared_cache_memory_footprint` | gauge | cql3/query_processor.cc:359 | Size (in bytes) of the prepared statements cache. |
| `scylla_query_processor_prepared_cache_size` | gauge | cql3/query_processor.cc:354 | A number of entries in the prepared statements cache. |
| `scylla_query_processor_reads` | counter | cql3/query_processor.cc:134 | Counts the total number of CQL SELECT requests. |
| `scylla_query_processor_reads_per_ks` | counter | cql3/query_processor.cc:208 | Counts the number of CQL SELECT requests executed on particular keyspaces. |
| `scylla_query_processor_replication_strategy_fail_list_violations` | counter | cql3/query_processor.cc:509 | Counts the number of replication_strategy_fail_list guardrail violations, |
| `scylla_query_processor_replication_strategy_warn_list_violations` | counter | cql3/query_processor.cc:503 | Counts the number of replication_strategy_warn_list guardrail violations, |
| `scylla_query_processor_reverse_queries` | counter | cql3/query_processor.cc:460 | Counts the number of CQL SELECT requests with reverse ORDER BY order. |
| `scylla_query_processor_rows_read` | counter | cql3/query_processor.cc:339 | Counts the total number of rows read during CQL requests. |
| `scylla_query_processor_secondary_index_creates` | counter | cql3/query_processor.cc:364 | Counts the total number of CQL CREATE INDEX requests. |
| `scylla_query_processor_secondary_index_drops` | counter | cql3/query_processor.cc:369 | Counts the total number of CQL DROP INDEX requests. |
| `scylla_query_processor_secondary_index_reads` | counter | cql3/query_processor.cc:375 | Counts the total number of CQL read requests performed using secondary indexes. |
| `scylla_query_processor_secondary_index_rows_read` | counter | cql3/query_processor.cc:381 | Counts the total number of rows read during CQL requests performed using secondary indexes. |
| `scylla_query_processor_select_allow_filtering` | counter | cql3/query_processor.cc:415 | Counts the number of SELECT query executions with ALLOW FILTERING option. |
| `scylla_query_processor_select_bypass_caches` | counter | cql3/query_processor.cc:410 | Counts the number of SELECT query executions with BYPASS CACHE option. |
| `scylla_query_processor_select_parallelized` | counter | cql3/query_processor.cc:430 | Counts the number of parallelized aggregation SELECT query executions. |
| `scylla_query_processor_select_partition_range_scan` | counter | cql3/query_processor.cc:420 | Counts the number of SELECT query executions requiring partition range scan. |
| `scylla_query_processor_select_partition_range_scan_no_bypass_cache` | counter | cql3/query_processor.cc:425 | Counts the number of SELECT query executions requiring partition range scan without BYPASS CACHE option. |
| `scylla_query_processor_statements_in_batches` | counter | cql3/query_processor.cc:308 | Counts the total number of sub-statements in CQL BATCH requests without conditions. |
| `scylla_query_processor_unpaged_select_queries` | counter | cql3/query_processor.cc:465 | Counts the total number of unpaged CQL SELECT requests. |
| `scylla_query_processor_unpaged_select_queries_per_ks` | counter | cql3/query_processor.cc:473 | Counts the number of unpaged CQL SELECT requests against particular keyspaces. |
| `scylla_query_processor_unprivileged_entries_evictions_on_size` | counter | cql3/query_processor.cc:349 | Counts a number of evictions of prepared statements from the prepared statements cache after they have been used only once. An increasing counter sugg |
| `scylla_query_processor_updates` | counter | cql3/query_processor.cc:166 | Counts the total number of CQL UPDATE requests with/without conditions. |
| `scylla_query_processor_updates_per_ks` | counter | cql3/query_processor.cc:247 | Counts the number of CQL UPDATE requests executed on particular keyspaces. |
| `scylla_query_processor_user_prepared_auth_cache_footprint` | gauge | cql3/query_processor.cc:455 | Size (in bytes) of the authenticated prepared statements cache. |
| `scylla_query_processor_writes_per_consistency_level` | counter | cql3/query_processor.cc:525 | Counts the number of writes for each consistency level. |

## raft (24 metrics)

| `scylla_raft_add_entries` | counter | raft/server.cc:1767 | Number of entries added on this node, the log_entry_type label can be command, dummy or config |
| `scylla_raft_applied_entries` | counter | raft/server.cc:1826 | Number of log entries applied |
| `scylla_raft_apply_index` | gauge | raft/server.cc:1847 | applied index |
| `scylla_raft_commit_index` | gauge | raft/server.cc:1845 | commit index |
| `scylla_raft_group0_status` | gauge | service/raft/raft_group0.cc:1083 | status of the raft group, 1 - normal, 2 - aborted |
| `scylla_raft_in_memory_log_size` | gauge | raft/server.cc:1831 | size of in-memory part of the log |
| `scylla_raft_log_last_index` | gauge | raft/server.cc:1835 | term of the last log entry |
| `scylla_raft_log_last_term` | gauge | raft/server.cc:1837 | index of the last log entry |
| `scylla_raft_log_memory_usage` | gauge | raft/server.cc:1833 | memory usage of in-memory part of the log in bytes |
| `scylla_raft_messages_received` | counter | raft/server.cc:1774 | Number of messages received, the message_type determines the type of message |
| `scylla_raft_messages_sent` | counter | raft/server.cc:1789 | Number of messages sent, the message_type determines the type of message |
| `scylla_raft_persisted_log_entries` | counter | raft/server.cc:1822 | Number of log entries persisted |
| `scylla_raft_polls` | counter | raft/server.cc:1812 | Number of times raft state machine polled |
| `scylla_raft_queue_entries_for_apply` | counter | raft/server.cc:1824 | Number of log entries queued to be applied |
| `scylla_raft_sm_load_snapshot` | counter | raft/server.cc:1818 | Number of times user state machine reloaded with a snapshot |
| `scylla_raft_snapshot_last_index` | gauge | raft/server.cc:1839 | term of the snapshot |
| `scylla_raft_snapshot_last_term` | gauge | raft/server.cc:1841 | index of the snapshot |
| `scylla_raft_snapshots_taken` | counter | raft/server.cc:1828 | Number of times user's state machine snapshotted |
| `scylla_raft_state` | gauge | raft/server.cc:1843 | current state: 0 - follower, 1 - candidate, 2 - leader |
| `scylla_raft_store_snapshot` | counter | raft/server.cc:1816 | Number of snapshots persisted |
| `scylla_raft_store_term_and_vote` | counter | raft/server.cc:1814 | Number of times term and vote persisted |
| `scylla_raft_truncate_persisted_log` | counter | raft/server.cc:1820 | Number of times log truncated on storage |
| `scylla_raft_waiter_awoken` | counter | raft/server.cc:1808 | Number of waiters that got result back |
| `scylla_raft_waiter_dropped` | counter | raft/server.cc:1810 | Number of waiters that did not get result back |

## reactor (27 metrics)

| `scylla_reactor_abandoned_failed_futures` | counter | seastar/src/core/reactor.cc:2621 | Total number of abandoned failed futures, futures destroyed while still containing an exception |
| `scylla_reactor_aio_errors` | counter | seastar/src/core/reactor.cc:2589 | Total aio errors |
| `scylla_reactor_aio_outsizes` | counter | seastar/src/core/reactor.cc:2588 | Total number of aio operations that exceed IO limit |
| `scylla_reactor_aio_reads` | counter | seastar/src/core/reactor.cc:2582 | Total aio-reads operations |
| `scylla_reactor_aio_retries` | counter | seastar/src/core/reactor.cc:2593 | Total number of IOCB-s re-submitted via thread-pool |
| `scylla_reactor_aio_writes` | counter | seastar/src/core/reactor.cc:2586 | Total aio-writes operations |
| `scylla_reactor_awake_time_ms_total` | counter | seastar/src/core/reactor.cc:2574 | Total reactor awake time (wall_clock) |
| `scylla_reactor_cpp_exceptions` | counter | seastar/src/core/reactor.cc:2619 | Total number of C++ exceptions |
| `scylla_reactor_cpu_busy_ms` | counter | seastar/src/core/reactor.cc:2570 | Total cpu busy time in milliseconds |
| `scylla_reactor_cpu_steal_time_ms` | counter | seastar/src/core/reactor.cc:2578 | Total steal time, the time in which something else was running while the reactor was runnable (not sleeping). |
| `scylla_reactor_cpu_used_time_ms` | counter | seastar/src/core/reactor.cc:2576 | Total reactor thread CPU time (from CLOCK_THREAD_CPUTIME) |
| `scylla_reactor_fstream_read_bytes` | counter | seastar/src/core/reactor.cc:2629 | Counts bytes read from disk file streams.  A high rate indicates high disk activity. |
| `scylla_reactor_fstream_read_bytes_blocked` | counter | seastar/src/core/reactor.cc:2637 | Counts the number of bytes read from disk that could not be satisfied from read-ahead buffers, and had to block. |
| `scylla_reactor_fstream_reads` | counter | seastar/src/core/reactor.cc:2625 | Counts reads from disk file streams.  A high rate indicates high disk activity. |
| `scylla_reactor_fstream_reads_ahead_bytes_discarded` | counter | seastar/src/core/reactor.cc:2645 | Counts the number of buffered bytes that were read ahead of time and were discarded because they were not needed, wasting disk bandwidth. |
| `scylla_reactor_fstream_reads_aheads_discarded` | counter | seastar/src/core/reactor.cc:2641 | Counts the number of times a buffer that was read ahead of time and was discarded because it was not needed, wasting disk bandwidth. |
| `scylla_reactor_fstream_reads_blocked` | counter | seastar/src/core/reactor.cc:2633 | Counts the number of times a disk read could not be satisfied from read-ahead buffers, and had to block. |
| `scylla_reactor_fsyncs` | counter | seastar/src/core/reactor.cc:2592 | Total number of fsync operations |
| `scylla_reactor_internal_errors` | counter | seastar/src/core/reactor.cc:2620 | Total number of internal errors (subset of cpp_exceptions) that usually indicate malfunction in the code |
| `scylla_reactor_logging_failures` | counter | seastar/src/core/reactor.cc:2617 | Total number of logging failures |
| `scylla_reactor_polls` | counter | seastar/src/core/reactor.cc:2567 | Number of times pollers were executed |
| `scylla_reactor_sleep_time_ms_total` | counter | seastar/src/core/reactor.cc:2572 | Total reactor sleep time (wall clock) |
| `scylla_reactor_stalls` | histogram | seastar/src/core/reactor.cc:2590 | A histogram of reactor stall durations |
| `scylla_reactor_tasks_pending` | gauge | seastar/src/core/reactor.cc:2564 | Number of pending tasks in the queue |
| `scylla_reactor_tasks_processed` | counter | seastar/src/core/reactor.cc:2566 | Total tasks processed |
| `scylla_reactor_timers_pending` | gauge | seastar/src/core/reactor.cc:2568 | Number of tasks in the timer-pending queue |
| `scylla_reactor_utilization` | gauge | seastar/src/core/reactor.cc:2569 | CPU utilization |

## repair (11 metrics)

| `scylla_repair_inc_sst_read_bytes` | counter | repair/row_level.cc:220 | Total number of bytes read from sstables for incremental repair on this shard. |
| `scylla_repair_inc_sst_skipped_bytes` | counter | repair/row_level.cc:218 | Total number of bytes skipped from sstables for incremental repair on this shard. |
| `scylla_repair_row_from_disk_bytes` | counter | repair/row_level.cc:216 | Total bytes of rows read from disk on this shard. |
| `scylla_repair_row_from_disk_nr` | counter | repair/row_level.cc:214 | Total number of rows read from disk on this shard. |
| `scylla_repair_rx_hashes_nr` | counter | repair/row_level.cc:212 | Total number of row hashes received on this shard. |
| `scylla_repair_rx_row_bytes` | counter | repair/row_level.cc:208 | Total bytes of rows received on this shard. |
| `scylla_repair_rx_row_nr` | counter | repair/row_level.cc:204 | Total number of rows received on this shard. |
| `scylla_repair_tablet_time_ms` | counter | repair/row_level.cc:222 | Time spent on tablet repair on this shard in milliseconds. |
| `scylla_repair_tx_hashes_nr` | counter | repair/row_level.cc:210 | Total number of row hashes sent on this shard. |
| `scylla_repair_tx_row_bytes` | counter | repair/row_level.cc:206 | Total bytes of rows sent on this shard. |
| `scylla_repair_tx_row_nr` | counter | repair/row_level.cc:202 | Total number of rows sent on this shard. |

## rpc (17 metrics)

| `scylla_rpc_client_count` | gauge | seastar/src/rpc/rpc.cc:894 | Total number of clients |
| `scylla_rpc_client_delay_samples` | counter | seastar/src/rpc/rpc.cc:904 | Total number of delay samples |
| `scylla_rpc_client_delay_total` | counter | seastar/src/rpc/rpc.cc:906 | Total delay in seconds |
| `scylla_rpc_client_exception_received` | counter | seastar/src/rpc/rpc.cc:900 | Total number of exceptional responses received |
| `scylla_rpc_client_pending` | gauge | seastar/src/rpc/rpc.cc:913 | Number of queued outbound messages |
| `scylla_rpc_client_replied` | counter | seastar/src/rpc/rpc.cc:898 | Total number of responses received |
| `scylla_rpc_client_sent_messages` | counter | seastar/src/rpc/rpc.cc:896 | Total number of messages sent |
| `scylla_rpc_client_timeout` | counter | seastar/src/rpc/rpc.cc:902 | Total number of timeout responses |
| `scylla_rpc_client_wait_reply` | gauge | seastar/src/rpc/rpc.cc:915 | Number of replies waiting for |
| `scylla_rpc_compression_bytes_received` | counter | message/advanced_rpc_compressor.cc:299 | bytes read from RPC connections, after decompression |
| `scylla_rpc_compression_bytes_sent` | counter | message/advanced_rpc_compressor.cc:294 | bytes written to RPC connections, before compression |
| `scylla_rpc_compression_compressed_bytes_received` | counter | message/advanced_rpc_compressor.cc:296 | bytes read from RPC connections, before decompression |
| `scylla_rpc_compression_compressed_bytes_sent` | counter | message/advanced_rpc_compressor.cc:295 | bytes written to RPC connections, after compression |
| `scylla_rpc_compression_compression_cpu_nanos` | counter | message/advanced_rpc_compressor.cc:300 | nanoseconds spent on compression |
| `scylla_rpc_compression_decompression_cpu_nanos` | counter | message/advanced_rpc_compressor.cc:301 | nanoseconds spent on decompression |
| `scylla_rpc_compression_messages_received` | counter | message/advanced_rpc_compressor.cc:297 | RPC messages received |
| `scylla_rpc_compression_messages_sent` | counter | message/advanced_rpc_compressor.cc:298 | RPC messages sent |

## s3 (41 metrics)

> **Note:** In 2026.3.0~dev builds, the old `scylla_s3_total_{read,write}_{bytes,requests,latency_sec}` metrics were replaced by per-HTTP-method variants (`get`, `put`, `head`, `delete`, `post`, `connect`, `options`, `patch`, `trace`). The old names are listed at the end for reference.

| `scylla_s3_downloads_blocked_on_memory` | gauge | utils/s3/client.cc | S3 downloads currently blocked waiting for memory |
| `scylla_s3_nr_active_connections` | gauge | utils/s3/client.cc | Total number of connections with running requests |
| `scylla_s3_nr_connections` | gauge | utils/s3/client.cc | Total number of connections |
| `scylla_s3_total_new_connections` | counter | utils/s3/client.cc | Total number of new connections created so far |
| `scylla_s3_total_read_prefetch_bytes` | counter | utils/s3/client.cc | Total number of bytes prefetched during S3 reads |
| `scylla_s3_total_get_bytes` | counter | utils/s3/client.cc | Total bytes received in GET requests (object reads) |
| `scylla_s3_total_get_latency_sec` | counter | utils/s3/client.cc | Cumulative latency of GET requests |
| `scylla_s3_total_get_requests` | counter | utils/s3/client.cc | Total number of GET requests |
| `scylla_s3_total_get_retries` | counter | utils/s3/client.cc | GET request retries |
| `scylla_s3_total_put_bytes` | counter | utils/s3/client.cc | Total bytes sent in PUT requests (object writes) |
| `scylla_s3_total_put_latency_sec` | counter | utils/s3/client.cc | Cumulative latency of PUT requests |
| `scylla_s3_total_put_requests` | counter | utils/s3/client.cc | Total number of PUT requests |
| `scylla_s3_total_put_retries` | counter | utils/s3/client.cc | PUT request retries |
| `scylla_s3_total_head_bytes` | counter | utils/s3/client.cc | Total bytes in HEAD requests |
| `scylla_s3_total_head_latency_sec` | counter | utils/s3/client.cc | Cumulative latency of HEAD requests |
| `scylla_s3_total_head_requests` | counter | utils/s3/client.cc | Total number of HEAD requests (metadata checks) |
| `scylla_s3_total_head_retries` | counter | utils/s3/client.cc | HEAD request retries |
| `scylla_s3_total_delete_bytes` | counter | utils/s3/client.cc | Total bytes in DELETE requests |
| `scylla_s3_total_delete_latency_sec` | counter | utils/s3/client.cc | Cumulative latency of DELETE requests |
| `scylla_s3_total_delete_requests` | counter | utils/s3/client.cc | Total number of DELETE requests (object removal) |
| `scylla_s3_total_delete_retries` | counter | utils/s3/client.cc | DELETE request retries |
| `scylla_s3_total_post_bytes` | counter | utils/s3/client.cc | Total bytes in POST requests (multipart upload) |
| `scylla_s3_total_post_latency_sec` | counter | utils/s3/client.cc | Cumulative latency of POST requests |
| `scylla_s3_total_post_requests` | counter | utils/s3/client.cc | Total number of POST requests |
| `scylla_s3_total_post_retries` | counter | utils/s3/client.cc | POST request retries |
| `scylla_s3_total_connect_bytes` | counter | utils/s3/client.cc | Total bytes in CONNECT requests |
| `scylla_s3_total_connect_latency_sec` | counter | utils/s3/client.cc | Cumulative latency of CONNECT requests |
| `scylla_s3_total_connect_requests` | counter | utils/s3/client.cc | Total number of CONNECT requests |
| `scylla_s3_total_connect_retries` | counter | utils/s3/client.cc | CONNECT request retries |
| `scylla_s3_total_options_bytes` | counter | utils/s3/client.cc | Total bytes in OPTIONS requests |
| `scylla_s3_total_options_latency_sec` | counter | utils/s3/client.cc | Cumulative latency of OPTIONS requests |
| `scylla_s3_total_options_requests` | counter | utils/s3/client.cc | Total number of OPTIONS requests |
| `scylla_s3_total_options_retries` | counter | utils/s3/client.cc | OPTIONS request retries |
| `scylla_s3_total_patch_bytes` | counter | utils/s3/client.cc | Total bytes in PATCH requests |
| `scylla_s3_total_patch_latency_sec` | counter | utils/s3/client.cc | Cumulative latency of PATCH requests |
| `scylla_s3_total_patch_requests` | counter | utils/s3/client.cc | Total number of PATCH requests |
| `scylla_s3_total_patch_retries` | counter | utils/s3/client.cc | PATCH request retries |
| `scylla_s3_total_trace_bytes` | counter | utils/s3/client.cc | Total bytes in TRACE requests |
| `scylla_s3_total_trace_latency_sec` | counter | utils/s3/client.cc | Cumulative latency of TRACE requests |
| `scylla_s3_total_trace_requests` | counter | utils/s3/client.cc | Total number of TRACE requests |
| `scylla_s3_total_trace_retries` | counter | utils/s3/client.cc | TRACE request retries |

**Legacy metrics (pre-2026.3.0, may still appear in older builds):**

| `scylla_s3_total_read_bytes` | counter | utils/s3/client.cc:250 | Total number of bytes read from objects |
| `scylla_s3_total_read_latency_sec` | counter | utils/s3/client.cc:254 | Total time spent reading data from objects |
| `scylla_s3_total_read_requests` | counter | utils/s3/client.cc:246 | Total number of object read requests |
| `scylla_s3_total_write_bytes` | counter | utils/s3/client.cc:252 | Total number of bytes written to objects |
| `scylla_s3_total_write_latency_sec` | counter | utils/s3/client.cc:256 | Total time spent writing data to objects |
| `scylla_s3_total_write_requests` | counter | utils/s3/client.cc:248 | Total number of object write requests |

## scheduler (7 metrics)

| `scylla_scheduler_queue_length` | gauge | seastar/src/core/reactor.cc:995 | Size of backlog on this queue, in tasks; indicates whether the queue is busy and/or contended |
| `scylla_scheduler_runtime_ms` | counter | seastar/src/core/reactor.cc:980 | Accumulated runtime of this task queue; an increment rate of 1000ms per second indicates full utilization |
| `scylla_scheduler_shares` | gauge | seastar/src/core/reactor.cc:998 | Shares allocated to this queue |
| `scylla_scheduler_starvetime_ms` | counter | seastar/src/core/reactor.cc:988 | Accumulated starvation time of this task queue; an increment rate of 1000ms per second indicates the scheduler feels really bad |
| `scylla_scheduler_tasks_processed` | counter | seastar/src/core/reactor.cc:992 | Count of tasks executing on this queue; indicates together with runtime_ms indicates length of tasks |
| `scylla_scheduler_time_spent_on_task_quota_violations_ms` | counter | seastar/src/core/reactor.cc:1001 | Total amount in milliseconds we were in violation of the task quota |
| `scylla_scheduler_waittime_ms` | counter | seastar/src/core/reactor.cc:984 | Accumulated waittime of this task queue; an increment rate of 1000ms per second indicates queue is waiting for something (e.g. IO) |

## scollectd (6 metrics)

| `scylla_scollectd_latency` | gauge | seastar/src/core/scollectd.cc:388 | avrage latency |
| `scylla_scollectd_records` | gauge | seastar/src/core/scollectd.cc:394 | number of records reported |
| `scylla_scollectd_total_bytes_sent` | counter | seastar/src/core/scollectd.cc:384 | total bytes sent |
| `scylla_scollectd_total_requests` | counter | seastar/src/core/scollectd.cc:386 | total requests |
| `scylla_scollectd_total_time_in_ms` | counter | seastar/src/core/scollectd.cc:390 | total time in milliseconds |
| `scylla_scollectd_total_values` | gauge | seastar/src/core/scollectd.cc:392 | current number of values reported |

## scylladb (1 metrics)

| `scylla_scylladb_current_version` | gauge | main.cc:798 | Current ScyllaDB version. |

## smp (3 metrics)

| `scylla_smp_total_completed_messages` | counter | seastar/src/core/reactor.cc:3796 | Total number of messages completed |
| `scylla_smp_total_received_messages` | counter | seastar/src/core/reactor.cc:3792 | Total number of received messages |
| `scylla_smp_total_sent_messages` | counter | seastar/src/core/reactor.cc:3794 | Total number of sent messages |

## sstable (1 metrics)

| `scylla_sstable_compression_dicts_total_live_memory_bytes` | counter | sstables/compressor.cc:929 | Total amount of memory consumed by SSTable compression dictionaries in RAM |

## sstables (45 metrics)

| `scylla_sstables_bloom_filter_memory_size` | gauge | sstables/sstables.cc:3860 | Bloom filter memory usage in bytes. |
| `scylla_sstables_capped_local_deletion_time` | counter | sstables/sstables.cc:3838 | Number of SStables with tombstones whose local deletion time was capped at the maximum allowed value in Statistics |
| `scylla_sstables_capped_tombstone_deletion_time` | counter | sstables/sstables.cc:3840 | Number of tombstones whose local deletion time was capped at the maximum allowed value |
| `scylla_sstables_cell_tombstone_writes` | counter | sstables/sstables.cc:3825 | Number of cell tombstones written |
| `scylla_sstables_cell_writes` | counter | sstables/sstables.cc:3812 | Number of cells written |
| `scylla_sstables_currently_open_for_reading` | gauge | sstables/sstables.cc:3848 | Number of sstables currently open for reading |
| `scylla_sstables_currently_open_for_writing` | gauge | sstables/sstables.cc:3852 | Number of sstables currently open for writing |
| `scylla_sstables_index_page_blocks` | counter | sstables/sstables.cc:3769 | Index page requests which needed to wait due to page not being loaded yet |
| `scylla_sstables_index_page_cache_bytes` | gauge | sstables/sstables.cc:3755 | Total number of bytes cached in the index page cache |
| `scylla_sstables_index_page_cache_bytes_in_std` | gauge | sstables/sstables.cc:3757 | Total number of bytes in temporary buffers which live in the std allocator |
| `scylla_sstables_index_page_cache_evictions` | counter | sstables/sstables.cc:3751 | Total number of index page cache pages which have been evicted |
| `scylla_sstables_index_page_cache_hits` | counter | sstables/sstables.cc:3747 | Index page cache requests which were served from cache |
| `scylla_sstables_index_page_cache_misses` | counter | sstables/sstables.cc:3749 | Index page cache requests which had to perform I/O |
| `scylla_sstables_index_page_cache_populations` | counter | sstables/sstables.cc:3753 | Total number of index page cache pages which were inserted into the cache |
| `scylla_sstables_index_page_evictions` | counter | sstables/sstables.cc:3771 | Index pages which got evicted from memory |
| `scylla_sstables_index_page_hits` | counter | sstables/sstables.cc:3765 | Index page requests which could be satisfied without waiting |
| `scylla_sstables_index_page_misses` | counter | sstables/sstables.cc:3767 | Index page requests which initiated a read from disk |
| `scylla_sstables_index_page_populations` | counter | sstables/sstables.cc:3773 | Index pages which got populated into memory |
| `scylla_sstables_index_page_used_bytes` | gauge | sstables/sstables.cc:3775 | Amount of bytes used by index pages in memory |
| `scylla_sstables_partition_reads` | counter | sstables/sstables.cc:3831 | Number of partitions read |
| `scylla_sstables_partition_seeks` | counter | sstables/sstables.cc:3833 | Number of partitions seeked |
| `scylla_sstables_partition_writes` | counter | sstables/sstables.cc:3806 | Number of partitions written |
| `scylla_sstables_pi_auto_scale_events` | counter | sstables/sstables.cc:3818 | Number of promoted index auto-scaling events |
| `scylla_sstables_pi_cache_block_count` | gauge | sstables/sstables.cc:3803 | Number of promoted index blocks currently cached |
| `scylla_sstables_pi_cache_bytes` | gauge | sstables/sstables.cc:3801 | Number of bytes currently used by cached promoted index blocks |
| `scylla_sstables_pi_cache_evictions` | counter | sstables/sstables.cc:3799 | Number of promoted index blocks which got evicted |
| `scylla_sstables_pi_cache_hits_l0` | counter | sstables/sstables.cc:3785 | Number of requests for promoted index block in state l0 which didn't have to go to the page cache |
| `scylla_sstables_pi_cache_hits_l1` | counter | sstables/sstables.cc:3787 | Number of requests for promoted index block in state l1 which didn't have to go to the page cache |
| `scylla_sstables_pi_cache_hits_l2` | counter | sstables/sstables.cc:3789 | Number of requests for promoted index block in state l2 which didn't have to go to the page cache |
| `scylla_sstables_pi_cache_misses_l0` | counter | sstables/sstables.cc:3791 | Number of requests for promoted index block in state l0 which had to go to the page cache |
| `scylla_sstables_pi_cache_misses_l1` | counter | sstables/sstables.cc:3793 | Number of requests for promoted index block in state l1 which had to go to the page cache |
| `scylla_sstables_pi_cache_misses_l2` | counter | sstables/sstables.cc:3795 | Number of requests for promoted index block in state l2 which had to go to the page cache |
| `scylla_sstables_pi_cache_populations` | counter | sstables/sstables.cc:3797 | Number of promoted index blocks which got inserted |
| `scylla_sstables_range_partition_reads` | counter | sstables/sstables.cc:3829 | Number of partition range flat mutation reads |
| `scylla_sstables_range_tombstone_reads` | counter | sstables/sstables.cc:3821 | Number of range tombstones read |
| `scylla_sstables_range_tombstone_writes` | counter | sstables/sstables.cc:3816 | Number of range tombstones written |
| `scylla_sstables_row_reads` | counter | sstables/sstables.cc:3835 | Number of rows read |
| `scylla_sstables_row_tombstone_reads` | counter | sstables/sstables.cc:3823 | Number of row tombstones read |
| `scylla_sstables_row_writes` | counter | sstables/sstables.cc:3810 | Number of clustering rows written |
| `scylla_sstables_single_partition_reads` | counter | sstables/sstables.cc:3827 | Number of single partition flat mutation reads |
| `scylla_sstables_static_row_writes` | counter | sstables/sstables.cc:3808 | Number of static rows written |
| `scylla_sstables_tombstone_writes` | counter | sstables/sstables.cc:3814 | Number of tombstones written |
| `scylla_sstables_total_deleted` | counter | sstables/sstables.cc:3857 | Counter of deleted sstables |
| `scylla_sstables_total_open_for_reading` | counter | sstables/sstables.cc:3843 | Counter of sstables open for reading |
| `scylla_sstables_total_open_for_writing` | counter | sstables/sstables.cc:3845 | Counter of sstables open for writing |

## stall (2 metrics)

| `scylla_stall_detector_io_threaded_fallbacks` | counter | seastar/src/core/reactor.cc:2559 | Total number of io-threaded-fallbacks operations |
| `scylla_stall_detector_reported` | counter | seastar/src/core/reactor.cc:1192 | Total number of reported stalls, look in the traces for the exact reason |

## storage (52 metrics)

| `scylla_storage_proxy_coordinator_background_read_repairs` | counter | service/storage_proxy.cc:3054 | number of background read repairs |
| `scylla_storage_proxy_coordinator_background_writes_failed` | counter | service/storage_proxy.cc:2979 | number of write requests that failed after CL was reached |
| `scylla_storage_proxy_coordinator_canceled_read_repairs` | counter | service/storage_proxy.cc:3046 | number of global read repairs canceled due to a concurrent write |
| `scylla_storage_proxy_coordinator_cas_background` | gauge | service/storage_proxy.cc:3162 | how many paxos operations are still running after a result was already returned |
| `scylla_storage_proxy_coordinator_cas_dropped_prune` | counter | service/storage_proxy.cc:3150 | how many times a coordinator did not perform prune after cas |
| `scylla_storage_proxy_coordinator_cas_failed_read_round_optimization` | counter | service/storage_proxy.cc:3134 | CAS read rounds issued only if previous value is missing on some replica |
| `scylla_storage_proxy_coordinator_cas_foreground` | gauge | service/storage_proxy.cc:3158 | how many paxos operations that did not yet produce a result are running |
| `scylla_storage_proxy_coordinator_cas_prune` | counter | service/storage_proxy.cc:3146 | how many times paxos prune was done after successful cas operation |
| `scylla_storage_proxy_coordinator_cas_read_contention` | histogram | service/storage_proxy.cc:3138 | how many contended reads were encountered |
| `scylla_storage_proxy_coordinator_cas_read_latency` | histogram | service/storage_proxy.cc:3093 | Transactional read latency histogram |
| `scylla_storage_proxy_coordinator_cas_read_timeouts` | counter | service/storage_proxy.cc:3109 | number of transactional read request failed due to a timeout |
| `scylla_storage_proxy_coordinator_cas_read_unavailable` | counter | service/storage_proxy.cc:3113 | number of transactional read requests failed due to an "unavailable" error |
| `scylla_storage_proxy_coordinator_cas_read_unfinished_commit` | counter | service/storage_proxy.cc:3118 | number of transaction commit attempts that occurred on read |
| `scylla_storage_proxy_coordinator_cas_total_operations` | counter | service/storage_proxy.cc:3154 | number of total paxos operations executed (reads and writes) |
| `scylla_storage_proxy_coordinator_cas_write_condition_not_met` | counter | service/storage_proxy.cc:3126 | number of transaction preconditions that did not match current values |
| `scylla_storage_proxy_coordinator_cas_write_contention` | histogram | service/storage_proxy.cc:3142 | how many contended writes were encountered |
| `scylla_storage_proxy_coordinator_cas_write_latency` | histogram | service/storage_proxy.cc:3097 | Transactional write latency histogram |
| `scylla_storage_proxy_coordinator_cas_write_timeout_due_to_uncertainty` | counter | service/storage_proxy.cc:3130 | how many times write timeout was reported because of uncertainty in the result |
| `scylla_storage_proxy_coordinator_cas_write_timeouts` | counter | service/storage_proxy.cc:3101 | number of transactional write request failed due to a timeout |
| `scylla_storage_proxy_coordinator_cas_write_unavailable` | counter | service/storage_proxy.cc:3105 | number of transactional write requests failed due to an "unavailable" error |
| `scylla_storage_proxy_coordinator_cas_write_unfinished_commit` | counter | service/storage_proxy.cc:3122 | number of transaction commit attempts that occurred on write |
| `scylla_storage_proxy_coordinator_foreground_read_repairs` | counter | service/storage_proxy.cc:3050 | number of foreground read repairs |
| `scylla_storage_proxy_coordinator_last_mv_flow_control_delay` | gauge | service/storage_proxy.cc:2951 | delay (in seconds) added for MV flow control in the last request |
| `scylla_storage_proxy_coordinator_mv_flow_control_delay_total` | counter | service/storage_proxy.cc:2955 | total delay (in microseconds) added for MV flow control, to delay the response sent to finished writes, divide this by throttled_base_writes_total to  |
| `scylla_storage_proxy_coordinator_range_timeouts` | counter | service/storage_proxy.cc:3074 | number of range read operations failed due to a timeout |
| `scylla_storage_proxy_coordinator_range_unavailable` | counter | service/storage_proxy.cc:3078 | number of range read operations failed due to an "unavailable" error |
| `scylla_storage_proxy_coordinator_read_latency` | histogram | service/storage_proxy.cc:3030 | The general read latency histogram |
| `scylla_storage_proxy_coordinator_read_rate_limited` | counter | service/storage_proxy.cc:3066 | number of read requests which were rejected because rate limit for the partition was reached. rejected_by_coordinator indicates if it was rejected by  |
| `scylla_storage_proxy_coordinator_read_retries` | counter | service/storage_proxy.cc:3042 | number of read retry attempts |
| `scylla_storage_proxy_coordinator_read_timeouts` | counter | service/storage_proxy.cc:3058 | number of read request failed due to a timeout |
| `scylla_storage_proxy_coordinator_read_unavailable` | counter | service/storage_proxy.cc:3062 | number read requests failed due to an "unavailable" error |
| `scylla_storage_proxy_coordinator_reads_coordinator_outside_replica_set` | counter | service/storage_proxy.cc:2987 | number of CQL read requests which arrived to a non-replica and had to be forwarded to a replica |
| `scylla_storage_proxy_coordinator_speculative_data_reads` | counter | service/storage_proxy.cc:3086 | number of speculative data read requests that were sent |
| `scylla_storage_proxy_coordinator_speculative_digest_reads` | counter | service/storage_proxy.cc:3082 | number of speculative digest read requests that were sent |
| `scylla_storage_proxy_coordinator_throttled_base_writes_total` | counter | service/storage_proxy.cc:2947 | number of throttled base replica write requests, a throttled write is one whose response was delayed, see mv_flow_control_delay_total |
| `scylla_storage_proxy_coordinator_throttled_writes` | counter | service/storage_proxy.cc:2959 | number of throttled write requests |
| `scylla_storage_proxy_coordinator_write_latency` | histogram | service/storage_proxy.cc:2931 | The general write latency histogram |
| `scylla_storage_proxy_coordinator_write_rate_limited` | counter | service/storage_proxy.cc:2971 | number of write requests which were rejected because rate limit for the partition was reached. rejected_by_coordinator indicates if it was rejected by |
| `scylla_storage_proxy_coordinator_write_timeouts` | counter | service/storage_proxy.cc:2963 | number of write request failed due to a timeout |
| `scylla_storage_proxy_coordinator_write_unavailable` | counter | service/storage_proxy.cc:2967 | number write requests failed due to an "unavailable" error |
| `scylla_storage_proxy_coordinator_writes_coordinator_outside_replica_set` | counter | service/storage_proxy.cc:2983 | number of CQL write requests which arrived to a non-replica and had to be forwarded to a replica |
| `scylla_storage_proxy_coordinator_writes_failed_due_to_too_many_in_flight_hints` | counter | service/storage_proxy.cc:2991 | number of CQL write requests which failed because the hinted handoff mechanism is overloaded |
| `scylla_storage_proxy_replica_cas_dropped_prune` | counter | service/storage_proxy.cc:3204 | how many times a coordinator did not perform prune after cas |
| `scylla_storage_proxy_replica_cross_shard_ops` | counter | service/storage_proxy.cc:3196 | number of operations that crossed a shard boundary |
| `scylla_storage_proxy_replica_fenced_out_requests` | counter | service/storage_proxy.cc:3200 | number of requests that resulted in a stale_topology_exception |
| `scylla_storage_proxy_replica_forwarded_mutations` | counter | service/storage_proxy.cc:3176 | number of mutations forwarded to other replica Nodes |
| `scylla_storage_proxy_replica_forwarding_errors` | counter | service/storage_proxy.cc:3180 | number of errors during forwarding mutations to other replica Nodes |
| `scylla_storage_proxy_replica_reads` | counter | service/storage_proxy.cc:3184 | number of remote reads this Node received. op_type label could be data, mutation_data or digest |
| `scylla_storage_proxy_replica_received_counter_updates` | counter | service/storage_proxy.cc:3168 | number of counter updates received by this node acting as an update leader |
| `scylla_storage_proxy_replica_received_hints_bytes_total` | counter | service/storage_proxy.cc:3212 | total size of hints and MV hints received by this node |
| `scylla_storage_proxy_replica_received_hints_total` | counter | service/storage_proxy.cc:3208 | number of hints and MV hints received by this node |
| `scylla_storage_proxy_replica_received_mutations` | counter | service/storage_proxy.cc:3172 | number of mutations received by a replica Node |

## streaming (3 metrics)

| `scylla_streaming_finished_percentage` | gauge | streaming/stream_manager.cc:61 | Finished percentage of node operation on this shard |
| `scylla_streaming_total_incoming_bytes` | counter | streaming/stream_manager.cc:55 | Total number of bytes received on this shard. |
| `scylla_streaming_total_outgoing_bytes` | counter | streaming/stream_manager.cc:58 | Total number of bytes sent on this shard. |

## tablet (2 metrics)

| `scylla_tablet_ops_failed` | gauge | service/topology_coordinator.cc:4829 | Number of failed tablet auto repair |
| `scylla_tablet_ops_succeeded` | gauge | service/topology_coordinator.cc:4831 | Number of succeeded tablet auto repair |

## tablets (1 metrics)

| `scylla_tablets_count` | gauge | replica/table.cc:2217 | Tablet count |

## test (8 metrics)

| `scylla_test_counter1_1` | counter | seastar/tests/unit/metrics_test.cc:240 | counter 1 |
| `scylla_test_counter_1` | counter | seastar/tests/unit/metrics_test.cc:180 | counter 1 |
| `scylla_test_counter_2` | counter | seastar/tests/unit/metrics_test.cc:193 | counter 2 |
| `scylla_test_gauge1_1` | gauge | seastar/tests/unit/metrics_test.cc:238 | gague 1 |
| `scylla_test_gauge_1` | gauge | seastar/tests/unit/metrics_test.cc:179 | gague 1 |
| `scylla_test_metric_alpha` | gauge | seastar/tests/unit/prometheus_http_test.cc:128 | (no description) |
| `scylla_test_metric_beta` | gauge | seastar/tests/unit/prometheus_http_test.cc:129 | (no description) |
| `scylla_test_metric_gamma` | gauge | seastar/tests/unit/prometheus_http_test.cc:130 | (no description) |

## test2 (2 metrics)

| `scylla_test2_counter_1` | counter | seastar/tests/unit/metrics_test.cc:268 | counter 1 |
| `scylla_test2_gauge_1` | gauge | seastar/tests/unit/metrics_test.cc:267 | gague 1 |

## test3 (4 metrics)

| `scylla_test3_counter_1` | counter | seastar/tests/unit/metrics_test.cc:298 | counter 1 |
| `scylla_test3_counter_2` | counter | seastar/tests/unit/metrics_test.cc:299 | counter 2 |
| `scylla_test3_counter_3` | counter | seastar/tests/unit/metrics_test.cc:337 | counter 2 |
| `scylla_test3_gauge_1` | gauge | seastar/tests/unit/metrics_test.cc:297 | gague 1 |

## tracing (10 metrics)

| `scylla_tracing_active_sessions` | gauge | tracing/tracing.cc:54 | Holds a number of a currently active tracing sessions. |
| `scylla_tracing_cached_records` | gauge | tracing/tracing.cc:57 | (no description) |
| `scylla_tracing_dropped_records` | counter | tracing/tracing.cc:44 | Counts a number of dropped records due to too many pending records. |
| `scylla_tracing_dropped_sessions` | counter | tracing/tracing.cc:40 | Counts a number of dropped sessions due to too many pending sessions/records. |
| `scylla_tracing_flushing_records` | gauge | tracing/tracing.cc:65 | (no description) |
| `scylla_tracing_keyspace_helper_bad_column_family_errors` | counter | tracing/trace_keyspace_helper.cc:205 | Counts a number of times write failed due to one of the tables in the system_traces keyspace has an incompatible schema. |
| `scylla_tracing_keyspace_helper_tracing_errors` | counter | tracing/trace_keyspace_helper.cc:201 | Counts a number of errors during writing to a system_traces keyspace. |
| `scylla_tracing_pending_for_write_records` | gauge | tracing/tracing.cc:61 | (no description) |
| `scylla_tracing_trace_errors` | counter | tracing/tracing.cc:51 | Counts a number of trace records dropped due to an error (e.g. OOM). |
| `scylla_tracing_trace_records_count` | counter | tracing/tracing.cc:48 | This metric is a rate of tracing records generation. |

## transport (15 metrics)

| `scylla_transport_connections_blocked` | counter | transport/server.cc:351 | Holds an incrementing counter with the CQL connections that were blocked before being processed due to threshold configured via uninitialized_connecti |
| `scylla_transport_connections_shed` | counter | transport/server.cc:348 | Holds an incrementing counter with the CQL connections that were shed due to concurrency semaphore timeout (threshold configured via uninitialized_con |
| `scylla_transport_cql-connections` | counter | transport/server.cc:325 | Counts a number of client connections. |
| `scylla_transport_cql_errors_total` | counter | transport/server.cc:383 | Counts the total number of returned CQL errors. |
| `scylla_transport_current_connections` | gauge | transport/server.cc:328 | Holds a current number of client connections. |
| `scylla_transport_requests_blocked_memory` | counter | transport/server.cc:341 | Holds an incrementing counter with the requests that were shed due to overload (threshold configured via max_concurrent_requests_per_shard). |
| `scylla_transport_requests_blocked_memory_current` | gauge | transport/server.cc:337 | (no description) |
| `scylla_transport_requests_forwarded_failed` | counter | transport/server.cc:361 | Counts the number of requests that were forwarded to another replica but failed to execute there. |
| `scylla_transport_requests_forwarded_prepared_not_found` | counter | transport/server.cc:367 | Counts the number of requests that were forwarded to another replica but failed there because the statement was not prepared on the target. |
| `scylla_transport_requests_forwarded_redirected` | counter | transport/server.cc:364 | Counts the number of requests that were forwarded to another replica but that replica responded with a redirect to another node. |
| `scylla_transport_requests_forwarded_successfully` | counter | transport/server.cc:358 | Counts the number of requests that were forwarded to another replica and executed successfully there. |
| `scylla_transport_requests_memory_available` | gauge | transport/server.cc:354 | Counts the number of requests that were forwarded to another replica and executed successfully there. |
| `scylla_transport_requests_served` | counter | transport/server.cc:331 | Counts a number of served requests. |
| `scylla_transport_requests_serving` | gauge | transport/server.cc:334 | Holds a number of requests that are being processed right now. |
| `scylla_transport_requests_shed` | counter | transport/server.cc:345 | Holds an incrementing counter with the requests that were shed due to overload (threshold configured via max_concurrent_requests_per_shard). |

## user (5 metrics)

| `scylla_user_functions_cache_blocks` | counter | lang/wasm_instance_cache.cc:64 | The number of times a user defined function waited for an instance |
| `scylla_user_functions_cache_hits` | counter | lang/wasm_instance_cache.cc:60 | The number of user defined function cache hits |
| `scylla_user_functions_cache_instace_count_any` | gauge | lang/wasm_instance_cache.cc:66 | The total number of cached wasm instances, instances in use and empty instances |
| `scylla_user_functions_cache_misses` | counter | lang/wasm_instance_cache.cc:62 | The number of user defined functions loaded |
| `scylla_user_functions_cache_total_size` | gauge | lang/wasm_instance_cache.cc:68 | The total size of instances stored in the user defined function cache |

## vector (1 metrics)

| `scylla_vector_store_dns_refreshes` | gauge | vector_search/vector_store_client.cc:280 | Number of DNS refreshes |

## view (8 metrics)

| `scylla_view_builder_builds_in_progress` | gauge | db/view/view.cc:2218 | Number of currently active view builds. |
| `scylla_view_builder_pending_bookkeeping_ops` | gauge | db/view/view.cc:2206 | Number of tasks waiting to perform bookkeeping operations |
| `scylla_view_builder_steps_failed` | counter | db/view/view.cc:2214 | Number of failed build steps. |
| `scylla_view_builder_steps_performed` | counter | db/view/view.cc:2210 | Number of performed build steps. |
| `scylla_view_update_generator_pending_registrations` | gauge | db/view/view_update_generator.cc:327 | Number of tasks waiting to register staging sstables |
| `scylla_view_update_generator_queued_batches_count` | gauge | db/view/view_update_generator.cc:330 | Number of sets of sstables queued for view update generation |
| `scylla_view_update_generator_sstables_pending_work` | gauge | db/view/view_update_generator.cc:338 | Number of bytes remaining to be processed from SSTables for view updates |
| `scylla_view_update_generator_sstables_to_move_count` | gauge | db/view/view_update_generator.cc:334 | Number of sets of sstables which are already processed and wait to be moved from their staging directory |

---

# Appendix A: Prometheus Name Aliases & Recording Rules

These metrics appear in Prometheus but are **not directly registered** in C++ code. They are either:
- **Recording rules** computed by the Prometheus monitoring stack
- **Histogram sub-metrics** auto-generated by Prometheus
- **Dynamic group names** resolved at runtime (the `group_name` variable in C++)

## A1: CQL Aliases (`scylla_cql_*` → `scylla_query_processor_*`)

The monitoring stack exposes `scylla_cql_*` as friendlier aliases for `scylla_query_processor_*`. These are **recording rules**, not C++ metrics.

| Prometheus Alias | Maps to C++ Metric |
|-----|-----|
| `scylla_cql_reads` | `scylla_query_processor_reads` |
| `scylla_cql_inserts` | `scylla_query_processor_inserts` |
| `scylla_cql_inserts_per_ks` | `scylla_query_processor_inserts_per_ks` |
| `scylla_cql_deletes` | `scylla_query_processor_deletes` |
| `scylla_cql_deletes_per_ks` | `scylla_query_processor_deletes_per_ks` |
| `scylla_cql_reads_per_ks` | `scylla_query_processor_reads_per_ks` |
| `scylla_cql_updates` | `scylla_query_processor_updates` |
| `scylla_cql_updates_per_ks` | `scylla_query_processor_updates_per_ks` |
| `scylla_cql_rows_read` | `scylla_query_processor_rows_read` |
| `scylla_cql_batches` | `scylla_query_processor_batches` |
| `scylla_cql_batches_pure_unlogged` | `scylla_query_processor_batches_pure_unlogged` |
| `scylla_cql_statements_in_batches` | `scylla_query_processor_statements_in_batches` |
| `scylla_cql_prepared_cache_evictions` | `scylla_query_processor_prepared_cache_evictions` |
| `scylla_cql_prepared_cache_size` | `scylla_query_processor_prepared_cache_size` |
| `scylla_cql_prepared_cache_memory_footprint` | `scylla_query_processor_prepared_cache_memory_footprint` |
| `scylla_cql_authorized_prepared_statements_cache_evictions` | `scylla_query_processor_authorized_prepared_statements_cache_evictions` |
| `scylla_cql_authorized_prepared_statements_cache_size` | `scylla_query_processor_authorized_prepared_statements_cache_size` |
| `scylla_cql_select_allow_filtering` | `scylla_query_processor_select_allow_filtering` |
| `scylla_cql_select_bypass_caches` | `scylla_query_processor_select_bypass_caches` |
| `scylla_cql_unpaged_select_queries` | `scylla_query_processor_unpaged_select_queries` |
| `scylla_cql_filtered_read_requests` | `scylla_query_processor_filtered_read_requests` |
| `scylla_cql_filtered_rows_read_total` | `scylla_query_processor_filtered_rows_read_total` |
| `scylla_cql_filtered_rows_matched_total` | `scylla_query_processor_filtered_rows_matched_total` |
| `scylla_cql_filtered_rows_dropped_total` | `scylla_query_processor_filtered_rows_dropped_total` |

## A2: Coordinator Count Aliases (`scylla_coordinator_*`)

| Prometheus Alias | Maps to C++ Metric |
|-----|-----|
| `scylla_coordinator_read_count` / `scylla_coordinator_read_count_total` | Derived from `scylla_storage_proxy_coordinator_read_latency` histogram count |
| `scylla_coordinator_write_count` / `scylla_coordinator_write_count_total` | Derived from `scylla_storage_proxy_coordinator_write_latency` histogram count |

## A3: Dynamic Group Names (`group_name` variable resolved at runtime)

Some metrics use a `group_name` variable that is set at object construction time. They appear in the mapping as `scylla_group_name_*` but in Prometheus with their actual group name.

### Hints Manager (`db/hints/manager.cc`)
Group name = `"hints_manager"` or `"hints_for_views_manager"` depending on the instance.

| Mapping File | Prometheus (hints_manager) | Prometheus (hints_for_views_manager) |
|-----|-----|-----|
| `scylla_group_name_written` | `scylla_hints_manager_written` | `scylla_hints_for_views_manager_written` |
| `scylla_group_name_dropped` | `scylla_hints_manager_dropped` | `scylla_hints_for_views_manager_dropped` |
| `scylla_group_name_errors` | `scylla_hints_manager_errors` | `scylla_hints_for_views_manager_errors` |
| `scylla_group_name_discarded` | `scylla_hints_manager_discarded` | `scylla_hints_for_views_manager_discarded` |
| `scylla_group_name_send_errors` | `scylla_hints_manager_send_errors` | `scylla_hints_for_views_manager_send_errors` |
| `scylla_group_name_size_of_hints_in_progress` | `scylla_hints_manager_size_of_hints_in_progress` | `scylla_hints_for_views_manager_size_of_hints_in_progress` |
| `scylla_group_name_pending_drains` | `scylla_hints_manager_pending_drains` | `scylla_hints_for_views_manager_pending_drains` |
| `scylla_group_name_pending_sends` | `scylla_hints_manager_pending_sends` | `scylla_hints_for_views_manager_pending_sends` |
| `scylla_group_name_sent_total` | `scylla_hints_manager_sent_total` | `scylla_hints_for_views_manager_sent_total` |
| `scylla_group_name_sent_bytes_total` | `scylla_hints_manager_sent_bytes_total` | `scylla_hints_for_views_manager_sent_bytes_total` |
| `scylla_group_name_corrupted_files` | `scylla_hints_manager_corrupted_files` | `scylla_hints_for_views_manager_corrupted_files` |

### Tablet Load Balancer (`service/tablet_allocator.cc`)
Group name = `"load_balancer"`.

| Mapping File | Prometheus |
|-----|-----|
| `scylla_group_name_calls` | `scylla_load_balancer_calls` |
| `scylla_group_name_migrations_produced` | `scylla_load_balancer_migrations_produced` |
| `scylla_group_name_migrations_skipped` | `scylla_load_balancer_migrations_skipped` |
| `scylla_group_name_cross_rack_collocations` | `scylla_load_balancer_cross_rack_collocations` |
| `scylla_group_name_load` | `scylla_load_balancer_load` |
| `scylla_group_name_resizes_emitted` | `scylla_load_balancer_resizes_emitted` |
| `scylla_group_name_resizes_revoked` | `scylla_load_balancer_resizes_revoked` |
| `scylla_group_name_resizes_finalized` | `scylla_load_balancer_resizes_finalized` |
| `scylla_group_name_auto_repair_needs_repair_nr` | `scylla_load_balancer_auto_repair_needs_repair_nr` |
| `scylla_group_name_auto_repair_enabled_nr` | `scylla_load_balancer_auto_repair_enabled_nr` |

### Alternator (`alternator/stats.cc`)
Group name = per-DynamoDB-operation name (e.g., `"alternator_GetItem"`, `"alternator_PutItem"`, etc.).

| Mapping File | Prometheus (example) |
|-----|-----|
| `scylla_group_name_operation` | `scylla_alternator_GetItem_operation`, `scylla_alternator_PutItem_operation`, etc. |
| `scylla_group_name_op_latency` | `scylla_alternator_GetItem_op_latency`, etc. |
| `scylla_group_name_total_operations` | `scylla_alternator_GetItem_total_operations`, etc. |

### Schema Commitlog
The `scylla_schema_commitlog_*` metrics are the same as `scylla_commitlog_*` but for the schema commitlog instance. Same C++ code in `db/commitlog/commitlog.cc`, different `metrics_category_name` passed at construction.

### Transport server (`transport/server.cc`)
Group name = `"transport"` (already mostly mapped, but `_category` variable resolves per scheduling group context).

The `scylla_?_cql_*` metrics from `transport/server.cc` appear in Prometheus as `scylla_transport_cql_*`:
| Mapping File | Prometheus |
|-----|-----|
| `scylla_?_cql_requests_count` | `scylla_transport_cql_requests_count` |
| `scylla_?_cql_request_bytes` | `scylla_transport_cql_request_bytes` |
| `scylla_?_cql_response_bytes` | `scylla_transport_cql_response_bytes` |
| `scylla_?_cql_pending_response_memory` | `scylla_transport_cql_pending_response_memory` |
| `scylla_?_cql_requests_serving` | `scylla_transport_cql_requests_serving` |

## A4: Aggregated Recording Rules (`*_ag` suffix)

These are Prometheus recording rules that aggregate (sum across shards/nodes) existing metrics:
- `scylla_database_total_reads_rate_limited_ag` → `sum(scylla_database_total_reads_rate_limited)`
- `scylla_database_total_writes_failed_ag` → `sum(scylla_database_total_writes_failed)`
- `scylla_database_total_writes_timedout_ag` → `sum(scylla_database_total_writes_timedout)`
- `scylla_hints_manager_written_ag` → `sum(scylla_hints_manager_written)`
- `scylla_reactor_utilization_ag` → `avg(scylla_reactor_utilization)`
- `scylla_storage_proxy_coordinator_background_writes_ag` → `sum(scylla_storage_proxy_coordinator_background_writes)`
- `scylla_storage_proxy_coordinator_read_timeouts_ag` → `sum(scylla_storage_proxy_coordinator_read_timeouts)`
- `scylla_storage_proxy_coordinator_write_timeouts_ag` → `sum(scylla_storage_proxy_coordinator_write_timeouts)`
- `scylla_ag_cache_bytes_used` → `sum(scylla_cache_bytes_used)` (pre-aggregated cache)
- `scylla_ag_cache_row_hits` → `sum(scylla_cache_row_hits)`
- `scylla_ag_cache_row_misses` → `sum(scylla_cache_row_misses)`

## A5: Histogram Sub-metrics (auto-generated by Prometheus)

For every `histogram` type metric, Prometheus auto-generates:
- `<name>_bucket{le="..."}` — cumulative count per bucket boundary
- `<name>_count` — total number of observations
- `<name>_sum` — sum of all observed values
- `<name>_summary` (some Scylla versions) — quantile-based summary

Examples: `scylla_column_family_read_latency_bucket`, `scylla_storage_proxy_coordinator_write_latency_count`, etc.

## A6: Non-ScyllaDB Metrics (from other components in the monitoring stack)

| Prometheus Metric | Source | Description |
|-----|-----|-----|
| `scylla_manager_agent_*` | Scylla Manager Agent | Manager agent metrics (not in ScyllaDB C++ code) |
| `scylla_manager_server_*` | Scylla Manager Server | Manager server metrics |
| `scylla_node_disk_read_bytes` | Node exporter / monitoring stack | Disk I/O bytes read |
| `scylla_node_disk_written_bytes` | Node exporter / monitoring stack | Disk I/O bytes written |
| `scylla_node_filesystem_avail_bytes` | Node exporter / monitoring stack | Available filesystem bytes |
| `scylla_node_filesystem_size_bytes` | Node exporter / monitoring stack | Total filesystem bytes |
| `scylla_node_filesystem_total_avail_bytes` | Node exporter / monitoring stack | Total available across all filesystems |
| `scylla_node_filesystem_total_size_bytes` | Node exporter / monitoring stack | Total size across all filesystems |
| `scylla_nodes_uptime_ts` | Monitoring stack | Node uptime timestamp |
| `scylla_total_compactios` | Monitoring stack (recording rule, note typo) | Total compactions cluster-wide |
| `scylla_total_connection` | Monitoring stack | Total CQL connections cluster-wide |
| `scylla_total_cores` | Monitoring stack | Total CPU cores in cluster |
| `scylla_total_joining_nodes` | Monitoring stack | Count of joining nodes |
| `scylla_total_nodes` | Monitoring stack | Total node count |
| `scylla_total_requests` | Monitoring stack | Total requests cluster-wide |
| `scylla_total_unreachable_nodes` | Monitoring stack | Count of unreachable nodes |

## A7: Seastar/Execution Stage Metrics (from Seastar, not extracted by the script)

| Prometheus Metric | Type | Source | Description |
|-----|-----|-----|-----|
| `scylla_execution_stages_function_calls_enqueued` | counter | `seastar/src/core/execution_stage.cc` | Function calls added to the stage |
| `scylla_execution_stages_function_calls_executed` | counter | `seastar/src/core/execution_stage.cc` | Function calls executed by the stage |
| `scylla_execution_stages_tasks_preempted` | counter | `seastar/src/core/execution_stage.cc` | Number of times execution was preempted |
| `scylla_execution_stages_tasks_scheduled` | counter | `seastar/src/core/execution_stage.cc` | Number of tasks scheduled by the stage |
| `scylla_alien_receive_batch_queue_length` | gauge | `seastar/src/core/alien.cc` | Length of the receive batch queue |

## A8: Additional storage_proxy metrics (registered via stats helper classes)

Some `scylla_storage_proxy_coordinator_*` metrics are registered in a different code pattern (via `split_stats` helper in `service/storage_proxy.cc`) and use per-node labels. These include:
- `scylla_storage_proxy_coordinator_total_write_attempts_local_node` / `_remote_node`
- `scylla_storage_proxy_coordinator_background_writes` / `_reads`
- `scylla_storage_proxy_coordinator_foreground_writes` / `_reads`
- `scylla_storage_proxy_coordinator_completed_reads_local_node` / `_remote_node`
- `scylla_storage_proxy_coordinator_reads_local_node` / `_remote_node`
- `scylla_storage_proxy_coordinator_read_errors_remote_node`
- `scylla_storage_proxy_coordinator_write_errors_local_node`
- `scylla_storage_proxy_coordinator_read_repair_write_attempts_local_node` / `_remote_node`
- `scylla_storage_proxy_coordinator_current_throttled_writes` / `_base_writes`
- `scylla_storage_proxy_coordinator_background_replica_writes_failed_local_node` / `_remote_node`
- `scylla_storage_proxy_replica_view_update_backlog`

These are defined around `service/storage_proxy.cc:2900-2930` and `3240-3350` using the `split_stats` and `register_stats` patterns.

---

# Appendix B: How to Trace an Unknown Metric

When you encounter a metric in a Prometheus dump that is NOT in this mapping:

1. **Check if it's a derived metric:**
   - Ends with `_bucket`, `_count`, `_sum`, `_total` → histogram/counter sub-metric of the base name
   - Ends with `_ag` → recording rule (aggregation), look up the base metric
   - Starts with `scylla_ag_` → Prometheus recording rule, not in C++

2. **Search C++ source for the metric name:**
   ```bash
   cd ~/Development/scylladb
   grep -rn '"<metric_short_name>"' --include="*.cc" --include="*.hh" | grep -v test/
   ```
   Where `<metric_short_name>` is the name after the group prefix (e.g., for `scylla_cache_row_hits`, search `"row_hits"`).

3. **If not found, search for partial name:**
   ```bash
   grep -rn 'row_hits' --include="*.cc" --include="*.hh" | grep -v test/
   ```

4. **Look for the `add_group` call** near the metric registration to determine the Prometheus group prefix.

5. **If the metric is from a dynamic group name**, check these files:
   - `db/hints/manager.cc` — `hints_manager` / `hints_for_views_manager`
   - `service/tablet_allocator.cc` — `load_balancer`
   - `alternator/stats.cc` — `alternator_<OperationName>`
   - `db/commitlog/commitlog.cc` — `commitlog` / `schema_commitlog`

6. **If still not found in C++ code**, it may be from:
   - Scylla Manager Agent (`scylla_manager_agent_*`)
   - Scylla Manager Server (`scylla_manager_server_*`)
   - Prometheus recording rules (check `scylla-monitoring` stack repo)
   - Node exporter (`scylla_node_*`)

7. **Add the mapping** to this file and update the SCT instructions reference.
