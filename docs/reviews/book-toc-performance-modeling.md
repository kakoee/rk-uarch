# *Performance Modeling of Computer Systems*: Table of Contents

Transcribed from eight photos of TOC pages vii–xxi, which cover the complete table of contents.

**Coverage notes**
- **Page numbers:** they sit next to the curved spine, so some are cut off in the photos. `3xx?` means only the first digit or two were legible. `(?)` means the number is my best reading of a partly visible digit. I rebuilt each number's row by counting entries against numbers on every page, because the curve pushes the dot leaders off their rows.
- **Recurring scaffolding:** every *Simulation* chapter (9, 10, 12, 13, 15, 17) uses the same template: Tool Setup → Simulator Configuration → Experimental Design (Workload Selection / Key Metrics / Experimental Process / Companion Repository Setup) → a set of experiments, each with "The Experiment" and "Results and Explanation" → Summary / Review Questions / Exercises. That template is itself a methodology concept, and the review checks it too.

---

## Front matter
- About the Author ... xxiii
- About the Technical Reviewer ... xxv
- Acknowledgments ... xxvii
- Introduction ... xxix

---

## Part I: Foundations ... 1

## Chapter 1: Introduction to Performance Modeling ... 3
- Prerequisites ... 4
- 1.1 The Role of Performance Modeling ... 4
  - 1.1.1 Why We Cannot Just Build and Test ... 5
  - 1.1.2 Use Cases for Performance Modeling ... 6
  - 1.1.3 A Brief Note on History ... 7
- 1.2 The Spectrum of Modeling Approaches ... 7
  - 1.2.1 Analytical Models ... 7
  - 1.2.2 Transaction Level Models (TLM) ... 8
  - 1.2.3 Cycle-Accurate Simulation ... 9
- 1.3 Accuracy, Speed, and Flexibility Tradeoffs ... 10
  - 1.3.1 The Fundamental Tradeoffs ... 10
  - 1.3.2 Accuracy vs. Speed ... 11
  - 1.3.3 Flexibility vs. Accuracy ... 11
  - 1.3.4 Fit for Purpose ... 11
  - 1.3.5 Case Study: Prefetcher Evaluation ... 12
- 1.4 Open-Source Simulation Tools ... 14
  - 1.4.1 The Toolkit ... 15
  - 1.4.2 ChampSim ... 15
  - 1.4.3 gem5 ... 16
  - 1.4.4 Accel-Sim ... 16
  - 1.4.5 SCALE-Sim ... 17
  - 1.4.6 Supporting Tools ... 18
- 1.5 Summary ... 18
- Review Questions ... 19

## Chapter 2: Architecture Through the Modeler's Lens ... 21
- 2.1 The Compute-Memory Balance ... 22
  - 2.1.1 The Fundamental Relationship ... 22
  - 2.1.2 Operational Intensity ... 23
  - 2.1.3 Compute Resources ... 24
  - 2.1.4 Memory Resources ... 25
  - 2.1.5 Cross-Platform Comparison ... 26
- 2.2 Bandwidth and Latency ... 27
  - 2.2.1 Bandwidth Constraints ... 27
  - 2.2.2 Latency Constraints ... 28
- 2.3 Parallelism ... 30
  - 2.3.1 Instruction-Level Parallelism (ILP) ... 30
  - 2.3.2 Thread-Level Parallelism (TLP) ... 32
  - 2.3.3 Data-Level Parallelism (DLP) ... 33
  - 2.3.4 Platform Comparison ... 34
- 2.4 Summary ... 36
- Review Questions ... 37
- Further Reading ... 37

## Chapter 3: Workload Selection and Experimental Validity ... 39
- 3.1 The Generalization Problem ... 40
  - 3.1.1 From Sample to Population ... 40
  - 3.1.2 Representativeness Failures ... 41
  - 3.1.3 Claims and Applicability ... 43
  - 3.1.4 Evidence Requirements by Claim Strength ... 44
  - 3.1.5 Working Backward from Claims ... 44
  - 3.1.6 Example: Cache Replacement Study ... 45
- 3.2 Workload Characterization ... 46
  - 3.2.1 Purpose of Workload Characterization ... 46
  - 3.2.2 Using Hardware Performance Counters ... 47
  - 3.2.3 Characterizing Operational Intensity ... 48
  - 3.2.4 Characterizing Memory Access Patterns ... 49
  - 3.2.5 Characterizing with Clustering and Visualization ... 50
