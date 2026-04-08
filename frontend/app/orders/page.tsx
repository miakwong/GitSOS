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

const STATUS_COLORS: Record<string, string> = {
  Placed: "bg-blue-100 text-blue-700",
  Preparing: "bg-yellow-100 text-yellow-700",
  Delivered: "bg-green-100 text-green-700",
  Cancelled: "bg-red-100 text-red-700",
};

const PAYMENT_COLORS: Record<string, string> = {
  pending: "text-yellow-600",
  completed: "text-green-600",
  failed: "text-red-600",
};

export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [payments, setPayments] = useState<Record<string, Payment>>({});
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/login"); return; }
    const user = getUser();
    const endpoint = user?.role === "admin" ? "/orders/" : `/search/orders?customer_id=${user?.id}`;
    api.get(endpoint)
      .then(({ data }) => {
        const orderList: Order[] = data.data ?? data;
        setOrders(orderList);
        // Fetch payment status for each order
        orderList.forEach((o) => {
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
    const user = getUser();
    await api.delete(`/orders/${id}/cancel`, { params: { customer_id: user?.id } });
    setOrders((prev) =>
      prev.map((o) => o.order_id === id ? { ...o, order_status: "Cancelled" } : o)
    );
    window.dispatchEvent(new Event("notifications-refresh"));
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
                  <p className="text-gray-400 text-xs">{new Date(o.order_time).toLocaleString()}</p>

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

                  {o.order_status === "Placed" && (
                    <Button
                      size="sm"
                      variant="destructive"
                      className="mt-2 ml-2"
                      onClick={() => cancelOrder(o.order_id)}
                    >
                      Cancel
                    </Button>
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
