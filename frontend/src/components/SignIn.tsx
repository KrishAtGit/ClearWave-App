import { useState, type SubmitEvent } from "react";
import { api } from "../lib/api";

type FormState =
  | { kind: "idle" }
  | { kind: "sending" }
  | { kind: "sent"; email: string }
  | { kind: "error"; message: string };

export default function SignIn({ linkExpired }: { linkExpired: boolean }) {
  const [email, setEmail] = useState("");
  const [form, setForm] = useState<FormState>({ kind: "idle" });

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setForm({ kind: "sending" });
    try {
      await api.requestLink(email);
      setForm({ kind: "sent", email });
    } catch (error) {
      console.error("Reuqesting a sign-in link failed: ", error);
      setForm({
        kind: "error",
        message:
          "Could not send a link. Check the email address and try again.",
      });
    }
  }

  if (form.kind === "sent") {
    return (
      <section className="card" aria-live="polite">
        <h2>Check your email</h2>
        <p>
          We sent a sign-in link to <strong>{form.email}</strong>. It works once
          and expires in 15 minutes.
        </p>
        {import.meta.env.DEV && (
          <p className="hint">
            {" "}
            In development, the link is printed in the API terminal.
          </p>
        )}
        <button
          type="button"
          className="link"
          onClick={() => setForm({ kind: "idle" })}
        >
          Use different email
        </button>
      </section>
    );
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
        <h2>
            Sign In 
        </h2>
        {linkExpired && <p className="notice"> That link has expired or was already used. Please ask for a new one.</p>}
        <label htmlFor="email">Email</label>
        <input 
            id="email"
            type="email"
            required
            autoComplete="email"
            placeholder="joe.dane@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
        />
        <button type="submit" disabled={form.kind === "sending"}>
            {form.kind==='sending' ? 'Sending...' : 'Email me a sign-in link'}
        </button>
        {form.kind === 'error' && <p className="error">{form.message}</p>}
        <p className="hint">
            No password needed. New here? Signing in creates your account.
        </p>        
    </form>
  )
}
