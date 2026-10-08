export default function Section({ title, children, className = "" }) {
  return (
    <section className={`section ${className}`.trim()}>
      <div className="section-title">{title}</div>
      {children}
    </section>
  );
}
