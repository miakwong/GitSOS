"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api";
import { isLoggedIn, getUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface MenuItem {
  restaurant_id: string;
  item_name: string;
  category: string;
  price: number;
}

interface ReviewSummary {
  restaurant_id: number;
  average_rating: number;
  review_count: number;
  tag_counts: Record<string, number>;
  reviews: { review_id: string; rating: number; tags: string[] }[];
}

export default function RestaurantDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [items, setItems] = useState<MenuItem[]>([]);
  const [allItems, setAllItems] = useState<MenuItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [sortBy, setSortBy] = useState("item_name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [loading, setLoading] = useState(true);
  const [ordering, setOrdering] = useState<string | null>(null);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [reviewSummary, setReviewSummary] = useState<ReviewSummary | null>(null);

  async function fetchMenu(category = selectedCategory, sort = sortBy, order = sortOrder) {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { restaurant_id: id, page_size: 100, sort_by: sort, sort_order: order };
      if (category) params.category = category;
      const { data } = await api.get("/search/menu-items", { params });
      setItems(data.data || []);
    } catch {
      // keep showing existing items on error
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const user = getUser();
    if (user?.role === "owner" || user?.role === "admin") {
      router.replace("/");
      return;
    }
    // Load all items once to extract unique categories
    api.get("/search/menu-items", { params: { restaurant_id: id, page_size: 100 } })
      .then(({ data }) => {
        const all: MenuItem[] = data.data || [];
        setAllItems(all);
        setItems(all);
        const unique = [...new Set(all.map((i) => i.category).filter(Boolean))].sort();
        setCategories(unique);
      })
      .finally(() => setLoading(false));

    api.get(`/reviews/restaurant/${id}`)
      .then(({ data }) => setReviewSummary(data))
      .catch(() => {});
  }, [id]);

  async function placeOrder(item: MenuItem) {
    if (!isLoggedIn()) {
      router.push(`/login?redirect=/restaurants/${id}`);
      return;
    }
    const user = getUser();
    setOrdering(item.item_name);
    setSuccess("");
    setError("");
    try {
      await api.post("/orders/", {
        customer_id: user.id,
        restaurant_id: parseInt(id),
        food_item: item.item_name,
        order_value: item.price,
        delivery_distance: 3.0,
        delivery_method: "Bike",
        traffic_condition: "Low",
        weather_condition: "Sunny",
      });
      setSuccess(`Order placed for ${item.item_name}!`);
      window.dispatchEvent(new Event("notifications-refresh"));
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail;
      setError(typeof msg === "string" ? msg : "Failed to place order.");
    } finally {
      setOrdering(null);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button
        onClick={() => router.back()}
        className="text-sm text-gray-500 hover:text-gray-800 mb-4 flex items-center gap-1"
      >
        ← Back
      </button>

      <h1 className="text-2xl font-bold mb-2">Restaurant #{id}</h1>

      {reviewSummary && reviewSummary.review_count > 0 && (
        <div className="mb-4 p-4 bg-orange-50 border border-orange-100 rounded-lg">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl font-bold text-orange-500">{reviewSummary.average_rating.toFixed(1)}</span>
            <span className="text-orange-400">{"⭐".repeat(Math.round(reviewSummary.average_rating))}</span>
            <span className="text-sm text-gray-500">({reviewSummary.review_count} review{reviewSummary.review_count !== 1 ? "s" : ""})</span>
          </div>
          {Object.keys(reviewSummary.tag_counts).length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(reviewSummary.tag_counts)
                .sort((a, b) => b[1] - a[1])
                .map(([tag, count]) => (
                  <span key={tag} className="text-xs px-2 py-0.5 bg-white border border-orange-200 rounded-full text-gray-600">
                    {tag} · {count}
                  </span>
                ))}
            </div>
          )}
        </div>
      )}

      <p className="text-gray-500 text-sm mb-4">Select an item to place an order</p>

      {/* Filters & sorting */}
      {!loading && (
        <div className="flex flex-wrap gap-3 mb-6 items-end">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Cuisine</label>
            <select
              value={selectedCategory}
              onChange={(e) => {
                const cat = e.target.value;
                setSelectedCategory(cat);
                if (cat) {
                  setItems(allItems.filter((i) => i.category === cat));
                } else {
                  fetchMenu("", sortBy, sortOrder);
                }
              }}
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">All cuisines</option>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Sort by</label>
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); fetchMenu(selectedCategory, e.target.value, sortOrder); }}
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="item_name">Name</option>
              <option value="price">Price</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Order</label>
            <button
              onClick={() => { const o = sortOrder === "asc" ? "desc" : "asc"; setSortOrder(o); fetchMenu(selectedCategory, sortBy, o); }}
              className="h-10 px-3 rounded-md border border-input bg-background text-sm hover:bg-gray-50"
            >
              {sortOrder === "asc" ? "↑ Asc" : "↓ Desc"}
            </button>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
          {success}{" "}
          <button
            className="underline ml-1"
            onClick={() => router.push("/orders")}
          >
            View orders
          </button>
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-gray-400">Loading menu…</p>
      ) : items.length === 0 ? (
        <p className="text-gray-400">No menu items available.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {items.map((item, idx) => (
            <Card key={idx} className="flex flex-col justify-between">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{item.item_name}</CardTitle>
              </CardHeader>
              <CardContent className="flex items-center justify-between">
                <div className="space-y-1">
                  {item.category && (
                    <Badge variant="secondary">{item.category}</Badge>
                  )}
                  <p className="text-lg font-semibold text-gray-800">
                    ${item.price?.toFixed(2)}
                  </p>
                </div>
                <Button
                  size="sm"
                  className="bg-orange-500 hover:bg-orange-600 text-white"
                  disabled={ordering === item.item_name}
                  onClick={() => placeOrder(item)}
                >
                  {ordering === item.item_name ? "Ordering…" : "Order"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
