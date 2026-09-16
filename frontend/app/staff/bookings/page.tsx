"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { approveBooking, getBookings, rejectBooking, type Booking } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function StaffBookingsPage() {
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  async function load(token: string) { setBookings(await getBookings(token)); }

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    load(token).catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load bookings."));
  }, [router]);

  async function decide(booking: Booking, action: "approve" | "reject") {
    const token = getAccessToken();
    if (!token) return;
    try {
      if (action === "reject") await rejectBooking(token, booking.id, "Rejected by staff");
      else {
        const unitIds = window.prompt("Enter assigned unit IDs separated by commas", "")?.split(",").map((value) => Number(value.trim())).filter(Boolean) ?? [];
        await approveBooking(token, booking.id, unitIds);
      }
      await load(token);
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Unable to update booking."); }
  }

  return <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20"><div className="mx-auto max-w-6xl"><nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/dashboard" className="text-2xl font-bold">AVault staff</Link><Link href="/staff/equipment" className="text-sm font-bold text-signal">Manage inventory</Link></nav><section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Staff workflow</p><h1 className="mt-4 text-5xl tracking-tight">Booking requests</h1>{errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}<div className="mt-10 overflow-x-auto border border-ink/15 bg-white"><table className="w-full min-w-[900px] text-left text-sm"><thead className="border-b border-ink/10 text-ink/55"><tr><th className="p-4">Borrower</th><th className="p-4">Equipment</th><th className="p-4">Dates</th><th className="p-4">Status</th><th className="p-4">Actions</th></tr></thead><tbody>{bookings.map((booking) => <tr className="border-b border-ink/10" key={booking.id}><td className="p-4">{booking.borrower_name}</td><td className="p-4">{booking.items.map((item) => `${item.equipment_name} x ${item.quantity}`).join(", ")}</td><td className="p-4">{booking.start_date} to {booking.end_date}</td><td className="p-4">{booking.status}</td><td className="flex gap-3 p-4">{booking.status === "PENDING" && <><button className="font-bold text-emerald-700" onClick={() => decide(booking, "approve")}>Approve</button><button className="font-bold text-signal" onClick={() => decide(booking, "reject")}>Reject</button></>}</td></tr>)}</tbody></table></div></section></div></main>;
}