"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getLoan, getLoanTransfers, type Loan, type LoanTransfer } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function LoanDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [loan, setLoan] = useState<Loan | null>(null);
  const [transfers, setTransfers] = useState<LoanTransfer[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    Promise.all([getLoan(token, params.id), getLoanTransfers(token, params.id)])
      .then(([loanData, transferData]) => { setLoan(loanData); setTransfers(transferData); })
      .catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load this loan."));
  }, [params.id, router]);

  if (errorMessage) return <main className="min-h-screen bg-canvas p-10 text-signal">{errorMessage}</main>;
  if (!loan) return <main className="flex min-h-screen items-center justify-center bg-canvas text-ink">Loading loan...</main>;

  const latestTransfer = transfers[0];
  const transferredToCurrentBorrower = latestTransfer?.new_borrower.id === loan.borrower;

  return <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20"><div className="mx-auto max-w-5xl"><nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/loans" className="text-sm font-bold text-signal">← My loans</Link><Link href="/dashboard" className="text-2xl font-bold">AVault</Link></nav><section className="py-12"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm uppercase tracking-[0.16em] text-ink/55">{loan.booking_code}</p><h1 className="mt-3 text-5xl tracking-tight">Loan #{loan.id}</h1></div><strong className={loan.status === "OVERDUE" ? "text-signal" : "text-emerald-700"}>{loan.status}</strong></div>{transferredToCurrentBorrower && <p className="mt-6 border border-emerald-500/30 bg-emerald-100 p-4 text-emerald-800">Transferred to you</p>}<div className="mt-8 grid gap-5 border border-ink/15 bg-white p-6 sm:grid-cols-3"><div><p className="text-sm text-ink/55">Current borrower</p><p className="mt-1 text-lg">{loan.borrower_name}</p></div><div><p className="text-sm text-ink/55">Issued</p><p className="mt-1">{loan.issued_at}</p></div><div><p className="text-sm text-ink/55">Due</p><p className="mt-1">{loan.due_at}</p></div></div><section className="mt-8"><h2 className="text-2xl">Equipment</h2><div className="mt-4 space-y-3">{loan.items.map((item) => <div className="flex flex-wrap justify-between gap-3 border border-ink/15 bg-white p-5" key={item.id}><span className="font-bold">{item.equipment_name} · {item.asset_code}</span><span className="text-ink/60">Issue condition: {item.condition_at_issue}</span></div>)}</div></section>{loan.late_fee && <section className="mt-8 border border-signal/30 bg-signal/10 p-6"><h2 className="text-2xl">Late fee</h2><p className="mt-2">{loan.late_fee.days_late} days · ₹{loan.late_fee.amount} · {loan.late_fee.status}</p></section>}{transfers.length > 0 && <section className="mt-8"><h2 className="text-2xl">Transfer history</h2><div className="mt-4 space-y-3">{transfers.map((transfer) => <div className="border border-ink/15 bg-white p-5" key={transfer.id}><p className="font-bold">{transfer.previous_borrower.name} → {transfer.new_borrower.name}</p><p className="mt-2 text-sm text-ink/60">{transfer.transferred_at} · {transfer.reason}</p></div>)}</div></section>}</section></div></main>;
}
