"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getBookings, getLoans, getStudents, issueBooking, transferLoan, type Booking, type Loan, type StudentSummary } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function StaffLoansPage() {
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [dueDates, setDueDates] = useState<Record<number, string>>({});
  const [selectedLoan, setSelectedLoan] = useState<Loan | null>(null);
  const [newBorrowerId, setNewBorrowerId] = useState("");
  const [reason, setReason] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function load(token: string) {
    const [bookingData, loanData, studentData] = await Promise.all([getBookings(token), getLoans(token), getStudents(token)]);
    setBookings(bookingData); setLoans(loanData); setStudents(studentData);
  }

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.replace("/login"); return; }
    load(token).catch((error: unknown) => setErrorMessage(error instanceof Error ? error.message : "Unable to load loan operations."));
  }, [router]);

  async function issue(booking: Booking) {
    const token = getAccessToken();
    if (!token || !dueDates[booking.id]) { setErrorMessage("Choose a due date before issuing equipment."); return; }
    try { await issueBooking(token, booking.id, { due_at: new Date(dueDates[booking.id]).toISOString() }); setMessage(`Equipment issued for ${booking.booking_code}.`); setErrorMessage(""); await load(token); } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Unable to issue equipment."); }
  }

  async function transfer() {
    const token = getAccessToken();
    if (!token || !selectedLoan || !newBorrowerId) { setErrorMessage("Choose a destination borrower."); return; }
    if (!window.confirm("You are transferring this active loan to another borrower. The original due date will remain unchanged and the equipment will remain issued.")) return;
    setIsSubmitting(true); setErrorMessage(""); setMessage("");
    try {
      const response = await transferLoan(token, selectedLoan.id, { new_borrower_id: Number(newBorrowerId), reason });
      setMessage("Loan successfully transferred.");
      setSelectedLoan(response.loan);
      setNewBorrowerId(""); setReason("");
      await load(token);
    } catch (error) { setErrorMessage(error instanceof Error ? error.message : "Unable to transfer loan."); }
    finally { setIsSubmitting(false); }
  }

  const transferableLoans = loans.filter((loan) => loan.status === "ACTIVE" || loan.status === "OVERDUE");

  return <main className="min-h-screen bg-canvas px-6 py-10 text-ink sm:px-10 lg:px-20"><div className="mx-auto max-w-6xl"><nav className="flex items-center justify-between border-b border-ink/15 pb-6"><Link href="/staff/dashboard" className="text-2xl font-bold">AVault staff</Link><div className="flex gap-4 text-sm font-bold"><Link href="/staff/bookings" className="text-signal">Bookings</Link><Link href="/staff/returns" className="text-signal">Returns</Link></div></nav><section className="py-12"><p className="text-sm font-bold uppercase tracking-[0.2em] text-signal">Loan operations</p><h1 className="mt-4 text-5xl tracking-tight">Issue and transfer loans</h1>{message && <p className="mt-5 border border-emerald-500/30 bg-emerald-100 p-4 text-emerald-800">{message}</p>}{errorMessage && <p className="mt-5 border border-signal/30 bg-signal/10 p-4 text-signal">{errorMessage}</p>}<section className="mt-10"><h2 className="text-2xl">Approved bookings awaiting issue</h2><div className="mt-4 space-y-4">{bookings.filter((booking) => booking.status === "APPROVED").map((booking) => <article className="border border-ink/15 bg-white p-6" key={booking.id}><p className="font-bold">{booking.booking_code} · {booking.borrower_name}</p><p className="mt-2 text-sm text-ink/60">{booking.items.map((item) => `${item.equipment_name} x ${item.quantity}`).join(", ")}</p><div className="mt-4 flex flex-wrap items-end gap-4"><div className="text-sm">{booking.booking_units.map((unit) => <span className="mr-2 inline-block bg-mint px-2 py-1 font-mono text-xs" key={unit.id}>{unit.asset_code}</span>)}</div><label className="text-sm font-bold">Due date/time<input className="mt-2 border border-ink/20 px-3 py-2 font-normal" type="datetime-local" value={dueDates[booking.id] ?? ""} onChange={(event) => setDueDates({ ...dueDates, [booking.id]: event.target.value })} /></label><button className="bg-ink px-4 py-3 font-bold text-white" onClick={() => issue(booking)}>Issue equipment</button></div></article>)}</div></section><section className="mt-12"><h2 className="text-2xl">Transfer active loan</h2><div className="mt-4 grid gap-6 border border-ink/15 bg-white p-6 lg:grid-cols-[1fr_1fr]"><label className="text-sm font-bold lg:col-span-2">Select active or overdue loan<select className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" value={selectedLoan?.id ?? ""} onChange={(event) => setSelectedLoan(transferableLoans.find((loan) => loan.id === Number(event.target.value)) ?? null)}><option value="">Choose loan</option>{transferableLoans.map((loan) => <option value={loan.id} key={loan.id}>Loan #{loan.id} · {loan.borrower_name} · {loan.status}</option>)}</select></label>{selectedLoan && <div className="grid gap-4 border-t border-ink/10 pt-5 text-sm lg:col-span-2 sm:grid-cols-2"><p><span className="text-ink/55">Current borrower</span><br /><strong>{selectedLoan.borrower_name}</strong></p><p><span className="text-ink/55">Status</span><br /><strong>{selectedLoan.status}</strong></p><p><span className="text-ink/55">Issued</span><br />{selectedLoan.issued_at}</p><p><span className="text-ink/55">Current due date</span><br />{selectedLoan.due_at}</p><p className="sm:col-span-2"><span className="text-ink/55">Equipment</span><br />{selectedLoan.items.map((item) => `${item.equipment_name} · ${item.asset_code}`).join(", ")}</p></div>}{selectedLoan && <><label className="text-sm font-bold">New borrower<select className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" value={newBorrowerId} onChange={(event) => setNewBorrowerId(event.target.value)} required><option value="">Choose active student</option>{students.filter((student) => student.id !== selectedLoan.borrower).map((student) => <option value={student.id} key={student.id}>{student.name}{student.student_id ? ` · ${student.student_id}` : ""}</option>)}</select></label><label className="text-sm font-bold">Reason<input className="mt-2 w-full border border-ink/20 px-3 py-3 font-normal" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Optional handover reason" /></label><button className="bg-signal px-4 py-3 font-bold text-white disabled:opacity-50 lg:col-span-2" disabled={isSubmitting || !newBorrowerId} onClick={transfer}>{isSubmitting ? "Transferring..." : "Transfer Loan"}</button></>}</div></section></section></div></main>;
}
