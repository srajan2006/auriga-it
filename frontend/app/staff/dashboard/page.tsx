"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getBookings, getEquipment, getLoans, type Booking, type EquipmentModel, type Loan } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function StaffDashboardPage() {
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [equipment, setEquipment] = useState<EquipmentModel[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    Promise.all([getBookings(token), getLoans(token), getEquipment(token, { is_active: "true" })])
      .then(([bookingData, loanData, equipmentData]) => { setBookings(bookingData); setLoans(loanData); setEquipment(equipmentData); })
      .catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load staff dashboard."));
  }, [router]);

  const today = new Date().toISOString().slice(0, 10);
  const pendingBookings = bookings.filter((booking) => booking.status === "PENDING");
  const pickups = bookings.filter((booking) => booking.status === "APPROVED" && booking.start_date === today);
  const returns = loans.filter((loan) => loan.due_at.slice(0, 10) === today && ["ACTIVE", "OVERDUE"].includes(loan.status));
  const activeLoans = loans.filter((loan) => loan.status === "ACTIVE");
  const overdueLoans = loans.filter((loan) => loan.status === "OVERDUE");
  const attention = equipment.filter((item) => item.available_quantity < item.total_quantity);

  return <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20"><div className="mx-auto max-w-6xl"><nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/dashboard" className="text-2xl font-bold">AVault staff</Link><div className="flex gap-4 text-sm font-bold"><Link href="/staff/bookings" className="text-signal">Bookings</Link><Link href="/staff/loans" className="text-signal">Issue</Link><Link href="/staff/returns" className="text-signal">Returns</Link></div></nav><section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Operations</p><h1 className="mt-4 text-5xl tracking-tight">Staff dashboard</h1>{errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}<div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[["Pending bookings", pendingBookings.length, "/staff/bookings"], ["Today's pickups", pickups.length, "/staff/bookings"], ["Today's returns", returns.length, "/staff/returns"], ["Active loans", activeLoans.length, "/staff/loans"], ["Overdue loans", overdueLoans.length, "/staff/overdue"], ["Equipment needing attention", attention.length, "/staff/equipment"]].map(([label, value, href]) => <Link href={href as string} className="border border-ink/15 bg-white p-6 transition hover:border-signal" key={label as string}><p className="text-sm uppercase tracking-[0.12em] text-ink/55">{label}</p><p className="mt-4 text-4xl">{value}</p></Link>)}</div></section></div></main>;
}
