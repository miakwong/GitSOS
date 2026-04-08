"use client";

import { useEffect, useState } from "react";
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

export default function SearchPage() {
  const router = useRouter();
  const [city, setCity] = useState("");
  const [cuisine, setCuisine] = useState("");
  const [results, setResults] = useState<Restaurant[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  async function search() {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (city) params.city = city;
      if (cuisine) params.cuisine = cuisine;
      const { data } = await api.get("/search/restaurants", { params });
      setResults(data.data || []);
      setTotal(data.meta?.total || 0);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    search();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Find Restaurants</h1>

      <div className="flex flex-wrap gap-3 mb-8">
        <Input
          placeholder="City…"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="w-40"
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        <Input
          placeholder="Cuisine…"
          value={cuisine}
          onChange={(e) => setCuisine(e.target.value)}
          className="w-40"
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        <Button onClick={search} className="bg-orange-500 hover:bg-orange-600 text-white">
          Search
        </Button>
      </div>

      <p className="text-sm text-gray-500 mb-4">{total} restaurants found</p>

      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {results.map((r) => (
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
                <p className="text-xs text-orange-500 font-medium pt-1">View menu →</p>
              </CardContent>
            </Card>
          ))}
          {results.length === 0 && (
            <p className="text-gray-400 col-span-3">No restaurants found.</p>
          )}
        </div>
      )}
    </div>
  );
}