- 3.3 Standard Benchmark Suites ... 51
  - 3.3.1 CPU Benchmarks ... 51
  - 3.3.2 GPU and Accelerator Workloads ... 52
  - 3.3.3 Server and Cloud Workloads ... 53
  - 3.3.4 Limitations ... 54
- 3.4 Practical Aspects of Workload Selection ... 55
  - 3.4.1 Common Workload Sources ... 55
  - 3.4.2 Selection in Practice ... 56
  - 3.4.3 Pragmatic Considerations ... 56
- 3.5 Summary ... 57
- Review Questions ... 58
- Further Reading ... 58

## Chapter 4: Simulator in a Nutshell ... 61
- 4.1 From Trace to Statistics ... 61
- 4.2 Path of a Memory Access ... 63
- Further Reading ... 66

## Part II: The Simulation Pipeline ... 67

## Chapter 5: Trace Collection and Management ... 69
- Tool Setup ... 70
- 5.1 What Traces Capture ... 72
  - 5.1.1 Trace Contents ... 72
  - 5.1.2 What Traces Omit ... 73
  - 5.1.3 Trace Formats ... 74
- 5.2 Choosing a Collection Approach ... 76
  - 5.2.1 When to Use Which Approach ... 77
- 5.3 Dynamic Binary Instrumentation Using Pin ... 79
  - 5.3.1 How Pin Works ... 79
  - 5.3.2 Starting with Pin ... 80
  - 5.3.3 Pintools ... 80
- 5.4 Generating ChampSim Traces ... 81
  - 5.4.1 Building the Tracer ... 81
  - 5.4.2 Collecting a Trace ... 81
  - 5.4.3 Trace Compression ... 83
- 5.5 Trace Validation ... 83
  - 5.5.1 Sanity Checks ... 83
  - 5.5.2 Instruction Mix Analysis ... 84
  - 5.5.3 Hardware Counter Validation ... 85
  - 5.5.4 End-to-End Validation ... 86
- 5.6 Trace Organization and Management ... 86
  - 5.6.1 Naming Conventions ... 87
  - 5.6.2 Metadata Documentation ... 87
  - 5.6.3 Storage Considerations ... 88
  - 5.6.4 Version Control and Artifact Management ... 88
- 5.7 Trace Fidelity Limitations ... 89
  - 5.7.1 The User-Kernel Gap ... 90
  - 5.7.2 Missing Wrong-Path Execution ... 90
- 5.8 Summary ... 91
- Review Questions ... 92
- Exercises ... 93
- Further Reading ... 93

## Chapter 6: Sampling and Simulation Efficiency ... 95
- 6.1 Why Sampling Matters ... 96
  - 6.1.1 Application Behavior ... 96
  - 6.1.2 Phase Behavior in Steady-State ... 97
- 6.2 The SimPoint Methodology ... 98
  - 6.2.1 Basic Block Vectors ... 98
  - 6.2.2 Clustering and Representative Intervals ... 99
  - 6.2.3 SimPoint in the Workflow ... 100
  - 6.2.4 From SimPoint to Traces ... 103
  - 6.2.5 Weighted Results ... 105
  - 6.2.6 Other Sampling Approaches ... 106
- 6.3 Warm-Up Strategies ... 108
  - 6.3.1 Functional Warming ... 108
  - 6.3.2 Checkpointing ... 109
  - 6.3.3 Warming Length Guidelines ... 109
- 6.4 Common Pitfalls ... 110
  - 6.4.1 Insufficient Warming ... 110
  - 6.4.2 Short Intervals ... 110
  - 6.4.3 Ignoring Low-Weight Points ... 111
  - 6.4.4 Unweighted Averaging ... 111
- 6.5 Summary ... 111
- Review Questions ... 112
- Exercises ... 113
- Further Reading ... 113

## Chapter 7: Understanding Simulation Output ... 115
- 7.1 Structure of ChampSim Output ... 116
  - 7.1.1 The Output Report ... 116
  - 7.1.2 Output and the Simulation Pipeline ... 120
- 7.2 Throughput Metrics ... 120
  - 7.2.1 Instructions Per Cycle (IPC) ... 121
  - 7.2.2 CPI and the Stall Budget ... 122
