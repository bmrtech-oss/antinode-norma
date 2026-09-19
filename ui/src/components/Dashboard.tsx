import React, { useEffect, useState } from "react";

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

  useEffect(() => {
    fetch("/api/dashboard")
      .then((res) => res.json())
      .then((data) => {
        if (data && data.summary) {
          setSummary(data.summary);
        }
      })
      .catch((err) => console.error("Error fetching dashboard summary:", err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-6 text-gray-500">Loading dashboard...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center border-b pb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Norma BDD Platform Overview</h1>
          <p className="text-sm text-gray-500">System metrics and governance status</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-600">Status:</span>
          <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
            {summary?.system_status || "operational"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="text-sm font-medium text-gray-500">Total Features</div>
          <div className="mt-2 text-3xl font-extrabold text-indigo-600">
            {summary?.total_features ?? 0}
          </div>
          <p className="mt-1 text-xs text-gray-400">Features in workspace</p>
        </div>

        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="text-sm font-medium text-gray-500">Pending Approvals</div>
          <div className="mt-2 text-3xl font-extrabold text-amber-500">
            {summary?.pending_approvals ?? 0}
          </div>
          <p className="mt-1 text-xs text-gray-400">Awaiting sign-off</p>
        </div>

        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="text-sm font-medium text-gray-500">Quality Gate Pass Rate</div>
          <div className="mt-2 text-3xl font-extrabold text-emerald-600">
            {Math.round((summary?.quality_gate_pass_rate ?? 0) * 100)}%
          </div>
          <p className="mt-1 text-xs text-gray-400">Hard & soft gates</p>
        </div>

        <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm">
          <div className="text-sm font-medium text-gray-500">Audit Events</div>
          <div className="mt-2 text-3xl font-extrabold text-blue-600">
            {summary?.total_audit_events ?? 0}
          </div>
          <p className="mt-1 text-xs text-gray-400">Hash-chained log events</p>
        </div>
      </div>
    </div>
  );
};
