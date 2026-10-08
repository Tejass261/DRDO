export default function ValueGroup({ title, children, className = "" }) {
  return (
    <div className={`value-group ${className}`.trim()}>
      <div className="value-group-title">{title}</div>
      <div className="value-group-content">{children}</div>
    </div>
  );
}
