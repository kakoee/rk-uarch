# hw — hardware specs

designs/     chips that do not exist (design_status: proposed). Design choices are
             STIPULATIONS, each with a rationale. They define the question; they are not claims.
references/  real chips (design_status: reference). CLAIMS ONLY, each with a URL to a vendor
             page or document. What the vendor does not publish is provenance: stub with
             source: null — never a stipulation. The loader refuses a stipulation here.
studies/     StudySpecs: variants of a proposed design that change stipulations only.

derive_rk_params() turns a spec into the params rk-sim's component entry must carry. If they
disagree, the spec is right and the component is wrong. Stipulations propagate as
stipulations; a derived claim is only as good as its worst input.
