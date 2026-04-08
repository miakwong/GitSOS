"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
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
import { Input } from "@/components/ui/input";

/* ── Types ── */
interface Restaurant {
  restaurant_id: string;
  name: string;
}

interface RestaurantProfile {
  restaurant_id: string;
  name: string;
}

interface MenuItem {
  restaurant_id: string;
  food_item: string;
  price: number;
}

interface KaggleMenuItem {
  restaurant_id: string;
  food_item: string;
  median_price: number;
}

export default function AdminRestaurantDetailPage() {
  const router = useRouter();
  const params = useParams();
  const restaurantId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null);
  const [profile, setProfile] = useState<RestaurantProfile | null>(null);
  const [kaggleMenu, setKaggleMenu] = useState<KaggleMenuItem[]>([]);
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  /* ── Profile edit state ── */
  const [editName, setEditName] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState<string | null>(null);

  /* ── Menu item create state ── */
  const [newItemName, setNewItemName] = useState("");
  const [newItemPrice, setNewItemPrice] = useState("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createMsg, setCreateMsg] = useState<string | null>(null);

  /* ── Menu item edit state ── */
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [editItemName, setEditItemName] = useState("");
  const [editItemPrice, setEditItemPrice] = useState("");
  const [editSaving, setEditSaving] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/login"); return; }
    const user = getUser();
    if (user?.role !== "admin") { router.push("/"); return; }

    Promise.all([
      api.get(`/admin/restaurants/${restaurantId}`).then(({ data }) => setRestaurant(data)),
      api.get(`/admin/restaurants/${restaurantId}/profile`).then(({ data }) => {
        setProfile(data);
        setEditName(data.name);
      }),
      api.get(`/admin/restaurants/${restaurantId}/menu`).then(({ data }) => setKaggleMenu(data)),
      api.get(`/admin/restaurants/${restaurantId}/menu/items`).then(({ data }) => setMenuItems(data)),
    ])
      .catch((err) => setError(err.response?.data?.detail || "Failed to load restaurant"))
      .finally(() => setLoading(false));
  }, [router, restaurantId]);

  /* ── Profile update ── */
  async function saveProfile() {
    setProfileSaving(true);
    setProfileMsg(null);
    try {
      const { data } = await api.put(`/admin/restaurants/${restaurantId}/profile`, { name: editName });
      setProfile(data);
      setProfileMsg("Profile updated successfully.");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to update profile";
      setProfileMsg(msg);
    } finally {
      setProfileSaving(false);
    }
  }

  /* ── Create menu item ── */
  async function createMenuItem() {
    if (!newItemName.trim() || !newItemPrice) return;
    setCreateLoading(true);
    setCreateMsg(null);
    try {
      const { data } = await api.post(`/admin/restaurants/${restaurantId}/menu/items`, {
        food_item: newItemName.trim(),
        price: parseFloat(newItemPrice),
      });
      setMenuItems((prev) => [...prev, data]);
      setNewItemName("");
      setNewItemPrice("");
      setCreateMsg("Item created.");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to create item";
      setCreateMsg(msg);
    } finally {
      setCreateLoading(false);
    }
  }

  /* ── Update menu item ── */
  async function updateMenuItem(originalName: string) {
    setEditSaving(true);
    try {
      const body: { food_item?: string; price?: number } = {};
      if (editItemName.trim() && editItemName.trim() !== originalName) body.food_item = editItemName.trim();
      if (editItemPrice) body.price = parseFloat(editItemPrice);
      const { data } = await api.put(
        `/admin/restaurants/${restaurantId}/menu/items/${encodeURIComponent(originalName)}`,
        body,
      );
      setMenuItems((prev) => prev.map((m) => (m.food_item === originalName ? data : m)));
      setEditingItem(null);
    } catch {
      // keep dialog open so user can retry
    } finally {
      setEditSaving(false);
    }
  }

  /* ── Delete menu item ── */
  async function deleteMenuItem(foodItem: string) {
    if (!confirm(`Delete "${foodItem}"?`)) return;
    try {
      await api.delete(`/admin/restaurants/${restaurantId}/menu/items/${encodeURIComponent(foodItem)}`);
      setMenuItems((prev) => prev.filter((m) => m.food_item !== foodItem));
    } catch {
      alert("Failed to delete item.");
    }
  }

  /* ── Loading / Error ── */
  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-64" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error || !restaurant) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-4">Restaurant Not Found</h1>
        <p className="text-red-600">{error ?? "The restaurant could not be loaded."}</p>
        <Link href="/admin" className="text-sm text-orange-600 hover:underline mt-4 inline-block">
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{restaurant.name}</h1>
          <p className="text-sm text-gray-500 mt-1">
            Restaurant ID: <span className="font-mono">{restaurant.restaurant_id}</span>
          </p>
        </div>
        <Link href="/admin" className="text-sm text-orange-600 hover:text-orange-800 hover:underline">
          ← Back to Dashboard
        </Link>
      </div>

      <Tabs defaultValue="profile">
        <TabsList className="mb-4">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="kaggle-menu">Kaggle Menu</TabsTrigger>
          <TabsTrigger value="menu-items">Custom Menu Items</TabsTrigger>
        </TabsList>

        {/* ── Profile Tab ── */}
        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Restaurant Profile</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {profile ? (
                <>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Restaurant Name</label>
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="mt-1 max-w-md"
                    />
                  </div>
                  <div className="flex items-center gap-3">
                    <Button onClick={saveProfile} disabled={profileSaving || !editName.trim()}>
                      {profileSaving ? "Saving…" : "Save Profile"}
                    </Button>
                    {profileMsg && (
                      <span className={`text-sm ${profileMsg.includes("success") ? "text-green-600" : "text-red-600"}`}>
                        {profileMsg}
                      </span>
                    )}
                  </div>
                </>
              ) : (
                <p className="text-gray-400">No profile data available.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Kaggle Menu Tab ── */}
        <TabsContent value="kaggle-menu">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Kaggle Menu ({kaggleMenu.length} items)</CardTitle>
            </CardHeader>
            <CardContent>
              {kaggleMenu.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {kaggleMenu.map((item) => (
                    <div
                      key={item.food_item}
                      className="flex justify-between items-center bg-gray-50 border rounded px-3 py-2 text-sm"
                    >
                      <span>{item.food_item}</span>
                      <span className="font-medium text-gray-600">
                        ${item.median_price?.toFixed(2) ?? "—"}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">No Kaggle menu items found.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Custom Menu Items Tab (CRUD) ── */}
        <TabsContent value="menu-items">
          {/* Create form */}
          <Card className="mb-4">
            <CardHeader>
              <CardTitle className="text-lg">Add Menu Item</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3 items-end">
                <div>
                  <label className="text-xs text-gray-500">Food Item</label>
                  <Input
                    placeholder="e.g. Margherita Pizza"
                    value={newItemName}
                    onChange={(e) => setNewItemName(e.target.value)}
                    className="w-56"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Price ($)</label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="12.99"
                    value={newItemPrice}
                    onChange={(e) => setNewItemPrice(e.target.value)}
                    className="w-28"
                  />
                </div>
                <Button size="sm" onClick={createMenuItem} disabled={createLoading}>
                  {createLoading ? "Adding…" : "Add Item"}
                </Button>
              </div>
              {createMsg && (
                <p className={`text-sm mt-2 ${createMsg.includes("created") ? "text-green-600" : "text-red-600"}`}>
                  {createMsg}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Items table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Custom Menu Items ({menuItems.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Food Item</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {menuItems.map((item) => (
                    <TableRow key={item.food_item}>
                      {editingItem === item.food_item ? (
                        <>
                          <TableCell>
                            <Input
                              value={editItemName}
                              onChange={(e) => setEditItemName(e.target.value)}
                              className="w-48"
                            />
                          </TableCell>
                          <TableCell>
                            <Input
                              type="number"
                              step="0.01"
                              value={editItemPrice}
                              onChange={(e) => setEditItemPrice(e.target.value)}
                              className="w-24"
                            />
                          </TableCell>
                          <TableCell className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={() => updateMenuItem(item.food_item)}
                              disabled={editSaving}
                            >
                              {editSaving ? "Saving…" : "Save"}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingItem(null)}
                            >
                              Cancel
                            </Button>
                          </TableCell>
                        </>
                      ) : (
                        <>
                          <TableCell>{item.food_item}</TableCell>
                          <TableCell>${item.price.toFixed(2)}</TableCell>
                          <TableCell className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setEditingItem(item.food_item);
                                setEditItemName(item.food_item);
                                setEditItemPrice(String(item.price));
                              }}
                            >
                              Edit
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600 border-red-300 hover:bg-red-50"
                              onClick={() => deleteMenuItem(item.food_item)}
                            >
                              Delete
                            </Button>
                          </TableCell>
                        </>
                      )}
                    </TableRow>
                  ))}
                  {menuItems.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-gray-400">
                        No custom menu items yet. Add one above.
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