- 7.3 Cache Metrics ... 122
  - 7.3.1 Cache Statistics ... 122
  - 7.3.2 Cross-Level Cache Analysis ... 125
  - 7.3.3 Prefetcher Statistics ... 126
- 7.4 Branch Predictor Metrics ... 127
- 7.5 DRAM Metrics ... 129
- 7.6 Comparative Analysis ... 131
  - 7.6.1 Normalized Speedup ... 131
  - 7.6.2 Geometric Mean for Multi-workload Studies ... 132
  - 7.6.3 General Guidelines for Reporting Results ... 132
- 7.7 Sanity Checks ... 133
  - 7.7.1 Internal Consistency Checks ... 134
  - 7.7.2 Cross-Metric Plausibility Checks ... 135
  - 7.7.3 Reference Data Comparison ... 136
- 7.8 Summary ... 137
- Review Questions ... 138
- Exercises ... 139
- Further Reading ... 140

---

## Part III: Memory System Modeling ... 141

## Chapter 8: Memory System Architecture ... 143
- 8.1 Cache Architecture ... 143
  - 8.1.1 Set-Associative Organization ... 144
  - 8.1.2 Cache Miss Classification ... 146
  - 8.1.3 Replacement Policies ... 146
  - 8.1.4 Prefetching ... 147
  - 8.1.5 Write Policies ... 148
  - 8.1.6 Inclusion Policies ... 149
- 8.2 DRAM Architecture ... 150
  - 8.2.1 DRAM Organization ... 150
  - 8.2.2 Timing Parameters ... 151
  - 8.2.3 Refresh Overhead ... 153
- 8.3 Memory Controller ... 153
  - 8.3.1 Address Mapping ... 154
  - 8.3.2 Scheduling Policies ... 154
  - 8.3.3 Row Buffer Management ... 155
- 8.4 Address Translation and TLBs ... 155
- 8.5 Summary ... 157
- Review Questions ... 157
- Further Reading ... 158

## Chapter 9: Cache and Prefetcher Simulation ... 159
- 9.1 Simulator Configuration ... 160
  - 9.1.1 Cache Hierarchy Organization ... 160
  - 9.1.2 Modifying Parameters ... 161
- 9.2 Experimental Design ... 163
  - 9.2.1 Workload Selection ... 163
  - 9.2.2 Key Metrics ... 164
  - 9.2.3 Experimental Process ... 164
  - 9.2.4 Companion Repository Setup ... 165 (?)
- 9.3 Cache Replacement Policies ... 165 (?)
  - 9.3.1 Replacement Policy Interface ... 165 (?)
  - 9.3.2 LRU ... 166 (?)
  - 9.3.3 SRRIP ... 168 (?)
- 9.4 Prefetchers ... 172 (?)
  - 9.4.1 Prefetcher Interface ... 173 (?)
  - 9.4.2 Next-Line Prefetcher ... 174
  - 9.4.3 Adding a Simple Filter to the Next-Line Prefetcher ... 176 (?)
- 9.5 Summary ... 182 (?)
- Review Questions ... 182
- Exercises ... 183

## Chapter 10: DRAM Simulation ... 185
- 10.1 Simulator Configuration ... 186
  - 10.1.1 DRAM Organization ... 186
  - 10.1.2 Modifying Parameters ... 188
- 10.2 Experimental Design ... 189
  - 10.2.1 Workload Selection ... 189
  - 10.2.2 Key Metrics ... 190
  - 10.2.3 Experimental Process ... 190
  - 10.2.4 Companion Repository Setup ... 190
- 10.3 DRAM Timing ... 191
  - 10.3.1 The Experiment ... 191
  - 10.3.2 Results and Explanation ... 193
- 10.4 Row Buffer Management ... 195
  - 10.4.1 The Experiment ... 197
  - 10.4.2 Results and Explanation ... 198
- 10.5 Adaptive Row Buffer Management ... 200
  - 10.5.1 The Experiment ... 200
  - 10.5.2 Results and Explanation ... 203
- 10.6 Summary ... 204
- Review Questions ... 205
- Exercises ... 205

---

## Part IV: CPU Core Modeling ... 207

## Chapter 11: CPU Core Architecture ... 209
- 11.1 Pipeline Fundamentals ... 210
  - 11.1.1 Pipeline Organization ... 210
  - 11.1.2 Depth and Frequency Tradeoff ... 212
