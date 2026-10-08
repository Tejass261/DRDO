import { valueOrDash } from "./DataBox";

export default function MainValues({ data }) {
  return (
    <div className="main-values">
      <div className="main-value-box g-main">
        <div className="main-value-label">G VALUE</div>
        <div className="main-value">{valueOrDash(data.gValue)}</div>
      </div>
      <div className="main-value-box h-main">
        <div className="main-value-label">H VALUE</div>
        <div className="main-value">{valueOrDash(data.hValue)}</div>
      </div>
    </div>
  );
}
