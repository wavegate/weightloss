import { useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "./assets/vite.svg";

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-8 bg-slate-950 px-4 text-slate-100">
      <div className="flex items-center gap-6">
        <a href="https://vite.dev" target="_blank" rel="noreferrer">
          <img src={viteLogo} className="h-16 w-16" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank" rel="noreferrer">
          <img
            src={reactLogo}
            className="h-16 w-16 motion-safe:animate-[spin_20s_linear_infinite]"
            alt="React logo"
          />
        </a>
      </div>
      <h1 className="text-4xl font-semibold tracking-tight">Vite + React</h1>
      <button
        type="button"
        className="rounded-lg border border-slate-700 bg-slate-900 px-5 py-2.5 font-medium transition hover:border-violet-500 hover:bg-slate-800"
        onClick={() => setCount((value) => value + 1)}
      >
        Count is {count}
      </button>
      <p className="text-slate-400">
        Edit <code className="text-violet-300">src/App.tsx</code> and save to
        test HMR
      </p>
    </div>
  );
}

export default App;
