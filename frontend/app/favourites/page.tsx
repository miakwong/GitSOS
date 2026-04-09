"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { getUser, isLoggedIn } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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

interface Favourite {
  favourite_id: string;
  order_id: string;
  customer_id: string;
  created_at: string;
}

interface PopularItem {
  food_item: string;
  restaurant_id: number;
  favourite_count: number;
}

export default function FavouritesPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: string; role: string } | null>(null);
  const [favourites, setFavourites] = useState<Favourite[]>([]);
  const [orderDetails, setOrderDetails] = useState<Record<string, Order>>({});
  const [popularItems, setPopularItems] = useState<PopularItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [reordering, setReordering] = useState<string | null>(null);
  const [removing, setRemoving] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) {
      router.push("/login?redirect=/favourites");
      return;
    }
    const currentUser = getUser();
    setUser(currentUser);

    if (currentUser?.role === "customer") {
      loadCustomerFavourites();
    } else if (currentUser?.role === "owner" || currentUser?.role === "admin") {
      loadPopularItems();
    } else {
      router.push("/");
    }
  }, [router]);

  async function loadCustomerFavourites() {
    setLoading(true);
    try {
      const { data: favs } = await api.get<Favourite[]>("/favourites/");
      setFavourites(favs);

      // Fetch order details for each favourite
      const details: Record<string, Order> = {};
      await Promise.all(
        favs.map(async (fav) => {
          try {
            const { data: order } = await api.get<Order>(`/orders/${fav.order_id}`);
            details[fav.order_id] = order;
          } catch {
            // Order may have been deleted or inaccessible
          }
        })
      );
      setOrderDetails(details);
    } catch {
      setError("Failed to load favourites.");
    } finally {
      setLoading(false);
    }
  }

  async function loadPopularItems() {
    setLoading(true);
    try {
      const { data } = await api.get<PopularItem[]>("/favourites/analytics/popular");
      setPopularItems(data);
    } catch {
      setError("Failed to load popular items.");
    } finally {
      setLoading(false);
    }
  }

  async function saveFavourite(orderId: string) {
    try {
      const { data: newFav } = await api.post<Favourite>("/favourites/", { order_id: orderId });
      setFavourites((prev) => [newFav, ...prev]);
      setSuccessMessage("Order saved to favourites!");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : "Failed to save favourite.");
      setTimeout(() => setError(""), 3000);
    }
  }

  async function removeFavourite(favouriteId: string) {
    setRemoving(favouriteId);
    try {
      await api.delete(`/favourites/${favouriteId}`);
      setFavourites((prev) => prev.filter((f) => f.favourite_id !== favouriteId));
      setSuccessMessage("Favourite removed.");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : "Failed to remove favourite.");
      setTimeout(() => setError(""), 3000);
    } finally {
      setRemoving(null);
    }
  }

  async function reorderFromFavourite(favouriteId: string) {
    setReordering(favouriteId);
    setError("");
    try {
      const { data: newOrder } = await api.post<Order>(`/favourites/${favouriteId}/reorder`);
      setSuccessMessage(`New order created! Order #${newOrder.order_id.slice(0, 8)}`);
      window.dispatchEvent(new Event("notifications-refresh"));
      setTimeout(() => {
        setSuccessMessage("");
        router.push("/orders");
      }, 2000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : "Failed to reorder.");
      setTimeout(() => setError(""), 5000);
    } finally {
      setReordering(null);
    }
  }

  // Customer view
  if (user?.role === "customer") {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">My Favourites</h1>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            {successMessage}
          </div>
        )}

        {loading ? (
          <div className="animate-pulse space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg" />
            ))}
          </div>
        ) : favourites.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="text-gray-400 mb-4">
                <svg
                  className="w-16 h-16 mx-auto"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                  />
                </svg>
              </div>
              <p className="text-gray-500 mb-4">No favourite orders yet.</p>
              <p className="text-sm text-gray-400 mb-6">
                Save orders from your order history to quickly reorder them here.
              </p>
              <Button
                onClick={() => router.push("/orders")}
                className="bg-orange-500 hover:bg-orange-600 text-white"
              >
                View My Orders
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {favourites.map((fav) => {
              const order = orderDetails[fav.order_id];
              return (
                <Card key={fav.favourite_id}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium text-gray-500">
                        Saved {new Date(fav.created_at).toLocaleDateString()}
                      </CardTitle>
                      <Badge variant="outline" className="text-orange-600 border-orange-300">
                        ❤️ Favourite
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {order ? (
                      <div className="space-y-3">
                        <div>
                          <p className="font-semibold text-lg">{order.food_item}</p>
                          <p className="text-gray-500 text-sm">
                            Restaurant #{order.restaurant_id} · ${order.order_value?.toFixed(2)}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2 text-xs">
                          <span className="px-2 py-1 bg-gray-100 rounded-full">
                            {order.delivery_method}
                          </span>
                          <span className="px-2 py-1 bg-gray-100 rounded-full">
                            {order.delivery_distance} km
                          </span>
                          <span className="px-2 py-1 bg-gray-100 rounded-full">
                            {order.traffic_condition} traffic
                          </span>
                          <span className="px-2 py-1 bg-gray-100 rounded-full">
                            {order.weather_condition}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400">
                          Original order: #{order.order_id.slice(0, 8)} ·{" "}
                          {new Date(order.order_time).toLocaleString()}
                        </p>
                        <div className="flex gap-2 pt-2">
                          <Button
                            size="sm"
                            className="bg-orange-500 hover:bg-orange-600 text-white"
                            disabled={reordering === fav.favourite_id}
                            onClick={() => reorderFromFavourite(fav.favourite_id)}
                          >
                            {reordering === fav.favourite_id ? "Creating order…" : "Reorder"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={removing === fav.favourite_id}
                            onClick={() => removeFavourite(fav.favourite_id)}
                          >
                            {removing === fav.favourite_id ? "Removing…" : "Remove"}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-gray-400 text-sm">
                        <p>Order details unavailable.</p>
                        <p className="text-xs mt-1">Order ID: {fav.order_id.slice(0, 8)}</p>
                        <Button
                          size="sm"
                          variant="outline"
                          className="mt-3"
                          disabled={removing === fav.favourite_id}
                          onClick={() => removeFavourite(fav.favourite_id)}
                        >
                          {removing === fav.favourite_id ? "Removing…" : "Remove"}
                        </Button>
                      </div>
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

  // Owner/Admin view - Popular Items Analytics
  if (user?.role === "owner" || user?.role === "admin") {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-2">Popular Favourited Items</h1>
        <p className="text-gray-500 mb-6">
          {user.role === "owner"
            ? "See which of your menu items are most frequently saved as favourites by customers."
            : "System-wide view of the most popular favourited menu items across all restaurants."}
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="animate-pulse">
            <div className="h-64 bg-gray-200 rounded-lg" />
          </div>
        ) : popularItems.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="text-gray-400 mb-4">
                <svg
                  className="w-16 h-16 mx-auto"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <p className="text-gray-500">No favourite data available yet.</p>
              <p className="text-sm text-gray-400 mt-2">
                Analytics will appear once customers start saving orders as favourites.
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Top Favourited Items</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">#</TableHead>
                    <TableHead>Food Item</TableHead>
                    <TableHead>Restaurant ID</TableHead>
                    <TableHead className="text-right">Times Favourited</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {popularItems.map((item, index) => (
                    <TableRow key={`${item.restaurant_id}-${item.food_item}`}>
                      <TableCell className="font-medium">
                        {index < 3 ? (
                          <span
                            className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                              index === 0
                                ? "bg-yellow-100 text-yellow-700"
                                : index === 1
                                ? "bg-gray-100 text-gray-600"
                                : "bg-orange-100 text-orange-700"
                            }`}
                          >
                            {index + 1}
                          </span>
                        ) : (
                          <span className="text-gray-400">{index + 1}</span>
                        )}
                      </TableCell>
                      <TableCell className="font-medium">{item.food_item}</TableCell>
                      <TableCell>#{item.restaurant_id}</TableCell>
                      <TableCell className="text-right">
                        <Badge
                          variant="outline"
                          className="bg-orange-50 text-orange-700 border-orange-200"
                        >
                          ❤️ {item.favourite_count}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // Fallback loading state
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="h-32 bg-gray-200 rounded" />
      </div>
    </div>
  );
}
