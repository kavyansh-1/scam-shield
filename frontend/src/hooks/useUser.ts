"use client";
import { useEffect, useState } from "react";
import { uuid } from "@/lib/api";

export function useUser(): { userId: string } {
  const [userId, setUserId] = useState("");
  useEffect(() => {
    try {
      let id = localStorage.getItem("ss_user_id");
      if (!id) { id = uuid(); localStorage.setItem("ss_user_id", id); }
      setUserId(id);
    } catch { setUserId(uuid()); }
  }, []);
  return { userId };
}
