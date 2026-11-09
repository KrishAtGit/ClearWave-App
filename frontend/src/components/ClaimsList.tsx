import { useState } from "react";
import {api, type Claim, type ClaimStatus} from "../lib/api";

const STATUS_LABELS: Record<ClaimStatus, string> = {
    uploaded: "Uploaded",
    matching: "Matching...",
    matched: "Matched",
    failed: "Matching failed"
};

function formatSize(bytes: number): string{
    if(bytes < 1024*1024) {
        return `${Math.round(bytes / 1024)} KB`
    }
    return `${(bytes / (1024*1024)).toFixed(1)} MB`;
}

export default function ClaimsList(
    { claims, onDeleted, onOpen } : { 
        claims: Claim[]; 
        onDeleted: (id: string) => void;
        onOpen: (id: string) => void;
    }
) {
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    
    async function handleDelete(claim: Claim){
        if(!window.confirm(`Delete "${claim.title}"? This also deletes the audio file.`))
            return;

        setDeletingId(claim.id);
        setError(null);
        try{
            await api.deleteClaim(claim.id);
            onDeleted(claim.id);
        }
        catch(err){
            console.error("Deleting the claim failed: ", err);
            setError(err instanceof Error ? err.message : "Could not delete the sample. Please try again");
        } 
        finally {
            setDeletingId(null);
        }
    }

    if (claims.length === 0){
        return <p className="hint">No samples yet. Upload one abov to get started.</p>
    }

    return(
        <section className="claims">
            <h2>Your samples</h2>
            {error && <p className="error">{error}</p>}
            <ul>
                {claims.map((claim) => (
                    <li key={claim.id} className="claim">
                        <div className="claim-info">
                            <button className="link claim-title" type="button" onClick={() => onOpen(claim.id)}> {claim.title}</button>
                            <span className="hint">
                                {claim.original_filename} - {formatSize(claim.size_bytes)} - {" "}
                                {new Date(claim.created_at).toLocaleDateString()}
                            </span>
                        </div>
                        <span className={`status status-${claim.status}`}>{STATUS_LABELS[claim.status]}</span>
                        <button 
                            type="button"
                            className="link"
                            disabled={deletingId === claim.id}
                            onClick={() => handleDelete(claim)}
                        >
                            {deletingId === claim.id ? "Deleting..." :  "Delete"}
                        </button>
                    </li>
                ))}
            </ul>
        </section>
    );


}