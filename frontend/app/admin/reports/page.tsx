"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { getUser, isLoggedIn } from "@/lib/auth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface OrderSummary {
  total_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  pending_orders: number;
  total_revenue: number;
  start_date?: string | null;
  end_date?: string | null;
  restaurant_id?: string | null;
}

interface DeliverySummary {
  total_deliveries: number;
  completed_deliveries: number;
  pending_deliveries: number;
  average_delivery_time: number | null;
}

interface PaymentSummary {
  total_transactions: number;
  total_revenue: number;
  successful_payments: number;
  failed_payments: number;
  total_refunds: number;
}

interface ReviewSummary {
  total_reviews: number;
  average_rating: number;
  total_restaurants_reviewed: number;
  five_star_reviews: number;
  one_star_reviews: number;
}

interface SystemReport {
  orders: OrderSummary;
  deliveries: DeliverySummary;
  payments: PaymentSummary;
  reviews: ReviewSummary;
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-500">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export default function AdminReportsPage() {
  const router = useRouter();
  const [report, setReport] = useState<SystemReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* ── Dedicated order report state ── */
  const [orderReport, setOrderReport] = useState<OrderSummary | null>(null);
  const [orderReportLoading, setOrderReportLoading] = useState(false);
  const [orderReportError, setOrderReportError] = useState<string | null>(null);

  /* ── Date filter state for system report ── */
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [restaurantFilter, setRestaurantFilter] = useState("");

  /* ── Date filter state for order report ── */
  const [orderDateStart, setOrderDateStart] = useState("");
  const [orderDateEnd, setOrderDateEnd] = useState("");
  const [orderRestaurantFilter, setOrderRestaurantFilter] = useState("");

  function buildParams(start: string, end: string, restId: string) {
    const params: Record<string, string> = {};
    if (start) params.date_start = start;
    if (end) params.date_end = end;
    if (restId) params.restaurant_id = restId;
    return params;
  }

  function fetchSystemReport(start = "", end = "", restId = "") {
    setLoading(true);
    setError(null);
    api
      .get("/reports/admin/system", { params: buildParams(start, end, restId) })
      .then(({ data }) => setReport(data))
      .catch((err) => setError(err.response?.data?.detail || "Failed to load reports"))
      .finally(() => setLoading(false));
  }

  function fetchOrderReport(start = "", end = "", restId = "") {
    setOrderReportLoading(true);
    setOrderReportError(null);
    api
      .get("/reports/admin/orders", { params: buildParams(start, end, restId) })
      .then(({ data }) => setOrderReport(data))
      .catch((err) => setOrderReportError(err.response?.data?.detail || "Failed to load order report"))
      .finally(() => setOrderReportLoading(false));
  }

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/login"); return; }
    const user = getUser();
    if (user?.role !== "admin") { router.push("/"); return; }

