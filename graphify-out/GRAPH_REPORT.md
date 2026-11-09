[START HERE: required working protocol](../docs/WORKING_PROTOCOL.md) · [Testing protocol](../Baymax-main/TESTING_PROTOCOL.md) · [Contribution route](../CONTRIBUTING.md)

[Feature log](../docs/features/FEATURE_LOG.md) · [Interactive graph](graph.html) · [Rendered feature log](FEATURE_LOG.html)

# Graph Report - Baymax-pi4  (2026-11-09)

## Corpus Check
- 225 files · ~198,502 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 47 file(s) not represented in the graph (top: .service 11, (none) 8, .cmd 7)

## Summary
- 2059 nodes · 3612 edges · 122 communities (89 shown, 33 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 110 edges (avg confidence: 0.86)
- Token usage: structural extraction uses no LLM; semantic usage was not reported by the host.

## Community Hubs (Navigation)
- Callable Tools
- Runtime and Setup
- Everyday Support
- Runtime and Setup
- Callable Tools
- Runtime and Setup
- Runtime and Setup
- Callable Tools
- Feature Documentation
- SD Card Builder
- Runtime and Setup
- Conversation and Audio
- Conversation and Audio
- Installation and Updates
- Callable Tools
- Runtime and Setup
- Pose and Inference
- Runtime and Setup
- Runtime and Setup
- Callable Tools
- Runtime and Setup
- Conversation and Audio
- Callable Tools
- Callable Tools
- Callable Tools
- Runtime and Setup
- Runtime and Setup
- Runtime and Setup
- Runtime and Setup
- Runtime and Setup
- Runtime and Setup
- Pose and Inference
- Runtime and Setup
- Feature Documentation
- Callable Tools
- Runtime and Setup
- Runtime and Setup
- Runtime and Setup
- Pose and Inference
- Pose and Inference
- Conversation and Audio
- Conversation and Audio
- Pose and Inference
- Callable Tools
- Callable Tools
- Callable Tools
- Runtime and Setup
- Physical Eyes
- Pose and Inference
- Pose and Inference
- Callable Tools
- Runtime and Setup
- Installation and Updates
- Physical Eyes
- Family Connections
- Family Connections
- Callable Tools
- Runtime and Setup
- Conversation and Audio
- Physical Eyes
- Pose and Inference
- Callable Tools
- Runtime and Setup
- Runtime and Setup
- Conversation and Audio
- Runtime and Setup
- Physical Eyes
- Callable Tools
- Everyday Support
- Family Connections
- Callable Tools
- Runtime and Setup
- Runtime and Setup
- SD Card Builder
- Conversation and Audio
- Callable Tools
- Pose and Inference
- Pose and Inference
- Callable Tools
- Callable Tools
- Installation and Updates
- Conversation and Audio
- Pose and Inference
- Callable Tools
- Callable Tools
- Runtime and Setup
- Conversation and Audio
- Physical Eyes
- Runtime and Setup
- Runtime and Setup
- Installation and Updates
- Callable Tools
- Physical Eyes
- Callable Tools
- Installation and Updates
- Installation and Updates
- Runtime and Setup
- Runtime and Setup
- SD Card Builder
- SD Card Builder
- Installation and Updates
- Runtime and Setup
- Runtime and Setup
- Installation and Updates
- Pose and Inference
- Callable Tools
- Runtime and Setup
- Runtime and Setup
- Runtime and Setup
- Runtime and Setup
- Installation and Updates
- Installation and Updates
- Runtime and Setup
- Runtime and Setup
- Runtime and Setup

## God Nodes (most connected - your core abstractions)
1. `START HERE: mandatory working protocol and authority` - 154 edges
2. `_run_gemini()` - 23 edges
3. `VoiceAnalyzer` - 22 edges
4. `OPi4 V1 organized feature log` - 22 edges
5. `Store` - 20 edges
6. `PublicSources` - 20 edges
7. `AddressGate` - 18 edges
8. `Player` - 18 edges
9. `record()` - 18 edges
10. `ConversationTiming` - 17 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `public_configuration()`  [INFERRED]
  devops/clickables/launch.py → Baymax-main/dev_settings.py
- `main()` --calls--> `public_configuration()`  [INFERRED]
  devops/opi4-flash/payload/ember-hardware.py → Baymax-main/dev_settings.py
- `main()` --calls--> `save_configuration()`  [INFERRED]
  devops/opi4-flash/payload/ember-hardware.py → Baymax-main/dev_settings.py
- `worker()` --calls--> `sample()`  [INFERRED]
  Baymax-main/runtime_monitor.py → devops/performance/check.py
- `main()` --calls--> `read_status()`  [INFERRED]
  devops/clickables/launch.py → Baymax-main/runtime_monitor.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Shared pose and fall-check-in flow** — baymax_main_features_toolkits_fall_detection_fall_toolkit, baymax_main_features_toolkits_fall_detection_shared_pose, baymax_main_features_pose_readme_vision_child, baymax_main_features_pose_readme_pose, baymax_main_features_toolkits_fall_detection_fall_checkin [EXTRACTED 1.00]
- **Family messages and everyday reminder sync** — baymax_main_features_toolkits_family_readme_family, baymax_main_features_toolkits_family_readme_app_sync, baymax_main_features_toolkits_family_readme_family_store, baymax_main_features_toolkits_everyday_readme_everyday, baymax_main_features_toolkits_family_readme_confirmed_replies [EXTRACTED 1.00]

## Communities (122 total, 33 thin omitted)

### Community 0 - "Callable Tools"
Cohesion: 0.05
Nodes (29): ConversationSources, discovery_enabled(), enabled_names(), extend_config(), handle_tool_call(), run_call(), Toolkit, Headlines (+21 more)

### Community 1 - "Runtime and Setup"
Cohesion: 0.05
Nodes (44): classify(), compile_report(), digest(), evidence(), load_inputs(), main(), review_template(), run_passes() (+36 more)

### Community 2 - "Everyday Support"
Cohesion: 0.07
Nodes (19): _at(), _candidates(), _clock(), _days_in_month(), describe(), device_timezone(), _ints(), local_start() (+11 more)

### Community 3 - "Runtime and Setup"
Cohesion: 0.07
Nodes (38): _alert_recipients(), auth_login(), auth_logout(), auth_me(), auth_resend(), auth_signup(), auth_verify(), camera_stream() (+30 more)

### Community 4 - "Callable Tools"
Cohesion: 0.06
Nodes (14): ensure_model(), EyeContact, FaceLandmarks, looking(), presence_enabled(), Proactive, remote_face(), _setting() (+6 more)

### Community 5 - "Runtime and Setup"
Cohesion: 0.04
Nodes (22): Mandatory Graphify-first agent instructions, migrate_data.sh script, test_hotspot.sh script, prepare_unit.sh script, fetch-debs.sh script, test_in_vm.sh script, Software, chamber simulation, hardware and release evidence, Authoritative repository, stable fixes and owner-selected channels (+14 more)

### Community 6 - "Runtime and Setup"
Cohesion: 0.07
Nodes (20): _build_transcript(), _collect_segments(), main(), _merge_segments(), _poll_jobs(), _report_failure(), _run_analysis(), _enqueue() (+12 more)

### Community 7 - "Callable Tools"
Cohesion: 0.05
Nodes (52): Fall package requirements, Optional strict address gate, Whole-frame PCM processing, Conversation and turn-taking, Existing Gemini Live session, Context compression and session resumption, Local speech and latency estimates, WebRTC echo cancellation and cleanup (+44 more)

### Community 8 - "Feature Documentation"
Cohesion: 0.06
Nodes (50): Independent Ember and Monitor user services, MVP startup and update guide, Opt-in release updater with rollback, On-board device settings, PortAudio / PipeWire / WirePlumber audio packages, Compiler, Python, Git and network system packages, XFCE / LightDM / Xorg desktop packages, Image system package list (+42 more)

### Community 9 - "SD Card Builder"
Cohesion: 0.09
Nodes (26): asset(), digest(), generate_credentials(), attach(), chroot_down(), chroot_up(), detach(), build_linux.sh script (+18 more)

### Community 10 - "Runtime and Setup"
Cohesion: 0.08
Nodes (25): _draw_angle_graph(), _draw_annotated(), _draw_fall_alert(), _draw_hud(), _draw_skeleton(), _draw_trunk_line(), _ensure_pose_model(), _fall_detection_thread() (+17 more)

### Community 11 - "Conversation and Audio"
Cohesion: 0.09
Nodes (5): AddressGate, follow_up_seconds(), is_speech(), names_ember(), _WatchedSession

### Community 12 - "Conversation and Audio"
Cohesion: 0.10
Nodes (9): ResidualEcho, create(), enabled(), extend_config(), fan_filter_hz(), FanFilter, InputEnhancer, mute_during_reply() (+1 more)

### Community 13 - "Installation and Updates"
Cohesion: 0.13
Nodes (23): block_ssid(), client_mode(), hostapd_config(), hotspot_name(), join_saved(), log(), main(), network_block() (+15 more)

### Community 14 - "Callable Tools"
Cohesion: 0.11
Nodes (14): _clean_query(), _covers_query(), download(), fetch_book(), _ia_search(), _keep_only(), _lucene_terms(), _normalise_title() (+6 more)

### Community 15 - "Runtime and Setup"
Cohesion: 0.08
Nodes (15): connection_lost(), hold_for_answer(), _abandon_reply(), _abort_connection(), _encode_video_frame(), fall_alert_monitor(), _flush_playback(), _leaves() (+7 more)

### Community 16 - "Pose and Inference"
Cohesion: 0.15
Nodes (18): compare(), fall_detector(), _jsonable(), main(), pct(), _print_clip(), _print_summary(), _rate() (+10 more)

### Community 17 - "Runtime and Setup"
Cohesion: 0.12
Nodes (24): Editing and validation protocol, Draft PR and software-lead review before merge/deployment, Preserve user edits, import paths and data flows, Board-specific live and fresh-card validation, Orange Pi scope: Pallas-Robotics/Baymax focused branch, Keep credentials, recordings, models and private images out of Git and graphs, Graphify AST extraction plus reviewed semantic document snapshot, Graphify feature map guide (+16 more)

### Community 18 - "Runtime and Setup"
Cohesion: 0.16
Nodes (17): transcript_overlap(), _append_playback(), receive_audio(), play_reply_audio(), show_reply_text(), _transcript_add(), consume_stop_request(), emit() (+9 more)

### Community 19 - "Callable Tools"
Cohesion: 0.13
Nodes (8): CheckIns, enabled(), _last_conversation(), _last_heard(), _path(), _setting(), window(), windows()

### Community 20 - "Runtime and Setup"
Cohesion: 0.13
Nodes (22): AI core and webapp container composition, Experimental Docker deployment, Experimental core/webapp containers, Host boot and optional Wi-Fi hotspot tooling, Synthetic Gemini-in-the-loop evaluation, MediaPipe fall detection setup, Integrated v10 MVP installation, Orange Pi board-specific Debian setup (+14 more)

### Community 23 - "Callable Tools"
Cohesion: 0.14
Nodes (4): coordinates(), fetch_json(), Location, Weather

### Community 24 - "Callable Tools"
Cohesion: 0.14
Nodes (5): complete_sentence(), config(), drain(), model(), Searcher

### Community 26 - "Runtime and Setup"
Cohesion: 0.16
Nodes (7): public_configuration(), read_configuration(), save_configuration(), audio_catalog(), Handler, LocalServer, main()

### Community 27 - "Runtime and Setup"
Cohesion: 0.16
Nodes (21): Competent-speaker review of every turn, Full candidate matrix and explicit valid_audio_languages output, Switch from native language to English, Human review bound to exact model/config/input/transcript/audio hashes, Multilingual evaluation and validated-language guide, Mixed Hindi-English scripted scenario, Follow-up in the same language, Scripted native-language question (+13 more)

### Community 28 - "Runtime and Setup"
Cohesion: 0.19
Nodes (9): enabled(), configured_models(), _listed(), PreflightError, PreflightUnavailable, validate_key(), main(), CredentialError (+1 more)

### Community 29 - "Runtime and Setup"
Cohesion: 0.19
Nodes (5): log(), main(), read_env(), _requirements(), Updater

### Community 30 - "Runtime and Setup"
Cohesion: 0.21
Nodes (11): test_device(), camera_catalog(), camera_devices(), check_camera_permission(), _framework(), resolve_camera(), camera_candidates(), configure_audio_backend() (+3 more)

### Community 31 - "Pose and Inference"
Cohesion: 0.12
Nodes (5): ChildPose, create_pose_backend(), pipeline_confidences(), _warn(), weights_warning()

### Community 32 - "Runtime and Setup"
Cohesion: 0.16
Nodes (20): Every feature PR records off/on/combined performance evidence, Feature active/on comparison, Explicit added-p95 speech-end-to-playback budget, Aggregate JSON performance reports under .local-review, Baseline/off with the same conversation workload, Separate explicit-PID cold-start collection, Normal combined-feature workload, Matched board, build, devices, model, network, duration and utterances (+12 more)

### Community 33 - "Feature Documentation"
Cohesion: 0.14
Nodes (20): Full candidate matrix: text-mode evidence, no validated audio simulations, Punctuation-only Spanish and empty/incomplete English input transcripts, Pinned model/config-specific simulation evidence, System CPU baseline 22.69/24.97%, tests 25.8/27.97% mean/peak, Orange Pi language simulation results — 2026-11-06, Text-turn-to-first-audio: median 1.48 s, p95 2.62 s, max 4.58 s, Orange Pi 4 Pro: ARM64, 8 CPU cores, 3903.7 MiB usable RAM, Hindi speech pilot failed content/tool behavior while text comparison passed (+12 more)

### Community 34 - "Callable Tools"
Cohesion: 0.18
Nodes (10): enabled(), execute(), extend_config(), handle_tool_call(), _keep_warm(), prewarm(), search_enabled(), enabled() (+2 more)

### Community 35 - "Runtime and Setup"
Cohesion: 0.11
Nodes (10): _format_transcript(), _generate_summary(), _keep_transcript_unsaved(), _mark_transcript_saved(), _memory_save_due(), _memory_saver_thread(), _memory_store(), _save_memories_on_stop() (+2 more)

### Community 36 - "Runtime and Setup"
Cohesion: 0.17
Nodes (10): feature_html(), flush(), flush_paragraph(), inline(), main(), portable_diagnostic(), source_group(), check() (+2 more)

### Community 37 - "Runtime and Setup"
Cohesion: 0.17
Nodes (8): _draw_angle_graph(), _draw_fall_alert(), _draw_hud(), _draw_skeleton(), _draw_trunk_line(), _ensure_model(), run(), _text()

### Community 38 - "Pose and Inference"
Cohesion: 0.15
Nodes (7): default_mediapipe_options(), PipelineBackend, frames_from(), main(), run(), summary(), Timed

### Community 39 - "Pose and Inference"
Cohesion: 0.17
Nodes (7): _by_size(), _finite(), heatmap_hwc(), OnnxEngine, split_detector(), split_landmarks(), port()

### Community 40 - "Conversation and Audio"
Cohesion: 0.14
Nodes (7): adapt(), _close(), configured(), generation(), takes_quiet_notes(), unavailable(), spoken_config()

### Community 41 - "Conversation and Audio"
Cohesion: 0.17
Nodes (6): enabled(), execute(), extend_config(), _level(), _path(), VoiceVolume

### Community 42 - "Pose and Inference"
Cohesion: 0.16
Nodes (9): _open_onnx(), check_passed(), check_section(), load_manifest(), model_dir(), ModelError, sha256(), task_matches_pinned() (+1 more)

### Community 43 - "Callable Tools"
Cohesion: 0.18
Nodes (3): enabled(), FallWorker, _record()

### Community 44 - "Callable Tools"
Cohesion: 0.14
Nodes (8): execute(), find_stations(), _miniaudio_source(), open_stream(), playable(), public_url(), stream_station(), UnsupportedStream

### Community 46 - "Runtime and Setup"
Cohesion: 0.17
Nodes (4): FallDetector, main(), open_camera(), say()

### Community 47 - "Physical Eyes"
Cohesion: 0.16
Nodes (7): clear_failures(), expected_sensors(), eyes_session(), sensors(), failure_face(), lost_sensor(), _mic_reports()

### Community 48 - "Pose and Inference"
Cohesion: 0.12
Nodes (4): _Backend, FallbackBackend, MediaPipeCpuBackend, loading_model()

### Community 49 - "Pose and Inference"
Cohesion: 0.17
Nodes (7): associate(), decode_landmarks(), project(), _rect_iou(), refine_from_heatmap(), _sigmoid(), warp()

### Community 50 - "Callable Tools"
Cohesion: 0.14
Nodes (6): attach(), _boost(), execute(), register(), session_task(), _volume()

### Community 51 - "Runtime and Setup"
Cohesion: 0.12
Nodes (7): between_turns(), _between_turns(), _memory_context(), _recall_memories(), _RestartAudio, _retrieve_memories(), _SessionHandover

### Community 52 - "Installation and Updates"
Cohesion: 0.18
Nodes (8): _device_setting(), home(), page_not_found(), profile_exists(), setup(), status(), switch_network(), uplink_iface()

### Community 53 - "Physical Eyes"
Cohesion: 0.28
Nodes (5): LedControl, crashed(), main(), settings(), show()

### Community 54 - "Family Connections"
Cohesion: 0.17
Nodes (7): deliver_messages(), enabled(), execute(), profile_section(), refresh_profile(), register(), session_task()

### Community 56 - "Callable Tools"
Cohesion: 0.20
Nodes (8): _ask_turn(), _default_searcher(), execute(), first_sentence(), first_sentence_end(), refused(), _sources(), text_turn()

### Community 57 - "Runtime and Setup"
Cohesion: 0.29
Nodes (13): cpu_ticks(), main(), monitor(), process_tree(), read(), report(), sample(), sensors() (+5 more)

### Community 58 - "Conversation and Audio"
Cohesion: 0.16
Nodes (7): extend_config(), handle_received_at(), not_tried(), on_server_message(), remember(), _tokens(), _handover_due()

### Community 59 - "Physical Eyes"
Cohesion: 0.23
Nodes (6): attach(), AutoEyes, cue(), medical_alert(), reply_cue(), requested()

### Community 60 - "Pose and Inference"
Cohesion: 0.18
Nodes (6): decode_detections(), Detection, detector_roi(), _iou(), remove_letterbox(), weighted_nms()

### Community 62 - "Runtime and Setup"
Cohesion: 0.26
Nodes (9): use_performance_cpus(), configuration_ready(), configure_once(), main(), pid_alive(), runtime_lock(), runtime_running(), _stop() (+1 more)

### Community 63 - "Runtime and Setup"
Cohesion: 0.17
Nodes (6): _download_memory_model(), _load_memory_embedder(), _memory_model_to_download(), download_model(), missing_packages(), model_present()

### Community 65 - "Runtime and Setup"
Cohesion: 0.23
Nodes (4): enabled(), apply(), instructions(), voice()

### Community 67 - "Callable Tools"
Cohesion: 0.23
Nodes (7): cpu_factory(), download_model(), heard(), model_path(), _pair(), _vosk_model(), _vosk_recognizer()

### Community 68 - "Everyday Support"
Cohesion: 0.27
Nodes (8): available_to_speak(), enabled(), execute(), notify_due(), _playback_active(), register(), session_task(), start()

### Community 71 - "Runtime and Setup"
Cohesion: 0.18
Nodes (6): _build_config(), _fire_initiation(), _initiation_memory_hint(), initiation_monitor(), _newest_memories(), _safe_to_initiate()

### Community 72 - "Runtime and Setup"
Cohesion: 0.36
Nodes (9): ensure_environment(), environment_python(), fingerprint(), install_shortcuts(), installation_lock(), main(), requirements_file(), run_checked() (+1 more)

### Community 73 - "SD Card Builder"
Cohesion: 0.24
Nodes (6): anydesk_id(), command(), duration(), Handler, progress(), status()

### Community 74 - "Conversation and Audio"
Cohesion: 0.22
Nodes (5): apply(), enabled(), heard(), _listener(), register()

### Community 75 - "Callable Tools"
Cohesion: 0.24
Nodes (3): execute(), Listen, record()

### Community 76 - "Pose and Inference"
Cohesion: 0.20
Nodes (4): alignment_rect(), normalize_radians(), Rect, transform_rect()

### Community 79 - "Callable Tools"
Cohesion: 0.22
Nodes (4): CpuPose, _detector_factory(), ensure_model(), remote_pose()

### Community 80 - "Installation and Updates"
Cohesion: 0.38
Nodes (9): cfg(), pactl_user(), run_gemini_with_retry(), set_audio_levels(), startup.sh script, start_containers(), start_portal_supervised(), start_robot() (+1 more)

### Community 82 - "Pose and Inference"
Cohesion: 0.22
Nodes (3): LandmarkSmoother, PosePipeline, ssd_anchors()

### Community 85 - "Runtime and Setup"
Cohesion: 0.33
Nodes (6): collect_suites(), local_settings_ignored(), __init__(), main(), render_report(), run_sections()

### Community 88 - "Runtime and Setup"
Cohesion: 0.25
Nodes (4): arm_linux(), latest_frames_only(), main(), runtime_script()

### Community 89 - "Runtime and Setup"
Cohesion: 0.22
Nodes (3): _boot_status(), _notify_webapp(), _TurnTranscript

### Community 90 - "Installation and Updates"
Cohesion: 0.50
Nodes (7): cfg(), compose(), healthy(), image_id(), log(), ember-update.sh script, wait_healthy()

### Community 91 - "Callable Tools"
Cohesion: 0.32
Nodes (4): main(), recognizer(), response(), speech()

### Community 92 - "Physical Eyes"
Cohesion: 0.33
Nodes (3): enabled(), extend_config(), silent()

### Community 93 - "Callable Tools"
Cohesion: 0.33
Nodes (3): _cause(), spoken_model(), _tell()

### Community 94 - "Installation and Updates"
Cohesion: 0.53
Nodes (4): closure(), imported_top_level_modules(), main(), root_distributions()

### Community 95 - "Installation and Updates"
Cohesion: 0.60
Nodes (5): cfg(), die(), run(), provision.sh script, step()

### Community 96 - "Runtime and Setup"
Cohesion: 0.53
Nodes (4): desktop_quote(), install(), main(), systemd_quote()

### Community 97 - "Runtime and Setup"
Cohesion: 0.53
Nodes (4): display_connected(), main(), open_monitor(), serve()

### Community 98 - "SD Card Builder"
Cohesion: 0.60
Nodes (4): load(), main(), save(), validate()

### Community 99 - "SD Card Builder"
Cohesion: 0.53
Nodes (4): audio_device(), camera_device(), identity(), main()

### Community 101 - "Installation and Updates"
Cohesion: 0.60
Nodes (3): die(), make_usb.sh script, step()

### Community 102 - "Runtime and Setup"
Cohesion: 0.40
Nodes (3): _audio_writer_thread(), _open_new_segment(), _prune_day_utterance()

### Community 103 - "Runtime and Setup"
Cohesion: 0.67
Nodes (4): Development and review protocol, Offline, live and lead-review evidence, Software-lead approval before merge/deployment, Offline core and toolkit review gate

### Community 104 - "Installation and Updates"
Cohesion: 0.83
Nodes (3): answer(), erase-confirm.sh script, stop_here()

### Community 107 - "Runtime and Setup"
Cohesion: 0.50
Nodes (4): macOS simulation and hardware verification, Simulated macOS device contract tests, Intel macOS dependency profile, Windows pinned dependency profile

### Community 112 - "Runtime and Setup"
Cohesion: 0.67
Nodes (3): Shared persona [LANGUAGE] adaptation guidance, Source integration is separate from robot deployment, Identical tested language instruction integrated in review-branch source

## Knowledge Gaps
- **88 isolated node(s):** `Development and review protocol`, `Desktop setup and device selection`, `Intel macOS dependency profile`, `Shared Orange Pi ARM64 dependency profile`, `Desktop dependency profile` (+83 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 725 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `START HERE: mandatory working protocol and authority` connect `Runtime and Setup` to `Callable Tools`, `Runtime and Setup`, `Everyday Support`, `Runtime and Setup`, `Callable Tools`, `Runtime and Setup`, `SD Card Builder`, `Runtime and Setup`, `Conversation and Audio`, `Conversation and Audio`, `Installation and Updates`, `Callable Tools`, `Pose and Inference`, `Runtime and Setup`, `Callable Tools`, `Conversation and Audio`, `Callable Tools`, `Runtime and Setup`, `Runtime and Setup`, `Runtime and Setup`, `Runtime and Setup`, `Pose and Inference`, `Callable Tools`, `Runtime and Setup`, `Runtime and Setup`, `Pose and Inference`, `Pose and Inference`, `Conversation and Audio`, `Conversation and Audio`, `Pose and Inference`, `Callable Tools`, `Runtime and Setup`, `Physical Eyes`, `Pose and Inference`, `Callable Tools`, `Installation and Updates`, `Physical Eyes`, `Family Connections`, `Callable Tools`, `Runtime and Setup`, `Conversation and Audio`, `Physical Eyes`, `Runtime and Setup`, `Runtime and Setup`, `Runtime and Setup`, `Callable Tools`, `Everyday Support`, `Family Connections`, `Callable Tools`, `Runtime and Setup`, `SD Card Builder`, `Conversation and Audio`, `Callable Tools`, `Installation and Updates`, `Runtime and Setup`, `Conversation and Audio`, `Physical Eyes`, `Runtime and Setup`, `Installation and Updates`, `Callable Tools`, `Physical Eyes`, `Installation and Updates`, `Installation and Updates`, `Runtime and Setup`, `Runtime and Setup`, `SD Card Builder`, `SD Card Builder`, `SD Card Builder`, `Installation and Updates`, `Installation and Updates`, `SD Card Builder`, `Runtime and Setup`, `SD Card Builder`, `Installation and Updates`, `Runtime and Setup`, `Media and Activities`, `Media and Activities`, `Runtime and Setup`?**
  _High betweenness centrality (0.612) - this node is a cross-community bridge._
- **What connects `Development and review protocol`, `Desktop setup and device selection`, `Intel macOS dependency profile` to the rest of the system?**
  _88 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Callable Tools` be split into smaller, more focused modules?**
  _Cohesion score 0.052184769038701624 - nodes in this community are weakly interconnected._
- **Why does `FamilyStore` connect `Family Connections` to `Family Connections`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Should `Runtime and Setup` be split into smaller, more focused modules?**
  _Cohesion score 0.05285592497868713 - nodes in this community are weakly interconnected._
- **Why does `Store` connect `Everyday Support` to `Everyday Support`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Should `Everyday Support` be split into smaller, more focused modules?**
  _Cohesion score 0.07080200501253132 - nodes in this community are weakly interconnected._
## Scope and integrity

The graph is documentation, not a hardware certification. Local paths are repository-relative. 931 unresolved/external references (including standard-library imports) are omitted from this project-only view and retained in `UNRESOLVED_REFERENCES.json`; these are not claimed to be missing runtime dependencies. Parallel relationships can collapse in the native undirected view; raw semantic evidence remains in `docs/features/semantic_graph.json`.

Project-view health:

```json
{
  "node_count": 2060,
  "unverified_node_count": 0,
  "raw_edge_count": 3685,
  "non_object_edges": 0,
  "missing_endpoint_edges": 0,
  "dangling_endpoint_edges": 0,
  "external_reference_edges": 0,
  "self_loop_edges": 7,
  "valid_candidate_edges": 3685,
  "exact_duplicate_edges": 0,
  "directed_unique_endpoint_pairs": 3619,
  "directed_same_endpoint_collapsed_edges": 66,
  "undirected_unique_endpoint_pairs": 3613,
  "undirected_same_endpoint_collapsed_edges": 72,
  "same_endpoint_group_count": 65,
  "relation_variant_groups": 63,
  "source_file_variant_groups": 0,
  "source_location_variant_groups": 2,
  "context_variant_groups": 0,
  "post_build_graph_type": "Graph",
  "post_build_node_count": 2059,
  "post_build_edge_count": 3612,
  "post_build_error": "",
  "producer_suppression": {
    "path": ".local-review/graphify-venv/Lib/site-packages/graphify/extract.py",
    "total_sites": 12,
    "sites": [
      {
        "line": 1789,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids = {n[\"id\"] for n in nodes}"
      },
      {
        "line": 2353,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids = {n[\"id\"] for n in nodes}"
      },
      {
        "line": 2355,
        "name": "seen_doc_refs",
        "tuple_arity": 0,
        "sample": "seen_doc_refs: set[str] = set()"
      },
      {
        "line": 3022,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = {n[\"id\"] for n in nodes}"
      },
      {
        "line": 3169,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids = {n.get(\"id\") for n in nodes}"
      },
      {
        "line": 4179,
        "name": "seen_keys",
        "tuple_arity": 0,
        "sample": "seen_keys: set[tuple] = set()"
      },
      {
        "line": 4365,
        "name": "seen_keys",
        "tuple_arity": 0,
        "sample": "seen_keys: set[tuple] = set()"
      },
      {
        "line": 7608,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = set()"
      },
      {
        "line": 7716,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = set()"
      },
      {
        "line": 7795,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = set()"
      },
      {
        "line": 8310,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = set()"
      },
      {
        "line": 8311,
        "name": "seen_edges",
        "tuple_arity": 4,
        "sample": "seen_edges: set[tuple[str, str, str, str | None]] = set()"
      }
    ],
    "error": ""
  },
  "examples": [
    {
      "source": "baymax_main_features_vision_process_main",
      "target": "baymax_main_features_vision_process_main_reply",
      "edge_count": 3,
      "relations": [
        "calls",
        "contains",
        "indirect_call"
      ],
      "source_files": [
        "Baymax-main/features/vision_process.py"
      ],
      "source_locations": [
        "L165",
        "L168",
        "L174"
      ],
      "contexts": [
        "",
        "assignment",
        "call"
      ]
    },
    {
      "source": "baymax_main_baymax_agent",
      "target": "baymax_main_baymax_cloud",
      "edge_count": 2,
      "relations": [
        "imports",
        "imports_from"
      ],
      "source_files": [
        "Baymax-main/baymax_agent.py"
      ],
      "source_locations": [
        "L26",
        "L27"
      ],
      "contexts": [
        "import"
      ]
    },
    {
      "source": "baymax_main_baymax_app_login_required",
      "target": "baymax_main_baymax_app_login_required_decorated",
      "edge_count": 2,
      "relations": [
        "contains",
        "indirect_call"
      ],
      "source_files": [
        "Baymax-main/baymax_app.py"
      ],
      "source_locations": [
        "L142",
        "L146"
      ],
      "contexts": [
        "",
        "return"
      ]
    },
    {
      "source": "baymax_main_baymax_app_send_verification_email",
      "target": "baymax_main_baymax_app_send_verification_email_send",
      "edge_count": 2,
      "relations": [
        "contains",
        "indirect_call"
      ],
      "source_files": [
        "Baymax-main/baymax_app.py"
      ],
      "source_locations": [
        "L185",
        "L204"
      ],
      "contexts": [
        "",
        "argument"
      ]
    },
    {
      "source": "baymax_main_baymax_app_camera_stream",
      "target": "baymax_main_baymax_app_camera_stream_relay",
      "edge_count": 2,
      "relations": [
        "calls",
        "contains"
      ],
      "source_files": [
        "Baymax-main/baymax_app.py"
      ],
      "source_locations": [
        "L440",
        "L450"
      ],
      "contexts": [
        "",
        "call"
      ]
    }
  ]
}
```

Raw extraction health before scope filtering:

```json
{
  "node_count": 2060,
  "unverified_node_count": 0,
  "raw_edge_count": 4616,
  "non_object_edges": 0,
  "missing_endpoint_edges": 0,
  "dangling_endpoint_edges": 931,
  "external_reference_edges": 0,
  "self_loop_edges": 7,
  "valid_candidate_edges": 3685,
  "exact_duplicate_edges": 0,
  "directed_unique_endpoint_pairs": 3619,
  "directed_same_endpoint_collapsed_edges": 66,
  "undirected_unique_endpoint_pairs": 3613,
  "undirected_same_endpoint_collapsed_edges": 72,
  "same_endpoint_group_count": 65,
  "relation_variant_groups": 63,
  "source_file_variant_groups": 0,
  "source_location_variant_groups": 2,
  "context_variant_groups": 0,
  "post_build_graph_type": "Graph",
  "post_build_node_count": 2143,
  "post_build_edge_count": 4542,
  "post_build_error": "",
  "producer_suppression": {
    "path": ".local-review/graphify-venv/Lib/site-packages/graphify/extract.py",
    "total_sites": 12,
    "sites": [
      {
        "line": 1789,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids = {n[\"id\"] for n in nodes}"
      },
      {
        "line": 2353,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids = {n[\"id\"] for n in nodes}"
      },
      {
        "line": 2355,
        "name": "seen_doc_refs",
        "tuple_arity": 0,
        "sample": "seen_doc_refs: set[str] = set()"
      },
      {
        "line": 3022,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = {n[\"id\"] for n in nodes}"
      },
      {
        "line": 3169,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids = {n.get(\"id\") for n in nodes}"
      },
      {
        "line": 4179,
        "name": "seen_keys",
        "tuple_arity": 0,
        "sample": "seen_keys: set[tuple] = set()"
      },
      {
        "line": 4365,
        "name": "seen_keys",
        "tuple_arity": 0,
        "sample": "seen_keys: set[tuple] = set()"
      },
      {
        "line": 7608,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = set()"
      },
      {
        "line": 7716,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = set()"
      },
      {
        "line": 7795,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = set()"
      },
      {
        "line": 8310,
        "name": "seen_ids",
        "tuple_arity": 0,
        "sample": "seen_ids: set[str] = set()"
      },
      {
        "line": 8311,
        "name": "seen_edges",
        "tuple_arity": 4,
        "sample": "seen_edges: set[tuple[str, str, str, str | None]] = set()"
      }
    ],
    "error": ""
  },
  "examples": [
    {
      "source": "baymax_main_features_vision_process_main",
      "target": "baymax_main_features_vision_process_main_reply",
      "edge_count": 3,
      "relations": [
        "calls",
        "contains",
        "indirect_call"
      ],
      "source_files": [
        "Baymax-main/features/vision_process.py"
      ],
      "source_locations": [
        "L165",
        "L168",
        "L174"
      ],
      "contexts": [
        "",
        "assignment",
        "call"
      ]
    },
    {
      "source": "baymax_main_baymax_agent",
      "target": "baymax_main_baymax_cloud",
      "edge_count": 2,
      "relations": [
        "imports",
        "imports_from"
      ],
      "source_files": [
        "Baymax-main/baymax_agent.py"
      ],
      "source_locations": [
        "L26",
        "L27"
      ],
      "contexts": [
        "import"
      ]
    },
    {
      "source": "baymax_main_baymax_app_login_required",
      "target": "baymax_main_baymax_app_login_required_decorated",
      "edge_count": 2,
      "relations": [
        "contains",
        "indirect_call"
      ],
      "source_files": [
        "Baymax-main/baymax_app.py"
      ],
      "source_locations": [
        "L142",
        "L146"
      ],
      "contexts": [
        "",
        "return"
      ]
    },
    {
      "source": "baymax_main_baymax_app_send_verification_email",
      "target": "baymax_main_baymax_app_send_verification_email_send",
      "edge_count": 2,
      "relations": [
        "contains",
        "indirect_call"
      ],
      "source_files": [
        "Baymax-main/baymax_app.py"
      ],
      "source_locations": [
        "L185",
        "L204"
      ],
      "contexts": [
        "",
        "argument"
      ]
    },
    {
      "source": "baymax_main_baymax_app_camera_stream",
      "target": "baymax_main_baymax_app_camera_stream_relay",
      "edge_count": 2,
      "relations": [
        "calls",
        "contains"
      ],
      "source_files": [
        "Baymax-main/baymax_app.py"
      ],
      "source_locations": [
        "L440",
        "L450"
      ],
      "contexts": [
        "",
        "call"
      ]
    }
  ]
}
```
