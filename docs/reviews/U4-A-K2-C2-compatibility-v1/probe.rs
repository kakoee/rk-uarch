//! Private C2 probe only. No engine source, mapped execution or authority.
use serde::de::{self, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::{Map, Number, Value, json};
use sha2::{Digest, Sha256};
use std::fmt;
use std::io::{self, BufRead, Write};
use std::str::FromStr;

#[inline(never)]
#[unsafe(no_mangle)]
pub fn c2_sha256_boundary(input: &[u8]) -> [u8; 32] {
    Sha256::digest(input).into()
}
fn hex(data: &[u8]) -> String {
    data.iter().map(|b| format!("{b:02x}")).collect()
}
fn unhex(s: &str) -> Result<Vec<u8>, String> {
    if s.len() % 2 != 0 {
        return Err("odd hexadecimal length".into());
    }
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).map_err(|e| e.to_string()))
        .collect()
}
fn hash(data: &[u8]) -> String {
    hex(&c2_sha256_boundary(data))
}

// The reviewed formatter uses the existing serializer's shortest digits. Only
// Python's notation threshold, exponent sign/padding and integral .0 are applied.
fn float_text(f: f64) -> Result<String, String> {
    if !f.is_finite() {
        return Err("nonfinite f64".into());
    }
    if f == 0.0 {
        return Ok("0.0".into());
    }
    let short = serde_json::to_string(&f).map_err(|e| e.to_string())?;
    let (sign, unsigned) = if let Some(s) = short.strip_prefix('-') {
        ("-", s)
    } else {
        ("", short.as_str())
    };
    let (mantissa, exponent) = if let Some((m, e)) = unsigned.split_once('e') {
        (m, e.parse::<i32>().map_err(|e| e.to_string())?)
    } else {
        (unsigned, 0)
    };
    let point = mantissa.find('.').unwrap_or(mantissa.len()) as i32;
    let mut digits = mantissa.replace('.', "");
    let leading = digits.bytes().take_while(|b| *b == b'0').count();
    digits.drain(..leading);
    while digits.ends_with('0') {
        digits.pop();
    }
    let decimal = point + exponent - leading as i32;
    let scientific = decimal - 1;
    let body = if (-4..16).contains(&scientific) {
        if decimal <= 0 {
            format!("0.{}{}", "0".repeat((-decimal) as usize), digits)
        } else if decimal as usize >= digits.len() {
            format!(
                "{}{}.0",
                digits,
                "0".repeat(decimal as usize - digits.len())
            )
        } else {
            format!(
                "{}.{}",
                &digits[..decimal as usize],
                &digits[decimal as usize..]
            )
        }
    } else {
        let mantissa = if digits.len() == 1 {
            digits
        } else {
            format!("{}.{}", &digits[..1], &digits[1..])
        };
        format!(
            "{}e{}{:02}",
            mantissa,
            if scientific < 0 { "-" } else { "+" },
            scientific.abs()
        )
    };
    Ok(format!("{sign}{body}"))
}

