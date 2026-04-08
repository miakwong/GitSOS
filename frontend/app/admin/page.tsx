"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { getUser, isLoggedIn } from "@/lib/auth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

/* ── Type definitions ── */
interface User {
  id: string;
  email: string;
  role: string;
  restaurant_id?: number;
}
interface Order {
  order_id: string;
  customer_id: string;
  restaurant_id: number;
  food_item: string;
  order_status: string;
  order_value: number;
}
interface Payment {
  payment_id: string;
  order_id: string;
  customer_id: string;
  status: string;
  amount: number;
}
interface Review {
  review_id: string;
  order_id: string;
  customer_id: string;
  restaurant_id: number;
  rating: number;
  tags: string[];
  created_at: string;
}
interface Restaurant {
  restaurant_id: string;
  name: string;
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
interface DeliveryAnalytics {
  traffic_condition?: string;
  weather_condition?: string;
  total_orders: number;
  avg_delivery_time?: number;
  avg_delivery_delay?: number;
}

/* ── Status helpers ── */
const STATUS_COLORS: Record<string, string> = {
  Placed: "bg-blue-100 text-blue-800",
  Preparing: "bg-yellow-100 text-yellow-800",
  Delivered: "bg-green-100 text-green-800",
  Cancelled: "bg-red-100 text-red-800",
};

const PAYMENT_COLORS: Record<string, string> = {
  Success: "bg-green-100 text-green-800",
  Pending: "bg-yellow-100 text-yellow-800",
  Failed: "bg-red-100 text-red-800",
  Refunded: "bg-purple-100 text-purple-800",
};

const NEXT_STATUS: Record<string, string | null> = {
  Placed: "Preparing",
  Preparing: "Delivered",
  Delivered: null,
  Cancelled: null,
};

function Stars({ rating }: { rating: number }) {
  return (
    <span className="text-orange-400">
      {"★".repeat(rating)}
      {"☆".repeat(5 - rating)}
    </span>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<User[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [deliveries, setDeliveries] = useState<DeliveryInfo[]>([]);
  const [deliveryAnalytics, setDeliveryAnalytics] = useState<DeliveryAnalytics | null>(null);
  const [selectedRestaurant, setSelectedRestaurant] = useState<string | null>(null);
  const [menuItems, setMenuItems] = useState<{ food_item: string; median_price: number }[]>([]);
  const [menuLoading, setMenuLoading] = useState(false);
  const [cancelledOrders, setCancelledOrders] = useState<Order[]>([]);
  const [refundedPayments, setRefundedPayments] = useState<Payment[]>([]);

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/login"); return; }
    const user = getUser();
    if (user?.role !== "admin") { router.push("/"); return; }

    Promise.all([
      api.get("/auth/admin/users").then(({ data }) => setUsers(data)).catch(() => {}),
      api.get("/admin/inspect/orders").then(({ data }) => setOrders(data)).catch(() => {}),
      api.get("/admin/inspect/payments").then(({ data }) => setPayments(data)).catch(() => {}),
      api.get("/admin/inspect/reviews").then(({ data }) => setReviews(data)).catch(() => {}),
      api.get("/admin/restaurants").then(({ data }) => setRestaurants(data)).catch(() => {}),
      api.get("/admin/inspect/deliveries").then(({ data }) => setDeliveries(data)).catch(() => {}),
      api.get("/delivery/analytics").then(({ data }) => setDeliveryAnalytics(data)).catch(() => {}),
      api.get("/orders/admin/cancelled").then(({ data }) => setCancelledOrders(data)).catch(() => {}),
      api.get("/payments/admin/refunds").then(({ data }) => setRefundedPayments(data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [router]);

  async function advanceStatus(orderId: string, status: string) {
    await api.patch(`/orders/admin/${orderId}/status`, { order_status: status });
    setOrders((prev) =>
      prev.map((o) => (o.order_id === orderId ? { ...o, order_status: status } : o))
    );
  }

  async function viewMenu(restaurantId: string) {
    if (selectedRestaurant === restaurantId) {
      setSelectedRestaurant(null);
      setMenuItems([]);
      return;
    }
    setSelectedRestaurant(restaurantId);
    setMenuLoading(true);
    try {
      const { data } = await api.get(`/admin/restaurants/${restaurantId}/menu`);
      setMenuItems(data);
    } catch {
      setMenuItems([]);
    } finally {
      setMenuLoading(false);
    }
  }

  /* ── Computed stats ── */
  const totalRevenue = payments
    .filter((p) => p.status === "Success")
    .reduce((sum, p) => sum + (p.amount ?? 0), 0);
  const avgRating =
    reviews.length > 0
      ? (reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1)
      : "—";

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[...Array(5)].map((_, i) => (
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
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <Link href="/admin/reports">
          <Button variant="outline" size="sm">
            View Detailed Reports
          </Button>
        </Link>
      </div>

      {/* ── Summary Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Users</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{users.length}</p>
            <p className="text-xs text-gray-400 mt-1">
              {users.filter((u) => u.role === "customer").length} customers,{" "}
              {users.filter((u) => u.role === "owner").length} owners
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{orders.length}</p>
            <p className="text-xs text-gray-400 mt-1">
              {orders.filter((o) => o.order_status === "Delivered").length} delivered
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">${totalRevenue.toFixed(2)}</p>
            <p className="text-xs text-gray-400 mt-1">{payments.length} payments</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Restaurants</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{restaurants.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-500">Reviews</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{reviews.length}</p>
            <p className="text-xs text-gray-400 mt-1">Avg: {avgRating} / 5</p>
          </CardContent>
        </Card>
      </div>

      {/* ── Tabs ── */}
      <Tabs defaultValue="users">
        <TabsList className="mb-4 flex-wrap">
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="restaurants">Restaurants</TabsTrigger>
          <TabsTrigger value="orders">Orders</TabsTrigger>
          <TabsTrigger value="cancelled">Cancelled Orders</TabsTrigger>
          <TabsTrigger value="refunds">Refunded Payments</TabsTrigger>
          <TabsTrigger value="payments">Payments</TabsTrigger>
          <TabsTrigger value="reviews">Reviews</TabsTrigger>
          <TabsTrigger value="deliveries">Deliveries</TabsTrigger>
        </TabsList>

        {/* ── Users Tab ── */}
        <TabsContent value="users">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Restaurant ID</TableHead>
                    <TableHead>User ID</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell>{u.email}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            u.role === "admin"
                              ? "border-orange-500 text-orange-600"
                              : u.role === "owner"
                              ? "border-blue-500 text-blue-600"
                              : ""
                          }
                        >
                          {u.role}
                        </Badge>
                      </TableCell>
                      <TableCell>{u.restaurant_id ?? "—"}</TableCell>
                      <TableCell className="text-xs text-gray-400 font-mono">
                        {u.id.slice(0, 8)}
                      </TableCell>
                    </TableRow>
                  ))}
                  {users.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-gray-400">
                        No users found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Restaurants Tab ── */}
        <TabsContent value="restaurants">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {restaurants.map((r) => (
                    <>
                      <TableRow key={r.restaurant_id}>
                        <TableCell className="font-mono text-xs">{r.restaurant_id}</TableCell>
                        <TableCell>{r.name}</TableCell>
                        <TableCell className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => viewMenu(r.restaurant_id)}
                          >
                            {selectedRestaurant === r.restaurant_id ? "Hide Menu" : "View Menu"}
                          </Button>
                          <Link href={`/admin/restaurants/${r.restaurant_id}`}>
                            <Button size="sm" variant="outline">
                              Manage
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                      {selectedRestaurant === r.restaurant_id && (
                        <TableRow key={`menu-${r.restaurant_id}`}>
                          <TableCell colSpan={3} className="bg-gray-50 p-4">
                            {menuLoading ? (
                              <p className="text-sm text-gray-400">Loading menu...</p>
                            ) : menuItems.length === 0 ? (
                              <p className="text-sm text-gray-400">No menu items found.</p>
                            ) : (
                              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                {menuItems.map((item) => (
                                  <div
                                    key={item.food_item}
                                    className="flex justify-between items-center bg-white border rounded px-3 py-2 text-sm"
                                  >
                                    <span>{item.food_item}</span>
                                    <span className="font-medium text-gray-600">
                                      ${item.median_price?.toFixed(2) ?? "—"}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </TableCell>
                        </TableRow>
                      )}
                    </>
                  ))}
                  {restaurants.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-gray-400">
                        No restaurants found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Orders Tab ── */}
        <TabsContent value="orders">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Food Item</TableHead>
                    <TableHead>Restaurant</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((o) => (
                    <TableRow key={o.order_id}>
                      <TableCell className="text-xs text-gray-400 font-mono">
                        {o.order_id.slice(0, 8)}
                      </TableCell>
                      <TableCell>{o.food_item}</TableCell>
                      <TableCell>#{o.restaurant_id}</TableCell>
                      <TableCell>${o.order_value?.toFixed(2)}</TableCell>
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
                        {NEXT_STATUS[o.order_status] && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => advanceStatus(o.order_id, NEXT_STATUS[o.order_status]!)}
                          >
                            Advance to {NEXT_STATUS[o.order_status]}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {orders.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-gray-400">
                        No orders found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Cancelled Orders Tab ── */}
        <TabsContent value="cancelled">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-700">All Cancelled Orders</h3>
                <Badge variant="outline" className="text-red-600 border-red-300">
                  {cancelledOrders.length} cancelled
                </Badge>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Food Item</TableHead>
                    <TableHead>Restaurant</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cancelledOrders.map((o) => (
                    <TableRow key={o.order_id}>
                      <TableCell className="text-xs text-gray-400 font-mono">
                        {o.order_id.slice(0, 8)}
                      </TableCell>
                      <TableCell>{o.food_item}</TableCell>
                      <TableCell>#{o.restaurant_id}</TableCell>
                      <TableCell className="text-xs font-mono">{o.customer_id.slice(0, 8)}</TableCell>
                      <TableCell>${o.order_value?.toFixed(2)}</TableCell>
                      <TableCell>
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          {o.order_status}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                  {cancelledOrders.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-gray-400">
                        No cancelled orders found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Refunded Payments Tab (Feat11) ── */}
        <TabsContent value="refunds">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-700">Refunded Payments</h3>
                <Badge variant="outline" className="text-purple-600 border-purple-300">
                  {refundedPayments.length} refunded
                </Badge>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Payment ID</TableHead>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {refundedPayments.map((p) => (
                    <TableRow key={p.payment_id}>
                      <TableCell className="text-xs font-mono">{p.payment_id.slice(0, 8)}</TableCell>
                      <TableCell className="text-xs font-mono">{p.order_id.slice(0, 8)}</TableCell>
                      <TableCell className="text-xs font-mono">{p.customer_id.slice(0, 8)}</TableCell>
                      <TableCell>${p.amount?.toFixed(2)}</TableCell>
                      <TableCell>
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                          Refunded
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                  {refundedPayments.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-gray-400">
                        No refunded payments found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Payments Tab ── */}
        <TabsContent value="payments">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Payment ID</TableHead>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payments.map((p) => (
                    <TableRow key={p.payment_id}>
                      <TableCell className="text-xs font-mono">
                        {p.payment_id.slice(0, 8)}
                      </TableCell>
                      <TableCell className="text-xs font-mono">
                        {p.order_id.slice(0, 8)}
                      </TableCell>
                      <TableCell className="text-xs font-mono">
                        {p.customer_id.slice(0, 8)}
                      </TableCell>
                      <TableCell>${p.amount?.toFixed(2)}</TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            PAYMENT_COLORS[p.status] ?? "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {p.status}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                  {payments.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-gray-400">
                        No payments found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Reviews Tab ── */}
        <TabsContent value="reviews">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Restaurant</TableHead>
                    <TableHead>Rating</TableHead>
                    <TableHead>Tags</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reviews.map((r) => (
                    <TableRow key={r.review_id}>
                      <TableCell>#{r.restaurant_id}</TableCell>
                      <TableCell>
                        <Stars rating={r.rating} />
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {r.tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-orange-50 text-orange-700 border border-orange-200"
                            >
                              {tag}
                            </span>
                          ))}
                          {r.tags.length === 0 && (
                            <span className="text-xs text-gray-400">No tags</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-xs font-mono">
                        {r.customer_id.slice(0, 8)}
                      </TableCell>
                      <TableCell className="text-xs text-gray-500">
                        {new Date(r.created_at).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                  {reviews.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-gray-400">
                        No reviews found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Deliveries Tab ── */}
        <TabsContent value="deliveries">
          {/* Analytics summary */}
          {deliveryAnalytics && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-gray-500">Total Deliveries</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">{deliveryAnalytics.total_orders}</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-gray-500">Avg Delivery Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">
                    {deliveryAnalytics.avg_delivery_time?.toFixed(1) ?? "—"} min
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-gray-500">Avg Delay</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">
                    {deliveryAnalytics.avg_delivery_delay?.toFixed(1) ?? "—"} min
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

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
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {deliveries.map((d) => (
                    <TableRow key={d.order_id}>
                      <TableCell className="text-xs font-mono">
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
                          <span
                            className={
                              d.delivery_delay > 0 ? "text-red-600" : "text-green-600"
                            }
                          >
                            {d.delivery_delay > 0 ? "+" : ""}
                            {d.delivery_delay.toFixed(0)} min
                          </span>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {d.is_historical ? "Historical" : "System"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                  {deliveries.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center text-gray-400">
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
