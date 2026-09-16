export type HealthResponse = {
  success: boolean;
  message: string;
  service: string;
  database: "available" | "unavailable";
};

export type UserRole = "STUDENT" | "STAFF" | "ADMIN";

export type User = {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  student_id: string | null;
  phone: string;
  created_at: string;
};

export type StudentSummary = Pick<User, "id" | "name" | "student_id">;

export type Category = {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
};

export type EquipmentUnit = {
  id: number;
  equipment_model: number;
  asset_code: string;
  serial_number: string | null;
  status: string;
  condition: string;
  location: string;
  notes: string;
  created_at: string;
  updated_at: string;
};

export type EquipmentModel = {
  id: number;
  category: number;
  category_name: string;
  name: string;
  description: string;
  manufacturer: string;
  model_number: string;
  deposit_amount: string;
  late_fee_per_day: string;
  max_borrow_quantity: number;
  image: string;
  is_active: boolean;
  total_quantity: number;
  available_quantity: number;
  units?: EquipmentUnit[];
  created_at: string;
  updated_at: string;
};

export type EquipmentAvailability = {
  equipment_model: number;
  name: string;
  total_quantity: number;
  available_quantity: number;
  available: boolean;
  requested_quantity: number | null;
  available_asset_codes: string[];
  status_counts?: Record<string, number>;
};

export type DateRangeAvailability = {
  equipment_model: number;
  name: string;
  start_date: string;
  end_date: string;
  total_quantity: number;
  available_quantity: number;
  requested_quantity: number | null;
  available: boolean;
  available_asset_codes: string[];
};

export type BookingItem = {
  id: number;
  equipment_model: number;
  equipment_name: string;
  quantity: number;
  available_quantity: number;
};

export type BookingUnit = {
  id: number;
  equipment_unit: number;
  asset_code: string;
};

export type Booking = {
  id: number;
  booking_code: string;
  borrower: number;
  borrower_name: string;
  start_date: string;
  end_date: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED" | "COMPLETED";
  purpose: string;
  notes: string;
  approved_by: number | null;
  approved_at: string | null;
  items: BookingItem[];
  booking_units: BookingUnit[];
  created_at: string;
  updated_at: string;
};

export type LoanItem = {
  id: number;
  equipment_unit: number;
  asset_code: string;
  equipment_name: string;
  condition_at_issue: string;
  condition_at_return: string | null;
  notes: string;
};

export type Loan = {
  id: number;
  booking: number;
  booking_code: string;
  borrower: number;
  borrower_name: string;
  issued_by: number;
  issued_by_name: string;
  issued_at: string;
  due_at: string;
  returned_at: string | null;
  status: "ACTIVE" | "OVERDUE" | "RETURNED" | "LOST";
  notes: string;
  items: LoanItem[];
  late_fee: LateFee | null;
  created_at: string;
  updated_at: string;
};

export type BorrowerSummary = {
  id: number;
  name: string;
  student_id: string | null;
};

export type LoanTransfer = {
  id: number;
  loan: number;
  previous_borrower: BorrowerSummary;
  new_borrower: BorrowerSummary;
  transferred_by: BorrowerSummary;
  reason: string;
  transferred_at: string;
};

export type LateFee = {
  id: number;
  loan: number;
  amount: string;
  days_late: number;
  status: "PENDING" | "PAID" | "WAIVED";
  calculated_at: string;
  created_at: string;
};

export type SystemSettings = {
  id: number;
  max_active_loans_per_user: number;
  max_units_per_booking: number;
  default_late_fee_per_day: string;
  updated_at: string;
};

export type AuthResponse = {
  success: true;
  message: string;
  access: string;
  refresh: string;
  user: User;
};

export type MeResponse = {
  success: true;
  user: User;
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiUrl}/health/`, { cache: "no-store" });
  const payload = (await response.json()) as HealthResponse;

  if (!response.ok) {
    throw new Error(payload.message || "The backend health check failed.");
  }

  return payload;
}

async function request<T>(path: string, options: RequestInit = {}, accessToken?: string): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${apiUrl}${path}`, { ...options, headers });
  const payload = (await response.json().catch(() => ({}))) as Record<string, unknown>;
  if (!response.ok) {
    const detail = payload.message ?? Object.values(payload).flat().join(" ");
    throw new ApiError(response.status, typeof detail === "string" ? detail : "The request failed.");
  }
  return payload as T;
}

export function register(data: {
  name: string;
  email: string;
  password: string;
  password_confirm: string;
  student_id: string;
  phone: string;
}) {
  return request<AuthResponse>("/auth/register/", { method: "POST", body: JSON.stringify(data) });
}

export function login(data: { email: string; password: string }) {
  return request<AuthResponse>("/auth/login/", { method: "POST", body: JSON.stringify(data) });
}

export function refreshAccessToken(refreshToken: string) {
  return request<{ success: true; access: string }>(
    "/auth/refresh/",
    { method: "POST", body: JSON.stringify({ refresh: refreshToken }) },
  );
}

