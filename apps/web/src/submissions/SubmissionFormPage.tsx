"use client";

import Link from "next/link";
import React, { FormEvent, useState } from "react";

import { AuthStatus } from "../auth/AuthStatus";
import { useAuthSession } from "../auth/useAuthSession";

import { createSubmission, SubmissionApiError } from "./api";
import type { SubmissionCreateInput } from "./types";

const initialInput: SubmissionCreateInput = {
  brand: "",
  category: "",
  currentPrice: "",
  description: "",
  modelName: "",
  offerType: "deal",
  originalPrice: "",
  productName: "",
  salePrice: "",
  seller: "",
  sourceUrl: "",
  title: ""
};

export function SubmissionFormPage() {
  const authSession = useAuthSession();
  const accessToken =
    authSession.status === "authenticated" ? authSession.accessToken : undefined;
  const [input, setInput] = useState<SubmissionCreateInput>(initialInput);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || isSubmitting) {
      return;
    }
    setIsSubmitting(true);
    setMessage(null);
    setErrorMessage(null);
    try {
      const submission = await createSubmission({ accessToken, input });
      setMessage(`제보가 접수되었습니다. 상태: ${submission.status}`);
      setInput(initialInput);
    } catch (error) {
      setErrorMessage(
        error instanceof SubmissionApiError ? error.message : "제보 접수에 실패했습니다."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="border-b border-black/10 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <Link href="/">
            <div className="text-xl font-bold">DealMoa</div>
            <p className="text-xs font-semibold text-signal">사용자 제보</p>
          </Link>
          <AuthStatus />
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-5 py-8">
        <h1 className="text-3xl font-bold">핫딜/경매 제보</h1>
        <p className="mt-2 text-sm leading-6 text-black/65">
          제보는 AI mock 검토 후 관리자 승인 전까지 공개되지 않습니다.
        </p>

        {authSession.status === "loading" ? (
          <p className="mt-6 rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
            로그인 상태 확인 중
          </p>
        ) : null}
        {authSession.status === "anonymous" ? (
          <p className="mt-6 rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
            로그인 후 제보할 수 있습니다.
          </p>
        ) : null}

        <form className="mt-6 grid gap-4 rounded-md border border-black/10 bg-white p-5" onSubmit={submit}>
          <fieldset className="flex flex-wrap gap-2">
            <legend className="sr-only">제보 유형</legend>
            {(["deal", "auction"] as const).map((offerType) => (
              <label
                className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-semibold"
                key={offerType}
              >
                <input
                  className="mr-2"
                  checked={input.offerType === offerType}
                  disabled={!accessToken || isSubmitting}
                  onChange={() => setInput((current) => ({ ...current, offerType }))}
                  type="radio"
                />
                {offerType === "deal" ? "핫딜" : "경매"}
              </label>
            ))}
          </fieldset>

          <FormInput input={input} name="sourceUrl" setInput={setInput} title="원문 URL" />
          <FormInput input={input} name="productName" setInput={setInput} title="상품명" />
          <div className="grid gap-4 sm:grid-cols-3">
            <FormInput input={input} name="brand" setInput={setInput} title="브랜드" />
            <FormInput input={input} name="modelName" setInput={setInput} title="모델명" />
            <FormInput input={input} name="category" setInput={setInput} title="카테고리" />
          </div>
          <FormInput input={input} name="title" setInput={setInput} title="제보 제목" />
          <FormInput input={input} name="seller" setInput={setInput} title="판매처" />
          <div className="grid gap-4 sm:grid-cols-2">
            <FormInput input={input} name="originalPrice" setInput={setInput} title="정가" type="number" />
            {input.offerType === "deal" ? (
              <FormInput input={input} name="salePrice" setInput={setInput} title="핫딜가" type="number" />
            ) : (
              <FormInput input={input} name="currentPrice" setInput={setInput} title="현재 경매가" type="number" />
            )}
          </div>
          <label className="grid gap-1 text-sm font-semibold">
            설명
            <textarea
              className="min-h-24 rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
              disabled={!accessToken || isSubmitting}
              onChange={(event) =>
                setInput((current) => ({ ...current, description: event.target.value }))
              }
              value={input.description}
            />
          </label>
          {message ? <p className="text-sm font-semibold text-signal">{message}</p> : null}
          {errorMessage ? <p className="text-sm font-semibold text-deal">{errorMessage}</p> : null}
          <button
            className="w-fit rounded bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-black disabled:cursor-not-allowed disabled:bg-black/40"
            disabled={!accessToken || isSubmitting}
            type="submit"
          >
            {isSubmitting ? "접수 중" : "제보 제출"}
          </button>
        </form>
      </section>
    </main>
  );
}

function FormInput({
  input,
  name,
  setInput,
  title,
  type = "text"
}: {
  input: SubmissionCreateInput;
  name: keyof SubmissionCreateInput;
  setInput: React.Dispatch<React.SetStateAction<SubmissionCreateInput>>;
  title: string;
  type?: "number" | "text";
}) {
  return (
    <label className="grid gap-1 text-sm font-semibold">
      {title}
      <input
        className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
        onChange={(event) => setInput((current) => ({ ...current, [name]: event.target.value }))}
        type={type}
        value={input[name]}
      />
    </label>
  );
}
