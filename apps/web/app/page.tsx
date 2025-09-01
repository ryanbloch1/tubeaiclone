export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-slate-900 mb-6">
            TubeAI Video Creator
          </h1>
          <p className="text-xl text-slate-600 mb-12">
            Create engaging YouTube videos with AI-powered scripts, voiceovers, and visuals
          </p>
          
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <a 
              href="/script" 
              className="group bg-white border border-slate-200 rounded-xl p-8 hover:border-blue-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="text-4xl mb-4">📝</div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">1. Script Generation</h2>
              <p className="text-slate-600 text-sm">
                Generate compelling video scripts from your topic ideas
              </p>
              <div className="mt-4 text-blue-600 group-hover:text-blue-700 font-medium">
                Start Here →
              </div>
            </a>
            
            <a 
              href="/voiceover" 
              className="group bg-white border border-slate-200 rounded-xl p-8 hover:border-purple-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="text-4xl mb-4">🎙️</div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">2. Voice Generation</h2>
              <p className="text-slate-600 text-sm">
                Add professional AI voices to your existing scripts
              </p>
              <div className="mt-4 text-purple-600 group-hover:text-purple-700 font-medium">
                Have a Script? →
              </div>
            </a>
            
            <a 
              href="/images" 
              className="group bg-white border border-slate-200 rounded-xl p-8 hover:border-green-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="text-4xl mb-4">🎨</div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">3. Scene Images</h2>
              <p className="text-slate-600 text-sm">
                Generate AI visuals that match your script scenes
              </p>
              <div className="mt-4 text-green-600 group-hover:text-green-700 font-medium">
                Create Visuals →
              </div>
            </a>
          </div>
          
          <div className="mt-16 text-center">
            <h3 className="text-2xl font-semibold text-slate-900 mb-4">Complete Video Creation Pipeline</h3>
            <div className="flex justify-center items-center space-x-4 text-slate-500">
              <span className="bg-blue-50 border-blue-200 border px-4 py-2 rounded-lg text-blue-700">Script</span>
              <span>→</span>
              <span className="bg-purple-50 border-purple-200 border px-4 py-2 rounded-lg text-purple-700">Voice</span>
              <span>→</span>
              <span className="bg-green-50 border-green-200 border px-4 py-2 rounded-lg text-green-700">Images</span>
              <span>→</span>
              <span className="bg-orange-50 border-orange-200 border px-4 py-2 rounded-lg text-orange-700">Video</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
