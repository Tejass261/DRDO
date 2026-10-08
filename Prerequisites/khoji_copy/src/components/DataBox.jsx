export function valueOrDash(value) {
  return value === undefined || value === null || value === "" ? "--" : value;
}

export default function DataBox({ label, value, unit = "", emphasis = false, className = "" }) {
  const displayValue = valueOrDash(value);

  return (
    <div className={`data-box ${emphasis ? "data-box-emphasis" : ""} ${className}`.trim()}>
      <div className="data-label">{label}</div>
      <div className="data-value">
        {displayValue}
        {unit && displayValue !== "--" ? ` ${unit}` : ""}
      </div>
    </div>
  );
}
