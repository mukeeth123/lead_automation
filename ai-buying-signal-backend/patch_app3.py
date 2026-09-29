import sys
import re

comp = """
function TargetAccountsPage() {
  const [query, setQuery] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [savedCompanies, setSavedCompanies] = React.useState([]);
  const [currentCompany, setCurrentCompany] = React.useState(null);

  React.useEffect(() => {
    fetchSaved();
  }, []);

  async function fetchSaved() {
    try {
      const res = await axios.get("http://localhost:8000/api/v1/companies/");
      setSavedCompanies(res.data.companies || []);
    } catch(e) {
      console.error(e);
    }
  }

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setCurrentCompany(null);
    try {
      const res = await axios.post("http://localhost:8000/api/v1/companies/analyze", { query });
      setCurrentCompany(res.data);
      fetchSaved();
    } catch(e) {
      console.error(e);
      alert("Failed to analyze company");
    }
    setLoading(false);
  }

  return (
    <div style={{ maxWidth: 900 }}>
      <h2 style={{ fontFamily: "var(--font-display)", margin: "0 0 8px 0" }}>Target Accounts (ICP Matcher)</h2>
      <p style={{ color: "var(--ink-soft)", marginBottom: 24, fontSize: 14 }}>
        Search for any company to instantly scrape their website and generate an AI-powered ICP score, identifying their pain points, recent news/funding, and giving you a custom pitch angle.
      </p>

      <form onSubmit={handleSearch} style={{ display: "flex", gap: 12, marginBottom: 32 }}>
        <input 
          placeholder="Enter a company name (e.g. Stripe, Acme Corp)" 
          value={query} 
          onChange={e => setQuery(e.target.value)}
          style={{ flex: 1, padding: "12px 16px", fontSize: 15, border: "1px solid var(--line)", borderRadius: 6, outline: "none" }}
        />
        <button type="submit" disabled={loading} style={{ background: "var(--accent-teal)", color: "#fff", padding: "0 24px", borderRadius: 6, border: "none", cursor: loading ? "default" : "pointer", fontWeight: 600, fontSize: 15 }}>
          {loading ? "Searching & Analyzing..." : "Analyze Company"}
        </button>
      </form>

      {currentCompany && (
        <div style={{ background: "var(--surface)", padding: 24, borderRadius: 8, border: "1px solid var(--accent-teal)", marginBottom: 32 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
            <div>
              <h3 style={{ margin: "0 0 4px 0", fontSize: 20 }}>{currentCompany.name}</h3>
              <div style={{ color: "var(--ink-soft)", fontSize: 13, marginBottom: 12 }}>
                {currentCompany.industry} • {currentCompany.location} • <a href={currentCompany.website} target="_blank" style={{ color: "var(--accent-teal)" }}>{currentCompany.website}</a>
              </div>
              
              <div style={{ display: "flex", gap: 16, marginTop: 8 }}>
                {currentCompany.key_executives && currentCompany.key_executives !== "Unknown" && (
                  <div style={{ fontSize: 12, background: "var(--surface-2)", padding: "4px 8px", borderRadius: 4, border: "1px solid var(--line)" }}>
                    <strong style={{color:"var(--ink)"}}>Leaders:</strong> {currentCompany.key_executives}
                  </div>
                )}
                {currentCompany.company_size && currentCompany.company_size !== "Unknown" && (
                  <div style={{ fontSize: 12, background: "var(--surface-2)", padding: "4px 8px", borderRadius: 4, border: "1px solid var(--line)" }}>
                    <strong style={{color:"var(--ink)"}}>Size:</strong> {currentCompany.company_size}
                  </div>
                )}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase", marginBottom: 4 }}>ICP Match Score</div>
              <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "var(--font-mono)", color: currentCompany.icp_score >= 80 ? "var(--accent-teal)" : currentCompany.icp_score >= 60 ? "#F58025" : "var(--accent-rose)" }}>
                {currentCompany.icp_score}/100
              </div>
            </div>
          </div>
          
          <p style={{ lineHeight: 1.5, fontSize: 14, marginBottom: 24, paddingBottom: 16, borderBottom: "1px solid var(--line)" }}>{currentCompany.description}</p>

          {currentCompany.sales_triggers && currentCompany.sales_triggers.length > 0 && (
             <div style={{ marginBottom: 24 }}>
                <h4 style={{ margin: "0 0 12px 0", fontSize: 13, textTransform: "uppercase", color: "var(--accent-teal)" }}>Strategic Sales Triggers</h4>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {currentCompany.sales_triggers.map((t, i) => (
                    <span key={i} style={{ background: "rgba(11, 169, 134, 0.1)", color: "var(--accent-teal)", padding: "6px 12px", borderRadius: 16, fontSize: 12, fontWeight: 600 }}>{t}</span>
                  ))}
                </div>
             </div>
          )}

          {currentCompany.latest_updates && currentCompany.latest_updates.length > 0 && currentCompany.latest_updates[0] !== "No major news or funding announced recently." && (
            <div style={{ marginBottom: 24, padding: "16px", background: "var(--surface-2)", borderRadius: 6, borderLeft: "4px solid #F58025" }}>
              <h4 style={{ margin: "0 0 12px 0", fontSize: 13, textTransform: "uppercase", color: "#F58025" }}>Recent News & Funding Updates</h4>
              <ul style={{ paddingLeft: 16, margin: 0, fontSize: 13, lineHeight: 1.5 }}>
                {currentCompany.latest_updates.map((p, i) => <li key={i} style={{ marginBottom: 6 }}>{p}</li>)}
              </ul>
            </div>
          )}
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            <div>
              <h4 style={{ margin: "0 0 12px 0", fontSize: 13, textTransform: "uppercase", color: "var(--ink-soft)" }}>Identified Pain Points</h4>
              <ul style={{ paddingLeft: 16, margin: 0, fontSize: 13, lineHeight: 1.5 }}>
                {currentCompany.pain_points?.map((p, i) => <li key={i} style={{ marginBottom: 6 }}>{p}</li>)}
              </ul>
            </div>
            <div>
              <h4 style={{ margin: "0 0 12px 0", fontSize: 13, textTransform: "uppercase", color: "var(--accent-teal)" }}>How to Pitch Them</h4>
              <ul style={{ paddingLeft: 16, margin: 0, fontSize: 13, lineHeight: 1.5 }}>
                {currentCompany.pitch_recommendations?.map((p, i) => <li key={i} style={{ marginBottom: 6 }}>{p}</li>)}
              </ul>
            </div>
          </div>
        </div>
      )}

      {savedCompanies.length > 0 && !loading && !currentCompany && (
        <div>
          <h3 style={{ margin: "0 0 16px 0" }}>Saved Accounts</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {savedCompanies.map(c => (
              <div key={c.id} onClick={() => setCurrentCompany(c)} style={{ background: "var(--surface)", padding: "16px 20px", borderRadius: 6, border: "1px solid var(--line)", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{c.name}</div>
                  <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>{c.industry} • {c.company_size || "Unknown Size"}</div>
                </div>
                <div style={{ fontWeight: 700, fontFamily: "var(--font-mono)", color: c.icp_score >= 80 ? "var(--accent-teal)" : c.icp_score >= 60 ? "#F58025" : "var(--accent-rose)" }}>
                  {c.icp_score}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
"""

with open(r'C:\Users\mukee\social media listening\frontend\src\App.jsx', 'r', encoding='utf8') as f:
    content = f.read()

pattern = r"function TargetAccountsPage\(\) \{.*?(?=\nexport default function App\(\) \{)"
new_content = re.sub(pattern, comp, content, flags=re.DOTALL)

with open(r'C:\Users\mukee\social media listening\frontend\src\App.jsx', 'w', encoding='utf8') as f:
    f.write(new_content)
