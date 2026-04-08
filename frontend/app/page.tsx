"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const user = getUser();
    if (user?.role === "owner") router.replace("/owner");
    else if (user?.role === "admin") router.replace("/admin");
  }, [router]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-20 text-center">
      <h1 className="text-5xl font-bold text-gray-900 mb-4">
        Food Delivery Made Simple
      </h1>
      <p className="text-xl text-gray-500 mb-10">
        Search restaurants, place orders, and track deliveries — all in one place.
      </p>
      <div className="flex gap-4 justify-center">
        <Link href="/search">
          <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-white">
            Browse Restaurants
          </Button>
        </Link>
        <Link href="/register">
          <Button size="lg" variant="outline">
            Get Started
          </Button>
        </Link>
      </div>
    </div>
  );
}
