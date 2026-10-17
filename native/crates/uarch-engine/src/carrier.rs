//! Closed K2 carrier shapes plus field-specific normalization. Joins are in admission.
use crate::wire;
use serde_json::{Number, Value};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Refusal {
    pub code: &'static str,
    pub message: String,
    pub pointer: String,
}
pub(crate) type Result<T> = std::result::Result<T, Refusal>;
pub(crate) fn refuse(code: &'static str, path: &str, message: impl Into<String>) -> Refusal {
    Refusal {
        code,
        message: message.into(),
        pointer: path.into(),
    }
}
fn field(path: &str, key: &str) -> String {
    format!("{}/{}", path, key.replace('~', "~0").replace('/', "~1"))
}
fn invalid(path: &str, message: impl Into<String>) -> Refusal {
    refuse("InvalidCarrier", path, message)
}
pub(crate) fn cmp_integer(a: &str, b: &str) -> std::cmp::Ordering {
    let an = a.starts_with('-');
    let bn = b.starts_with('-');
    match (an, bn) {
        (true, false) => std::cmp::Ordering::Less,
        (false, true) => std::cmp::Ordering::Greater,
        _ => {
            let aa = a.trim_start_matches('-');
            let bb = b.trim_start_matches('-');
            let order = aa.len().cmp(&bb.len()).then(aa.cmp(bb));
            if an { order.reverse() } else { order }
        }
    }
}
pub(crate) fn normalize(mut value: Value) -> Result<Value> {
    let schema: Value =
        serde_json::from_str(include_str!("carriers.json")).expect("compiled schema");
    shape(&mut value, &schema, &schema, "")?;
    Ok(value)
}
pub(crate) fn normalize_component(mut value: Value) -> Result<Value> {
    let schema: Value = serde_json::from_str(include_str!("component_carriers.json"))
        .expect("compiled component schema");
    shape(&mut value, &schema, &schema, "")?;
    Ok(value)
}
fn shape(v: &mut Value, s: &Value, root: &Value, path: &str) -> Result<()> {
    if let Some(reference) = s["$ref"].as_str() {
        let name = reference
            .strip_prefix("#/$defs/")
            .ok_or_else(|| invalid(path, "schema reference"))?;
        if name == "SourcedValue" {
            *v = wire::sourced(v).map_err(|e| invalid(path, e))?;
            return Ok(());
        }
        shape(v, &root["$defs"][name], root, path)?;
        if name == "RationalValue" {
            wire::rational_value(v).map_err(|e| invalid(path, e))?;
        }
        return Ok(());
    }
    if let Some(variants) = s
        .get("anyOf")
        .or_else(|| s.get("oneOf"))
        .and_then(Value::as_array)
    {
        for variant in variants {
            let mut attempt = v.clone();
            if shape(&mut attempt, variant, root, path).is_ok() {
                *v = attempt;
                return Ok(());
            }
        }
        return Err(invalid(path, "no carrier variant matches"));
    }
    if let Some(c) = s.get("const") {
        if path.ends_with("/transaction_bytes")
            && c == &Value::from(256)
            && v.as_f64() == Some(256.0)
        {
            *v = Value::from(256);
        }

        // Literal boolean in CoreClockDomain follows installed Pydantic literal:
        // JSON integer 1 is normalized to true, not an arbitrary truthy value.
        if c == &Value::Bool(true) && v.as_f64() == Some(1.0) {
            *v = Value::Bool(true);
        }
        if v != c {
            return Err(invalid(path, "literal mismatch"));
        }
    }
    if let Some(enums) = s["enum"].as_array()
        && !enums.contains(v)
    {
        return Err(invalid(path, "enum mismatch"));
    }
    match s["type"].as_str() {
        Some("null") => {
            if !v.is_null() {
                return Err(invalid(path, "null required"));
            }
        }
        Some("string") => {
            let text = v
                .as_str()
                .ok_or_else(|| invalid(path, "string token required"))?;
            if s["minLength"]
                .as_u64()
                .is_some_and(|n| text.chars().count() < (n as usize))
            {
                return Err(invalid(path, "short string"));
            }
            if let Some(pattern) = s["pattern"].as_str() {
                let good = match pattern {
                    "\\S" => !text.trim().is_empty(),
                    "^sha256:[0-9a-f]{64}$" => text.strip_prefix("sha256:").is_some_and(|s| {
                        s.len() == 64
                            && s.bytes()
                                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
                    }),
                    "^[0-9a-f]{40}$" => {
                        text.len() == 40
                            && text
                                .bytes()
                                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
                    }
                    _ => return Err(invalid(path, "unsupported compiled pattern")),
                };
                if !good {
                    return Err(invalid(path, "string pattern mismatch"));
                }
            }
        }
        Some("integer") => {
            // The only admitted non-strict integer fields are hardware coordinates.
            if path.contains("/attach/")
                && v.as_number()
                    .is_some_and(|n| n.to_string().contains(['.', 'e', 'E']))
            {
                let f = v
                    .as_f64()
                    .filter(|n| n.is_finite() && n.fract() == 0.0 && *n >= 0.0)
                    .ok_or_else(|| invalid(path, "integral coordinate required"))?;
                *v = wire::parse(&format!("{f:.0}")).map_err(|e| invalid(path, e))?;
            }
            let token = wire::integer_text(v).map_err(|e| invalid(path, e))?;
            for (key, strict, lower) in [
                ("minimum", false, true),
                ("exclusiveMinimum", true, true),
                ("maximum", false, false),
                ("exclusiveMaximum", true, false),
            ] {
                if let Some(bound) = s.get(key) {
                    let order = cmp_integer(&token, &bound.to_string());
                    let good = if lower {
                        order.is_gt() || (!strict && order.is_eq())
                    } else {
                        order.is_lt() || (!strict && order.is_eq())
                    };
                    if !good {
                        return Err(invalid(path, "integer range"));
                    }
                }
            }
        }
        Some("number") => {
            let f = v
                .as_number()
                .and_then(|n| n.to_string().parse::<f64>().ok())
                .filter(|f| f.is_finite())
                .ok_or_else(|| invalid(path, "finite JSON number required"))?;
            for (key, strict, lower) in [
                ("minimum", false, true),
                ("exclusiveMinimum", true, true),
                ("maximum", false, false),
                ("exclusiveMaximum", true, false),
            ] {
                if let Some(bound) = s[key].as_f64() {
                    let good = if lower {
                        f > bound || (!strict && f == bound)
                    } else {
                        f < bound || (!strict && f == bound)
                    };
                    if !good {
                        return Err(invalid(path, "number range"));
                    }
                }
            }
            *v = Value::Number(Number::from_f64(f).ok_or_else(|| invalid(path, "finite number"))?);
        }
        Some("boolean") => {
            // Strict booleans in NumericLeaf stay distinct; only installed hardware
            // scales_with_core uses the legacy bool carrier.
            if path.ends_with("/scales_with_core") && !v.is_boolean() {
                *v = match v {
                    Value::Number(n) if n.as_f64() == Some(0.0) => Value::Bool(false),
                    Value::Number(n) if n.as_f64() == Some(1.0) => Value::Bool(true),
                    Value::String(t) => match t.to_ascii_lowercase().as_str() {
                        "0" | "off" | "f" | "false" | "n" | "no" => Value::Bool(false),
                        "1" | "on" | "t" | "true" | "y" | "yes" => Value::Bool(true),
                        _ => return Err(invalid(path, "boolean required")),
                    },
                    _ => return Err(invalid(path, "boolean required")),
                };
            }
            if !v.is_boolean() {
                return Err(invalid(path, "boolean token required"));
            }
        }
        Some("array") => {
            let items = v
                .as_array_mut()
                .ok_or_else(|| invalid(path, "array required"))?;
            if s["minItems"]
                .as_u64()
                .is_some_and(|n| items.len() < n as usize)
                || s["maxItems"]
                    .as_u64()
                    .is_some_and(|n| items.len() > n as usize)
            {
                return Err(invalid(path, "array length"));
            }
            for (i, child) in items.iter_mut().enumerate() {
                let schema = if let Some(prefix) = s["prefixItems"].as_array() {
                    prefix.get(i).ok_or_else(|| invalid(path, "tuple length"))?
                } else {
                    &s["items"]
                };
                shape(child, schema, root, &field(path, &i.to_string()))?;
            }
        }
        Some("object") => {
            let obj = v
                .as_object_mut()
                .ok_or_else(|| invalid(path, "object required"))?;
            if let Some(props) = s["properties"].as_object() {
                if obj.keys().any(|k| !props.contains_key(k)) {
                    return Err(invalid(path, "unknown field"));
                }
                for (key, schema) in props {
                    if let Some(child) = obj.get_mut(key) {
                        shape(child, schema, root, &field(path, key))?;
                    } else if let Some(default) = schema.get("default") {
                        obj.insert(key.clone(), default.clone());
                    } else if s["required"]
                        .as_array()
                        .is_some_and(|a| a.contains(&Value::String(key.clone())))
                    {
                        return Err(invalid(&field(path, key), "missing field"));
                    }
                }
            } else {
                for (key, child) in obj {
                    if let Some(names) = s.get("propertyNames") {
                        shape(
                            &mut Value::String(key.clone()),
                            names,
                            root,
                            &field(path, key),
                        )?;
                    }
                    if s["additionalProperties"] == false {
                        return Err(invalid(path, "unknown mapping key"));
                    }
                    shape(child, &s["additionalProperties"], root, &field(path, key))?;
                }
            }
        }
        None => {}
        _ => return Err(invalid(path, "unsupported compiled carrier")),
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn field_local_hardware_normalization() {
        let root = serde_json::json!({});
        let mut coordinate = wire::parse("9007199254740993").unwrap();
        shape(
            &mut coordinate,
            &serde_json::json!({"type":"integer","minimum":0}),
            &root,
            "/memory/controllers/0/attach/0",
        )
        .unwrap();
        assert_eq!(coordinate.to_string(), "9007199254740993");
        let mut core_bool = serde_json::json!(1.0);
        shape(
            &mut core_bool,
            &serde_json::json!({"type":"boolean","const":true}),
            &root,
            "/clock_domains/core/scales_with_core",
        )
        .unwrap();
        assert_eq!(core_bool, serde_json::json!(true));
        let mut numeric_leaf = serde_json::json!(1.0);
        assert!(
            shape(
                &mut numeric_leaf,
                &serde_json::json!({"type":"integer"}),
                &root,
                "/hardware/leaves/0/value"
            )
            .is_err()
        );
    }
    #[test]
    fn exact_integer_bounds_without_float() {
        assert!(cmp_integer("18446744073709551616", "18446744073709551615").is_gt());
        assert!(cmp_integer("-340282366920938463463374607431768211456", "-1").is_lt());
    }
    #[test]
    fn strict_duplicate_marker_and_integer_tokens() {
        assert!(wire::parse(r#"{"x":1,"x":2}"#).is_err());
        assert!(wire::parse(r#"{"$serde_json::private::Number":"1"}"#).is_err());
        assert!(wire::integer_text(&serde_json::json!(1.0)).is_err());
        assert_eq!(
            wire::parse(&wire::normalize_integer_zero("-0")).unwrap(),
            serde_json::json!(0)
        );
    }
}
