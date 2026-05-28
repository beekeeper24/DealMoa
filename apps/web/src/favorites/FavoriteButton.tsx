"use client";

import React, { useState } from "react";

import { addFavorite, removeFavorite, type FavoriteTargetType } from "./api";

type FavoriteButtonProps = {
  accessToken?: string;
  targetId: string;
  targetType: FavoriteTargetType;
};

export function FavoriteButton({ accessToken, targetId, targetType }: FavoriteButtonProps) {
  const [isFavorited, setIsFavorited] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hasError, setHasError] = useState(false);

  async function toggleFavorite() {
    if (!accessToken || isSaving) {
      return;
    }

    setIsSaving(true);
    setHasError(false);
    try {
      if (isFavorited) {
        await removeFavorite({ accessToken, targetId, targetType });
        setIsFavorited(false);
      } else {
        await addFavorite({ accessToken, targetId, targetType });
        setIsFavorited(true);
      }
    } catch {
      setHasError(true);
    } finally {
      setIsSaving(false);
    }
  }

  const label = !accessToken ? "로그인 후 찜" : isFavorited ? "찜 해제" : "찜하기";

  return (
    <div className="flex shrink-0 flex-col items-end gap-1">
      <button
        aria-pressed={accessToken ? isFavorited : undefined}
        className="rounded border border-black/15 bg-white px-3 py-1.5 text-xs font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
        disabled={!accessToken || isSaving}
        onClick={() => void toggleFavorite()}
        type="button"
      >
        {isSaving ? "저장 중" : label}
      </button>
      {hasError ? <span className="text-xs font-semibold text-deal">찜 실패</span> : null}
    </div>
  );
}
