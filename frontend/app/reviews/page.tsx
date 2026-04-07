"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { isLoggedIn, getUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const TAGS = [
  "Delicious", "Just okay", "Disappointing",
  "Fast delivery", "On time", "Late delivery",
  "Great value", "Overpriced",
];

interface Order {
  order_id: string;
  food_item: string;
  restaurant_id: number;
  order_status: string;
}

export default function ReviewsPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<string>("");
  const [rating, setRating] = useState(5);
  const [tags, setTags] = useState<string[]>([]);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/login"); return; }
    const user = getUser();
    api.get(`/search/orders?customer_id=${user?.id}`)
      .then(({ data }) => {
        const delivered = (data.data ?? []).filter((o: Order) => o.order_status === "Delivered");
        setOrders(delivered);
      });
  }, [router]);

  function toggleTag(tag: string) {
    setTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      await api.post("/reviews/", { order_id: selectedOrder, rating, tags });
      setSuccess("Review submitted!");
      setSelectedOrder(""); setRating(5); setTags([]);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === "string" ? msg : "Failed to submit review.");
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Submit a Review</h1>
      <Card>
        <CardHeader><CardTitle>Rate your order</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="text-sm font-medium block mb-1">Order</label>
              <select
                className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                value={selectedOrder}
                onChange={(e) => setSelectedOrder(e.target.value)}
                required
              >
                <option value="">Select a delivered order…</option>
                {orders.map((o) => (
                  <option key={o.order_id} value={o.order_id}>
                    {o.food_item} — Restaurant #{o.restaurant_id} (#{o.order_id.slice(0, 8)})
                  </option>
                ))}
              </select>
              {orders.length === 0 && (
                <p className="text-xs text-gray-400 mt-1">No delivered orders available to review.</p>
              )}
            </div>

            <div>
              <label className="text-sm font-medium block mb-2">Rating</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setRating(n)}
                    className={`text-2xl transition-transform ${n <= rating ? "scale-110" : "opacity-30"}`}
                  >
                    ⭐
                  </button>
                ))}
                <span className="text-sm text-gray-500 self-center ml-2">{rating}/5</span>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium block mb-2">Tags (optional)</label>
              <div className="flex flex-wrap gap-2">
                {TAGS.map((tag) => (
                  <Badge
                    key={tag}
                    variant={tags.includes(tag) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => toggleTag(tag)}
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}
            {success && <p className="text-sm text-green-600">{success}</p>}

            <Button type="submit" className="w-full bg-orange-500 hover:bg-orange-600 text-white">
              Submit Review
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
