"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getMe, getSystemSettings, updateSystemSettings, type SystemSettings } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function AdminSettingsPage() {
  const router = useRouter();
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    Promise.all([getMe(token), getSystemSettings(token)]).then(([me, data]) => {
      if (me.user.role !== "ADMIN") { router.replace("/dashboard"); return; }
      setSettings(data);
    }).catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load settings."));
  }, [router]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token || !settings) return;
    try {
      setSettings(await updateSystemSettings(token, { max_active_loans_per_user: settings.max_active_loans_per_user, max_units_per_booking: settings.max_units_per_booking, default_late_fee_per_day: settings.default_late_fee_per_day }));
      setMessage("System settings updated."); setErrorMessage("");
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Unable to update settings."); }
  }

  if (!settings) return <main className="flex min-h-screen items-center justify-center bg-canvas text-ink">Loading settings...</main>;
  return <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20"><div className="mx-auto max-w-3xl"><nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/dashboard" className="text-2xl font-bold">AVault admin</Link><Link href="/staff/dashboard" className="text-sm font-bold text-signal">Operations</Link></nav><section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Administration</p><h1 className="mt-4 text-5xl tracking-tight">System settings</h1>{message && <p className="mt-5 border border-emerald-500/30 bg-emerald-100 p-4 text-emerald-800">{message}</p>}{errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}<form onSubmit={save} className="mt-10 space-y-5 border border-ink/15 bg-white p-6"><label className="block text-sm font-bold">Maximum active loans per user<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" type="number" min="1" value={settings.max_active_loans_per_user} onChange={(event) => setSettings({ ...settings, max_active_loans_per_user: Number(event.target.value) })} /></label><label className="block text-sm font-bold">Maximum units per booking<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" type="number" min="1" value={settings.max_units_per_booking} onChange={(event) => setSettings({ ...settings, max_units_per_booking: Number(event.target.value) })} /></label><label className="block text-sm font-bold">Default late fee per day<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" type="number" min="0" step="0.01" value={settings.default_late_fee_per_day} onChange={(event) => setSettings({ ...settings, default_late_fee_per_day: event.target.value })} /></label><button className="bg-ink px-4 py-3 font-bold text-white" type="submit">Save settings</button></form></section></div></main>;
}