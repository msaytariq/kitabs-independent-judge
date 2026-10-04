"use client";
import { useCallback, useEffect, useState } from "react";
import {
  commandReview,
  createReview,
  getReview,
  scopeFromTexts,
} from "../../shared/api/editorial";
import type { Inputs, Review } from "../../shared/types/editorial";

export function useEditorialReview() {
  const [review, setReview] = useState<Review | null>(null);
  const [actor, setActor] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const transact = useCallback(async (operation: () => Promise<Review>) => {
    setBusy(true);
    setError("");
    try {
      const next = await operation();
      setReview(next);
      window.history.replaceState(null, "", `#${next.id}`);
      return next;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Operation failed.");
      return null;
    } finally {
      setBusy(false);
    }
  }, []);
  useEffect(() => {
    const id = window.location.hash.slice(1);
    if (id) void transact(() => getReview(id));
  }, [transact]);
  const command = async (kind: string, params: Record<string, unknown>) => {
    if (!review || busy) return null;
    if (!actor.trim()) {
      setError("Enter your editor label first.");
      return null;
    }
    return transact(() => commandReview(review, actor, kind, params));
  };
  const create = async (scopeId: string, rubric: string, inputs?: Inputs) => {
    if (!actor.trim()) {
      setError("Enter your editor label first.");
      return;
    }
    await transact(async () => {
      const id = inputs ? (await scopeFromTexts(inputs)).id : scopeId;
      return createReview(id, rubric, actor);
    });
  };
  const open = (id: string) => transact(() => getReview(id));
  return { review, actor, setActor, busy, error, command, create, open };
}
