"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { getUser, isLoggedIn } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Order {
  order_id: string;
  restaurant_id: number;
  food_item: string;
  order_value: number;
  order_status: string;
  order_time: string;
}

interface Payment {
  payment_id: string;
  status: string;
  amount: number;
}

interface PriceBreakdown {
  order_id: string;
  food_price: number;
  delivery_fee: {
    base_fee: number;
    distance_fee: number;
    method_surcharge: number;
    traffic_surcharge: number;
    weather_surcharge: number;
    total_delivery_fee: number;
  };
  subtotal: number;
  tax: number;
  total: number;
}

const STATUS_COLORS: Record<string, string> = {
  Placed: "bg-blue-100 text-blue-700",
  Paid: "bg-indigo-100 text-indigo-700",
  Preparing: "bg-yellow-100 text-yellow-700",
  Delivered: "bg-green-100 text-green-700",
  Cancelled: "bg-red-100 text-red-700",
};

const PAYMENT_COLORS: Record<string, string> = {
  Success: "bg-green-100 text-green-700",
  Pending: "bg-yellow-100 text-yellow-700",
  Failed: "bg-red-100 text-red-700",
  Refunded: "bg-purple-100 text-purple-700",
};

const PAYMENT_LABELS: Record<string, string> = {
  Success: "Paid",
  Pending: "Payment pending",
  Failed: "Payment failed",
  Refunded: "Refunded",
};

