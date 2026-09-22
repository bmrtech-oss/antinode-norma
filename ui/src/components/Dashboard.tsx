import React, { useEffect, useState } from "react";
import { Activity, CheckCircle2, Clock3, FileCheck2, LayoutDashboard, ShieldAlert } from "lucide-react";
import { getJson } from "../lib/api";
import { ErrorState, LoadingState } from "./ui/AsyncState";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/Card";
import { Tooltip } from "./ui/Tooltip";

interface DashboardSummary {
  total_features: number;
  total_approvals: number;
  pending_approvals: number;
  approved_count: number;
  rejected_count: number;
  total_audit_events: number;
  quality_gate_pass_rate: number;
  system_status: string;
}

export const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = () => {
    setLoading(true);
    setError(null);
    getJson<{ summary: DashboardSummary }>("/api/dashboard")
      .then((data) => {
        if (data && data.summary) {
          setSummary(data.summary);
        }
      })
      .catch(() => setError("Dashboard metrics are unavailable."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  if (loading) {
    return <LoadingState label="Loading dashboard..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchSummary} />;
  }

  const totalApprovals = summary?.total_approvals ?? 0;
  const approvedCount = summary?.approved_count ?? 0;
  const rejectedCount = summary?.rejected_count ?? 0;
  const pendingApprovals = summary?.pending_approvals ?? 0;
  const approvalTotal = Math.max(totalApprovals, approvedCount + rejectedCount + pendingApprovals);
  const percentage = (value: number) => approvalTotal > 0 ? Math.round((value / approvalTotal) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
            <LayoutDashboard className="h-6 w-6 text-primary" aria-hidden="true" />
            <Tooltip content="Workspace metrics, approval summaries, quality gates, and system health.">
              <span>Norma BDD Platform Overview</span>
            </Tooltip>
          </h1>
          <p className="text-sm text-muted-foreground">Current workspace metrics and governance status</p>
        </div>
        <div className="flex items-center gap-2">
          <Tooltip content="Overall health reported by the selected backend.">
            <span className="text-sm font-medium text-muted-foreground">System status:</span>
          </Tooltip>
          <Badge variant={summary?.system_status === "operational" ? "success" : "warning"}>
            <Activity className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
            {summary?.system_status || "unknown"}
          </Badge>
          <Button variant="outline" size="sm" onClick={fetchSummary}>Refresh</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total features", value: summary?.total_features ?? 0, description: "Features in workspace", icon: FileCheck2, tone: "text-primary" },
          { label: "Pending approvals", value: pendingApprovals, description: "Awaiting sign-off", icon: Clock3, tone: "text-warning" },
          { label: "Quality gate pass rate", value: `${Math.round((summary?.quality_gate_pass_rate ?? 0) * 100)}%`, description: "Current reported snapshot", icon: CheckCircle2, tone: "text-success" },
          { label: "Audit events", value: summary?.total_audit_events ?? 0, description: "Hash-chained events", icon: ShieldAlert, tone: "text-info" },
        ].map(({ label, value, description, icon: Icon, tone }) => (
          <Card key={label}>
            <CardContent className="!p-5">
              <div className="flex items-start justify-between gap-3">
                <Tooltip content={description}>
                  <span className="text-sm font-medium text-muted-foreground">{label}</span>
                </Tooltip>
                <Icon className={`h-5 w-5 ${tone}`} aria-hidden="true" />
              </div>
              <div className="mt-2 text-3xl font-extrabold text-foreground">{value}</div>
              <p className="mt-1 text-xs text-muted-foreground">{description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Approval distribution</CardTitle>
            <p className="text-xs text-muted-foreground">Current approval request snapshot</p>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: "Approved", value: approvedCount, tone: "bg-success", text: "text-success" },
              { label: "Pending", value: pendingApprovals, tone: "bg-warning", text: "text-warning" },
              { label: "Rejected", value: rejectedCount, tone: "bg-destructive", text: "text-destructive" },
            ].map(({ label, value, tone, text }) => (
              <div key={label}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-muted-foreground">{label}</span>
                  <span className={`font-semibold ${text}`}>{value} ({percentage(value)}%)</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div className={`h-full ${tone}`} style={{ width: `${percentage(value)}%` }} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Operational context</CardTitle>
            <p className="text-xs text-muted-foreground">Metrics currently exposed by the dashboard API</p>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="text-muted-foreground">Total approval requests</span>
              <span className="font-semibold text-foreground">{totalApprovals}</span>
            </div>
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="text-muted-foreground">Reported quality pass rate</span>
              <span className="font-semibold text-success">{Math.round((summary?.quality_gate_pass_rate ?? 0) * 100)}%</span>
            </div>
            <p className="text-xs text-muted-foreground">
              This dashboard intentionally presents the current API snapshot. Historical trends are not shown because the backend does not currently expose time-series data.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
