# OPI4 CPU pose validation

Software checks verify CPU selection, timestamps, child isolation, watchdog/restart
behavior and pipeline math. Stale accelerator settings must not load a vendor
runtime or change affinity/GIL settings.

The configured target is 10 FPS with MediaPipe lite by default. Actual A733
throughput, frame age, CPU/RAM, thermals and simultaneous speech/pose latency
remain measurements to perform on OPI4. Chamber replay and controlled physical
checks remain pending. Record revision, board/OS/peripherals, settings,
expected/actual outputs, false results, stalls and recovery. Do not ask a person
to perform an unsafe fall. Algorithm/local speech results do not establish
medical safety or contact anyone automatically.

Use the root pose suite and application release gate for software evidence;
follow the testing protocol and performance sampler for target evidence.
OPI5 results are not OPI4 evidence.
