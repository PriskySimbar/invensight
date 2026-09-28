import { DashboardLayout } from "@/components/layout/dashboard-layout";

export default function AnalyticsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Analytics</h1>
          <p className="text-sm text-muted-foreground">
            Advanced analytics and reporting features coming soon
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <p className="text-muted-foreground">Analytics page - Coming Soon</p>
        </div>
      </div>
    </DashboardLayout>
  );
}
