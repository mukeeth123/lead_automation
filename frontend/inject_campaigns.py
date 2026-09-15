import re

file_path = "src/App.jsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

campaigns_component = """
/* ---------------------------- Campaigns Page ---------------------------- */

function CampaignsPage({ nav }) {
  const [campaigns, setCampaigns] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [newCampaign, setNewCampaign] = React.useState({ name: "", service_description: "", target_industry: "", target_geography: "" });
  
  React.useEffect(() => {
    fetchCampaigns();
  }, []);

  async function fetchCampaigns() {
    setLoading(true);
    try {
      const res = await axios.get("http://localhost:8000/api/v1/campaigns");
      setCampaigns(res.data.campaigns || []);
    } catch(e) {
      console.error(e);
    }
    setLoading(false);
  }

  async function handleCreate(e) {
    e.preventDefault();
    try {
      await axios.post("http://localhost:8000/api/v1/campaigns", newCampaign);
      setNewCampaign({ name: "", service_description: "", target_industry: "", target_geography: "" });
      fetchCampaigns();
    } catch(e) {
      console.error(e);
    }
  }

  async function handleRun(campaign_id) {
    try {
      await axios.post(`http://localhost:8000/api/v1/campaigns/${campaign_id}/discover`);
      alert("Discovery job queued!");
    } catch(e) {
      console.error(e);
      alert("Failed to queue discovery job");
    }
  }

  if (loading) return <div>Loading campaigns...</div>;

  return (
    <div style={{ maxWidth: 800 }}>
      <h2 style={{ fontFamily: "var(--font-display)", marginBottom: 24 }}>Campaigns</h2>
      
      <div style={{ background: "var(--surface)", padding: 24, borderRadius: 8, marginBottom: 32, boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
        <h3 style={{ marginTop: 0, marginBottom: 16 }}>Create New Campaign</h3>
        <form onSubmit={handleCreate} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <input placeholder="Campaign Name (e.g. Q4 Marketing Agencies)" value={newCampaign.name} onChange={e => setNewCampaign({...newCampaign, name: e.target.value})} required style={{ padding: "8px 12px", border: "1px solid var(--line)", borderRadius: 4 }} />
          <textarea placeholder="Service Description (What do you sell?)" value={newCampaign.service_description} onChange={e => setNewCampaign({...newCampaign, service_description: e.target.value})} required style={{ padding: "8px 12px", border: "1px solid var(--line)", borderRadius: 4, minHeight: 80 }} />
          <input placeholder="Target Industry (e.g. Marketing, SaaS, Healthcare)" value={newCampaign.target_industry} onChange={e => setNewCampaign({...newCampaign, target_industry: e.target.value})} style={{ padding: "8px 12px", border: "1px solid var(--line)", borderRadius: 4 }} />
          <input placeholder="Target Geography (e.g. US, UK, Global)" value={newCampaign.target_geography} onChange={e => setNewCampaign({...newCampaign, target_geography: e.target.value})} style={{ padding: "8px 12px", border: "1px solid var(--line)", borderRadius: 4 }} />
          <button type="submit" style={{ background: "var(--chrome)", color: "#fff", padding: "10px", borderRadius: 4, border: "none", cursor: "pointer", fontWeight: 600 }}>Create Campaign</button>
        </form>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {campaigns.map(c => (
          <div key={c.id} style={{ background: "var(--surface)", padding: 20, borderRadius: 8, border: "1px solid var(--line)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h3 style={{ margin: "0 0 8px 0" }}>{c.name}</h3>
              <p style={{ margin: 0, fontSize: 13, color: "var(--ink-soft)" }}>{c.service_description.substring(0, 100)}...</p>
            </div>
            <div style={{ display: "flex", gap: 12 }}>
              <button onClick={() => handleRun(c.id)} style={{ background: "var(--accent-teal)", color: "#fff", padding: "8px 16px", borderRadius: 4, border: "none", cursor: "pointer", fontWeight: 500 }}>Run Discovery</button>
            </div>
          </div>
        ))}
        {campaigns.length === 0 && <div style={{ color: "var(--ink-soft)", fontSize: 14 }}>No campaigns found. Create one above.</div>}
      </div>
    </div>
  );
}

export default function App() {
"""

# Insert component
content = content.replace("export default function App() {", campaigns_component)

# Update NAV_ITEMS
content = content.replace(
    '  { id: "ai_search", label: "AI Search" },\n  { id: "overview", label: "Overview" },',
    '  { id: "ai_search", label: "AI Search" },\n  { id: "campaigns", label: "Campaigns" },\n  { id: "overview", label: "Overview" },'
)

# Insert route
content = content.replace(
    '{page === "ai_search" && <AiSearchPage leads={leads} nav={nav} />}',
    '{page === "ai_search" && <AiSearchPage leads={leads} nav={nav} />}\n        {page === "campaigns" && <CampaignsPage nav={nav} />}'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Injected CampaignsPage into App.jsx")
