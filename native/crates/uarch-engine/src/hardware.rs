//! Installed HardwareSpec semantic rules and exact scalar projection.
use crate::{
    carrier::{Result, refuse},
    wire,
};
use serde_json::{Value, json};
pub(crate) fn digest(v: &Value) -> Result<String> {
    Ok(format!(
        "sha256:{}",
        wire::hash(
            wire::canonical(v)
                .map_err(|e| refuse("InvalidCarrier", "", e))?
                .as_bytes()
        )
    ))
}
pub(crate) fn ratio(v: &Value) -> Result<(u128, u128)> {
    let s = wire::canonical(v).map_err(|e| refuse("HardwareMismatch", "", e))?;
    let (m, e) = s.split_once('e').map_or((s.as_str(), 0), |(m, e)| {
        (m, e.parse::<i32>().unwrap_or(i32::MAX))
    });
    if m.starts_with('-') {
        return Err(refuse(
            "HardwareMismatch",
            "",
            "negative rational projection",
        ));
    }
    let decimals = m.split_once('.').map_or(0, |(_, s)| s.len() as i32);
    let mut digits = m.replace('.', "");
    let mut power = e - decimals;
    while digits.ends_with('0') && digits.len() > 1 {
        digits.pop();
        power += 1;
    }
    let mut n = digits
        .parse::<u128>()
        .map_err(|_| refuse("HardwareMismatch", "", "rational range"))?;
    if n == 0 {
        return Ok((0, 1));
    }
    let mut d = 1u128;
    if power >= 0 {
        n = n
            .checked_mul(
                10u128
                    .checked_pow(power as u32)
                    .ok_or_else(|| refuse("HardwareMismatch", "", "rational range"))?,
            )
            .ok_or_else(|| refuse("HardwareMismatch", "", "rational range"))?;
    } else {
        // Cancel factors before constructing the denominator.
        let mut twos = -power;
        let mut fives = -power;
        while twos > 0 && n % 2 == 0 {
            n /= 2;
            twos -= 1;
        }
        while fives > 0 && n % 5 == 0 {
            n /= 5;
            fives -= 1;
        }
        d = 2u128
            .checked_pow(twos as u32)
            .and_then(|a| {
                5u128
                    .checked_pow(fives as u32)
                    .and_then(|b| a.checked_mul(b))
            })
            .ok_or_else(|| refuse("HardwareMismatch", "", "rational range"))?;
    }
    let g = wire::gcd(n, d);
    Ok((n / g, d / g))
}
pub(crate) fn frequencies(spec: &Value, scale: &Value) -> Result<Value> {
    let (a, b) = ratio(scale)?;
    let mut out = serde_json::Map::new();
    for domain in ["core", "noc", "dram"] {
        let c = &spec["clock_domains"][domain];
        let (mut n, mut d) = ratio(&c["freq_hz"]["value"])?;
        if c["scales_with_core"] == true {
            let g1 = wire::gcd(n, b);
            let g2 = wire::gcd(a, d);
            n = (n / g1)
                .checked_mul(a / g2)
                .ok_or_else(|| refuse("UnsupportedFrequency", "", "frequency overflow"))?;
            d = (d / g2)
                .checked_mul(b / g1)
                .ok_or_else(|| refuse("UnsupportedFrequency", "", "frequency overflow"))?;
        }
        if d != 1 || n == 0 || n > u64::MAX as u128 {
            return Err(refuse(
                "UnsupportedFrequency",
                "",
                "positive integral u64 frequency required",
            ));
        }
        out.insert(domain.into(), Value::from(n as u64));
    }
    Ok(Value::Object(out))
}
pub(crate) fn projection(spec: &Value) -> Result<Value> {
    fn walk(v: &Value, path: String, out: &mut Vec<Value>) -> Result<()> {
        match v {
            Value::Object(o) => {
                for (k, v) in o {
                    walk(
                        v,
                        format!("{}/{}", path, k.replace('~', "~0").replace('/', "~1")),
                        out,
                    )?;
                }
            }
            Value::Array(a) => {
                for (i, v) in a.iter().enumerate() {
                    walk(v, format!("{path}/{i}"), out)?;
                }
            }
            _ => {
                let value = if v
                    .as_number()
                    .is_some_and(|n| n.to_string().contains(['.', 'e', 'E']))
                {
                    let (n, d) = ratio(v)?;
                    wire::parse(&format!("{{\"numerator\":{n},\"denominator\":{d}}}"))
                        .map_err(|e| refuse("HardwareMismatch", "", e))?
                } else {
                    v.clone()
                };
                out.push(json!({"path":path,"value":value}));
            }
        }
        Ok(())
    }
    let mut leaves = Vec::new();
    walk(spec, String::new(), &mut leaves)?;
    Ok(
        json!({"format":"uarch-resolved-hardware/1","hardware_spec_hash":digest(spec)?,"leaves":leaves}),
    )
}
fn unit_rule(pattern: &str, path: &str) -> bool {
    if let Some(prefix) = pattern.strip_suffix(".*") {
        return path
            .strip_prefix(&format!("{prefix}."))
            .is_some_and(|s| !s.is_empty());
    }
    let p: Vec<_> = pattern.split('.').collect();
    let s: Vec<_> = path.split('.').collect();
    p.len() == s.len()
        && p.iter().zip(s).all(|(p, s)| {
            *p == "*"
                || *p == s
                || p.strip_suffix("[]").is_some_and(|p| {
                    s.strip_prefix(p)
                        .is_some_and(|t| t.starts_with('[') && t.ends_with(']'))
                })
        })
}
fn coordinate_below(value:&Value,bound:f64)->bool {
    wire::integer_text(value).is_ok_and(|n|crate::carrier::cmp_integer(&n,&format!("{bound:.0}")).is_lt())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn integer_grid_comparison_does_not_round_the_coordinate() {
        let maximum=wire::parse("36893488147419103231").unwrap();
        assert!(coordinate_below(&maximum,36893488147419103232.0));
        assert!(!coordinate_below(&wire::parse("36893488147419103232").unwrap(),36893488147419103232.0));
    }
}
pub(crate) fn validate(spec: &mut Value) -> Result<()> {
    // Float dictionary keys are the sole key normalization in HardwareSpec.
    let volt = spec["energy"]["voltage_ratio"]
        .as_object_mut()
        .ok_or_else(|| refuse("HardwareMismatch", "", "voltage mapping"))?;
    let mut normalized = serde_json::Map::new();
    for (k, v) in std::mem::take(volt) {
        let f =
            wire::legacy_number(Value::String(k)).map_err(|e| refuse("HardwareMismatch", "", e))?;
        if f <= 0.0 {
            return Err(refuse(
                "HardwareMismatch",
                "",
                "positive voltage key required",
            ));
        }
        let key = wire::float_text(f).map_err(|e| refuse("HardwareMismatch", "", e))?;
        if normalized.insert(key, v).is_some() {
            return Err(refuse(
                "HardwareMismatch",
                "",
                "duplicate normalized voltage key",
            ));
        }
    }
    *volt = normalized;
    let shapes: Value =
        serde_json::from_str(include_str!("carriers.json")).expect("compiled shapes");
    let rules = shapes["$defs"]["HardwareSpec"]["x-hardware-unit-rules"]
        .as_object()
        .expect("unit rules");
    let reference = spec["design_status"] == "reference";
    fn walk(
        v: &Value,
        path: String,
        rules: &serde_json::Map<String, Value>,
        reference: bool,
    ) -> Result<()> {
        if let Some(obj) = v.as_object() {
            if obj.contains_key("unit") && obj.contains_key("value") {
                let allowed = rules
                    .iter()
                    .find(|(p, _)| unit_rule(p, &path))
                    .map(|(_, v)| v)
                    .ok_or_else(|| refuse("HardwareMismatch", &path, "no unit rule"))?;
                if !allowed.as_array().is_some_and(|a| a.contains(&v["unit"])) {
                    return Err(refuse("HardwareMismatch", &path, "unit mismatch"));
                }
                let n = v["value"]
                    .as_f64()
                    .ok_or_else(|| refuse("HardwareMismatch", &path, "quantity"))?;
                let zero_ok = path == "static_power_w"
                    || path.starts_with("energy.pj_per_")
                    || path.ends_with(".block_scale_bytes")
                    || path.ends_with(".job_overhead_cycles")
                    || path.ends_with(".barrier_latency_cycles")
                    || path.ends_with(".router_latency_cycles")
                    || path == "shared_sram.latency_cycles"
                    || (path.starts_with("memory.dram.timing.")
                        && !path.ends_with(".t_refi_cycles"));
                if n < 0.0 || (!zero_ok && n == 0.0) || (v["unit"] == "count" && n.fract() != 0.0) {
                    return Err(refuse(
                        "HardwareMismatch",
                        &path,
                        "quantity bound/integrality",
                    ));
                }
                if reference && v["kind"] == "stipulation" {
                    return Err(refuse("HardwareMismatch", &path, "reference stipulation"));
                }
            } else {
                for (k, c) in obj {
                    walk(
                        c,
                        if path.is_empty() {
                            k.clone()
                        } else {
                            format!("{path}.{k}")
                        },
                        rules,
                        reference,
                    )?;
                }
            }
        } else if let Some(a) = v.as_array() {
            for (i, c) in a.iter().enumerate() {
                walk(c, format!("{path}[{i}]"), rules, reference)?;
            }
        }
        Ok(())
    }
    walk(spec, String::new(), rules, reference)?;
    if spec["energy"]["pj_per_byte"].get("sram").is_none()
        || spec["formats"].as_object().is_none_or(|x| x.is_empty())
        || spec["cores"]["core_type"]["matrix_engine"]["macs_per_cycle"]
            .as_object()
            .is_none_or(|x| x.is_empty())
    {
        return Err(refuse(
            "HardwareMismatch",
            "",
            "empty required hardware map",
        ));
    }
    let rows = spec["cores"]["grid"]["rows"]["value"]
        .as_f64()
        .expect("quantity");
    let cols = spec["cores"]["grid"]["cols"]["value"]
        .as_f64()
        .expect("quantity");
    let mut coordinates: Vec<&Value> = spec["memory"]["controllers"]
        .as_array()
        .expect("shape")
        .iter()
        .map(|c| &c["attach"])
        .collect();
    if let Some(a) = spec["shared_sram"]["attach"].as_array() {
        coordinates.extend(a);
    }
    if coordinates
        .iter()
        .any(|c| !coordinate_below(&c[0], rows) || !coordinate_below(&c[1], cols))
    {
        return Err(refuse("HardwareMismatch", "", "coordinate outside grid"));
    }
    let dram = &spec["memory"]["dram"];
    let preset = &dram["timing_preset"];
    if (dram["timing_source"] == "direct") != preset.is_null() {
        return Err(refuse(
            "HardwareMismatch",
            "",
            "timing source/preset mismatch",
        ));
    }
    if !preset.is_null() {
        let citation = format!(
            "{}@{}",
            preset["file"].as_str().expect("shape"),
            preset["sha"].as_str().expect("shape")
        );
        for q in dram["timing"].as_object().expect("shape").values() {
            if q["kind"] == "claim" && q["provenance"] != "stub" && q["source"] != citation {
                return Err(refuse("HardwareMismatch", "", "preset citation mismatch"));
            }
        }
    }
    Ok(())
}
