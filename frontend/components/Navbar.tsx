"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { getUser, logout } from "@/lib/auth";
import { useEffect, useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

interface Notification {
  notification_id: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export default function Navbar() {
  const router = useRouter();
  const [user, setUser] = useState<{ email: string; role: string } | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setUser(getUser());
    const handler = () => setUser(getUser());
    window.addEventListener("auth-change", handler);
    return () => window.removeEventListener("auth-change", handler);
  }, []);

  useEffect(() => {
    if (!user) { setNotifications([]); return; }
    const fetchNotifs = () =>
      api.get("/notifications/").then(({ data }) => setNotifications([...data].reverse())).catch(() => {});
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 15000);
    const handler = () => fetchNotifs();
    window.addEventListener("notifications-refresh", handler);
    return () => {
      clearInterval(interval);
      window.removeEventListener("notifications-refresh", handler);
    };
  }, [user]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowNotifs(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleLogout() {
    logout();
    setUser(null);
    router.push("/login");
  }

  async function markRead(id: string) {
    await api.patch(`/notifications/${id}/read`).catch(() => {});
    setNotifications((prev) =>
      prev.map((n) => n.notification_id === id ? { ...n, is_read: true } : n)
    );
  }

  const unread = notifications.filter((n) => !n.is_read).length;

  return (
    <nav className="bg-white border-b shadow-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="font-bold text-lg text-orange-500">
            GitSOS
          </Link>
          {(!user || user.role === "customer") && (
            <Link href="/search" className="text-sm text-gray-600 hover:text-gray-900">
              Restaurants
            </Link>
          )}
          {user?.role === "customer" && (
            <Link href="/orders" className="text-sm text-gray-600 hover:text-gray-900">
              My Orders
            </Link>
          )}
          {user?.role === "customer" && (
            <Link href="/favourites" className="text-sm text-gray-600 hover:text-gray-900">
              Favourites
            </Link>
          )}
          {user?.role === "customer" && (
            <Link href="/reviews" className="text-sm text-gray-600 hover:text-gray-900">
              Reviews
            </Link>
          )}
          {user?.role === "owner" && (
            <Link href="/owner" className="text-sm text-orange-600 font-medium hover:text-orange-800">
              Dashboard
            </Link>
          )}
          {user?.role === "admin" && (
            <Link href="/admin" className="text-sm text-orange-600 font-medium hover:text-orange-800">
              Admin
            </Link>
          )}
          {user?.role === "admin" && (
            <Link href="/admin/reports" className="text-sm text-orange-600 font-medium hover:text-orange-800">
              Reports
            </Link>
          )}
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowNotifs((v) => !v)}
                className="relative p-1.5 rounded-full hover:bg-gray-100 text-gray-600"
                aria-label="Notifications"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                {unread > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 bg-orange-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center font-medium">
                    {unread > 9 ? "9+" : unread}
                  </span>
                )}
              </button>
              {showNotifs && (
                <div className="absolute right-0 mt-2 w-80 bg-white border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
                  <div className="px-4 py-2 border-b text-sm font-medium text-gray-700">
                    Notifications
                  </div>
                  {notifications.length === 0 ? (
                    <p className="text-sm text-gray-400 px-4 py-3">No notifications</p>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.notification_id}
                        className={`px-4 py-3 text-sm border-b last:border-0 flex items-start gap-2 ${n.is_read ? "bg-white text-gray-500" : "bg-orange-50 text-gray-800"}`}
                      >
                        <div className="flex-1">
                          <p>{n.message}</p>
                          <p className="text-xs text-gray-400 mt-0.5">
                            {new Date(n.created_at).toLocaleString()}
                          </p>
                        </div>
                        {!n.is_read && (
                          <button
                            onClick={() => markRead(n.notification_id)}
                            className="text-xs text-orange-500 hover:underline shrink-0 mt-0.5"
                          >
                            Mark read
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}
          {user ? (
            <>
              <span className="text-sm text-gray-500">{user.email}</span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="outline" size="sm">Login</Button>
              </Link>
              <Link href="/register">
                <Button size="sm">Register</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
