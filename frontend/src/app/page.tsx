export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8 text-center sm:p-20">
      <main className="flex flex-col items-center gap-8">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          Enterprise Knowledge Assistant
        </h1>
        <p className="max-w-2xl text-lg text-zinc-600 dark:text-zinc-400">
          Transform your corporate documents into an intelligent conversational engine.
          Upload PDFs, SOPs, and manuals to create a searchable, citation-backed AI expert.
        </p>
        <div className="flex flex-col gap-4 sm:flex-row">
          <button className="rounded-full bg-blue-600 px-8 py-3 font-semibold text-white transition-colors hover:bg-blue-700">
            Get Started
          </button>
          <button className="rounded-full border border-zinc-300 px-8 py-3 font-semibold transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-900">
            Documentation
          </button>
        </div>
      </main>
      <footer className="mt-20 text-sm text-zinc-500">
        Built with Next.js, Tailwind CSS, and FastAPI
      </footer>
    </div>
  );
}
