"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getCategories, getEquipment, type Category, type EquipmentModel } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function EquipmentPage() {
  const router = useRouter();
  const [equipment, setEquipment] = useState<EquipmentModel[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [availability, setAvailability] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    Promise.all([getCategories(token), getEquipment(token)])
      .then(([categoryData, equipmentData]) => {
        setCategories(categoryData);
        setEquipment(equipmentData);
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
    setIsLoading(true);
    setErrorMessage("");
    try {
      setEquipment(await getEquipment(token, { search, category, availability, start_date: startDate, end_date: endDate }));
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to filter equipment.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <nav className="flex items-center justify-between border-b border-ink/15 pb-6">
          <Link href="/dashboard" className="text-2xl font-bold tracking-tight">AVault</Link>
          <Link href="/dashboard" className="text-sm font-bold text-signal">Dashboard</Link>
        </nav>
        <section className="py-12">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Inventory</p>
          <h1 className="mt-4 text-5xl tracking-tight">Find equipment</h1>
          <form onSubmit={handleSearch} className="mt-8 grid gap-3 border border-ink/15 bg-white p-5 md:grid-cols-[1fr_180px_180px_150px_150px_auto]">
            <input className="border border-ink/20 px-3 py-3 outline-none focus:border-signal" placeholder="Search cameras, projectors..." value={search} onChange={(event) => setSearch(event.target.value)} />
            <select className="border border-ink/20 px-3 py-3 outline-none focus:border-signal" value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="">All categories</option>
              {categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <select className="border border-ink/20 px-3 py-3 outline-none focus:border-signal" value={availability} onChange={(event) => setAvailability(event.target.value)}>
              <option value="">Any availability</option>
              <option value="available">Available now</option>
              <option value="unavailable">Unavailable</option>
            </select>
            <input className="border border-ink/20 px-3 py-3 outline-none focus:border-signal" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} aria-label="Start date" />
            <input className="border border-ink/20 px-3 py-3 outline-none focus:border-signal" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} aria-label="End date" />
            <button className="bg-ink px-5 py-3 font-bold text-white" type="submit">Search</button>
          </form>
          {errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}
          {isLoading ? <p className="mt-10 text-ink/60">Loading inventory...</p> : equipment.length === 0 ? <p className="mt-10 text-ink/60">No equipment matches those filters.</p> : <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {equipment.map((item) => (
              <Link href={`/equipment/${item.id}`} key={item.id} className="border border-ink/15 bg-white p-6 transition hover:-translate-y-1 hover:border-signal">
                <p className="text-sm uppercase tracking-[0.14em] text-signal">{item.category_name}</p>
                <h2 className="mt-3 text-2xl">{item.name}</h2>
                <p className="mt-2 text-sm text-ink/60">{item.manufacturer} {item.model_number}</p>
                <div className="mt-8 flex justify-between border-t border-ink/10 pt-4 text-sm"><span>Available</span><strong>{item.available_quantity} / {item.total_quantity}</strong></div>
                <div className="mt-2 flex justify-between text-sm text-ink/60"><span>Deposit</span><span>₹{item.deposit_amount}</span></div>
              </Link>
            ))}
          </div>}
        </section>
      </div>
    </main>
  );
}
