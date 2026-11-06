import { useState, type SubmitEvent } from "react";
import { api, type Claim } from "../lib/api"

const MAX_UPLOAD_MB = 20;
type UploadState = 
    | { kind: "idle"}
    | { kind : "uploading"}
    | { kind: "error"; message: string};

export default function UploadClaim({
    onUploaded,
}: {
    onUploaded: (claim: Claim) => void;
}) {
    const [title, setTitle] = useState("");
    // file -> value, setFile -> func that updates file
    // <File | null> : can hold either "File" value (.mp3 and so on) or null, with starting value as null
    const [file, setFile] = useState<File | null>(null);
    const [upload, setUpload] = useState<UploadState>({kind : 'idle'})

    function handleFileChange(chosen : File | null){
        setFile(chosen);
        if (chosen && title.trim() == ""){
            setTitle(chosen.name.replace(/\.[^.]+$/, ""));
        }
    }

    async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    
    if (!file)
        return;

    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setUpload({ 
        kind: "error", 
        message: `File is too large, over ${MAX_UPLOAD_MB} MB.` 
        });
      return;
    }

    setUpload({kind: "uploading"});
    try{
        const claim = await api.uploadClaim(title.trim(), file);
        onUploaded(claim);
        formElement.reset();
        setTitle("");
        setFile(null);
        setUpload({
            kind: "idle"
        });
    } 
    catch(error){
        console.error("Uploading a sample failed: ", error)
        setUpload({
            kind: "error",
            message: error instanceof Error ? error.message : "Upload failed. Please try again."
        });
    }
}

    const uploading = upload.kind === "uploading";
    
    return (
        <form className="card" onSubmit={handleSubmit}>
            <h2>Upload a sample</h2>

            <label htmlFor="sample-file">Audio file</label>
            <input
                id="sample-file"
                type="file"
                accept="audio/*,.wav,.mp3,.flac,.ogg,.aif,.aiff,.m4a"
                required
                disabled={uploading}
                onChange={
                    (event) => handleFileChange(event.target.files?.[0] ?? null)
                }
            />

            <label htmlFor="sample-title">Title</label>
            <input 
                id="sample-title"
                type="text"
                required
                maxLength={200}
                placeholder="Weird ahh drums"
                value={title}
                disabled={uploading}
                onChange={
                    (event) => setTitle(event.target.value)
                }    
            />

            <button type="submit" disabled={uploading || !file}>
                {uploading ? "Uploading..." : "Upload sample"}
            </button>

            {upload.kind == "error" && <p className="error">{upload.message}</p>}
            <p className="hint">
                WAV, MP3, FLAC, OGG, AIFF or M4A, with up to {MAX_UPLOAD_MB} MB only.
            </p>
        </form>
    );
}