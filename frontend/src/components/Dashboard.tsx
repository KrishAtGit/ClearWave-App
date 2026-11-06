import { useEffect, useState } from "react";
import { api, type Claim } from "../lib/api";
import ClaimsList from "./ClaimsList";
import UploadClaim from "./UploadForm";

type ClaimsState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; claims: Claim[] };

export default function Dashboard() {
  const [state, setState] = useState<ClaimsState>({ kind: "loading" });
  useEffect(() => {
    let ignore = false;
    api
      .listClaims()
      .then((claims) => {
        if (!ignore) setState({ kind: "ready", claims });
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
  }, []);
  function handleUploaded(claim: Claim) {
    setState((prev) => {
      if (prev.kind === "ready") {
        const updatedClaims = [claim, ...prev.claims];
        return { kind: "ready", claims: updatedClaims };
      }
      return prev;
    });
  }

  function handleDeleted(id: string){
    setState((prev) => {
        if(prev.kind === "ready"){
            const updatedClaims = prev.claims.filter((claim) => claim.id !==id)
            return{
                kind: "ready", claims: updatedClaims
            }
        }
        return prev;
    });
  }

  return (
    <>
    <UploadClaim onUploaded={handleUploaded}/>
    {state.kind === "loading" && <p className="hint">Loading your samples...</p>}
    {state.kind === "error" && <p className="error">{state.message}</p>}
    {state.kind === "ready" && <ClaimsList claims = {state.claims} onDeleted={handleDeleted}/>}
    </>
  );
}
