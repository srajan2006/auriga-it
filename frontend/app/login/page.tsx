"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { login } from "@/lib/api";
import { saveAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    try {
      const response = await login({ email, password });
      saveAuth(response);
      router.push("/dashboard");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to log in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-canvas px-6 py-12 text-ink sm:px-10">
      <div className="mx-auto max-w-md">
        <Link href="/" className="text-2xl font-bold tracking-tight">AVault</Link>
        <div className="mt-16 border border-ink/15 bg-white p-8 shadow-[8px_8px_0_#d8f3e4]">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Welcome back</p>
          <h1 className="mt-4 text-4xl tracking-tight">Log in</h1>
          <p className="mt-3 text-sm leading-6 text-ink/65">Use your AVault account to continue.</p>
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <label className="block text-sm font-bold">
              Email
              <input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            </label>
            <label className="block text-sm font-bold">
              Password
              <input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            </label>
            {errorMessage && <p className="border border-signal/30 bg-signal/10 p-3 text-sm text-signal">{errorMessage}</p>}
            <button className="w-full bg-ink px-4 py-3 font-bold text-white disabled:cursor-not-allowed disabled:opacity-50" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Logging in..." : "Log in"}
            </button>
          </form>
          <p className="mt-6 text-sm text-ink/65">Need an account? <Link className="font-bold text-signal" href="/register">Register here</Link></p>
        </div>
      </div>
    </main>
  );
}
