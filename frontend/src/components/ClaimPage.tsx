import { useEffect, useState, useRef } from "react";
import {
  api,
  type ClaimDetail,
  type ClaimStatus,
  type Match,
} from "../lib/api";
import EstimateForm from "./EstimateForm";
// how often to re-check while matching is running
const POLL_MS = 2000;

type PageState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; claim: ClaimDetail };

// one recording, shown once, even if ACRCloud found it on several releases
type SongGroup = { main: Match; otherReleases: Match[] };

function groupByRecording(matches: Match[]): SongGroup[] {
  const groups = new Map<string, SongGroup>();
  for (const match of matches) {
    // same ISRC = same recording; without an ISRC we can't tell, so it stays on its own
    const key = match.isrc ?? match.id;
    const existing = groups.get(key);
    if (existing) {
      existing.otherReleases.push(match);
    } else {
      groups.set(key, { main: match, otherReleases: [] });
    }
  }
  return [...groups.values()];
}

// 46.26 -> "0:46"
function formatOffset(seconds: number): string {
  const whole = Math.floor(seconds);
  const minutes = Math.floor(whole / 60);
  const rest = String(whole % 60).padStart(2, "0");
  return `${minutes}:${rest}`;
}

function isWorking(status: ClaimStatus): boolean {
  return status === "uploaded" || status === "matching";
}

export default function ClaimPage({
  claimId,
  onBack,
}: {
  claimId: string;
  onBack: () => void;
}) {
  const [state, setState] = useState<PageState>({ kind: "loading" });
  const refreshedAudio = useRef(false);

  useEffect(() => {
    let ignore = false;
    let timer: number | undefined;

    async function load() {
      try {
        const claim = await api.getClaim(claimId);
        if (ignore) return;

        setState((prev) => {
          if (prev.kind === "ready") {
            // keep the first audio link: a new link on every poll would restart the player
            return {
              kind: "ready",
              claim: { ...claim, audio_url: prev.claim.audio_url },
            };
          }
          return { kind: "ready", claim };
        });

        // still working? check again in 2 seconds
        if (isWorking(claim.status)) {
          timer = window.setTimeout(load, POLL_MS);
        }
      } catch (error) {
        console.error("Loading the claim failed: ", error);
        if (!ignore) {
          setState({
            kind: "error",
            message: "Could not load this sample. Go back and try again.",
          });
        }
      }
    }

    load();

    // leaving the page: ignore late answers and cancel the next scheduled check
    return () => {
      ignore = true;
      window.clearTimeout(timer);
    };
  }, [claimId]);

  async function refreshAudioLink(){
    if (refreshedAudio.current)
        return
    refreshedAudio.current = true;
    try{
        const fresh = await api.getClaim(claimId);
        setState((prev) => {
            if(prev.kind === 'ready'){
                return {kind: "ready", claim: {
                    ...prev.claim, audio_url: fresh.audio_url
                }};
            }
            return prev;
        });

    }
    catch(err){
        console.error("Refreshing the audio link failed: ", err);
    }
  }

  // swap the saved match into the claim, so the card shows the new estimate
  function handleMatchSaved(updated: Match) {
    setState((prev) => {
      if (prev.kind === "ready") {
        const matches = prev.claim.matches.map((match) => (match.id === updated.id ? updated : match));
        return { kind: "ready", claim: { ...prev.claim, matches } };
      }
      return prev;
    });
  }

  if (state.kind === "loading") {
    return <p className="hint">Loading...</p>;
  }

  if (state.kind === "error") {
    return (
      <section className="claim-page">
        <button type="button" className="link" onClick={onBack}>
          ← All samples
        </button>
        <p className="error">{state.message}</p>
      </section>
    );
  }

  const { claim } = state;
  const songs = groupByRecording(claim.matches);

  return (
    <section className="claim-page">
      <button type="button" className="link" onClick={onBack}>
        ← All samples
      </button>

      <header>
        <h2>{claim.title}</h2>
        <p className="hint">{claim.original_filename}</p>
      </header>

      <audio controls preload="none" src={claim.audio_url} onError={refreshAudioLink}/>

      {isWorking(claim.status) && (
        <p className="hint" aria-live="polite">
          Searching released songs for your sample...
        </p>
      )}
      {claim.status === "failed" && (
        <p className="error">
          Matching failed. Please try uploading the sample again later.
        </p>
      )}
      {claim.status === "matched" && songs.length === 0 && (
        <p className="hint">No released songs found containing this sample.</p>
      )}

      {songs.length > 0 && (
        <>
          <h3>
            Found in {songs.length} {songs.length === 1 ? "song" : "songs"}
          </h3>
          <ul className="songs">
            {songs.map((group) => (
              <SongCard 
              key={group.main.id} 
              group={group} 
              claimId={claim.id}
              payoutPerStream={claim.payout_per_stream}
              payoutSource={claim.payout_source}
              onSaved={handleMatchSaved}
              />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function SongCard({
  group,
  claimId,
  payoutPerStream,
  payoutSource,
  onSaved,
}: {
  group: SongGroup;
  claimId: string;
  payoutPerStream: number;
  payoutSource: string;
  onSaved: (updated: Match) => void;
}) {
  const { main, otherReleases } = group;
  // "The Album · Some Label · 2015", skipping whatever is missing
  const details = [main.album, main.label, main.release_date?.slice(0, 4)]
    .filter(Boolean)
    .join(" · ");

  return (
    <li className="song">
      <div className="song-head">
        <div>
          <strong>{main.title}</strong>
          <span>{main.artists.join(", ")}</span>
        </div>
        <span className="score">Confidence {main.score}</span>
      </div>

      {details && <p className="hint">{details}</p>}
      {main.offset_seconds !== null && (
        <p className="hint">
          Your sample appears at {formatOffset(main.offset_seconds)}
        </p>
      )}
      {main.composers.length > 0 && (
        <p className="hint">Written by {main.composers.join(", ")}</p>
      )}

      <p className="song-links">
        {main.spotify_track_id && (
          <a
            href={`https://open.spotify.com/track/${main.spotify_track_id}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            Spotify
          </a>
        )}
        {main.youtube_video_id && (
          <a
            href={`https://www.youtube.com/watch?v=${main.youtube_video_id}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            YouTube
          </a>
        )}
        {main.isrc && <span className="hint">ISRC {main.isrc}</span>}
      </p>

      {otherReleases.length > 0 && (
        <p className="hint">
          Also on {otherReleases.length} other{" "}
          {otherReleases.length === 1 ? "release" : "releases"}
        </p>
      )}
      <EstimateForm
        claimId={claimId}
        match={main}
        payoutPerStream={payoutPerStream}
        payoutSource={payoutSource}
        onSaved={onSaved}
      />

    </li>
  );
}
