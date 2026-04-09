"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Restaurant {
  restaurant_id: string;
  restaurant_name: string;
  city: string;
  cuisine: string;
}

const PAGE_SIZE = 12;

export default function SearchPage() {
  const router = useRouter();
  const [allRestaurants, setAllRestaurants] = useState<Restaurant[]>([]);
  const [city, setCity] = useState("");
  const [cuisine, setCuisine] = useState("");
  const [sortBy, setSortBy] = useState("restaurant_id");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Fetch all restaurants once
  useEffect(() => {
    api
      .get("/search/restaurants", { params: { page_size: 100 } })
      .then(({ data }) => setAllRestaurants(data.data || []))
      .finally(() => setLoading(false));
  }, []);

  // Filter + sort + paginate entirely client-side
  const filtered = useMemo(() => {
    let list = allRestaurants;
    if (city)
      list = list.filter((r) =>
        r.city?.toLowerCase().includes(city.toLowerCase()),
      );
    if (cuisine)
      list = list.filter((r) =>
        r.cuisine?.toLowerCase().includes(cuisine.toLowerCase()),
      );
    list = [...list].sort((a, b) => {
      if (sortBy === "restaurant_id") {
        const diff = parseInt(a.restaurant_id) - parseInt(b.restaurant_id);
        return sortOrder === "asc" ? diff : -diff;
      }
      const av = (a.restaurant_name || "").toLowerCase();
      const bv = (b.restaurant_name || "").toLowerCase();
      return sortOrder === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    return list;
  }, [allRestaurants, city, cuisine, sortBy, sortOrder]);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pageResults = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function handleSearch() {
    setPage(1);
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Find Restaurants</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4 items-end">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">City</label>
          <Input
            placeholder="e.g. Vancouver"
            value={city}
            onChange={(e) => {
              setCity(e.target.value);
              setPage(1);
            }}
            className="w-40"
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Cuisine</label>
          <Input
            placeholder="e.g. Italian"
            value={cuisine}
            onChange={(e) => {
              setCuisine(e.target.value);
              setPage(1);
            }}
            className="w-40"
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Sort by</label>
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="restaurant_id">Restaurant ID</option>
            <option value="restaurant_name">Name</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Order</label>
          <button
            onClick={() => {
              setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
              setPage(1);
            }}
            className="h-10 px-3 rounded-md border border-input bg-background text-sm hover:bg-gray-50"
          >
            {sortOrder === "asc" ? "↑ Asc" : "↓ Desc"}
          </button>
        </div>
      </div>

      <p className="text-sm text-gray-500 mb-4">
        {filtered.length} restaurant{filtered.length !== 1 ? "s" : ""} found
        {totalPages > 1 && ` · Page ${page} of ${totalPages}`}
      </p>

      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {pageResults.map((r) => (
              <Card
                key={r.restaurant_id}
                className="hover:shadow-md transition-shadow cursor-pointer hover:border-orange-300"
                onClick={() => router.push(`/restaurants/${r.restaurant_id}`)}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">
                    {r.restaurant_name || `Restaurant #${r.restaurant_id}`}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-gray-500">
                  {r.city && <p>📍 {r.city}</p>}
                  {r.cuisine && <Badge variant="secondary">{r.cuisine}</Badge>}
                  <p className="text-xs text-orange-500 font-medium pt-1">
                    View menu →
                  </p>
                </CardContent>
              </Card>
            ))}
            {pageResults.length === 0 && (
              <p className="text-gray-400 col-span-3">No restaurants found.</p>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                ← Prev
              </Button>
              {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                const p = i + 1;
                return (
                  <Button
                    key={p}
                    variant={p === page ? "default" : "outline"}
                    size="sm"
                    className={
                      p === page ? "bg-orange-500 hover:bg-orange-600" : ""
                    }
                    onClick={() => setPage(p)}
                  >
                    {p}
                  </Button>
                );
              })}
              {totalPages > 7 && (
                <>
                  <span className="text-gray-400">…</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(totalPages)}
                  >
                    {totalPages}
                  </Button>
                </>
              )}
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next →
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
