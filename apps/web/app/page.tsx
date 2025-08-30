export default function Home() {
  return (
    <div className="mx-auto max-w-3xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">TubeAI Web</h1>
      <p>Choose a demo:</p>
      <ul className="list-disc pl-6">
        <li><a className="text-blue-600 underline" href="/script">Script generation</a></li>
        <li><a className="text-blue-600 underline" href="/voiceover">Voiceover</a></li>
      </ul>
    </div>
  );
}
