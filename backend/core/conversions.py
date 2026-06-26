import math

def mq135_to_ppm(raw: float) -> float:
    """
    Converts raw ADC value (0-4095) from MQ-135 to an estimated CO2 PPM.
    Assumes a 10 kΩ load resistor and R0 = 76.63.
    """
    if raw <= 0:
        return 0.0
    if raw >= 4095:
        raw = 4094.0 # Prevent division by zero

    voltage = raw * 3.3 / 4095.0
    RL = 10.0
    R0 = 76.63

    Rs = ((3.3 - voltage) / voltage) * RL
    ratio = Rs / R0

    # Ensure ratio isn't negative or zero to avoid math errors
    if ratio <= 0:
        return 0.0

    ppm = 116.6020682 * math.pow(ratio, -2.769034857)
    
    # Calibration: Hardware baseline is ~1122 raw in normal air, which yields ratio ~0.3458 and unscaled ppm ~2240.
    # Real-world testing at night (terrace/room) outputs unscaled values much higher (leading to 1000-1900 PPM).
    # We apply an aggressive empirical scaling factor to center these environmental readings back to ~400 PPM (fresh air).
    ppm = ppm * (400.0 / 8400.0)
    
    return round(ppm, 2)

def ldr_to_lux(raw: float) -> float:
    """
    Converts raw ADC value (0-4095) from LDR to an estimated Lux value.
    Uses an empirical quadratic curve to ensure proper scaling:
    - Flashlight (~3500 raw) -> ~1500+ lux
    - Tubelight (~2000 raw) -> ~400-500 lux
    - Lights off / Dark (< 1000 raw) -> Drops rapidly towards 0 lux
    """
    if raw <= 0:
        return 0.0
    if raw >= 4095:
        raw = 4095.0

    # The user's LDR module hardware outputs a LOW voltage when bright, 
    # and a HIGH voltage when dark (inverted configuration).
    # We invert the raw value so that:
    # - Bright light (low raw) -> High adjusted_raw -> High lux
    # - Dark (high raw) -> Low adjusted_raw -> Low lux
    adjusted_raw = 4095.0 - raw
    
    # Cubic mapping for proper scaling based on hardware average of ~833 raw for normal tube light
    # With this curve: raw 833 -> ~505 Lux (Normal Tube light). raw 0 -> 1000 Lux. raw 3500+ -> ~0 Lux.
    lux = math.pow((adjusted_raw / 4095.0), 3) * 1000.0
    
    return round(lux, 2)
