"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { getUser, isLoggedIn } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Order {
  order_id: string;
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

interface Payment {
  payment_id: string;
  status: string;
  amount: number;
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
  Placed: "bg-blue-100 text-blue-700",
  Paid: "bg-indigo-100 text-indigo-700",
  Preparing: "bg-yellow-100 text-yellow-700",
  Delivered: "bg-green-100 text-green-700",
  Cancelled: "bg-red-100 text-red-700",
};

const PAYMENT_COLORS: Record<string, string> = {
  pending: "text-yellow-600",
  completed: "text-green-600",
  failed: "text-red-600",
};

const DELIVERY_METHODS = ["Walk", "Bike", "Car"];
const TRAFFIC_CONDITIONS = ["Low", "Medium", "High"];
const WEATHER_CONDITIONS = ["Sunny", "Rainy", "Snowy"];

export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [payments, setPayments] = useState<Record<string, Payment>>({});
  const [deliveryInfos, setDeliveryInfos] = useState<Record<string, DeliveryInfo>>({});
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState<string | null>(null);
  const [expandedDelivery, setExpandedDelivery] = useState<string | null>(null);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [editForm, setEditForm] = useState({
    food_item: "",
    order_value: 0,
    delivery_distance: 3.0,
    delivery_method: "Bike",
    traffic_condition: "Low",
    weather_condition: "Sunny",
  });
  const [editError, setEditError] = useState("");
  const [saving, setSaving] = useState(false);
  const [savingFavourite, setSavingFavourite] = useState<string | null>(null);
  const [savedFavourites, setSavedFavourites] = useState<Set<string>>(new Set());
  const [favouriteMessage, setFavouriteMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/login"); return; }
    const user = getUser();
    const endpoint = user?.role === "admin" ? "/orders/" : `/search/orders?customer_id=${user?.id}`;
    api.get(endpoint)
      .then(({ data }) => {
        const orderList: Order[] = data.data ?? data;
        setOrders(orderList);
        orderList.forEach((o) => {
          api.get(`/payments/order/${o.order_id}`)
            .then(({ data: p }) => {
              if (p) setPayments((prev) => ({ ...prev, [o.order_id]: p }));
            })
            .catch(() => {});
        });
      })
      .finally(() => setLoading(false));

    // Load existing favourites for customers
    if (user?.role === "customer") {
      api.get("/favourites/")
        .then(({ data: favs }) => {
          const favOrderIds = new Set<string>(favs.map((f: { order_id: string }) => f.order_id));
          setSavedFavourites(favOrderIds);
        })
        .catch(() => {});
    }
  }, [router]);

  async function fetchDeliveryInfo(orderId: string) {
    if (expandedDelivery === orderId) {
      setExpandedDelivery(null);
      return;
    }
    try {
      const { data } = await api.get<DeliveryInfo>(`/delivery/${orderId}`);
      setDeliveryInfos((prev) => ({ ...prev, [orderId]: data }));
      setExpandedDelivery(orderId);
    } catch {
      setExpandedDelivery(null);
    }
  }

  async function cancelOrder(id: string) {
    const user = getUser();
    try {
      await api.delete(`/orders/${id}/cancel`, { params: { customer_id: user?.id } });
      setOrders((prev) =>
        prev.map((o) => o.order_id === id ? { ...o, order_status: "Cancelled" } : o)
      );
      window.dispatchEvent(new Event("notifications-refresh"));
    } catch {
      // silently fail
    }
  }

  async function payOrder(order: Order) {
    setPaying(order.order_id);
    try {
      const { data: p } = await api.post("/payments/", { order_id: order.order_id });
      setPayments((prev) => ({ ...prev, [order.order_id]: p }));
      window.dispatchEvent(new Event("notifications-refresh"));
    } catch {
      api.get(`/payments/order/${order.order_id}`)
        .then(({ data: p }) => {
          if (p) setPayments((prev) => ({ ...prev, [order.order_id]: p }));
        })
        .catch(() => {});
    } finally {
      setPaying(null);
    }
  }

  function startEdit(order: Order) {
    setEditingOrder(order);
    setEditForm({
      food_item: order.food_item,
      order_value: order.order_value,
      delivery_distance: order.delivery_distance,
      delivery_method: order.delivery_method,
      traffic_condition: order.traffic_condition,
      weather_condition: order.weather_condition,
    });
    setEditError("");
  }

  async function saveEdit() {
    if (!editingOrder) return;
    setSaving(true);
    setEditError("");
    try {
      const { data: updated } = await api.put(`/orders/${editingOrder.order_id}`, editForm);
      setOrders((prev) =>
        prev.map((o) => o.order_id === editingOrder.order_id ? { ...o, ...updated } : o)
      );
      setEditingOrder(null);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setEditError(typeof msg === "string" ? msg : "Failed to update order.");
    } finally {
      setSaving(false);
    }
  }

  async function saveToFavourites(orderId: string) {
    setSavingFavourite(orderId);
    setFavouriteMessage(null);
    try {
      await api.post("/favourites/", { order_id: orderId });
      setSavedFavourites((prev) => new Set([...prev, orderId]));
      setFavouriteMessage({ type: "success", text: "Order saved to favourites!" });
      setTimeout(() => setFavouriteMessage(null), 3000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFavouriteMessage({
        type: "error",
        text: typeof msg === "string" ? msg : "Failed to save favourite.",
      });
      setTimeout(() => setFavouriteMessage(null), 3000);
    } finally {
      setSavingFavourite(null);
    }
  }

  const user = isLoggedIn() ? getUser() : null;
  const isCustomer = user?.role === "customer";

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">My Orders</h1>

      {/* Favourite Message */}
      {favouriteMessage && (
        <div
          className={`mb-4 p-3 rounded-lg text-sm ${
            favouriteMessage.type === "success"
              ? "bg-green-50 border border-green-200 text-green-700"
              : "bg-red-50 border border-red-200 text-red-700"
          }`}
        >
          {favouriteMessage.text}
        </div>
      )}

      {/* Edit Order Modal */}
      {editingOrder && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-bold mb-4">Edit Order</h2>
            <p className="text-xs text-gray-400 mb-4">#{editingOrder.order_id.slice(0, 8)} — Only orders in &quot;Placed&quot; status can be edited.</p>

            {editError && (
              <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {editError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Food Item</label>
                <Input
                  value={editForm.food_item}
                  onChange={(e) => setEditForm((f) => ({ ...f, food_item: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Order Value ($)</label>
                <Input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={editForm.order_value}
                  onChange={(e) => setEditForm((f) => ({ ...f, order_value: parseFloat(e.target.value) || 0 }))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Delivery Distance (km, 2.0–15.0)</label>
                <Input
                  type="number"
                  step="0.1"
                  min="2.0"
                  max="15.0"
                  value={editForm.delivery_distance}
                  onChange={(e) => setEditForm((f) => ({ ...f, delivery_distance: parseFloat(e.target.value) || 2.0 }))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Delivery Method</label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  value={editForm.delivery_method}
                  onChange={(e) => setEditForm((f) => ({ ...f, delivery_method: e.target.value }))}
                >
                  {DELIVERY_METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Traffic</label>
                  <select
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    value={editForm.traffic_condition}
                    onChange={(e) => setEditForm((f) => ({ ...f, traffic_condition: e.target.value }))}
                  >
                    {TRAFFIC_CONDITIONS.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Weather</label>
                  <select
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    value={editForm.weather_condition}
                    onChange={(e) => setEditForm((f) => ({ ...f, weather_condition: e.target.value }))}
                  >
                    {WEATHER_CONDITIONS.map((w) => <option key={w} value={w}>{w}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" size="sm" onClick={() => setEditingOrder(null)}>
                Cancel
              </Button>
              <Button
                size="sm"
                className="bg-orange-500 hover:bg-orange-600 text-white"
                disabled={saving}
                onClick={saveEdit}
              >
                {saving ? "Saving…" : "Save Changes"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : orders.length === 0 ? (
        <p className="text-gray-400">No orders yet.</p>
      ) : (
        <div className="space-y-4">
          {orders.map((o) => {
            const payment = payments[o.order_id];
            const canCancel = o.order_status === "Placed" || o.order_status === "Paid";
            const canEdit = o.order_status === "Placed" && isCustomer;
            const delivery = deliveryInfos[o.order_id];
            const isExpanded = expandedDelivery === o.order_id;
            return (
              <Card key={o.order_id}>
                <CardHeader className="pb-2 flex flex-row items-center justify-between">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    #{o.order_id.slice(0, 8)}
                  </CardTitle>
                  <div className="flex items-center gap-1.5">
                    {payment && (
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${payment.status === "completed" ? "bg-green-100 text-green-700" : payment.status === "failed" ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"}`}>
                        {payment.status === "completed" ? "Paid" : payment.status === "failed" ? "Payment failed" : "Payment pending"}
                      </span>
                    )}
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_COLORS[o.order_status] ?? "bg-gray-100 text-gray-600"}`}>
                      {o.order_status}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="text-sm space-y-1">
                  <p className="font-medium">{o.food_item}</p>
                  <p className="text-gray-500">Restaurant #{o.restaurant_id} · ${o.order_value?.toFixed(2)}</p>
                  <div className="flex gap-2 text-xs text-gray-400">
                    <span>{o.delivery_method}</span>
                    <span>·</span>
                    <span>{o.delivery_distance} km</span>
                    <span>·</span>
                    <span>{o.traffic_condition} traffic</span>
                    <span>·</span>
                    <span>{o.weather_condition}</span>
                  </div>
                  <p className="text-gray-400 text-xs">{new Date(o.order_time).toLocaleString()}</p>

                  {/* Delivery Details Toggle */}
                  <button
                    className="text-xs text-orange-500 hover:underline mt-1"
                    onClick={() => fetchDeliveryInfo(o.order_id)}
                  >
                    {isExpanded ? "Hide delivery details" : "View delivery details"}
                  </button>

                  {isExpanded && delivery && (
                    <div className="mt-2 p-3 bg-gray-50 border rounded text-xs space-y-1">
                      <p className="font-medium text-gray-700">Delivery Details</p>
                      <p>Distance: {delivery.delivery_distance} km</p>
                      {delivery.delivery_method && <p>Method: {delivery.delivery_method}</p>}
                      {delivery.traffic_condition && <p>Traffic: {delivery.traffic_condition}</p>}
                      {delivery.weather_condition && <p>Weather: {delivery.weather_condition}</p>}
                      {delivery.delivery_time != null && (
                        <p>Delivery Time: {delivery.delivery_time.toFixed(1)} min</p>
                      )}
                      {delivery.delivery_delay != null && (
                        <p className={delivery.delivery_delay > 0 ? "text-red-600" : "text-green-600"}>
                          Delay: {delivery.delivery_delay > 0 ? "+" : ""}{delivery.delivery_delay.toFixed(1)} min
                        </p>
                      )}
                      <p className="text-gray-400">
                        {delivery.is_historical ? "Historical (Kaggle)" : "System order"}
                      </p>
                    </div>
                  )}

                  {payment ? (
                    <p className={`text-xs font-medium mt-1 ${PAYMENT_COLORS[payment.status] ?? "text-gray-500"}`}>
                      Payment: {payment.status} · ${payment.amount?.toFixed(2)}
                    </p>
                  ) : o.order_status !== "Cancelled" && (
                    <Button
                      size="sm"
                      className="mt-2 bg-orange-500 hover:bg-orange-600 text-white"
                      disabled={paying === o.order_id}
                      onClick={() => payOrder(o)}
                    >
                      {paying === o.order_id ? "Processing…" : "Pay now"}
                    </Button>
                  )}

                  <div className="flex gap-2 mt-2">
                    {canEdit && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => startEdit(o)}
                      >
                        Edit
                      </Button>
                    )}
                    {canCancel && isCustomer && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => cancelOrder(o.order_id)}
                      >
                        Cancel
                      </Button>
                    )}
                    {isCustomer && o.order_status !== "Cancelled" && (
                      savedFavourites.has(o.order_id) ? (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled
                          className="text-orange-500 border-orange-300"
                        >
                          ❤️ Saved
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={savingFavourite === o.order_id}
                          onClick={() => saveToFavourites(o.order_id)}
                        >
                          {savingFavourite === o.order_id ? "Saving…" : "♡ Save"}
                        </Button>
                      )
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
