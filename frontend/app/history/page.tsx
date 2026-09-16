"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getBookings, getLateFees, getLoans, getLoanTransfers, type Booking, type LateFee, type Loan, type LoanTransfer } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function HistoryPage() {
  const router = useRouter();
  const [loans, setLoans] = useState<Loan[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [fees, setFees] = useState<LateFee[]>([]);
  const [transfers, setTransfers] = useState<LoanTransfer[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    Promise.all([getLoans(token), getBookings(token), getLateFees(token)])
      .then(async ([loanData, bookingData, feeData]) => {
        setLoans(loanData); setBookings(bookingData); setFees(feeData);
        const transferGroups = await Promise.all(loanData.map((loan) => getLoanTransfers(token, String(loan.id))));
        setTransfers(transferGroups.flat());
      })
      .catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load history."));
  }, [router]);

  return <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20"><div className="mx-auto max-w-6xl"><nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/dashboard" className="text-2xl font-bold">AVault</Link><Link href="/loans" className="text-sm font-bold text-signal">Current loans</Link></nav><section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">History</p><h1 className="mt-4 text-5xl tracking-tight">Your AVault record</h1>{errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}<div className="mt-10 grid gap-8 lg:grid-cols-3"><section><h2 className="text-2xl">Loans</h2><div className="mt-4 space-y-3">{loans.map((loan) => <Link href={`/loans/${loan.id}`} className="block border border-ink/15 bg-white p-4" key={loan.id}>Loan #{loan.id}<span className="ml-2 text-sm text-ink/60">{loan.status}</span></Link>)}</div></section><section><h2 className="text-2xl">Bookings</h2><div className="mt-4 space-y-3">{bookings.map((booking) => <div className="border border-ink/15 bg-white p-4" key={booking.id}><p className="font-bold">{booking.booking_code}</p><p className="mt-1 text-sm text-ink/60">{booking.status} · {booking.start_date} to {booking.end_date}</p></div>)}</div></section><section><h2 className="text-2xl">Late fees</h2><div className="mt-4 space-y-3">{fees.map((fee) => <div className="border border-ink/15 bg-white p-4" key={fee.id}>₹{fee.amount}<span className="ml-2 text-sm text-ink/60">{fee.status}</span></div>)}</div></section></div>{transfers.length > 0 && <section className="mt-12"><h2 className="text-2xl">Transfer events</h2><div className="mt-4 space-y-3">{transfers.map((transfer) => <div className="border border-ink/15 bg-white p-5" key={transfer.id}><p className="font-bold">Loan #{transfer.loan}: {transfer.previous_borrower.name} → {transfer.new_borrower.name}</p><p className="mt-2 text-sm text-ink/60">{transfer.transferred_at} · {transfer.reason}</p></div>)}</div></section>}</section></div></main>;
}
