use crate::Error;
const PS_PER_SECOND: u128 = 1_000_000_000_000;

/// First rounded edge at or after t_ps, plus n_cycles. Never round a period.
pub fn next_edge(freq_hz: u64, t_ps: u64, n_cycles: u64) -> Result<u64, Error> {
    if freq_hz == 0 {
        return Err(Error::InvalidClock);
    }
    let freq = u128::from(freq_hz);
    // ceil(k*S/f) >= t iff k*S > (t-1)*f, for positive integer t.
    let k = if t_ps == 0 {
        0
    } else {
        u128::from(t_ps - 1)
            .checked_mul(freq)
            .ok_or(Error::TimeOverflow)?
            / PS_PER_SECOND
            + 1
    };
    let numerator = k
        .checked_add(u128::from(n_cycles))
        .and_then(|v| v.checked_mul(PS_PER_SECOND))
        .ok_or(Error::TimeOverflow)?;
    u64::try_from(numerator.div_ceil(freq)).map_err(|_| Error::TimeOverflow)
}
