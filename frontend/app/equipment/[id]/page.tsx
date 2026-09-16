"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getEquipmentAvailability, getEquipmentById, type EquipmentAvailability, type EquipmentModel } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function EquipmentDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [equipment, setEquipment] = useState<EquipmentModel | null>(null);
  const [availability, setAvailability] = useState<EquipmentAvailability | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    Promise.all([getEquipmentById(token, params.id), getEquipmentAvailability(token, params.id)])
      .then(([equipmentData, availabilityData]) => {
        setEquipment(equipmentData);
        setAvailability(availabilityData);
      })
      .catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load equipment."));
  }, [params.id, router]);

  async function checkDateAvailability() {
    const token = getAccessToken();
    if (!token || !startDate || !endDate) return;
    try {
      setAvailability(await getEquipmentAvailability(token, params.id, { start_date: startDate, end_date: endDate }));
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to check date availability.");
    }
  }

  if (errorMessage) return <main className="min-h-screen bg-canvas px-6 py-12 text-signal"><p>{errorMessage}</p></main>;
  if (!equipment || !availability) return <main className="flex min-h-screen items-center justify-center bg-canvas text-ink">Loading equipment...</main>;

  return (
    <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20">
      <div className="mx-auto max-w-5xl">
        <Link href="/equipment" className="text-sm font-bold text-signal">← Back to inventory</Link>
        <section className="mt-10 grid gap-10 lg:grid-cols-[1fr_0.8fr]">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">{equipment.category_name}</p>
            <h1 className="mt-4 text-5xl tracking-tight">{equipment.name}</h1>
            <p className="mt-4 text-lg text-ink/65">{equipment.description || "No description has been added yet."}</p>
            <dl className="mt-10 grid gap-5 border-t border-ink/15 pt-6 sm:grid-cols-2">
              <div><dt className="text-sm text-ink/55">Manufacturer</dt><dd className="mt-1 text-lg">{equipment.manufacturer || "Not specified"}</dd></div>
              <div><dt className="text-sm text-ink/55">Model</dt><dd className="mt-1 text-lg">{equipment.model_number || "Not specified"}</dd></div>
              <div><dt className="text-sm text-ink/55">Deposit</dt><dd className="mt-1 text-lg">₹{equipment.deposit_amount}</dd></div>
              <div><dt className="text-sm text-ink/55">Late fee per day</dt><dd className="mt-1 text-lg">₹{equipment.late_fee_per_day}</dd></div>
            </dl>
          </div>
          <aside className="border border-ink/15 bg-white p-7 shadow-[8px_8px_0_#d8f3e4]">
            <p className="text-sm font-bold uppercase tracking-[0.16em]">Current availability</p>
            <p className="mt-5 text-5xl">{availability.available_quantity}<span className="text-xl text-ink/45"> / {availability.total_quantity}</span></p>
            <p className="mt-2 text-ink/60">units available now</p>
            <div className="mt-7 space-y-3 border-t border-ink/10 pt-5">
              <p className="text-sm font-bold">Check a date range</p>
              <input className="w-full border border-ink/20 px-3 py-2" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
              <input className="w-full border border-ink/20 px-3 py-2" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
              <button className="w-full bg-ink px-3 py-2 font-bold text-white disabled:opacity-50" type="button" disabled={!startDate || !endDate} onClick={checkDateAvailability}>Check availability</button>
            </div>
            <div className="mt-8 space-y-3 border-t border-ink/10 pt-5 text-sm">
              {availability.status_counts && Object.entries(availability.status_counts).map(([status, count]) => <div className="flex justify-between" key={status}><span className="text-ink/60">{status}</span><strong>{count}</strong></div>)}
              {availability.available_asset_codes.length > 0 && <div className="flex justify-between"><span className="text-ink/60">Matching assets</span><strong>{availability.available_asset_codes.join(", ")}</strong></div>}
            </div>
            <p className="mt-8 border-t border-ink/10 pt-5 text-sm text-ink/60">Booking requests will be available in the next phase.</p>
          </aside>
        </section>
      </div>
    </main>
  );
}