    fetchSystemReport();
    fetchOrderReport();
  }, [router]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-gray-100 rounded-lg animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-4">Admin Reports</h1>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-600 font-medium">Error loading reports</p>
            <p className="text-sm text-red-500 mt-1">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-3 text-sm text-orange-600 hover:underline"
            >
              Try again
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!report) return null;

  const { orders, deliveries, payments, reviews } = report;

  const completionRate = orders.total_orders > 0
    ? ((orders.completed_orders / orders.total_orders) * 100).toFixed(1)
    : "0";

  const paymentSuccessRate = payments.total_transactions > 0
    ? ((payments.successful_payments / payments.total_transactions) * 100).toFixed(1)
    : "0";

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Admin Reports</h1>
          <p className="text-sm text-gray-500 mt-1">Aggregated platform statistics</p>
        </div>
        <Link
          href="/admin"
          className="text-sm text-orange-600 hover:text-orange-800 hover:underline"
        >
          ← Back to Dashboard
        </Link>
      </div>

      {/* ── System Report Filters ── */}
      <Card className="mb-6">
        <CardContent className="pt-4">
          <p className="text-sm font-medium text-gray-600 mb-2">Filter System Report</p>
          <div className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="text-xs text-gray-500">Start Date</label>
              <Input type="date" value={dateStart} onChange={(e) => setDateStart(e.target.value)} className="w-40" />
            </div>
            <div>
              <label className="text-xs text-gray-500">End Date</label>
              <Input type="date" value={dateEnd} onChange={(e) => setDateEnd(e.target.value)} className="w-40" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Restaurant ID</label>
              <Input placeholder="e.g. 1001" value={restaurantFilter} onChange={(e) => setRestaurantFilter(e.target.value)} className="w-32" />
            </div>
            <Button size="sm" onClick={() => fetchSystemReport(dateStart, dateEnd, restaurantFilter)}>Apply</Button>
            <Button size="sm" variant="outline" onClick={() => { setDateStart(""); setDateEnd(""); setRestaurantFilter(""); fetchSystemReport(); }}>Reset</Button>
          </div>
        </CardContent>
      </Card>

      {/* Top-level KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Orders" value={orders.total_orders} sub={`${completionRate}% completion rate`} />
        <StatCard label="Revenue" value={`$${orders.total_revenue.toFixed(2)}`} sub="from completed orders" />
        <StatCard label="Avg Rating" value={reviews.average_rating.toFixed(1)} sub={`${reviews.total_reviews} total reviews`} />
        <StatCard label="Deliveries" value={deliveries.total_deliveries} sub={`${deliveries.completed_deliveries} completed`} />
      </div>

      <Tabs defaultValue="orders">
        <TabsList className="mb-4">
          <TabsTrigger value="orders">Orders</TabsTrigger>
          <TabsTrigger value="order-report">Order Report</TabsTrigger>
          <TabsTrigger value="deliveries">Deliveries</TabsTrigger>
          <TabsTrigger value="payments">Payments</TabsTrigger>
          <TabsTrigger value="reviews">Reviews</TabsTrigger>
        </TabsList>

        {/* Orders Tab */}
        <TabsContent value="orders">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Orders" value={orders.total_orders} />
            <StatCard label="Completed" value={orders.completed_orders} />
            <StatCard label="Pending" value={orders.pending_orders} />
            <StatCard label="Cancelled" value={orders.cancelled_orders} />
          </div>
          <Card className="mt-4">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-700">Order Breakdown</h3>
                <Badge variant="outline" className="text-green-700 border-green-300">
                  ${orders.total_revenue.toFixed(2)} revenue
                </Badge>
              </div>
              {orders.total_orders > 0 ? (
                <div className="space-y-3">
                  <ProgressRow label="Completed" count={orders.completed_orders} total={orders.total_orders} color="bg-green-500" />
                  <ProgressRow label="Pending" count={orders.pending_orders} total={orders.total_orders} color="bg-yellow-500" />
                  <ProgressRow label="Cancelled" count={orders.cancelled_orders} total={orders.total_orders} color="bg-red-500" />
                </div>
              ) : (
                <p className="text-gray-400 text-sm">No orders to display.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Order Report Tab (dedicated /reports/admin/orders endpoint) ── */}
        <TabsContent value="order-report">
          <Card className="mb-4">
            <CardContent className="pt-4">
              <p className="text-sm font-medium text-gray-600 mb-2">Filter Order Report</p>
              <div className="flex flex-wrap gap-3 items-end">
                <div>
                  <label className="text-xs text-gray-500">Start Date</label>
                  <Input type="date" value={orderDateStart} onChange={(e) => setOrderDateStart(e.target.value)} className="w-40" />
                </div>
                <div>
                  <label className="text-xs text-gray-500">End Date</label>
                  <Input type="date" value={orderDateEnd} onChange={(e) => setOrderDateEnd(e.target.value)} className="w-40" />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Restaurant ID</label>
                  <Input placeholder="e.g. 1001" value={orderRestaurantFilter} onChange={(e) => setOrderRestaurantFilter(e.target.value)} className="w-32" />
                </div>
                <Button size="sm" onClick={() => fetchOrderReport(orderDateStart, orderDateEnd, orderRestaurantFilter)}>Apply</Button>
                <Button size="sm" variant="outline" onClick={() => { setOrderDateStart(""); setOrderDateEnd(""); setOrderRestaurantFilter(""); fetchOrderReport(); }}>Reset</Button>
              </div>
            </CardContent>
          </Card>

          {orderReportLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : orderReportError ? (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="pt-6">
                <p className="text-red-600 font-medium">Error</p>
                <p className="text-sm text-red-500 mt-1">{orderReportError}</p>
              </CardContent>
            </Card>
          ) : orderReport ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="Total Orders" value={orderReport.total_orders} />
                <StatCard label="Completed" value={orderReport.completed_orders} />
                <StatCard label="Pending" value={orderReport.pending_orders} />
                <StatCard label="Cancelled" value={orderReport.cancelled_orders} />
              </div>
              <Card className="mt-4">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-700">Order Report Breakdown</h3>
                    <Badge variant="outline" className="text-green-700 border-green-300">
                      ${orderReport.total_revenue.toFixed(2)} revenue
                    </Badge>
                  </div>
                  {orderReport.total_orders > 0 ? (
                    <div className="space-y-3">
                      <ProgressRow label="Completed" count={orderReport.completed_orders} total={orderReport.total_orders} color="bg-green-500" />
                      <ProgressRow label="Pending" count={orderReport.pending_orders} total={orderReport.total_orders} color="bg-yellow-500" />
                      <ProgressRow label="Cancelled" count={orderReport.cancelled_orders} total={orderReport.total_orders} color="bg-red-500" />
                    </div>
                  ) : (
                    <p className="text-gray-400 text-sm">No orders in this range.</p>
                  )}
                  {(orderReport.start_date || orderReport.end_date || orderReport.restaurant_id) && (
                    <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t">
                      {orderReport.start_date && <Badge variant="outline" className="text-xs">From: {orderReport.start_date}</Badge>}
                      {orderReport.end_date && <Badge variant="outline" className="text-xs">To: {orderReport.end_date}</Badge>}
                      {orderReport.restaurant_id && <Badge variant="outline" className="text-xs">Restaurant: {orderReport.restaurant_id}</Badge>}
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          ) : null}
        </TabsContent>

        {/* Deliveries Tab */}
        <TabsContent value="deliveries">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <StatCard label="Total Deliveries" value={deliveries.total_deliveries} />
            <StatCard label="Completed" value={deliveries.completed_deliveries} />
            <StatCard label="Pending" value={deliveries.pending_deliveries} />
          </div>
          {deliveries.average_delivery_time !== null && (
            <Card className="mt-4">
              <CardContent className="pt-6">
                <p className="text-sm text-gray-500">Average Delivery Time</p>
                <p className="text-3xl font-bold mt-1">
                  {deliveries.average_delivery_time.toFixed(1)} <span className="text-base font-normal text-gray-400">min</span>
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Payments Tab */}
        <TabsContent value="payments">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Transactions" value={payments.total_transactions} />
            <StatCard
              label="Successful"
              value={payments.successful_payments}
              sub={`${paymentSuccessRate}% success rate`}
            />
            <StatCard label="Failed" value={payments.failed_payments} />
            <StatCard label="Total Refunds" value={`$${payments.total_refunds.toFixed(2)}`} />
          </div>
          <Card className="mt-4">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-700">Payment Revenue</h3>
                <Badge variant="outline" className="text-green-700 border-green-300">
                  ${payments.total_revenue.toFixed(2)}
                </Badge>
              </div>
              {payments.total_transactions > 0 ? (
                <div className="space-y-3 mt-4">
                  <ProgressRow label="Successful" count={payments.successful_payments} total={payments.total_transactions} color="bg-green-500" />
                  <ProgressRow label="Failed" count={payments.failed_payments} total={payments.total_transactions} color="bg-red-500" />
                </div>
              ) : (
                <p className="text-gray-400 text-sm mt-2">No transactions to display.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reviews Tab */}
        <TabsContent value="reviews">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Reviews" value={reviews.total_reviews} />
            <StatCard label="Average Rating" value={reviews.average_rating.toFixed(1)} />
            <StatCard label="5-Star Reviews" value={reviews.five_star_reviews} />
            <StatCard label="1-Star Reviews" value={reviews.one_star_reviews} />
          </div>
          <Card className="mt-4">
            <CardContent className="pt-6">
              <h3 className="font-semibold text-gray-700 mb-2">Review Distribution</h3>
              <p className="text-sm text-gray-500">
                {reviews.total_restaurants_reviewed} restaurant{reviews.total_restaurants_reviewed !== 1 ? "s" : ""} reviewed
              </p>
              {reviews.total_reviews > 0 && (
                <div className="flex items-center gap-2 mt-3">
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <span
                        key={star}
                        className={`text-lg ${star <= Math.round(reviews.average_rating) ? "text-yellow-400" : "text-gray-300"}`}
                      >
                        ★
                      </span>
                    ))}
                  </div>
                  <span className="text-sm text-gray-500">{reviews.average_rating.toFixed(1)} / 5.0</span>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ProgressRow({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="text-gray-500">{count} ({pct.toFixed(1)}%)</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
