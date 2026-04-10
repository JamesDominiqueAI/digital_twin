import Twin from '@/components/twin';

export default function Home() {
  return (
    <main className="min-h-screen">
      <div className="container mx-auto px-4 py-8 md:py-12">
        <div className="max-w-4xl mx-auto">
          <h1 className="mb-2 text-center text-5xl tracking-tight text-slate-900 [font-family:var(--font-display)] md:text-6xl">
            AI in Production
          </h1>
          <p className="mb-8 text-center text-base text-slate-600 md:text-lg">
            Deploy your Digital Twin to the cloud
          </p>

          <div className="h-[600px]">
            <Twin />
          </div>

          <footer className="mt-8 text-center text-sm text-slate-500">
            <p>Week 2: Building Your Digital Twin</p>
          </footer>
        </div>
      </div>
    </main>
  );
}
