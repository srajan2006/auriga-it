"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getEquipment,
  getEquipmentAvailabilityForDates,
  type DateRangeAvailability,
  type EquipmentModel,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function AvailabilityPage() {
  const router = useRouter();
  const [equipment, setEquipment] = useState<EquipmentModel[]>([]);
  const [equipmentId, setEquipmentId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [result, setResult] = useState<DateRangeAvailability | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    getEquipment(token)
      .then((items) => {
        setEquipment(items);
        if (items[0]) setEquipmentId(String(items[0].id));
      })
      .catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load equipment."))
      .finally(() => setIsLoading(false));
  }, [router]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    if (!equipmentId || !startDate || !endDate) {
      setErrorMessage("Choose equipment and both dates to check availability.");
      return;
    }
    setErrorMessage("");
    setResult(null);
    setIsSearching(true);
    try {
      setResult(await getEquipmentAvailabilityForDates(token, equipmentId, startDate, endDate));
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to check availability.");
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20">
      <div className="mx-auto max-w-5xl">
        <nav className="flex items-center justify-between border-b border-ink/15 pb-6">
          <Link href="/dashboard" className="text-2xl font-bold tracking-tight">AVault</Link>
          <Link href="/equipment" className="text-sm font-bold text-signal">Browse inventory</Link>
        </nav>
        <section className="py-12">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Date-range search</p>
          <h1 className="mt-4 text-5xl tracking-tight">Check availability</h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-ink/65">Select an equipment model and dates. Results exclude units reserved by overlapping pending or approved reservations and units that are not currently available.</p>
          <form onSubmit={handleSearch} className="mt-10 grid gap-4 border border-ink/15 bg-white p-6 md:grid-cols-[1.4fr_1fr_1fr_auto] md:items-end">
            <label className="text-sm font-bold">Equipment<select className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)} disabled={isLoading} required><option value="">Choose equipment</option>{equipment.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
            <label className="text-sm font-bold">Start date<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} required /></label>
            <label className="text-sm font-bold">End date<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal outline-none focus:border-signal" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} required /></label>
            <button className="bg-ink px-5 py-3 font-bold text-white disabled:cursor-not-allowed disabled:opacity-50" type="submit" disabled={isSearching}>{isSearching ? "Checking..." : "Check"}</button>
          </form>
          {errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}
          {result && <section className="mt-10 border border-ink/15 bg-white p-7 shadow-[8px_8px_0_#d8f3e4]">
            <div className="flex flex-wrap items-end justify-between gap-4 border-b border-ink/10 pb-6"><div><p className="text-sm uppercase tracking-[0.16em] text-ink/55">{result.start_date} to {result.end_date}</p><h2 className="mt-2 text-3xl">{result.name}</h2></div><p className={`text-2xl ${result.available ? "text-emerald-700" : "text-signal"}`}>{result.available_quantity} available</p></div>
            <p className="mt-6 text-ink/65">{result.available ? "These physical units are available for the selected range." : "No physical units are available for the selected range."}</p>
            {result.available_asset_codes.length > 0 && <div className="mt-6 flex flex-wrap gap-3">{result.available_asset_codes.map((assetCode) => <span className="border border-ink/15 bg-mint px-3 py-2 text-sm font-bold" key={assetCode}>{assetCode}</span>)}</div>}
          </section>}
        </section>
      </div>
    </main>
  );
}