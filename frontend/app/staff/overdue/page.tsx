"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getLoans, type Loan } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function StaffOverduePage() {
  const router = useRouter();
  const [loans, setLoans] = useState<Loan[]>([]);
  const [errorMessage, setErrorMessage] = useState("");
  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    getLoans(token).then((items) => setLoans(items.filter((loan) => loan.status === "OVERDUE"))).catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load overdue loans."));
  }, [router]);
  return <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20"><div className="mx-auto max-w-6xl"><nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/staff/dashboard" className="text-2xl font-bold">AVault staff</Link><Link href="/staff/returns" className="text-sm font-bold text-signal">Returns</Link></nav><section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Attention required</p><h1 className="mt-4 text-5xl tracking-tight">Overdue loans</h1>{errorMessage && <p className="mt-5 text-signal">{errorMessage}</p>}<div className="mt-10 space-y-4">{loans.length === 0 ? <p className="text-ink/60">No overdue loans.</p> : loans.map((loan) => <Link href={`/loans/${loan.id}`} className="block border border-signal/30 bg-white p-6" key={loan.id}><div className="flex justify-between gap-4"><span className="font-bold">Loan #{loan.id} · {loan.borrower_name}</span><strong className="text-signal">OVERDUE</strong></div><p className="mt-2 text-sm text-ink/60">Due {loan.due_at} · {loan.items.map((item) => `${item.equipment_name} (${item.asset_code})`).join(", ")}</p></Link>)}</div></section></div></main>;
}
