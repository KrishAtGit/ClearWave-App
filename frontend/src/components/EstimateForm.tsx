import { useState, type SubmitEvent } from "react";
import { api, type Match } from "../lib/api";

// formats numbers as US dollars: 2100000 -> "$2,100,000.00"
const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export default function EstimateForm({
  claimId,
  match,
  payoutPerStream,
  payoutSource,
  onSaved,
}: {
  claimId: string;
  match: Match;
  payoutPerStream: number;
  payoutSource: string;
  onSaved: (updated: Match) => void;
}) {
  // inputs start with the saved values, if there are any
  const [streamsText, setStreamsText] = useState(match.streams?.toString() ?? "");
  const [shareText, setShareText] = useState(match.share_percent?.toString() ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    // let people type "2,100,000,000" or "2 100 000 000"
    const streams = Number(streamsText.replace(/[,\s]/g, ""));
    const share = Number(shareText);

    if (!Number.isInteger(streams) || streams < 0) {
      setError("Enter the streams as a whole number, e.g. 2,100,000,000.");
      return;
    }
    if (Number.isNaN(share) || share < 0 || share > 100) {
      setError("Enter a share between 0 and 100.");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateEstimate(claimId, match.id, streams, share);
      onSaved(updated);
    } catch (err) {
      console.error("Saving the estimate failed: ", err);
      setError(err instanceof Error ? err.message : "Could not save the estimate. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  const hasEstimate =
    match.estimated_value !== null && match.streams !== null && match.share_percent !== null;

  return (
    <form className="estimate" onSubmit={handleSubmit}>
      <h4>Royalty estimate</h4>

      <div className="estimate-fields">
        <div className="field">
          <label htmlFor={`streams-${match.id}`}>Streams</label>
          <input
            id={`streams-${match.id}`}
            inputMode="numeric"
            required
            placeholder="2,100,000,000"
            value={streamsText}
            onChange={(event) => setStreamsText(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor={`share-${match.id}`}>Sample share %</label>
          <input
            id={`share-${match.id}`}
            type="number"
            min={0}
            max={100}
            step="any"
            required
            placeholder="25"
            value={shareText}
            onChange={(event) => setShareText(event.target.value)}
          />
        </div>
      </div>

      {match.spotify_track_id && (
        <p className="hint">
          Find the play count on{" "}
          <a href={`https://open.spotify.com/track/${match.spotify_track_id}`} target="_blank" rel="noopener noreferrer">
            Spotify
          </a>{" "}
          (shown next to the track on its album page).
        </p>
      )}

      <button type="submit" disabled={saving}>
        {saving ? "Calculating..." : "Calculate estimate"}
      </button>
      {error && <p className="error">{error}</p>}

      {hasEstimate && (
        <div className="estimate-result" aria-live="polite">
          <p className="estimate-total">≈ {money.format(match.estimated_value!)}</p>
          <p className="hint">
            {match.streams!.toLocaleString()} streams × ${payoutPerStream} per stream × {match.share_percent}% share
          </p>
          <details className="hint">
            <summary>Where does ${payoutPerStream} come from?</summary>
            <p>{payoutSource}</p>
          </details>
          <p className="hint">A rough estimate for guidance only, not legal or financial advice.</p>
        </div>
      )}
    </form>
  );
}