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
#[serde(untagged)]
enum LeafValue {
    Rational(Rational),
    Unsigned(u128),
    Signed(i128),
    Text(String),
    Bool(bool),
    Null(()),
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Leaf {
    path: String,
    value: LeafValue,
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
fn typed<T: serde::de::DeserializeOwned + Serialize>(s: &str) -> Result<Value, String> {
    let t: T = serde_json::from_str(s).map_err(|e| e.to_string())?;
    serde_json::to_value(t).map_err(|e| e.to_string())
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
    let mut v = parse(s).map_err(|e| fail("strict-json", e))?;
    v = match op {
        "u128" => typed::<u128>(s).map_err(|e| fail("carrier", e))?,
        "rational" => {
            let t: Rational =
                serde_json::from_str(s).map_err(|e| fail("carrier", e.to_string()))?;
            t.check().map_err(|e| fail("carrier", e))?;
            serde_json::to_value(t).unwrap()
        }
        "leaf" => {
            let t: Leaf = serde_json::from_str(s).map_err(|e| fail("carrier", e.to_string()))?;
            if t.path.trim().is_empty() {
                return Err(fail("carrier", "empty path".into()));
            }
            if let LeafValue::Rational(r) = &t.value {
                r.check().map_err(|e| fail("carrier", e))?;
            }
            serde_json::to_value(t).unwrap()
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
