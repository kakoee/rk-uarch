//! Token-preserving JSON and reconciled C2 scalar routines; no host authority.
use serde::de::{self, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::{Map, Number, Value};
use sha2::{Digest, Sha256};
use std::fmt;
use std::str::FromStr;

#[inline(never)]
pub fn c2_sha256_boundary(input: &[u8]) -> [u8; 32] {
    Sha256::digest(input).into()
}
fn hex(data: &[u8]) -> String {
    data.iter().map(|b| format!("{b:02x}")).collect()
}
pub(crate) fn hash(data: &[u8]) -> String {
    hex(&c2_sha256_boundary(data))
}

// The reviewed formatter uses the existing serializer's shortest digits. Only
// Python's notation threshold, exponent sign/padding and integral .0 are applied.
pub(crate) fn float_text(f: f64) -> Result<String, String> {
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
pub(crate) fn parse(s: &str) -> Result<Value, String> {
    reserved_key_guard(s)?;
    let mut d = serde_json::Deserializer::from_str(s);
    let Strict(v) = Strict::deserialize(&mut d).map_err(|e| e.to_string())?;
    d.end().map_err(|e| e.to_string())?;
    Ok(v)
}
pub(crate) fn canonical(v: &Value) -> Result<String, String> {
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
pub(crate) fn gcd(mut a: u128, mut b: u128) -> u128 {
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
pub(crate) fn integer_text(v: &Value) -> Result<String, String> {
    let Value::Number(n) = v else {
        return Err("IntegerToken".into());
    };
    let token = n.to_string();
    if token.contains(['.', 'e', 'E']) {
        return Err("IntegerToken".into());
    }
    Ok(token)
}
pub(crate) fn integer_u128(v: &Value) -> Result<u128, String> {
    integer_text(v)?
        .parse::<u128>()
        .map_err(|_| "IntegerRange".into())
}
pub(crate) fn rational_value(v: &Value) -> Result<(), String> {
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
pub(crate) fn normalize_integer_zero(s: &str) -> String {
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

// Pinned CPython 3.12 / Unicode 15.0 str.strip() emptiness set, independently
// enumerated in python-freeze.json. This predicate never changes stored text and
// is restricted to Sourced unit/rationale/non-stub source; numeric trim is separate.
fn sourced_nonblank(s: &str) -> bool {
    s.chars().any(|c| {
        !matches!(c,
            '\u{0009}'..='\u{000d}' | '\u{001c}'..='\u{0020}' |
            '\u{0085}' | '\u{00a0}' | '\u{1680}' | '\u{2000}'..='\u{200a}' |
            '\u{2028}' | '\u{2029}' | '\u{202f}' | '\u{205f}' | '\u{3000}'
        )
    })
}

pub(crate) fn sourced(v: &Value) -> Result<Value, String> {
    let t: Sourced = serde_json::from_str(&canonical(v)?).map_err(|e| e.to_string())?;
    let good = t.value.is_finite()
        && sourced_nonblank(&t.unit)
        && match t.kind.as_str() {
            "stipulation" => {
                t.provenance.is_none()
                    && t.source.is_none()
                    && t.date.is_none()
                    && t.rationale.as_ref().is_some_and(|s| sourced_nonblank(s))
            }
            "claim" => {
                t.rationale.is_none()
                    && match t.provenance {
                        Some(Calibration::Stub) => t.source.is_none(),
                        Some(_) => t.source.as_ref().is_some_and(|s| sourced_nonblank(s)),
                        None => false,
                    }
            }
            _ => false,
        };
    if !good {
        return Err("SourcedValue rules".into());
    }
    serde_json::to_value(t).map_err(|e| e.to_string())
}