- 11.2 Front End ... 213
  - 11.2.1 Fetch and Decode ... 213
  - 11.2.2 Branch Prediction ... 214
- 11.3 Execution Back End ... 216
  - 11.3.1 Execution Models ... 217
  - 11.3.2 Rename and Dispatch ... 217
  - 11.3.3 Reorder Buffer ... 218
  - 11.3.4 Scheduling and Execution ... 219
  - 11.3.5 Retirement ... 221
- 11.4 Core-Memory Interface ... 222
  - 11.4.1 Load/Store Queue ... 222
  - 11.4.2 MSHRs and Memory-Level Parallelism ... 222
  - 11.4.3 Store Buffer ... 223
- 11.5 Multicore Execution ... 223
  - 11.5.1 Shared Resources and Contention ... 224
  - 11.5.2 Cache Coherence ... 224
  - 11.5.3 On-Chip Interconnect ... 226
  - 11.5.4 Synchronization Cost ... 227
- 11.6 Summary ... 228
- Review Questions ... 229
- Further Reading ... 229

## Chapter 12: CPU Simulation ... 231
- Tool Setup ... 232
- 12.1 Simulator Configuration ... 233
  - 12.1.1 CPU Models ... 233
  - 12.1.2 Configuration Script ... 234
  - 12.1.3 Default CPU Parameters ... 236
  - 12.1.4 Pipeline in Code ... 237
- 12.2 Experimental Design ... 239
  - 12.2.1 Workload Selection ... 240
  - 12.2.2 Key Metrics ... 241
  - 12.2.3 Experimental Process ... 242
  - 12.2.4 Companion Repository Setup ... 242
- 12.3 ROB Size and the Instruction Window ... 242
  - The Experiment ... 243
  - Results and Explanation ... 244
- 12.4 Execution Unit Bandwidth ... 245
  - The Experiment ... 245
  - Results and Explanation ... 247
- 12.5 Squash Recovery Delay ... 248
  - The Experiment ... 249
  - Results and Explanation ... 252
- 12.6 Summary ... 253
- Review Questions ... 254
- Exercises ... 254

## Chapter 13: Multicore CPU Simulation ... 255
- Tool Setup ... 256
- 13.1 Simulator Configuration ... 257
  - 13.1.1 Classic and Ruby Memory Systems ... 257
  - 13.1.2 MESI Two-Level Hierarchy ... 257
  - 13.1.3 Configuration Script ... 258
  - 13.1.4 Ruby Statistics Output ... 260
- 13.2 Experimental Design ... 262
  - 13.2.1 Workload Selection ... 262
  - 13.2.2 Key Metrics ... 264
  - 13.2.3 Experimental Process ... 264
  - 13.2.4 Companion Repository Setup ... 265
- 13.3 Multicore Scaling ... 26x?
  - The Experiment ... 26x?
  - Results and Explanation ... 26x?
- 13.4 False Sharing ... 268 (?)
  - The Experiment ... 269 (?)
  - Results and Explanation ... 270 (?)
- 13.5 Synchronization Cost ... 271
  - The Experiment ... 272 (?)
  - Results and Explanation ... 274
- 13.6 Summary ... 275 (?)
- Review Questions ... 276 (?)
- Exercises ... 276 (?)

---

## Part V: GPU Modeling ... 277

## Chapter 14: GPU Architecture ... 279
- 14.1 GPU Execution Model ... 280
  - 14.1.1 SIMT and Warps ... 280
  - 14.1.2 Thread Blocks and Grids ... 281
  - 14.1.3 The Compute Unit ... 282
- 14.2 Warp Scheduling ... 287
  - 14.2.1 Scheduling Mechanics ... 287
  - 14.2.2 Instruction and Memory Latencies ... 288
  - 14.2.3 Latency Hiding ... 289
- 14.3 Memory Hierarchy ... 290
  - 14.3.1 Shared Memory and L1 Cache ... 290
  - 14.3.2 L2 Cache and HBM ... 291
  - 14.3.3 Memory Coalescing ... 293
  - 14.3.4 Asynchronous Data Movement ... 293
- 14.4 Occupancy and Resource Limits ... 294
  - 14.4.1 Resource Limits ... 295
