"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getBookings, getLateFees, getLoans, getMe, logout, type Booking, type LateFee, type Loan, type User } from "@/lib/api";
import { clearAuth, getAccessToken, getRefreshToken } from "@/lib/auth";

function isUpcoming(booking: Booking) {
  return booking.status === "PENDING" || booking.status === "APPROVED";
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [fees, setFees] = useState<LateFee[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const accessToken = getAccessToken();
    if (!accessToken) { router.replace("/login"); return; }
    Promise.all([getMe(accessToken), getLoans(accessToken), getBookings(accessToken), getLateFees(accessToken)])
      .then(([me, loanData, bookingData, feeData]) => { setUser(me.user); setLoans(loanData); setBookings(bookingData); setFees(feeData); })
      .catch((error: unknown) => { clearAuth(); setErrorMessage(error instanceof Error ? error.message : "Unable to load your dashboard."); router.replace("/login"); })
      .finally(() => setIsLoading(false));
  }, [router]);

  async function handleLogout() {
    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();
    if (accessToken && refreshToken) { try { await logout(accessToken, refreshToken); } catch { /* Clear local session regardless. */ } }
    clearAuth();
    router.replace("/");
  }

  if (isLoading || !user) return <main className="flex min-h-screen items-center justify-center bg-canvas text-ink">Loading your dashboard...</main>;

  const activeLoans = loans.filter((loan) => loan.status === "ACTIVE");
  const overdueLoans = loans.filter((loan) => loan.status === "OVERDUE");
  const pendingBookings = bookings.filter((booking) => booking.status === "PENDING");
  const upcomingBookings = bookings.filter(isUpcoming);
  const outstandingFees = fees.filter((fee) => fee.status === "PENDING");
  const totalFees = outstandingFees.reduce((total, fee) => total + Number(fee.amount), 0);
  const metricCards = [["Active loans", activeLoans.length, "/loans"], ["Upcoming bookings", upcomingBookings.length, "/bookings"], ["Pending requests", pendingBookings.length, "/bookings"], ["Overdue loans", overdueLoans.length, "/loans"], ["Outstanding fees", `₹${totalFees.toFixed(2)}`, "/loans"]] as const;
  const visibleLoans = loans.filter((loan) => loan.status === "ACTIVE" || loan.status === "OVERDUE");

  return <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20"><div className="mx-auto max-w-6xl"><nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/" className="text-2xl font-bold tracking-tight">AVault</Link><button className="text-sm font-bold text-signal" onClick={handleLogout}>Log out</button></nav><section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Student dashboard</p><h1 className="mt-4 text-5xl tracking-tight">Hello, {user.name}.</h1><p className="mt-4 max-w-2xl text-lg leading-8 text-ink/70">Your current loans, bookings, overdue items, and fees are kept here in one place.</p>{errorMessage && <p className="mt-6 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}<div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">{metricCards.map(([label, value, href]) => <Link href={href} className="border border-ink/15 bg-white p-5 transition hover:border-signal" key={label}><p className="text-sm uppercase tracking-[0.12em] text-ink/55">{label}</p><p className="mt-4 text-3xl">{value}</p></Link>)}</div><div className="mt-12 grid gap-8 lg:grid-cols-2"><section><div className="flex items-center justify-between"><h2 className="text-2xl">Active and overdue loans</h2><Link href="/loans" className="text-sm font-bold text-signal">View all</Link></div><div className="mt-4 space-y-3">{visibleLoans.slice(0, 4).map((loan) => <Link href={`/loans/${loan.id}`} className="block border border-ink/15 bg-white p-5" key={loan.id}><div className="flex justify-between gap-3"><span className="font-bold">Loan #{loan.id}</span><strong className={loan.status === "OVERDUE" ? "text-signal" : "text-emerald-700"}>{loan.status}</strong></div><p className="mt-2 text-sm text-ink/60">Due {new Date(loan.due_at).toLocaleString()}</p></Link>)}{visibleLoans.length === 0 && <p className="text-ink/60">No active loans.</p>}</div></section><section><div className="flex items-center justify-between"><h2 className="text-2xl">Upcoming bookings</h2><Link href="/bookings" className="text-sm font-bold text-signal">View all</Link></div><div className="mt-4 space-y-3">{upcomingBookings.slice(0, 4).map((booking) => <Link href="/bookings" className="block border border-ink/15 bg-white p-5" key={booking.id}><div className="flex justify-between gap-3"><span className="font-bold">{booking.booking_code}</span><strong className="text-signal">{booking.status}</strong></div><p className="mt-2 text-sm text-ink/60">{booking.start_date} to {booking.end_date}</p></Link>)}{upcomingBookings.length === 0 && <p className="text-ink/60">No upcoming bookings.</p>}</div></section></div><div className="mt-10 flex flex-wrap gap-4 text-sm font-bold"><Link href="/equipment" className="bg-ink px-4 py-3 text-white">Browse equipment</Link><Link href="/availability" className="border border-ink/20 px-4 py-3 text-signal">Check availability</Link><Link href="/history" className="border border-ink/20 px-4 py-3 text-signal">View history</Link></div></section></div></main>;
}
