import React, { useEffect, useState } from "react";
import { listUsers, setUserRoles, AdminUserRow } from "../api/adminUsers";

const ROLE_OPTIONS = ["user", "pro", "admin"] as const;

export function AdminUsers() {
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const data = await listUsers();
      setRows(data.items);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onChangeRole(userId: number, role: string) {
    await setUserRoles(userId, [role]);
    await load();
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Users</h1>
      <table>
        <thead>
          <tr>
            <th>id</th>
            <th>email</th>
            <th>role</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((u) => (
            <tr key={u.id}>
              <td>{u.id}</td>
              <td>{u.email}</td>
              <td>
                <select
                  value={u.roles[0] ?? "user"}
                  onChange={(e) => void onChangeRole(u.id, e.target.value)}
                >
                  {ROLE_OPTIONS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