export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [payments, setPayments] = useState<Record<string, Payment>>({});
  const [breakdowns, setBreakdowns] = useState<Record<string, PriceBreakdown>>({});
  const [expandedBreakdown, setExpandedBreakdown] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/login"); return; }
    const user = getUser();
    const endpoint = user?.role === "admin" ? "/orders/" : `/search/orders?customer_id=${user?.id}&page_size=100`;
    api.get(endpoint)
      .then(({ data }) => {
        const raw: Order[] = data.data ?? data;
        // Show newest orders first (reverse insertion order)
        const orderList = [...raw].reverse();
        setOrders(orderList);
        orderList.forEach((o) => {
          // Fetch full order details to get order_time for customer search results
          if (!o.order_time || !o.food_item) {
            api.get(`/orders/${o.order_id}`)
              .then(({ data: full }) => {
                setOrders((prev) => prev.map((x) =>
                  x.order_id === o.order_id
                    ? { ...x, order_time: full.order_time ?? x.order_time, food_item: full.food_item ?? x.food_item }
                    : x
                ));
              })
              .catch(() => {});
          }
          // Fetch payment status for each order
          api.get(`/payments/order/${o.order_id}`)
            .then(({ data: p }) => {
              if (p) setPayments((prev) => ({ ...prev, [o.order_id]: p }));
            })
            .catch(() => {});
        });
      })
      .finally(() => setLoading(false));
  }, [router]);

  async function cancelOrder(id: string) {
    // Auth via JWT token in header — no customer_id param needed
    await api.delete(`/orders/${id}/cancel`);
    setOrders((prev) =>
      prev.map((o) => o.order_id === id ? { ...o, order_status: "Cancelled" } : o)
    );
    // Refresh payment to show Refunded status if applicable (Feat11)
    api.get(`/payments/order/${id}`)
      .then(({ data: p }) => {
        if (p) setPayments((prev) => ({ ...prev, [id]: p }));
      })
      .catch(() => {});
    window.dispatchEvent(new Event("notifications-refresh"));
  }

  async function toggleBreakdown(orderId: string) {
    if (expandedBreakdown === orderId) {
      setExpandedBreakdown(null);
      return;
    }
    setExpandedBreakdown(orderId);
    if (!breakdowns[orderId]) {
      try {
        const { data } = await api.get(`/pricing/orders/${orderId}/breakdown`);
        setBreakdowns((prev) => ({ ...prev, [orderId]: data }));
      } catch {
        // breakdown not available for this order
      }
    }
  }

  async function payOrder(order: Order) {
    setPaying(order.order_id);
    try {
      const { data: p } = await api.post("/payments/", { order_id: order.order_id });
      setPayments((prev) => ({ ...prev, [order.order_id]: p }));
      window.dispatchEvent(new Event("notifications-refresh"));
    } catch {
      // payment may already exist — refresh
      api.get(`/payments/order/${order.order_id}`)
        .then(({ data: p }) => {
          if (p) setPayments((prev) => ({ ...prev, [order.order_id]: p }));
        })
        .catch(() => {});
    } finally {
      setPaying(null);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">My Orders</h1>
      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : orders.length === 0 ? (
        <p className="text-gray-400">No orders yet.</p>
      ) : (
        <div className="space-y-4">
          {orders.map((o) => {
            const payment = payments[o.order_id];
            const breakdown = breakdowns[o.order_id];
            const isExpanded = expandedBreakdown === o.order_id;
            return (
              <Card key={o.order_id}>
                <CardHeader className="pb-2 flex flex-row items-center justify-between">
                  <CardTitle className="text-sm font-medium text-gray-500">
                    #{o.order_id.slice(0, 8)}
                  </CardTitle>
                  <div className="flex items-center gap-1.5">
                    {payment && (
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${PAYMENT_COLORS[payment.status] ?? "bg-gray-100 text-gray-600"}`}>
                        {PAYMENT_LABELS[payment.status] ?? payment.status}
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
                  {o.order_time && !isNaN(new Date(o.order_time).getTime()) && (
                    <p className="text-gray-400 text-xs">{new Date(o.order_time).toLocaleString()}</p>
                  )}

                  <div className="flex flex-wrap gap-2 mt-2">
                    {!payment && o.order_status !== "Cancelled" && (
                      <Button
                        size="sm"
                        className="bg-orange-500 hover:bg-orange-600 text-white"
                        disabled={paying === o.order_id}
                        onClick={() => payOrder(o)}
                      >
                        {paying === o.order_id ? "Processing…" : "Pay now"}
                      </Button>
                    )}
                    {(o.order_status === "Placed" || o.order_status === "Paid") && (
                      <Button size="sm" variant="destructive" onClick={() => cancelOrder(o.order_id)}>
                        Cancel
                      </Button>
                    )}
                    {o.order_status !== "Cancelled" && (
                      <Button size="sm" variant="outline" onClick={() => toggleBreakdown(o.order_id)}>
                        {isExpanded ? "Hide breakdown" : "Price breakdown"}
                      </Button>
                    )}
                  </div>

                  {/* Price Breakdown Panel — Feat6 */}
                  {isExpanded && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-md text-xs space-y-1 border">
                      {breakdown ? (
                        <>
                          <p className="font-semibold text-gray-700 mb-2">Price Breakdown</p>
                          <div className="flex justify-between"><span className="text-gray-500">Food price</span><span>${breakdown.food_price?.toFixed(2)}</span></div>
                          <div className="flex justify-between"><span className="text-gray-500">Base delivery fee</span><span>${breakdown.delivery_fee?.base_fee?.toFixed(2)}</span></div>
                          <div className="flex justify-between"><span className="text-gray-500">Distance fee</span><span>${breakdown.delivery_fee?.distance_fee?.toFixed(2)}</span></div>
                          <div className="flex justify-between"><span className="text-gray-500">Weather surcharge</span><span>${breakdown.delivery_fee?.weather_surcharge?.toFixed(2)}</span></div>
                          <div className="flex justify-between"><span className="text-gray-500">Traffic surcharge</span><span>${breakdown.delivery_fee?.traffic_surcharge?.toFixed(2)}</span></div>
                          <div className="flex justify-between"><span className="text-gray-500">Subtotal</span><span>${breakdown.subtotal?.toFixed(2)}</span></div>
                          <div className="flex justify-between"><span className="text-gray-500">Tax</span><span>${breakdown.tax?.toFixed(2)}</span></div>
                          <div className="flex justify-between font-semibold border-t pt-1 mt-1"><span>Total</span><span>${breakdown.total?.toFixed(2)}</span></div>
                        </>
                      ) : (
                        <p className="text-gray-400">Loading breakdown…</p>
                      )}
                    </div>
                  )}

                  {/* Refund notice — Feat11 */}
                  {payment?.status === "Refunded" && (
                    <p className="text-xs text-purple-600 font-medium mt-1">
                      Refund of ${payment.amount?.toFixed(2)} processed after cancellation.
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
