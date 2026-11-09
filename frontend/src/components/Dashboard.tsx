import { useEffect, useState } from "react";
import { api, type Claim } from "../lib/api";
import ClaimsList from "./ClaimsList";
import UploadClaim from "./UploadForm";
import ClaimPage from "./ClaimPage";

type ClaimsState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; claims: Claim[] };

export default function Dashboard() {
  const [state, setState] = useState<ClaimsState>({ kind: "loading" });
  const [openClaimId, setOpenClaimId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let ignore = false;
    api
      .listClaims()
      .then((claims) => {
        if (!ignore) 
          setState({ kind: "ready", claims });
      })
      .catch((error) => {
        console.error("Loading claims failed: ", error);
        if (!ignore)
          setState({
            kind: "error",
            message: "Could not load your samples. Refresh to try again!",
          });
      });
    return () => {
      ignore = true;
    };
  }, [refreshKey]);

  function handleUploaded(claim: Claim) {
    setOpenClaimId(claim.id);
  }

  function handleBack() {
    setOpenClaimId(null);
    setRefreshKey((key) => key + 1)
  }

  function handleDeleted(id: string){
    setState((prev) => {
      if (prev.kind === "ready") {
        const updatedClaims = prev.claims.filter(
          (claim) => claim.id !== id
        );
        return { 
          kind: "ready", 
          claims: updatedClaims 
        };
      }
      return prev;
    });
  }

  if(openClaimId != null) {
    return <ClaimPage claimId={openClaimId} onBack={handleBack} />;
  }

  return (
    <>
    <UploadClaim onUploaded={handleUploaded}/>
    {state.kind === "loading" && <p className="hint">Loading your samples...</p>}
    {state.kind === "error" && <p className="error">{state.message}</p>}
    {state.kind === "ready" && <ClaimsList claims = {state.claims} onDeleted={handleDeleted} onOpen={setOpenClaimId}/>}
    </>
  );
}
