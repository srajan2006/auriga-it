"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getLateFees, getLoans, type LateFee, type Loan } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function LoansPage() {
  const router = useRouter();
  const [loans, setLoans] = useState<Loan[]>([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [fees, setFees] = useState<LateFee[]>([]);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    Promise.all([getLoans(token), getLateFees(token)]).then(([loanData, feeData]) => { setLoans(loanData); setFees(feeData); }).catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load loans."));
  }, [router]);

  return <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20"><div className="mx-auto max-w-5xl"><nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/dashboard" className="text-2xl font-bold">AVault</Link><div className="flex gap-4 text-sm font-bold"><Link href="/bookings" className="text-signal">My bookings</Link><Link href="/history" className="text-signal">History</Link></div></nav><section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Student loans</p><h1 className="mt-4 text-5xl tracking-tight">Equipment in your care</h1>{errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}{fees.filter((fee) => fee.status === "PENDING").length > 0 && <div className="mt-8 border border-signal/30 bg-signal/10 p-5"><p className="text-sm uppercase tracking-[0.14em] text-signal">Outstanding late fees</p><p className="mt-2 text-3xl">₹{fees.filter((fee) => fee.status === "PENDING").reduce((sum, fee) => sum + Number(fee.amount), 0).toFixed(2)}</p></div>}{loans.length === 0 ? <p className="mt-10 text-ink/60">No loans have been issued to you.</p> : <div className="mt-10 space-y-5">{loans.map((loan) => <Link href={`/loans/${loan.id}`} className="block border border-ink/15 bg-white p-6 transition hover:border-signal" key={loan.id}><div className="flex flex-wrap justify-between gap-4"><div><p className="text-sm uppercase tracking-[0.14em] text-ink/55">{loan.booking_code}</p><h2 className="mt-2 text-2xl">Loan #{loan.id}</h2></div><strong className={loan.status === "OVERDUE" ? "text-signal" : "text-emerald-700"}>{loan.status}</strong></div><div className="mt-6 grid gap-4 border-t border-ink/10 pt-5 sm:grid-cols-2"><div><p className="text-sm text-ink/55">Issued</p><p className="mt-1">{loan.issued_at}</p></div><div><p className="text-sm text-ink/55">Due</p><p className="mt-1">{loan.due_at}</p></div></div><div className="mt-6 space-y-3">{loan.items.map((item) => <div className="flex flex-wrap justify-between gap-3 border-t border-ink/10 pt-3" key={item.id}><span>{item.equipment_name} · {item.asset_code}</span><span className="text-ink/60">Condition: {item.condition_at_issue}</span></div>)}</div></Link>)}</div>}</section></div></main>;
}