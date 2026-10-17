# Derived hotspot data

Read-only extraction from the existing `focused.pstats`, JUnit records and canonical source
identities. No new profiling or tests; the original evidence archive is unchanged.
This fenced JSON is documentation, not an executable probe or new acceptance receipt.

```json
{
  "profile_total_s": 59.66942920600015,
  "caller_tuple_order": [
    "primitive_calls",
    "total_calls",
    "exclusive_s",
    "cumulative_s"
  ],
  "hotspots": {
    "validate_execution_bundle": {
      "file": "/tmp/rk-uarch-verification-b/src/rkuarch/workload/prepared.py",
      "line": 47,
      "primitive_calls": 618,
      "total_calls": 618,
      "exclusive_s": 0.118794304,
      "cumulative_s": 17.689849524,
      "callers": [
        {
          "file": "/tmp/rk-uarch-verification-b/src/rkuarch/workload/prepared.py",
          "line": 296,
          "function": "prepare_engine_job",
          "stats": [
            324,
            324,
            0.061564731000000004,
            8.485487974
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/validation/strategies.py",
          "line": 57,
          "function": "fixed_bundle",
          "stats": [
            190,
            190,
            0.037123203,
            6.003165053
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/validation/reporting/analytic_report.py",
          "line": 994,
          "function": "replay",
          "stats": [
            44,
            44,
            0.009179797,
            1.442253207
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/src/rkuarch/table/artifacts.py",
          "line": 170,
          "function": "_complete_closure",
          "stats": [
            24,
            24,
            0.004697512,
            0.7589210160000001
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/src/rkuarch/table/artifacts.py",
          "line": 386,
          "function": "_load_verified",
          "stats": [
            12,
            12,
            0.002413765,
            0.397639609
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/src/rkuarch/workload/prepared.py",
          "line": 292,
          "function": "load_prepared_input",
          "stats": [
            6,
            6,
            0.001318741,
            0.190245302
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/src/rkuarch/table/artifacts.py",
          "line": 116,
          "function": "__getitem__",
          "stats": [
            4,
            4,
            0.0008271110000000001,
            0.129115413
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/validation/reporting/analytic_report.py",
          "line": 1117,
          "function": "validate_objects",
          "stats": [
            4,
            4,
            0.000753589,
            0.128743155
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/validation/reporting/analytic_report.py",
          "line": 388,
          "function": "parsed_bundle",
          "stats": [
            4,
            4,
            0.000906436,
            0.120801896
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/validation/reporting/analytic_report.py",
          "line": 683,
          "function": "exercise",
          "stats": [
            6,
            6,
            9.419e-06,
            0.033476899000000004
          ]
        }
      ]
    },
    "_load_verified": {
      "file": "/tmp/rk-uarch-verification-b/src/rkuarch/table/artifacts.py",
      "line": 386,
      "primitive_calls": 12,
      "total_calls": 12,
      "exclusive_s": 0.00806219,
      "cumulative_s": 24.289232013000003,
      "callers": [
        {
          "file": "/tmp/rk-uarch-verification-b/src/rkuarch/table/artifacts.py",
          "line": 354,
          "function": "verify_report_inputs",
          "stats": [
            8,
            8,
            0.004682193,
            16.840207203000002
          ]
        },
        {
          "file": "/tmp/rk-uarch-verification-b/src/rkuarch/table/artifacts.py",
          "line": 336,
          "function": "load_verified_report_inputs",
          "stats": [
            4,
            4,
            0.003379997,
            7.44902481
          ]
        }
      ]
    },
    "hardware_unit_rule": {
      "file": "/tmp/rk-uarch-verification-b/contract/uarch_contract/hardware.py",
      "line": 320,
      "primitive_calls": 246470,
      "total_calls": 246470,
      "exclusive_s": 2.9880020660000004,
      "cumulative_s": 19.614256843,
      "callers": [
        {
          "file": "/tmp/rk-uarch-verification-b/contract/uarch_contract/hardware.py",
          "line": 354,
          "function": "coherent",
          "stats": [
            246470,
            246470,
            2.9880020660000004,
            19.614256843
          ]
        }
      ]
    }
  },
  "profile_sha256": "f8ee8b5d7852081b5efef1a083e79143f97af9a9ed6b55ac745e172612e69726",
  "profile_subject": "620896870a6479a69fa607dfad8c6582847c4cc1",
  "documentation_subject": "756d63289e1d9b9ae61bc2cddb2b49d9f8e60938",
  "new_execution": "None; derived from existing pstats/JUnit and read-only source/history inspection.",
  "input_identity_limit": "cProfile records no arguments or input digests; repeated calls do not prove byte-identical requests or safe acceptance reuse.",
  "hardware_rule_patterns": 54,
  "hardware_rule_escape_edge": {
    "calls": 6735170,
    "exclusive_s": 1.455955153,
    "cumulative_s": 10.388020309
  },
  "normal_ci_node_seconds": {
    "baseline": {
      "json_control": 13.169,
      "companions_positive": 12.535,
      "support_policy_hardware_drift": 0.598,
      "sum": 26.302,
      "whole_command": 921.33
    },
    "final_pre_component": {
      "json_control": 12.477,
      "companions_positive": 11.999,
      "support_policy_hardware_drift": 0.522,
      "sum": 24.998,
      "whole_python_command": 901.26
    }
  },
  "canonical_vs_K2_candidate": {
    "src/rkuarch/engines/native/runner.py": {
      "canonical_sha256": "9f7ec1e626a418d3a77c8f6982e730543169254257e2baaa9dc6acb6f44c10be",
      "baseline_sha256": "9f7ec1e626a418d3a77c8f6982e730543169254257e2baaa9dc6acb6f44c10be",
      "candidate_sha256": "ce82a76e6887ace0d65349a7c09159293466b73ff656680e90184a716ffd7ed9",
      "patch_sha256": "e67f0463afa29560e5c9c72bc80d0a2883c3137b87c5a33bb273d4c3fdcfddba"
    },
    "contract/uarch_contract/hardware.py": {
      "canonical_sha256": "8f737384d95be4ccce6c916c0c6bbe416ebfa48c108738c9030079da04880e94",
      "baseline_sha256": "8f737384d95be4ccce6c916c0c6bbe416ebfa48c108738c9030079da04880e94",
      "candidate_sha256": "98b1b06ddf686da948223ca517b0ac16729fbd0f3f6fd1b5bc6f61c1507cb1b5",
      "patch_sha256": "e5894ee8fa2530bc5c51af9ef3faa03ec3ead02d6922aa9424e4626947c72fb8"
    },
    "src/rkuarch/engines/native/host.py": {
      "canonical_sha256": "dd868311c41ceb798d92b437c4161072b48ed9ca75d1b61fe089c5d2b127ba2e",
      "baseline_sha256": "dd868311c41ceb798d92b437c4161072b48ed9ca75d1b61fe089c5d2b127ba2e",
      "candidate_sha256": "0f44dee94c753829b05d3a646d3ffb33a297468da11e5d8647aeaf64c24508ba",
      "patch_sha256": "c98a604b532630b943b9958cee5824ac8cabe5912a8243fe2644cef0b878966f"
    }
  }
}
```
