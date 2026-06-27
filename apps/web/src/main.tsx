import React, { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { BookOpen, Link, MessageSquareText, ScrollText, Send } from "lucide-react";
import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type Campaign = {
  id: string;
  name: string;
  tone: string;
};

type Session = {
  id: string;
  session_date: string;
  label: string | null;
  note_count: number;
};

type Citation = {
  label: string;
};

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    }
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json() as Promise<T>;
}

function App() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [status, setStatus] = useState("");

  const selectedCampaign = campaigns.find((campaign) => campaign.id === selectedCampaignId);

  async function refreshCampaigns() {
    const nextCampaigns = await api<Campaign[]>("/campaigns");
    setCampaigns(nextCampaigns);
    if (!selectedCampaignId && nextCampaigns.length > 0) {
      setSelectedCampaignId(nextCampaigns[0].id);
    }
  }

  async function refreshSessions(campaignId: string) {
    if (!campaignId) {
      setSessions([]);
      return;
    }
    setSessions(await api<Session[]>(`/campaigns/${campaignId}/sessions`));
  }

  useEffect(() => {
    refreshCampaigns().catch((error) => setStatus(error.message));
  }, []);

  useEffect(() => {
    refreshSessions(selectedCampaignId).catch((error) => setStatus(error.message));
  }, [selectedCampaignId]);

  async function createCampaign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const campaign = await api<Campaign>("/campaigns", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        tone: form.get("tone"),
        owner_display_name: form.get("owner")
      })
    });
    setCampaigns([campaign, ...campaigns]);
    setSelectedCampaignId(campaign.id);
    setStatus("Campaign created.");
    event.currentTarget.reset();
  }

  async function linkGuild(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await api("/discord/guild-links", {
      method: "POST",
      body: JSON.stringify({
        campaign_id: selectedCampaignId,
        guild_id: form.get("guildId")
      })
    });
    setStatus("Discord guild linked.");
  }

  async function submitSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const result = await api<{ chunk_count: number }>("/sessions", {
      method: "POST",
      body: JSON.stringify({
        campaign_id: selectedCampaignId,
        session_date: form.get("sessionDate"),
        label: form.get("label"),
        raw_content: form.get("notes"),
        author_display_name: form.get("author")
      })
    });
    setStatus(`Session filed and ${result.chunk_count} chunk(s) indexed.`);
    await refreshSessions(selectedCampaignId);
    event.currentTarget.reset();
  }

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const result = await api<{ answer: string; citations: Citation[] }>("/ask", {
      method: "POST",
      body: JSON.stringify({
        campaign_id: selectedCampaignId,
        question: form.get("question")
      })
    });
    setAnswer(result.answer);
    setCitations(result.citations);
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <h1>Lore Goblin</h1>
          <p>Campaign memory, session receipts, and question answering for the table.</p>
        </div>
        <select value={selectedCampaignId} onChange={(event) => setSelectedCampaignId(event.target.value)}>
          <option value="">No campaign selected</option>
          {campaigns.map((campaign) => (
            <option key={campaign.id} value={campaign.id}>
              {campaign.name}
            </option>
          ))}
        </select>
      </section>

      <section className="grid">
        <form className="panel" onSubmit={createCampaign}>
          <h2><BookOpen size={18} /> Setup</h2>
          <label>
            Campaign name
            <input name="name" placeholder="The Ember Road" required />
          </label>
          <label>
            Owner display name
            <input name="owner" placeholder="GM" required />
          </label>
          <label>
            Campaign tone
            <textarea
              name="tone"
              rows={4}
              defaultValue="A cheerful in-world notetaking goblin who answers with receipts."
              required
            />
          </label>
          <button type="submit">Create campaign</button>
        </form>

        <form className="panel" onSubmit={linkGuild}>
          <h2><Link size={18} /> Discord</h2>
          <p className="muted">{selectedCampaign ? selectedCampaign.name : "Create or select a campaign first."}</p>
          <label>
            Guild ID
            <input name="guildId" placeholder="123456789012345678" required disabled={!selectedCampaignId} />
          </label>
          <button type="submit" disabled={!selectedCampaignId}>Link guild</button>
        </form>

        <form className="panel wide" onSubmit={submitSession}>
          <h2><ScrollText size={18} /> Session Notes</h2>
          <div className="split">
            <label>
              Session date
              <input name="sessionDate" type="date" required disabled={!selectedCampaignId} />
            </label>
            <label>
              Label
              <input name="label" placeholder="The Ruined Mill" disabled={!selectedCampaignId} />
            </label>
            <label>
              Author
              <input name="author" placeholder="Player name" required disabled={!selectedCampaignId} />
            </label>
          </div>
          <label>
            Note dump
            <textarea name="notes" rows={8} placeholder="NPCs met, party choices, loot, revelations..." required disabled={!selectedCampaignId} />
          </label>
          <button type="submit" disabled={!selectedCampaignId}>File session</button>
        </form>

        <form className="panel wide" onSubmit={ask}>
          <h2><MessageSquareText size={18} /> Ask</h2>
          <label>
            Question
            <input name="question" placeholder="What did we learn about the black obelisk?" required disabled={!selectedCampaignId} />
          </label>
          <button type="submit" disabled={!selectedCampaignId}><Send size={16} /> Ask Lore Goblin</button>
          {answer && (
            <article className="answer">
              <p>{answer}</p>
              {citations.length > 0 && (
                <p className="muted">Sources: {citations.map((citation) => citation.label).join(", ")}</p>
              )}
            </article>
          )}
        </form>

        <section className="panel">
          <h2>Sessions</h2>
          {sessions.length === 0 ? (
            <p className="muted">No session notes filed yet.</p>
          ) : (
            <ul className="session-list">
              {sessions.map((session) => (
                <li key={session.id}>
                  <strong>{session.session_date}</strong>
                  {session.label ? ` - ${session.label}` : ""}
                  <span>{session.note_count} note(s)</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </section>

      {status && <div className="status">{status}</div>}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

