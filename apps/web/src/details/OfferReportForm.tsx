"use client";

import React, { FormEvent, useState } from "react";

import { DetailApiError, reportAuction, reportDeal } from "./api";

type OfferReportFormProps = {
  accessToken?: string;
  targetId: string;
  targetType: "auction" | "deal";
};

const reportReasons = [
  { label: "가격 정보 오류", value: "wrong_price" },
  { label: "종료된 정보", value: "expired" },
  { label: "의심 링크", value: "fraud" },
  { label: "중복 제보", value: "duplicate" },
  { label: "기타", value: "other" }
];

export function OfferReportForm({ accessToken, targetId, targetType }: OfferReportFormProps) {
  const [reasonCode, setReasonCode] = useState(reportReasons[0].value);
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function submitReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setMessage(null);
    setErrorMessage(null);
    try {
      if (targetType === "deal") {
        await reportDeal({ accessToken, dealId: targetId, description, reasonCode });
      } else {
        await reportAuction({ accessToken, auctionId: targetId, description, reasonCode });
      }
      setDescription("");
      setMessage("신고가 접수되었습니다.");
    } catch (error) {
      setErrorMessage(
        error instanceof DetailApiError ? error.message : "신고 접수에 실패했습니다."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      aria-label="신고 제출"
      className="rounded-md border border-black/10 bg-white p-4"
      onSubmit={submitReport}
    >
      <h2 className="text-base font-bold">신고</h2>
      <div className="mt-4 grid gap-3">
        <label className="grid gap-1 text-sm font-semibold">
          신고 사유
          <select
            className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
            disabled={!accessToken || isSubmitting}
            onChange={(event) => setReasonCode(event.target.value)}
            value={reasonCode}
          >
            {reportReasons.map((reason) => (
              <option key={reason.value} value={reason.value}>
                {reason.label}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm font-semibold">
          신고 설명
          <textarea
            className="min-h-24 rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
            disabled={!accessToken || isSubmitting}
            maxLength={2000}
            onChange={(event) => setDescription(event.target.value)}
            value={description}
          />
        </label>
        {!accessToken ? (
          <p className="text-sm text-black/60">로그인 후 신고할 수 있습니다.</p>
        ) : null}
        {message ? <p className="text-sm font-semibold text-signal">{message}</p> : null}
        {errorMessage ? <p className="text-sm font-semibold text-deal">{errorMessage}</p> : null}
        <button
          className="w-fit rounded bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-black disabled:cursor-not-allowed disabled:bg-black/40"
          disabled={!accessToken || isSubmitting}
          type="submit"
        >
          {isSubmitting ? "제출 중" : "신고 제출"}
        </button>
      </div>
    </form>
  );
}