- 14.5 Performance Pathologies ... 296
  - 14.5.1 Warp Divergence ... 297
  - 14.5.2 Uncoalesced Memory Access ... 297
  - 14.5.3 Bank Conflicts ... 298
  - 14.5.4 Atomic Contention ... 298
  - 14.5.5 Execution Throughput Bottlenecks ... 298
- 14.6 Summary ... 299
- Review Questions ... 300
- Further Reading ... 300

## Chapter 15: GPU Simulation ... 303
- Tool Setup ... 304
- 15.1 Simulator Configuration ... 305
  - 15.1.1 Accel-Sim Organization ... 306
  - 15.1.2 Configuration Files ... 307
  - 15.1.3 Trace Format ... 308
- 15.2 Experimental Design ... 310
  - 15.2.1 Workload Selection ... 310
  - 15.2.2 Key Metrics ... 311
  - 15.2.3 Experimental Process ... 311
  - 15.2.4 Companion Repository Setup ... 311
- 15.3 Memory Coalescing ... 312
  - The Experiment ... 312
  - Results and Explanation ... 314
- 15.4 Warp Divergence ... 315
  - The Experiment ... 315
  - Results and Explanation ... 316
- 15.5 Latency Tolerance ... 3xx?
  - The Experiment ... 3xx?
  - Results and Explanation ... 3xx?
- 15.6 Summary ... 3xx?
- Review Questions ... 3xx?
- Exercises ... 3xx?

---

## Part VI: Accelerator Modeling ... 3xx?

## Chapter 16: Tensor Accelerator Architecture ... 3xx?
- 16.1 The Case for Tensor Accelerators ... 32x?
- 16.2 The Systolic Array ... 32x?
  - 16.2.1 Array Organization ... 32x?
  - 16.2.2 Data Movement Through the Array ... 3xx?
  - 16.2.3 The TPU Example ... 3xx?
- 16.3 Dataflow Choices ... 33x?
- 16.4 Memory Hierarchy on Accelerators ... 33x?
  - 16.4.1 Scratchpad Hierarchy ... 33x?
  - 16.4.2 Software-Managed Data Movement ... 334 (?)
- 16.5 Mapping and Performance Bottlenecks ... 335 (?)
- 16.6 Summary ... 33x?
- Review Questions ... 337 (?)
- Further Reading ... 33x?

## Chapter 17: Accelerator Simulation ... 339
- Tool Setup ... 340
- 17.1 Simulator Configuration ... 341
  - 17.1.1 SCALE-Sim Architecture Model ... 342
  - 17.1.2 Configuration File ... 342
  - 17.1.3 Topology File ... 344
  - 17.1.4 Layout File ... 345
- 17.2 Experimental Design ... 345
  - 17.2.1 Workload Selection ... 346
  - 17.2.2 Key Metrics ... 346
  - 17.2.3 Experimental Process ... 347
  - 17.2.4 Companion Repository Setup ... 347
- 17.3 Dataflow Comparison ... 347
  - The Experiment ... 348
  - Results and Explanation ... 349
- 17.4 Array Size and Mapping Efficiency ... 349
  - The Experiment ... 350
  - Results and Explanation ... 351
- 17.5 Sparsity ... 352
  - The Experiment ... 352
  - Results and Explanation ... 353
- 17.6 Summary ... 354
- Review Questions ... 354
- Exercises ... 355

---

## Part VII: Power Modeling ... 357

## Chapter 18: Power Modeling – A Walkthrough ... 359
- 18.1 Why Model Power ... 359
- 18.2 CPU Power with McPAT ... 360
- 18.3 GPU Power with AccelWattch ... 361
- 18.4 Looking Further ... 362

## Closing Thoughts ... 365
## Index ... 367

---

## Tools the book uses (for cross-reference)

| Stage | Tool in the book |
|---|---|
| Trace collection | Intel Pin (DBI), ChampSim tracer |
| Sampling | SimPoint (BBVs + k-means clustering) |
| Cache / prefetcher / DRAM / branch simulation | ChampSim |
| Out-of-order core and multicore | gem5 (O3 CPU; Classic and Ruby memory; MESI Two-Level) |
| GPU | Accel-Sim (GPGPU-Sim, trace-driven) |
| Tensor accelerator | SCALE-Sim (systolic array; config / topology / layout files) |
| Power | McPAT (CPU), AccelWattch (GPU) |
