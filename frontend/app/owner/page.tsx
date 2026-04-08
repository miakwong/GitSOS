"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { isLoggedIn, getUser } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Order {
  order_id: string;
  customer_id: string;
  restaurant_id: number;
  food_item: string;
  order_value: number;
  order_status: string;
  order_time: string;
  delivery_distance: number;
  delivery_method: string;
  traffic_condition: string;
  weather_condition: string;
}

interface DeliveryInfo {
  order_id: string;
  delivery_distance: number;
  delivery_method?: string;
  traffic_condition?: string;
  weather_condition?: string;
  delivery_time?: number;
  delivery_delay?: number;
  is_historical: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  Placed: "bg-blue-100 text-blue-800",
  Paid: "bg-indigo-100 text-indigo-800",
  Preparing: "bg-yellow-100 text-yellow-800",
  Delivered: "bg-green-100 text-green-800",
  Cancelled: "bg-red-100 text-red-800",
};

const OWNER_NEXT_STATUS: Record<string, string | null> = {
  Placed: "Paid",
  Paid: "Preparing",
  Preparing: "Delivered",
  Delivered: null,
  Cancelled: null,
};

export default function OwnerDashboardPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [cancelledOrders, setCancelledOrders] = useState<Order[]>([]);
  const [deliveries, setDeliveries] = useState<DeliveryInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [advancing, setAdvancing] = useState<string | null>(null);

  // Delivery outcome recording
  const [outcomeOrderId, setOutcomeOrderId] = useState<string | null>(null);
  const [outcomeForm, setOutcomeForm] = useState({ actual_delivery_time: "", delivery_delay: "" });
  const [outcomeError, setOutcomeError] = useState("");
  const [savingOutcome, setSavingOutcome] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/login"); return; }
    const user = getUser();
    if (user?.role !== "owner") { router.push("/"); return; }

    Promise.all([
      api.get("/orders/owner/restaurant")
        .then(({ data }) => setOrders(data))
        .catch(() => {}),
      api.get("/orders/owner/cancelled")
        .then(({ data }) => setCancelledOrders(data))
        .catch(() => {}),
      api.get("/delivery")
        .then(({ data }) => setDeliveries(data))
        .catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [router]);

  async function advanceStatus(orderId: string, newStatus: string) {
    setAdvancing(orderId);
    try {
      await api.patch(`/orders/owner/restaurant/${orderId}/status`, {
        order_status: newStatus,
      });
      setOrders((prev) =>
        prev.map((o) =>
          o.order_id === orderId ? { ...o, order_status: newStatus } : o
        )
      );
    } catch {
      // silently fail
    } finally {
      setAdvancing(null);
    }
  }

  function startOutcome(orderId: string) {
    setOutcomeOrderId(orderId);
    setOutcomeForm({ actual_delivery_time: "", delivery_delay: "" });
    setOutcomeError("");
  }

  async function saveOutcome() {
    if (!outcomeOrderId) return;
    const time = parseFloat(outcomeForm.actual_delivery_time);
    const delay = parseFloat(outcomeForm.delivery_delay);
    if (isNaN(time) || time <= 0) {
      setOutcomeError("Delivery time must be a positive number.");
      return;
    }
    if (isNaN(delay)) {
      setOutcomeError("Delay must be a number.");
      return;
    }
    setSavingOutcome(true);
    setOutcomeError("");
    try {
      await api.patch(`/delivery/${outcomeOrderId}/outcome`, {
        actual_delivery_time: time,
        delivery_delay: delay,
      });
      // Update the delivery list with the new outcome
      setDeliveries((prev) =>
        prev.map((d) =>
          d.order_id === outcomeOrderId
            ? { ...d, delivery_time: time, delivery_delay: delay }
            : d
        )
      );
      setOutcomeOrderId(null);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setOutcomeError(typeof msg === "string" ? msg : "Failed to record outcome.");
    } finally {
      setSavingOutcome(false);
    }
  }

  const activeOrders = orders.filter(
    (o) => o.order_status !== "Cancelled" && o.order_status !== "Delivered"
  );
  const deliveredOrders = orders.filter((o) => o.order_status === "Delivered");

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded" />
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Owner Dashboard</h1>

      {/* Outcome Recording Modal */}
      {outcomeOrderId && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-bold mb-2">Record Delivery Outcome</h2>
            <p className="text-xs text-gray-400 mb-4">Order #{outcomeOrderId.slice(0, 8)}</p>

            {outcomeError && (
              <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {outcomeError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Actual Delivery Time (minutes)
                </label>
                <Input
                  type="number"
                  step="0.1"
                  min="0.1"
                  placeholder="e.g. 25.5"
                  value={outcomeForm.actual_delivery_time}
                  onChange={(e) =>
                    setOutcomeForm((f) => ({ ...f, actual_delivery_time: e.target.value }))
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Delivery Delay (minutes, 0 = on time)
                </label>
                <Input
                  type="number"
                  step="0.1"
                  placeholder="e.g. 3.0 or -2.0"
                  value={outcomeForm.delivery_delay}
                  onChange={(e) =>
                    setOutcomeForm((f) => ({ ...f, delivery_delay: e.target.value }))
                  }
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" size="sm" onClick={() => setOutcomeOrderId(null)}>
                Cancel
              </Button>
              <Button
                size="sm"
                className="bg-orange-500 hover:bg-orange-600 text-white"
                disabled={savingOutcome}
                onClick={saveOutcome}
              >
                {savingOutcome ? "Saving…" : "Save Outcome"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Total Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{orders.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Active Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-600">{activeOrders.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Delivered</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-600">{deliveredOrders.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Cancelled</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-red-600">{cancelledOrders.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="active">
        <TabsList className="mb-4">
          <TabsTrigger value="active">Active Orders</TabsTrigger>
          <TabsTrigger value="all">All Orders</TabsTrigger>
          <TabsTrigger value="cancelled">Cancelled</TabsTrigger>
          <TabsTrigger value="deliveries">Deliveries</TabsTrigger>
        </TabsList>

        {/* Active Orders Tab */}
        <TabsContent value="active">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Food Item</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Delivery</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {activeOrders.map((o) => (
                    <TableRow key={o.order_id}>
                      <TableCell className="text-xs font-mono text-gray-400">
                        {o.order_id.slice(0, 8)}
                      </TableCell>
                      <TableCell className="text-xs font-mono text-gray-400">
                        {o.customer_id.slice(0, 8)}
                      </TableCell>
                      <TableCell className="font-medium">{o.food_item}</TableCell>
                      <TableCell>${o.order_value?.toFixed(2)}</TableCell>
                      <TableCell className="text-xs text-gray-500">
                        {o.delivery_method} · {o.delivery_distance} km
                      </TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            STATUS_COLORS[o.order_status] ?? "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {o.order_status}
                        </span>
                      </TableCell>
                      <TableCell>
                        {OWNER_NEXT_STATUS[o.order_status] && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={advancing === o.order_id}
                            onClick={() =>
                              advanceStatus(o.order_id, OWNER_NEXT_STATUS[o.order_status]!)
                            }
                          >
                            {advancing === o.order_id
                              ? "Updating…"
                              : `→ ${OWNER_NEXT_STATUS[o.order_status]}`}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {activeOrders.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-gray-400">
                        No active orders.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* All Orders Tab */}
        <TabsContent value="all">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Food Item</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Delivery</TableHead>
                    <TableHead>Conditions</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((o) => (
                    <TableRow key={o.order_id}>
                      <TableCell className="text-xs font-mono text-gray-400">
                        {o.order_id.slice(0, 8)}
                      </TableCell>
                      <TableCell className="text-xs font-mono text-gray-400">
                        {o.customer_id.slice(0, 8)}
                      </TableCell>
                      <TableCell className="font-medium">{o.food_item}</TableCell>
                      <TableCell>${o.order_value?.toFixed(2)}</TableCell>
                      <TableCell className="text-xs text-gray-500">
                        {o.delivery_method} · {o.delivery_distance} km
                      </TableCell>
                      <TableCell className="text-xs text-gray-500">
                        {o.traffic_condition} · {o.weather_condition}
                      </TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            STATUS_COLORS[o.order_status] ?? "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {o.order_status}
                        </span>
                      </TableCell>
                      <TableCell className="text-xs text-gray-400">
                        {new Date(o.order_time).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                  {orders.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center text-gray-400">
                        No orders found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cancelled Orders Tab */}
        <TabsContent value="cancelled">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-700">Cancelled Orders</h3>
                <Badge variant="outline" className="text-red-600 border-red-300">
                  {cancelledOrders.length} cancelled
                </Badge>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Food Item</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cancelledOrders.map((o) => (
                    <TableRow key={o.order_id}>
                      <TableCell className="text-xs font-mono text-gray-400">
                        {o.order_id.slice(0, 8)}
                      </TableCell>
                      <TableCell className="text-xs font-mono text-gray-400">
                        {o.customer_id.slice(0, 8)}
                      </TableCell>
                      <TableCell>{o.food_item}</TableCell>
                      <TableCell>${o.order_value?.toFixed(2)}</TableCell>
                      <TableCell className="text-xs text-gray-400">
                        {new Date(o.order_time).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                  {cancelledOrders.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-gray-400">
                        No cancelled orders.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Deliveries Tab */}
        <TabsContent value="deliveries">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Distance</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Traffic</TableHead>
                    <TableHead>Weather</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Delay</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {deliveries.map((d) => {
                    const order = orders.find((o) => o.order_id === d.order_id);
                    const isDelivered = order?.order_status === "Delivered";
                    const hasOutcome = d.delivery_time != null;
                    return (
                      <TableRow key={d.order_id}>
                        <TableCell className="text-xs font-mono text-gray-400">
                          {d.order_id.length > 8 ? d.order_id.slice(0, 8) : d.order_id}
                        </TableCell>
                        <TableCell>{d.delivery_distance.toFixed(1)} km</TableCell>
                        <TableCell>{d.delivery_method ?? "—"}</TableCell>
                        <TableCell>{d.traffic_condition ?? "—"}</TableCell>
                        <TableCell>{d.weather_condition ?? "—"}</TableCell>
                        <TableCell>
                          {d.delivery_time != null ? `${d.delivery_time.toFixed(0)} min` : "—"}
                        </TableCell>
                        <TableCell>
                          {d.delivery_delay != null ? (
                            <span className={d.delivery_delay > 0 ? "text-red-600" : "text-green-600"}>
                              {d.delivery_delay > 0 ? "+" : ""}{d.delivery_delay.toFixed(0)} min
                            </span>
                          ) : "—"}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {d.is_historical ? "Historical" : "System"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {!d.is_historical && isDelivered && !hasOutcome && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => startOutcome(d.order_id)}
                            >
                              Record Outcome
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  {deliveries.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center text-gray-400">
                        No delivery records found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