struct Strict(Value);
impl<'de> Deserialize<'de> for Strict {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct V;
        impl<'de> Visitor<'de> for V {
            type Value = Strict;
            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("duplicate-free JSON")
            }
            fn visit_bool<E: de::Error>(self, v: bool) -> Result<Strict, E> {
                Ok(Strict(Value::Bool(v)))
            }
            fn visit_unit<E: de::Error>(self) -> Result<Strict, E> {
                Ok(Strict(Value::Null))
            }
            fn visit_i64<E: de::Error>(self, v: i64) -> Result<Strict, E> {
                Ok(Strict(Value::Number(v.into())))
            }
            fn visit_u64<E: de::Error>(self, v: u64) -> Result<Strict, E> {
                Ok(Strict(Value::Number(v.into())))
            }
            fn visit_f64<E: de::Error>(self, v: f64) -> Result<Strict, E> {
                Number::from_f64(v)
                    .map(|n| Strict(Value::Number(n)))
                    .ok_or_else(|| E::custom("nonfinite"))
            }
            fn visit_str<E: de::Error>(self, v: &str) -> Result<Strict, E> {
                Ok(Strict(Value::String(v.to_owned())))
            }
            fn visit_string<E: de::Error>(self, v: String) -> Result<Strict, E> {
                Ok(Strict(Value::String(v)))
            }
            fn visit_seq<A: SeqAccess<'de>>(self, mut seq: A) -> Result<Strict, A::Error> {
                let mut values = Vec::new();
                while let Some(Strict(v)) = seq.next_element()? {
                    values.push(v);
                }
                Ok(Strict(Value::Array(values)))
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Strict, A::Error> {
                let mut values = Map::new();
                while let Some(key) = map.next_key::<String>()? {
                    if values.contains_key(&key) {
                        return Err(de::Error::custom("DuplicateJsonKey"));
                    }
                    let Strict(value) = map.next_value()?;
                    values.insert(key, value);
                }
                // Caller marker keys are rejected lexically before this visitor;
                // only serde_json's internal arbitrary-precision number map remains.
                if values.len() == 1 && values.contains_key("$serde_json::private::Number") {
                    let s = values["$serde_json::private::Number"]
                        .as_str()
                        .ok_or_else(|| de::Error::custom("invalid number marker"))?;
                    return Number::from_str(s)
                        .map(|n| Strict(Value::Number(n)))
                        .map_err(de::Error::custom);
                }
                Ok(Strict(Value::Object(values)))
            }
        }
        deserializer.deserialize_any(V)
    }
}
fn reserved_key_guard(s: &str) -> Result<(), String> {
    let b = s.as_bytes();
    let mut i = 0;
    while i < b.len() {
        if b[i] != b'"' {
            i += 1;
            continue;
        }
        let start = i;
        i += 1;
        while i < b.len() {
            if b[i] == b'\\' {
                i += 2;
            } else if b[i] == b'"' {
                break;
            } else {
                i += 1;
            }
        }
        if i >= b.len() {
            return Err("unterminated string".into());
        }
        let end = i + 1;
        i = end;
        while i < b.len() && b[i].is_ascii_whitespace() {
            i += 1;
        }
        if i < b.len() && b[i] == b':' {
            let key: String = serde_json::from_str(&s[start..end]).map_err(|e| e.to_string())?;
            if key == "$serde_json::private::Number" {
                return Err("ReservedNumericMarker".into());
            }
        }
    }
    Ok(())
}
fn parse(s: &str) -> Result<Value, String> {
    reserved_key_guard(s)?;
    let mut d = serde_json::Deserializer::from_str(s);
    let Strict(v) = Strict::deserialize(&mut d).map_err(|e| e.to_string())?;
    d.end().map_err(|e| e.to_string())?;
    Ok(v)
}
fn canonical(v: &Value) -> Result<String, String> {
    match v {
        Value::Null => Ok("null".into()),
        Value::Bool(b) => Ok(b.to_string()),
        Value::String(s) => serde_json::to_string(s).map_err(|e| e.to_string()),
        Value::Number(n) => {
            let s = n.to_string();
            if s.contains(['.', 'e', 'E']) {
                float_text(s.parse::<f64>().map_err(|e| e.to_string())?)
            } else if s == "-0" {
                Ok("0".into())
            } else {
                Ok(s)
            }
        }
        Value::Array(items) => Ok(format!(
            "[{}]",
            items
                .iter()
                .map(canonical)
                .collect::<Result<Vec<_>, _>>()?
                .join(",")
        )),
        Value::Object(items) => {
            let mut keys: Vec<_> = items.keys().collect();
            keys.sort();
            let pairs = keys
                .into_iter()
                .map(|k| {
                    Ok(format!(
                        "{}:{}",
                        serde_json::to_string(k).map_err(|e| e.to_string())?,
                        canonical(&items[k])?
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            Ok(format!("{{{}}}", pairs.join(",")))
        }
    }
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Rational {
    numerator: u128,
    denominator: u128,
}
fn gcd(mut a: u128, mut b: u128) -> u128 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}
impl Rational {
    fn check(&self) -> Result<(), String> {
        if self.denominator == 0 || gcd(self.numerator, self.denominator) != 1 {
            Err("InvalidRatio".into())
        } else {
            Ok(())
        }
    }
}
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum Calibration {
    Measured,
    SpecDerived,
    Estimated,
    Stub,
}
fn default_kind() -> String {
    "claim".into()
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Sourced {
    #[serde(deserialize_with = "legacy_float")]
    value: f64,
    unit: String,
    #[serde(default)]
    provenance: Option<Calibration>,
    #[serde(default)]
    source: Option<String>,
    #[serde(default)]
    date: Option<String>,
    #[serde(default = "default_kind")]
    kind: String,
    #[serde(default)]
    rationale: Option<String>,
}
// Token-preserving dispatch uses the strict parser's arbitrary-precision Number;
// no untagged serde Content or float intermediate participates in strict integers.
fn integer_text(v: &Value) -> Result<String, String> {
    let Value::Number(n) = v else {
        return Err("IntegerToken".into());
    };
    let token = n.to_string();
    if token.contains(['.', 'e', 'E']) {
        return Err("IntegerToken".into());
    }
    Ok(token)
}
fn integer_u128(v: &Value) -> Result<u128, String> {
    integer_text(v)?
        .parse::<u128>()
        .map_err(|_| "IntegerRange".into())
}
fn rational_value(v: &Value) -> Result<(), String> {
    let o = v.as_object().ok_or("RationalFields")?;
    if o.len() != 2 || !o.contains_key("numerator") || !o.contains_key("denominator") {
        return Err("RationalFields".into());
    }
    Rational {
        numerator: integer_u128(&o["numerator"])?,
        denominator: integer_u128(&o["denominator"])?,
    }
    .check()
}
fn leaf_value(v: &Value) -> Result<(), String> {
    let o = v.as_object().ok_or("LeafFields")?;
    if o.len() != 2
        || !o.contains_key("value")
        || !o
            .get("path")
            .and_then(Value::as_str)
            .is_some_and(|s| !s.trim().is_empty())
    {
        return Err("LeafFields".into());
    }
    match &o["value"] {
        Value::Object(_) => rational_value(&o["value"]),
        Value::Number(_) => integer_text(&o["value"]).map(|_| ()),
        Value::Bool(_) | Value::String(_) | Value::Null => Ok(()),
        Value::Array(_) => Err("LeafScalar".into()),
    }
}
fn normalize_integer_zero(s: &str) -> String {
    let bytes = s.as_bytes();
    let mut out = Vec::with_capacity(bytes.len());
    let mut i = 0;
    let mut quoted = false;
    let mut escaped = false;
    while i < bytes.len() {
        let b = bytes[i];
        if quoted {
            out.push(b);
            if escaped {
                escaped = false;
            } else if b == b'\\' {
                escaped = true;
            } else if b == b'"' {
                quoted = false;
            }
            i += 1;
            continue;
        }
        if b == b'"' {
            quoted = true;
        }
        let before = i == 0
            || matches!(
                bytes[i - 1],
                b' ' | b'\t' | b'\r' | b'\n' | b'[' | b':' | b','
            );
        let after = i + 2 == bytes.len()
            || bytes
                .get(i + 2)
                .is_some_and(|c| matches!(c, b' ' | b'\t' | b'\r' | b'\n' | b']' | b'}' | b','));
        if b == b'-' && bytes.get(i + 1) == Some(&b'0') && before && after {
            out.push(b'0');
            i += 2;
        } else {
            out.push(b);
            i += 1;
        }
    }
    String::from_utf8(out).expect("only ASCII minus removed from UTF-8")
}
// Installed Pydantic legacy float conversion is field-local. The frozen Python
// boundaries establish trimming and underscore behavior; it is not Python float().
fn legacy_float<'de, D: Deserializer<'de>>(d: D) -> Result<f64, D::Error> {
    let Strict(v) = Strict::deserialize(d)?;
    let f = match v {
        Value::Bool(b) => {
            if b {
                1.0
            } else {
                0.0
            }
        }
        Value::Number(n) => n
            .to_string()
            .parse::<f64>()
            .map_err(|_| de::Error::custom("LegacyFloatSyntax"))?,
        Value::String(s) => {
            let s = s.trim();
            if s.starts_with('_') || s.ends_with('_') || s.contains("__") {
                return Err(de::Error::custom("LegacyFloatSyntax"));
            }
            s.replace('_', "")
                .parse::<f64>()
                .map_err(|_| de::Error::custom("LegacyFloatSyntax"))?
        }
        _ => return Err(de::Error::custom("LegacyFloatType")),
    };
    if !f.is_finite() {
        return Err(de::Error::custom("LegacyFloatFinite"));
    }
    Ok(f)
}

fn process(row: &Value) -> Result<Value, (String, String)> {
    let op = row["op"].as_str().unwrap();
    let fail = |layer: &str, e: String| (layer.to_string(), e);
    if op == "float" {
        let bits = u64::from_str_radix(row["bits"].as_str().unwrap(), 16)
            .map_err(|e| fail("transport", e.to_string()))?;
        let c = float_text(f64::from_bits(bits)).map_err(|e| fail("canonical", e))?;
        return Ok(json!({"status":"ok","canonical":c,"sha256":hash(c.as_bytes())}));
    }
    let data = unhex(row["hex"].as_str().unwrap()).map_err(|e| fail("transport", e))?;
    if op == "sha" {
        return Ok(json!({"status":"ok","sha256":hash(&data)}));
    }
    let s = std::str::from_utf8(&data).map_err(|e| fail("utf8", e.to_string()))?;
    // Only typed integer-bearing carriers normalize the lexical integer -0.
    // The scanner never rewrites text inside JSON strings or decimal/exponent tokens.
    let normalized = normalize_integer_zero(s);
    let s = if matches!(op, "u128" | "rational" | "leaf") {
        normalized.as_str()
    } else {
        s
    };
    let mut v = parse(s).map_err(|e| fail("strict-json", e))?;
    v = match op {
        "u128" => {
            integer_u128(&v).map_err(|e| fail("carrier", e))?;
            v
        }
        "rational" => {
            rational_value(&v).map_err(|e| fail("carrier", e))?;
            v
        }
        "leaf" => {
            leaf_value(&v).map_err(|e| fail("carrier", e))?;
            v
        }
        "json-float" => {
            let n = v
                .as_number()
                .ok_or_else(|| fail("carrier", "JsonFloatType".into()))?;
            let f = n
                .to_string()
                .parse::<f64>()
                .map_err(|_| fail("carrier", "JsonFloatFinite".into()))?;
            let n = Number::from_f64(f).ok_or_else(|| fail("carrier", "JsonFloatFinite".into()))?;
            Value::Number(n)
        }
        "sourced" => {
            let t: Sourced = serde_json::from_str(s).map_err(|e| fail("carrier", e.to_string()))?;
            let good = t.value.is_finite()
                && !t.unit.trim().is_empty()
                && match t.kind.as_str() {
                    "stipulation" => {
                        t.provenance.is_none()
                            && t.source.is_none()
                            && t.date.is_none()
                            && t.rationale.as_ref().is_some_and(|s| !s.trim().is_empty())
                    }
                    "claim" => {
                        t.rationale.is_none()
                            && match t.provenance {
                                Some(Calibration::Stub) => t.source.is_none(),
                                Some(_) => t.source.as_ref().is_some_and(|s| !s.trim().is_empty()),
                                None => false,
                            }
                    }
                    _ => false,
                };
            if !good {
                return Err(fail("carrier", "SourcedValue rules".into()));
            }
            serde_json::to_value(t).unwrap()
        }
        _ => v,
    };
    if op == "identity" || op == "exclude" {
        let field = row["field"].as_str().unwrap();
        let declared = v[field].clone();
        v.as_object_mut()
            .ok_or_else(|| fail("identity", "not an object".into()))?
            .remove(field);
        let c = canonical(&v).map_err(|e| fail("canonical", e))?;
        if op == "identity" && declared.as_str() != Some(&format!("sha256:{}", hash(c.as_bytes())))
        {
            return Err(fail("identity", "ArtifactHashMismatch".into()));
        }
    }
    let c = canonical(&v).map_err(|e| fail("canonical", e))?;
    Ok(json!({"status":"ok","canonical":c,"sha256":hash(c.as_bytes())}))
}
fn main() {
    let stdin = io::stdin();
    let mut out = io::BufWriter::new(io::stdout().lock());
    for line in stdin.lock().lines() {
        let row: Value =
            serde_json::from_str(&line.expect("input read")).expect("probe transport JSON");
        let mut result = match process(&row) {
            Ok(r) => r,
            Err((layer, error)) => json!({"status":"refuse","layer":layer,"error":error}),
        };
        result["id"] = row["id"].clone();
        serde_json::to_writer(&mut out, &result).expect("result write");
        writeln!(out).unwrap();
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn sha_vectors() {
        assert_eq!(
            hash(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }
    #[test]
    fn float_conventions() {
        for (x, s) in [
            (-0.0, "0.0"),
            (1e-7, "1e-07"),
            (1e20, "1e+20"),
            (1.0, "1.0"),
        ] {
            assert_eq!(float_text(x).unwrap(), s);
        }
    }
    #[test]
    fn duplicate_refusal() {
        assert!(parse(r#"{"a":1,"a":2}"#).is_err());
        assert!(parse(r#"{"x":{"a":1,"\u0061":2}}"#).is_err());
    }
    #[test]
    fn marker_refusal() {
        assert!(parse(r#"{"\u0024serde_json::private::Number":"1"}"#).is_err());
    }
    #[test]
    fn huge_integer_exact() {
        let s = u128::MAX.to_string();
        assert_eq!(canonical(&parse(&s).unwrap()).unwrap(), s);
    }
    #[test]
    fn strict_integer_tokens() {
        assert!(serde_json::from_str::<u128>("true").is_err());
        assert!(serde_json::from_str::<u128>("1.0").is_err());
    }
}

#[cfg(test)]
mod compatibility_tests {
    use super::*;
    fn result(op: &str, input: &str) -> Result<Value, (String, String)> {
        process(&json!({"op":op,"hex":hex(input.as_bytes())}))
    }
    #[test]
    fn explicit_leaf_rational_and_unbounded_integer() {
        for token in [
            "340282366920938463463374607431768211456",
            "-170141183460469231731687303715884105729",
        ] {
            let raw = format!(r#"{{"path":"x","value":{token}}}"#);
            assert_eq!(result("leaf", &raw).unwrap()["canonical"], raw);
        }
        assert_eq!(
            result(
                "leaf",
                r#"{"path":"x","value":{"numerator":1,"denominator":2}}"#
            )
            .unwrap()["canonical"],
            r#"{"path":"x","value":{"denominator":2,"numerator":1}}"#
        );
        for value in ["true", "false", "null", r#""1""#] {
            let raw = format!(r#"{{"path":"x","value":{value}}}"#);
            assert_eq!(result("leaf", &raw).unwrap()["canonical"], raw);
        }
    }
    #[test]
    fn rational_refusal_conditions() {
        for (raw, layer, reason) in [
            (
                r#"{"numerator":2,"denominator":4}"#,
                "carrier",
                "InvalidRatio",
            ),
            (
                r#"{"numerator":0,"denominator":2}"#,
                "carrier",
                "InvalidRatio",
            ),
            (
                r#"{"numerator":1,"denominator":0}"#,
                "carrier",
                "InvalidRatio",
            ),
            (
                r#"{"numerator":1,"denominator":1,"extra":0}"#,
                "carrier",
                "RationalFields",
            ),
            (r#"{"numerator":1}"#, "carrier", "RationalFields"),
            (
                r#"{"numerator":true,"denominator":1}"#,
                "carrier",
                "IntegerToken",
            ),
            (
                r#"{"numerator":340282366920938463463374607431768211456,"denominator":1}"#,
                "carrier",
                "IntegerRange",
            ),
        ] {
            assert_eq!(
                result("rational", raw).unwrap_err(),
                (layer.into(), reason.into())
            );
        }
        let (layer, error) = result(
            "leaf",
            r#"{"path":"x","value":{"numerator":1,"denominator":1,"denominator":1}}"#,
        )
        .unwrap_err();
        assert_eq!(layer, "strict-json");
        assert!(error.starts_with("DuplicateJsonKey"));
    }
    #[test]
    fn lexical_integer_zero_only() {
        assert_eq!(result("u128", "-0").unwrap()["canonical"], "0");
        assert_eq!(
            result("rational", r#"{"numerator":-0,"denominator":1}"#).unwrap()["canonical"],
            r#"{"denominator":1,"numerator":0}"#
        );
        assert_eq!(
            result("leaf", r#"{"path":"-0","value":"-0"}"#).unwrap()["canonical"],
            r#"{"path":"-0","value":"-0"}"#
        );
        for token in ["-0.0", "1e0", "true", r#""-0""#] {
            assert_eq!(
                result("u128", token).unwrap_err(),
                ("carrier".into(), "IntegerToken".into())
            );
        }
        assert_eq!(
            result("rational", r#"{"numerator":1,"denominator":-0}"#).unwrap_err(),
            ("carrier".into(), "InvalidRatio".into())
        );
    }
    #[test]
    fn legacy_float_local_compatibility() {
        for (token, canonical_value) in [
            ("false", "0.0"),
            ("true", "1.0"),
            (r#"" 1_.0 ""#, "1.0"),
            (r#""1e_2""#, "100.0"),
            (r#""1_0""#, "10.0"),
        ] {
            let raw = format!(
                r#"{{"value":{token},"unit":"Hz","kind":"stipulation","rationale":"test"}}"#
            );
            let got = result("sourced", &raw).unwrap();
            assert!(
                got["canonical"]
                    .as_str()
                    .unwrap()
                    .ends_with(&format!("\"value\":{canonical_value}}}"))
            );
        }
        for token in [r#""1__0""#, r#""NaN""#, "null", "{}"] {
            let raw = format!(
                r#"{{"value":{token},"unit":"Hz","kind":"stipulation","rationale":"test"}}"#
            );
            assert!(result("sourced", &raw).is_err());
        }
    }
    #[test]
    fn strict_float_and_leaf_stay_distinct() {
        for token in ["true", r#""1.0""#, "null"] {
            assert_eq!(
                result("json-float", token).unwrap_err(),
                ("carrier".into(), "JsonFloatType".into())
            );
        }
        assert_eq!(result("json-float", "1").unwrap()["canonical"], "1.0");
        assert_eq!(
            result("leaf", r#"{"path":"x","value":1.0}"#).unwrap_err(),
            ("carrier".into(), "IntegerToken".into())
        );
    }
    #[test]
    fn marker_guard_precedes_leaf_dispatch() {
        let (layer, error) = result(
            "leaf",
            r#"{"path":"x","value":{"\u0024serde_json::private::Number":"1"}}"#,
        )
        .unwrap_err();
        assert_eq!(layer, "strict-json");
        assert_eq!(error, "ReservedNumericMarker");
    }
}
