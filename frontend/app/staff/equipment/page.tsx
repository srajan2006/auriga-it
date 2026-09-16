"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { createEquipment, createEquipmentUnit, getCategories, getEquipment, getMe, updateEquipment, type Category, type EquipmentModel, type User } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const blankModel = { category: "", name: "", manufacturer: "", model_number: "", deposit_amount: "0", late_fee_per_day: "0", max_borrow_quantity: "1" };

export default function StaffEquipmentPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [equipment, setEquipment] = useState<EquipmentModel[]>([]);
  const [model, setModel] = useState(blankModel);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [unit, setUnit] = useState({ equipment_model: "", asset_code: "" });
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function load(token: string) {
    const [me, categoryData, equipmentData] = await Promise.all([getMe(token), getCategories(token), getEquipment(token)]);
    setUser(me.user);
    setCategories(categoryData);
    setEquipment(equipmentData);
  }

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    load(token).catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load inventory."));
  }, [router]);

  async function submitModel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token) return;
    setMessage(""); setErrorMessage("");
    try {
      const payload = { ...model, category: Number(model.category), max_borrow_quantity: Number(model.max_borrow_quantity) };
      if (editingId) await updateEquipment(token, editingId, payload);
      else await createEquipment(token, payload);
      await load(token);
      setModel(blankModel);
      setEditingId(null);
      setMessage(editingId ? "Equipment model updated." : "Equipment model created.");
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Unable to create equipment."); }
  }

  async function submitUnit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getAccessToken();
    if (!token) return;
    setMessage(""); setErrorMessage("");
    try {
      await createEquipmentUnit(token, { equipment_model: Number(unit.equipment_model), asset_code: unit.asset_code });
      await load(token);
      setUnit({ equipment_model: "", asset_code: "" });
      setMessage("Equipment unit added.");
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Unable to add equipment unit."); }
  }

  async function toggleActive(item: EquipmentModel) {
    const token = getAccessToken();
    if (!token) return;
    try { await updateEquipment(token, item.id, { is_active: !item.is_active }); await load(token); }
    catch (error) { setErrorMessage(error instanceof Error ? error.message : "Unable to update equipment."); }
  }

  if (!user) return <main className="flex min-h-screen items-center justify-center bg-canvas text-ink">Loading staff inventory...</main>;
  if (user.role === "STUDENT") return <main className="min-h-screen bg-canvas p-10 text-ink"><p className="text-signal">Staff access is required.</p></main>;

  return (
    <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/dashboard" className="text-2xl font-bold">AVault staff</Link><Link href="/equipment" className="text-sm font-bold text-signal">Student view</Link></nav>
        <section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Staff inventory</p><h1 className="mt-4 text-5xl tracking-tight">Manage equipment</h1>
          {message && <p className="mt-5 border border-emerald-500/30 bg-emerald-100 p-4 text-emerald-800">{message}</p>}
          {errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}
          <div className="mt-10 grid gap-6 lg:grid-cols-2">
            <form onSubmit={submitModel} className="border border-ink/15 bg-white p-6"><h2 className="text-2xl">{editingId ? "Edit equipment model" : "Add equipment model"}</h2><div className="mt-5 grid gap-4 sm:grid-cols-2"><select className="border border-ink/20 px-3 py-3 sm:col-span-2" value={model.category} onChange={(e) => setModel({ ...model, category: e.target.value })} required><option value="">Choose category</option>{categories.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select><input className="border border-ink/20 px-3 py-3 sm:col-span-2" placeholder="Name" value={model.name} onChange={(e) => setModel({ ...model, name: e.target.value })} required /><input className="border border-ink/20 px-3 py-3" placeholder="Manufacturer" value={model.manufacturer} onChange={(e) => setModel({ ...model, manufacturer: e.target.value })} /><input className="border border-ink/20 px-3 py-3" placeholder="Model number" value={model.model_number} onChange={(e) => setModel({ ...model, model_number: e.target.value })} /><input className="border border-ink/20 px-3 py-3" type="number" min="0" step="0.01" placeholder="Deposit" value={model.deposit_amount} onChange={(e) => setModel({ ...model, deposit_amount: e.target.value })} /><input className="border border-ink/20 px-3 py-3" type="number" min="0" step="0.01" placeholder="Late fee/day" value={model.late_fee_per_day} onChange={(e) => setModel({ ...model, late_fee_per_day: e.target.value })} /><input className="border border-ink/20 px-3 py-3" type="number" min="1" placeholder="Max borrow quantity" value={model.max_borrow_quantity} onChange={(e) => setModel({ ...model, max_borrow_quantity: e.target.value })} /><button className="bg-ink px-4 py-3 font-bold text-white sm:col-span-2" type="submit">{editingId ? "Save changes" : "Create model"}</button>{editingId && <button className="border border-ink/20 px-4 py-3 font-bold sm:col-span-2" type="button" onClick={() => { setEditingId(null); setModel(blankModel); }}>Cancel edit</button>}</div></form>
            <form onSubmit={submitUnit} className="border border-ink/15 bg-white p-6"><h2 className="text-2xl">Add physical unit</h2><div className="mt-5 grid gap-4"><select className="border border-ink/20 px-3 py-3" value={unit.equipment_model} onChange={(e) => setUnit({ ...unit, equipment_model: e.target.value })} required><option value="">Choose model</option>{equipment.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select><input className="border border-ink/20 px-3 py-3" placeholder="Asset code, e.g. DSLR-004" value={unit.asset_code} onChange={(e) => setUnit({ ...unit, asset_code: e.target.value })} required /><button className="bg-ink px-4 py-3 font-bold text-white" type="submit">Add unit</button></div></form>
          </div>
          <div className="mt-10 overflow-x-auto border border-ink/15 bg-white"><table className="w-full min-w-[720px] text-left text-sm"><thead className="border-b border-ink/10 text-ink/55"><tr><th className="p-4">Equipment</th><th className="p-4">Category</th><th className="p-4">Units</th><th className="p-4">Status</th><th className="p-4">Action</th></tr></thead><tbody>{equipment.map((item) => <tr className="border-b border-ink/10" key={item.id}><td className="p-4 font-bold">{item.name}</td><td className="p-4">{item.category_name}</td><td className="p-4">{item.available_quantity} / {item.total_quantity} available</td><td className="p-4">{item.is_active ? "Active" : "Archived"}</td><td className="flex gap-4 p-4"><button className="font-bold text-signal" onClick={() => { setEditingId(item.id); setModel({ category: String(item.category), name: item.name, manufacturer: item.manufacturer, model_number: item.model_number, deposit_amount: item.deposit_amount, late_fee_per_day: item.late_fee_per_day, max_borrow_quantity: String(item.max_borrow_quantity) }); }}>{"Edit"}</button><button className="font-bold text-signal" onClick={() => toggleActive(item)}>{item.is_active ? "Archive" : "Activate"}</button></td></tr>)}</tbody></table></div>
        </section>
      </div>
    </main>
  );
}
