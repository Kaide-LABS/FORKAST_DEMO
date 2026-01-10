import Sidebar from '@/components/Sidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <main className="md:pl-60 py-6 pr-6 lg:py-8 lg:pr-8">
        {children}
      </main>
    </div>
  );
}
