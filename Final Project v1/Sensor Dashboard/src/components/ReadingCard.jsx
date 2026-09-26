// ============================================================
// READING CARD
// ============================================================
//
// One value box in the sensor detail page's reading grid.
// Shows "—" until a reading has been received.
// ============================================================

export default function ReadingCard({ label, value, hasReading }) {
  return (
    <div>
      <span>{label}</span>
      <strong className={hasReading ? "" : "reading-empty"}>
        {value}
      </strong>
    </div>
  );
}
