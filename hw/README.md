# hw — hardware specs

designs/     chips that do not exist (design_status: proposed). Design choices are
             STIPULATIONS, each with a rationale. They define the question; they are not claims.
references/  real chips (design_status: reference). CLAIMS ONLY, each with a URL to a vendor
             page or document. What the vendor does not publish is provenance: stub with
             source: null — never a stipulation. The loader refuses a stipulation here.
studies/     StudySpecs: variants of a proposed design that change only what the design is
             free to choose (stipulated values, counts included, and categorical fields).

derive_rk_params() turns a spec into the params rk-sim's component entry must carry. If they
disagree, the spec is right and the component is wrong. Stipulations propagate as
stipulations; a derived claim is only as good as its worst input.

Every numeric leaf is a SourcedValue, counts and DRAM organisation and timing included. A
simulator preset supplies DRAM timing only through memory.dram.timing_preset {file, sha}, as
claims citing that file@sha. Each *_cycles leaf is in its block's clock domain (build-spec
§2.3.2). SRAM size and SRAM pJ/byte travel together: a
variant that changes one re-stipulates the other. studies/ also holds the versioned workload
suite (workload-suite@N.yaml) that studies and L3 shape selection read.
