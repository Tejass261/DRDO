// ============================================================
// SENSOR GRAPH (SVG line chart, no libraries)
// ============================================================
//
// series = [
//   { label, color, points: [number, number, ...] }
// ]
//
// The newest point is the LAST item in each points array,
// so the newest value is drawn on the RIGHT side.
// ============================================================

export default function SensorGraph({ series, yLabel }) {

  // ---- Collect all values to scale the Y axis ----

  const allValues = [];

  for (const line of series) {
    for (const value of line.points) {
      if (Number.isFinite(value)) {
        allValues.push(value);
      }
    }
  }

  // Nothing to draw yet.
  if (allValues.length === 0) {
    return (
      <div className="graph-empty">
        Waiting for data to draw the graph…
      </div>
    );
  }

  let min = Math.min(...allValues);
  let max = Math.max(...allValues);

  // If every value is identical, give the axis some height
  // so the line doesn't fill the whole box.
  if (min === max) {
    min = min - 1;
    max = max + 1;
  }

  // ---- SVG drawing area ----

  const WIDTH = 600;
  const HEIGHT = 210;
  const PAD_LEFT = 48;
  const PAD_RIGHT = 12;
  const PAD_TOP = 12;
  const PAD_BOTTOM = 24;

  const innerWidth = WIDTH - PAD_LEFT - PAD_RIGHT;
  const innerHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;

  const maxPoints = Math.max(
    ...series.map(line => line.points.length),
    2
  );

  function xFor(index) {
    return PAD_LEFT + (index / (maxPoints - 1)) * innerWidth;
  }

  function yFor(value) {
    return PAD_TOP + innerHeight - ((value - min) / (max - min)) * innerHeight;
  }

  // ---- Y axis grid lines ----

  const gridLines = [];

  for (let step = 0; step <= 4; step++) {
    const fraction = step / 4;
    const value = min + fraction * (max - min);
    const y = yFor(value);
    gridLines.push(
      <g key={step}>
        <line
          x1={PAD_LEFT}
          y1={y}
          x2={WIDTH - PAD_RIGHT}
          y2={y}
          className="graph-grid"
        />
        <text
          x={PAD_LEFT - 7}
          y={y + 4}
          textAnchor="end"
          className="graph-axis-text"
        >
          {value.toFixed(1)}
        </text>
      </g>
    );
  }

  // ---- Latest value per line (for the legend) ----

  const latestValues = series.map(line => {
    const numbers = line.points.filter(Number.isFinite);
    return numbers[numbers.length - 1];
  });

  return (
    <div className="graph-box">

      <div className="graph-legend">
        {series.map((line, index) => (
          <span key={line.key || line.label}>
            <i style={{ background: line.color }} />
            {line.label}
            {Number.isFinite(latestValues[index]) && (
              <b>: {latestValues[index]}</b>
            )}
          </span>
        ))}
      </div>

      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="live-graph"
        preserveAspectRatio="none"
      >
        {gridLines}

        <text
          x={10}
          y={HEIGHT / 2}
          textAnchor="middle"
          className="graph-axis-text"
          transform={`rotate(-90 10 ${HEIGHT / 2})`}
        >
          {yLabel}
        </text>

        {series.map(line => {
          const points = line.points
            .map((value, index) => {
              if (!Number.isFinite(value)) {
                return null;
              }
              return `${xFor(index)},${yFor(value)}`;
            })
            .filter(Boolean)
            .join(" ");

          if (!points) {
            return null;
          }

          return (
            <polyline
              key={line.key || line.label}
              points={points}
              fill="none"
              stroke={line.color}
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />
          );
        })}
      </svg>

    </div>
  );
}
