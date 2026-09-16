"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { createBooking, getBookings, getEquipment, type Booking, type EquipmentModel } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function BookingsPage() {
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [equipment, setEquipment] = useState<EquipmentModel[]>([]);
  const [equipmentModel, setEquipmentModel] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [purpose, setPurpose] = useState("");
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function load(token: string) {
    const [bookingData, equipmentData] = await Promise.all([getBookings(token), getEquipment(token)]);
    setBookings(bookingData);
    setEquipment(equipmentData);
    if (!equipmentModel && equipmentData[0]) setEquipmentModel(String(equipmentData[0].id));
  }

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    load(token).catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load bookings."));
  }, [router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token) return;
    setErrorMessage(""); setMessage("");
    try {
      await createBooking(token, { start_date: startDate, end_date: endDate, purpose, notes: "", items: [{ equipment_model: Number(equipmentModel), quantity: Number(quantity) }] });
      await load(token);
      setMessage("Booking request submitted for staff review.");
      setPurpose("");
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Unable to submit booking request."); }
  }

  return (
    <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/dashboard" className="text-2xl font-bold">AVault</Link><Link href="/equipment" className="text-sm font-bold text-signal">Browse inventory</Link></nav>
        <section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Student bookings</p><h1 className="mt-4 text-5xl tracking-tight">Request equipment</h1>
          {message && <p className="mt-5 border border-emerald-500/30 bg-emerald-100 p-4 text-emerald-800">{message}</p>}
          {errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}
          <form onSubmit={submit} className="mt-8 grid gap-4 border border-ink/15 bg-white p-6 md:grid-cols-2"><select className="border border-ink/20 px-3 py-3 md:col-span-2" value={equipmentModel} onChange={(event) => setEquipmentModel(event.target.value)} required><option value="">Choose equipment</option>{equipment.map((item) => <option value={item.id} key={item.id}>{item.name} ({item.available_quantity} available now)</option>)}</select><label className="text-sm font-bold">Start date<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} required /></label><label className="text-sm font-bold">End date<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} required /></label><label className="text-sm font-bold">Quantity<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" type="number" min="1" value={quantity} onChange={(event) => setQuantity(event.target.value)} required /></label><label className="text-sm font-bold">Purpose<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" value={purpose} onChange={(event) => setPurpose(event.target.value)} required /></label><button className="bg-ink px-4 py-3 font-bold text-white md:col-span-2" type="submit">Request booking</button></form>
          <div className="mt-10 space-y-4">{bookings.length === 0 ? <p className="text-ink/60">No booking requests yet.</p> : bookings.map((booking) => <article className="border border-ink/15 bg-white p-6" key={booking.id}><div className="flex flex-wrap justify-between gap-3"><h2 className="text-2xl">{booking.booking_code}</h2><strong className="text-signal">{booking.status}</strong></div><p className="mt-2 text-ink/60">{booking.start_date} to {booking.end_date} · {booking.purpose}</p><p className="mt-4 text-sm">{booking.items.map((item) => `${item.equipment_name} x ${item.quantity}`).join(", ")}</p></article>)}</div>
        </section>
      </div>
    </main>
  );
}