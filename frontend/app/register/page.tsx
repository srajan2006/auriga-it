"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { register } from "@/lib/api";
import { saveAuth } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", password: "", password_confirm: "", student_id: "", phone: "" });
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    try {
      const response = await register(form);
      saveAuth(response);
      router.push("/dashboard");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to register.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-canvas px-6 py-12 text-ink sm:px-10">
      <div className="mx-auto max-w-lg">
        <Link href="/" className="text-2xl font-bold tracking-tight">AVault</Link>
        <div className="mt-12 border border-ink/15 bg-white p-8 shadow-[8px_8px_0_#d8f3e4]">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Student access</p>
          <h1 className="mt-4 text-4xl tracking-tight">Create an account</h1>
          <p className="mt-3 text-sm leading-6 text-ink/65">New public accounts are created as students.</p>
          <form onSubmit={handleSubmit} className="mt-8 grid gap-5 sm:grid-cols-2">
            <label className="block text-sm font-bold sm:col-span-2">Full name<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" value={form.name} onChange={(event) => updateField("name", event.target.value)} required /></label>
            <label className="block text-sm font-bold sm:col-span-2">Email<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} required /></label>
            <label className="block text-sm font-bold">Student ID<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" value={form.student_id} onChange={(event) => updateField("student_id", event.target.value)} /></label>
            <label className="block text-sm font-bold">Phone<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" value={form.phone} onChange={(event) => updateField("phone", event.target.value)} /></label>
            <label className="block text-sm font-bold">Password<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" type="password" minLength={8} value={form.password} onChange={(event) => updateField("password", event.target.value)} required /></label>
            <label className="block text-sm font-bold">Confirm password<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" type="password" minLength={8} value={form.password_confirm} onChange={(event) => updateField("password_confirm", event.target.value)} required /></label>
            {errorMessage && <p className="border border-signal/30 bg-signal/10 p-3 text-sm text-signal sm:col-span-2">{errorMessage}</p>}
            <button className="bg-ink px-4 py-3 font-bold text-white disabled:cursor-not-allowed disabled:opacity-50 sm:col-span-2" type="submit" disabled={isSubmitting}>{isSubmitting ? "Creating account..." : "Create account"}</button>
          </form>
          <p className="mt-6 text-sm text-ink/65">Already registered? <Link className="font-bold text-signal" href="/login">Log in</Link></p>
        </div>
      </div>
    </main>
  );
}
