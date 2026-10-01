PEAK_DEMAND_ALERT = "PEAK_DEMAND"
HIGH_SEVERITY = "HIGH"
MEDIUM_SEVERITY = "MEDIUM"
OPEN_STATUS = "OPEN"
THRESHOLD_PERCENTILE = 0.80

def calculate_threshold(predicted_values):
    """Calculate the regional peak-demand threshold using the top 20%% of the forecast range."""
    if not predicted_values:
        raise ValueError("Cannot calculate threshold from empty forecast values.")
    minimum = min(predicted_values)
    maximum = max(predicted_values)
    return minimum + THRESHOLD_PERCENTILE * (maximum - minimum)

def get_severity(predicted_kwh, threshold_kwh):
    """Assign alert severity based on how far demand exceeds the threshold."""
    if predicted_kwh >= threshold_kwh * 1.10:
        return HIGH_SEVERITY
    return MEDIUM_SEVERITY

def build_peak_demand_alert(forecast_date, region_name, predicted_kwh, threshold_kwh):
    """Build a standardized peak-demand alert record."""
    severity = get_severity(predicted_kwh, threshold_kwh)
    return {
        "alert_type": PEAK_DEMAND_ALERT,
        "severity": severity,
        "alert_date": forecast_date,
        "region_name": region_name,
        "predicted_kwh": predicted_kwh,
        "threshold_kwh": threshold_kwh,
        "trigger_reason": (
            f"Predicted demand of {predicted_kwh:.2f} kWh exceeded "
            f"the regional threshold of {threshold_kwh:.2f} kWh."
        ),
        "status": OPEN_STATUS,
    }
