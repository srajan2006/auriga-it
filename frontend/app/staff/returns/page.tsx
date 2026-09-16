"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getLoans, returnLoan, type Loan } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const conditions = ["EXCELLENT", "GOOD", "FAIR", "DAMAGED"];
const statuses = ["AVAILABLE", "DAMAGED", "MAINTENANCE", "LOST"];

type ReturnState = Record<number, { condition: string; status: string }>;

export default function StaffReturnsPage() {
  const router = useRouter();
  const [loans, setLoans] = useState<Loan[]>([]);
  const [returnState, setReturnState] = useState<ReturnState>({});
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function load(token: string) {
    setLoans((await getLoans(token)).filter((loan) => loan.status === "ACTIVE" || loan.status === "OVERDUE"));
  }

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    load(token).catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load returns."));
  }, [router]);

  async function processReturn(loan: Loan) {
    const token = getAccessToken();
    if (!token) return;
    const items = loan.items.map((item) => ({
      loan_item_id: item.id,
      condition: returnState[item.id]?.condition ?? item.condition_at_issue,
      status: returnState[item.id]?.status ?? "AVAILABLE",
    }));
    try {
      await returnLoan(token, loan.id, { items });
      setMessage(`Return completed for ${loan.booking_code}.`);
      setErrorMessage("");
      await load(token);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to process return.");
    }
  }

  function updateItem(itemId: number, field: "condition" | "status", value: string) {
    setReturnState((current) => ({
      ...current,
      [itemId]: { condition: current[itemId]?.condition ?? "GOOD", status: current[itemId]?.status ?? "AVAILABLE", [field]: value },
    }));
  }

  return (
    <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <nav className="flex items-center justify-between border-b border-ink/15 pb-6">
          <Link href="/dashboard" className="text-2xl font-bold">AVault staff</Link>
          <Link href="/staff/loans" className="text-sm font-bold text-signal">Issue desk</Link>
        </nav>
        <section className="py-12">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Staff return desk</p>
          <h1 className="mt-4 text-5xl tracking-tight">Process returns</h1>
          {message && <p className="mt-5 border border-emerald-500/30 bg-emerald-100 p-4 text-emerald-800">{message}</p>}
          {errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}
          <div className="mt-10 space-y-6">
            {loans.length === 0 ? <p className="text-ink/60">No active or overdue loans are waiting for return.</p> : loans.map((loan) => (
              <article className="border border-ink/15 bg-white p-6" key={loan.id}>
                <div className="flex flex-wrap justify-between gap-3">
                  <div><p className="text-sm uppercase tracking-[0.14em] text-ink/55">{loan.booking_code} · {loan.borrower_name}</p><p className="mt-2 text-sm text-ink/60">Due {new Date(loan.due_at).toLocaleString()}</p></div>
                  <strong className={loan.status === "OVERDUE" ? "text-signal" : "text-emerald-700"}>{loan.status}</strong>
                </div>
                <div className="mt-6 space-y-4 border-t border-ink/10 pt-5">
                  {loan.items.map((item) => <div className="grid gap-3 border-b border-ink/10 pb-4 md:grid-cols-[1fr_180px_180px] md:items-end" key={item.id}><div><p className="font-bold">{item.equipment_name} · {item.asset_code}</p><p className="mt-1 text-sm text-ink/60">Issued condition: {item.condition_at_issue}</p></div><label className="text-sm font-bold">Return condition<select className="mt-2 w-full border border-ink/20 px-3 py-2 font-normal" value={returnState[item.id]?.condition ?? "GOOD"} onChange={(event) => updateItem(item.id, "condition", event.target.value)}>{conditions.map((condition) => <option value={condition} key={condition}>{condition}</option>)}</select></label><label className="text-sm font-bold">Unit status<select className="mt-2 w-full border border-ink/20 px-3 py-2 font-normal" value={returnState[item.id]?.status ?? "AVAILABLE"} onChange={(event) => updateItem(item.id, "status", event.target.value)}>{statuses.map((status) => <option value={status} key={status}>{status}</option>)}</select></label></div>)}
                </div>
                <button className="mt-5 bg-ink px-4 py-3 font-bold text-white" onClick={() => processReturn(loan)}>Complete return</button>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
