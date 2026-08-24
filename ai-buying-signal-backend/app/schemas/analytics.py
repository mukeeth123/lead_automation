from pydantic import BaseModel

class SourceAnalytics(BaseModel):
    id: str
    name: str
    count: int
    hotCount: int
    avgIntent: int

class AnalyticsOverview(BaseModel):
    totalSignals: int
    hotLeads: int
    highIntent: int
    newToday: int
    totalCompanies: int
    sourceStats: list[SourceAnalytics]
