"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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

interface User { id: string; email: string; role: string; restaurant_id?: number }
interface Order { order_id: string; customer_id: string; restaurant_id: number; food_item: string; order_status: string; order_value: number }
interface Payment { payment_id: string; order_id: string; customer_id: string; status: string; amount: number }

export default function AdminPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/login"); return; }
    const user = getUser();
    if (user?.role !== "admin") { router.push("/"); return; }

    api.get("/auth/admin/users").then(({ data }) => setUsers(data));
    api.get("/orders/").then(({ data }) => setOrders(data));
    api.get("/payments/").catch(() => {}).then((res) => res && setPayments(res.data ?? []));
  }, [router]);

  async function advanceStatus(orderId: string, status: string) {
    await api.patch(`/orders/admin/${orderId}/status`, { order_status: status });
    setOrders((prev) => prev.map((o) => o.order_id === orderId ? { ...o, order_status: status } : o));
  }

  const NEXT_STATUS: Record<string, string | null> = {
    Placed: "Preparing",
    Preparing: "Delivered",
    Delivered: null,
    Cancelled: null,
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <Card><CardHeader><CardTitle className="text-sm text-gray-500">Users</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{users.length}</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm text-gray-500">Orders</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{orders.length}</p></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm text-gray-500">Payments</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{payments.length}</p></CardContent></Card>
      </div>

      <Tabs defaultValue="users">
        <TabsList className="mb-4">
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="orders">Orders</TabsTrigger>
          <TabsTrigger value="payments">Payments</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Restaurant ID</TableHead>
                    <TableHead>ID</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell>{u.email}</TableCell>
                      <TableCell><Badge variant="outline">{u.role}</Badge></TableCell>
                      <TableCell>{u.restaurant_id ?? "—"}</TableCell>
                      <TableCell className="text-xs text-gray-400">{u.id.slice(0, 8)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="orders">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
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
                      <TableCell className="text-xs text-gray-400">{o.order_id.slice(0, 8)}</TableCell>
                      <TableCell>{o.food_item}</TableCell>
                      <TableCell>#{o.restaurant_id}</TableCell>
                      <TableCell>${o.order_value?.toFixed(2)}</TableCell>
                      <TableCell>
                        <Badge variant={o.order_status === "Delivered" ? "default" : "outline"}>
                          {o.order_status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {NEXT_STATUS[o.order_status] && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => advanceStatus(o.order_id, NEXT_STATUS[o.order_status]!)}
                          >
                            → {NEXT_STATUS[o.order_status]}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Payment ID</TableHead>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payments.map((p) => (
                    <TableRow key={p.payment_id}>
                      <TableCell className="text-xs">{p.payment_id.slice(0, 8)}</TableCell>
                      <TableCell className="text-xs">{p.order_id.slice(0, 8)}</TableCell>
                      <TableCell>${p.amount?.toFixed(2)}</TableCell>
                      <TableCell><Badge variant="outline">{p.status}</Badge></TableCell>
                    </TableRow>
                  ))}
                  {payments.length === 0 && (
                    <TableRow><TableCell colSpan={4} className="text-gray-400 text-center">No payments yet.</TableCell></TableRow>
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
