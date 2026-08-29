import { useState } from "react";
import { useNavigate } from "react-router-dom";
interface LoginProps {}

export default function Login({ }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-slate-900">
            PatientTriage<span className="text-blue-600">.ai</span>
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Emergency coordination desk
          </p>
        </div>

        <div className="space-y-4">

          <div>
            <label className="text-sm font-medium text-slate-700">
              Email
            </label>

            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">
              Password
            </label>

            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
              placeholder="••••••••"
            />
          </div>

          <button
  type="button"
  onClick={() => navigate("/dashboard")}
  className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-700"
>
  Log in
</button>

        </div>

        <p className="mt-5 text-center text-sm text-slate-500">
          Don't have an account?{" "}
          <button
  type="button"
  onClick={() => navigate("/dashboard")}
  className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-700"
>
  Sign Up
</button>
        </p>

      </div>
    </div>
  );
}