export function getMe(accessToken: string) {
  return request<MeResponse>("/auth/me/", {}, accessToken);
}

export function getStudents(accessToken: string) {
  return request<StudentSummary[]>("/auth/students/", {}, accessToken);
}

export function getSystemSettings(accessToken: string) {
  return request<SystemSettings>("/settings/", {}, accessToken);
}

export function updateSystemSettings(accessToken: string, data: Partial<Omit<SystemSettings, "id" | "updated_at">>) {
  return request<SystemSettings>("/settings/", { method: "PATCH", body: JSON.stringify(data) }, accessToken);
}

export function getCategories(accessToken: string) {
  return request<Category[]>("/categories/", {}, accessToken);
}

export function getEquipment(accessToken: string, params: { search?: string; category?: string; availability?: string; start_date?: string; end_date?: string; is_active?: string } = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<EquipmentModel[]>(`/equipment/${suffix}`, {}, accessToken);
}

export function getEquipmentById(accessToken: string, id: string) {
  return request<EquipmentModel>(`/equipment/${id}/`, {}, accessToken);
}

export function getEquipmentAvailability(accessToken: string, id: string, params: { start_date?: string; end_date?: string } = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<EquipmentAvailability>(`/equipment/${id}/availability/${suffix}`, {}, accessToken);
}

export function getEquipmentAvailabilityForDates(
  accessToken: string,
  id: string,
  startDate: string,
  endDate: string,
) {
  const query = new URLSearchParams({ start_date: startDate, end_date: endDate });
  return request<DateRangeAvailability>(`/equipment/${id}/availability/?${query.toString()}`, {}, accessToken);
}

export function createEquipment(accessToken: string, data: Record<string, unknown>) {
  return request<EquipmentModel>("/equipment/", { method: "POST", body: JSON.stringify(data) }, accessToken);
}

export function updateEquipment(accessToken: string, id: number, data: Record<string, unknown>) {
  return request<EquipmentModel>(`/equipment/${id}/`, { method: "PATCH", body: JSON.stringify(data) }, accessToken);
}

export function createEquipmentUnit(accessToken: string, data: Record<string, unknown>) {
  return request<EquipmentUnit>("/equipment-units/", { method: "POST", body: JSON.stringify(data) }, accessToken);
}

export function getBookings(accessToken: string) {
  return request<Booking[]>("/bookings/", {}, accessToken);
}

export function createBooking(accessToken: string, data: {
  start_date: string;
  end_date: string;
  purpose: string;
  notes: string;
  items: { equipment_model: number; quantity: number }[];
}) {
  return request<Booking>("/bookings/", { method: "POST", body: JSON.stringify(data) }, accessToken);
}

export function approveBooking(accessToken: string, id: number, unitIds: number[]) {
  return request<Booking>(`/bookings/${id}/approve/`, { method: "POST", body: JSON.stringify({ unit_ids: unitIds }) }, accessToken);
}

export function rejectBooking(accessToken: string, id: number, reason: string) {
  return request<Booking>(`/bookings/${id}/reject/`, { method: "POST", body: JSON.stringify({ reason }) }, accessToken);
}

export function cancelBooking(accessToken: string, id: number) {
  return request<Booking>(`/bookings/${id}/cancel/`, { method: "POST" }, accessToken);
}

export function getLoans(accessToken: string) {
  return request<Loan[]>("/loans/", {}, accessToken);
}

export function getLoan(accessToken: string, id: string) {
  return request<Loan>(`/loans/${id}/`, {}, accessToken);
}

export function getLoanTransfers(accessToken: string, id: string) {
  return request<LoanTransfer[]>(`/loans/${id}/transfers/`, {}, accessToken);
}

export function transferLoan(accessToken: string, id: number, data: { new_borrower_id: number; reason: string }) {
  return request<{ success: true; message: string; loan: Loan }>(`/loans/${id}/transfer/`, { method: "POST", body: JSON.stringify(data) }, accessToken);
}

export function issueBooking(accessToken: string, bookingId: number, data: { due_at: string; notes?: string; conditions?: Record<string, string> }) {
  return request<Loan>(`/loans/issue-booking/${bookingId}/`, { method: "POST", body: JSON.stringify(data) }, accessToken);
}

export function returnLoan(accessToken: string, loanId: number, data: { items: { loan_item_id: number; condition: string; status: string; notes?: string }[]; notes?: string }) {
  return request<Loan>(`/loans/${loanId}/return/`, { method: "POST", body: JSON.stringify(data) }, accessToken);
}

export function getLateFees(accessToken: string) {
  return request<LateFee[]>("/late-fees/", {}, accessToken);
}

export function logout(accessToken: string, refreshToken: string) {
  return request<{ success: true; message: string }>(
    "/auth/logout/",
    { method: "POST", body: JSON.stringify({ refresh: refreshToken }) },
    accessToken,
  );
}

export function getApiUrl() {
  return apiUrl;
}
